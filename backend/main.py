# axon/backend/main.py

import io
import json
import logging
import re
import time
from typing import cast

import qrcode
import redis.asyncio as redis
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from starlette.middleware.base import BaseHTTPMiddleware

from agent.doc_source_tracker import DocSourceTracker
from agent.github_auto_commit import GitHubAutoCommit
from agent.goal_tracker import GoalTracker
from agent.llm_router import LLMRouter
from agent.mcp_handler import MCPHandler
from agent.mcp_metrics import MCPMetrics
from agent.mcp_router import mcp_router
from agent.notifier import Notifier
from agent.pasteback_handler import PastebackHandler
from agent.plugin_loader import AVAILABLE_PLUGINS, load_plugins
from agent.reminder import MemoryLike, ReminderManager
from agent.session_tracker import SessionTracker
from axon.config.settings import settings
from axon.utils.health import check_service, service_status
from memory.markdown_sync import MarkdownQdrantSync
from memory.memory_handler import MemoryHandler
from memory.preload import preload
from memory.speaker_embedding import SpeakerEmbeddingManager
from memory.user_profile import UserProfileManager

# --- NEW: Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# NOTE: check external services and record availability
if settings.database.postgres_uri:
    service_status.postgres = check_service(settings.database.postgres_uri)
    if not service_status.postgres:
        logging.warning("Postgres unreachable—goal tracking disabled.")
if settings.database.qdrant_host:
    q_url = f"tcp://{settings.database.qdrant_host}:{settings.database.qdrant_port}"
    service_status.qdrant = check_service(q_url)
    if not service_status.qdrant:
        logging.warning("Qdrant unreachable—vector search disabled.")
if settings.database.redis_url:
    service_status.redis = check_service(settings.database.redis_url)
    if not service_status.redis:
        logging.warning("Redis unreachable—fallback to memory store.")


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter and optional token auth."""

    def __init__(self, app: FastAPI, limit: int, token: str | None) -> None:
        super().__init__(app)
        self.limit = limit
        self.token = token
        self.calls: dict[str, list[float]] = {}
        self.redis = None
        if service_status.redis and settings.database.redis_url:
            try:
                self.redis = redis.from_url(settings.database.redis_url)
            except Exception as exc:  # pragma: no cover - optional Redis
                logging.warning("Redis init error: %s", exc)

    async def dispatch(self, request: Request, call_next):
        if self.token and request.headers.get("X-API-Token") != self.token:
            return Response(status_code=401)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        if self.redis:
            key = f"rate:{client_ip}"
            try:
                await self.redis.zremrangebyscore(key, 0, now - 60)
                count = await self.redis.zcard(key)
                if count >= self.limit:
                    return Response(status_code=429)
                await self.redis.zadd(key, {now: now})
                await self.redis.expire(key, 60)
            except Exception as exc:  # pragma: no cover - optional Redis
                logging.warning("Redis error: %s", exc)
                self.redis = None
                history = self.calls.setdefault(client_ip, [])
                history = [t for t in history if now - t < 60]
                if len(history) >= self.limit:
                    return Response(status_code=429)
                history.append(now)
                self.calls[client_ip] = history
        else:
            history = self.calls.setdefault(client_ip, [])
            history = [t for t in history if now - t < 60]
            if len(history) >= self.limit:
                return Response(status_code=429)
            history.append(now)
            self.calls[client_ip] = history
        return await call_next(request)


def log_traffic(entry: dict) -> None:
    """Append traffic data to the MCP log if enabled."""
    if not settings.app.mcp_mode:
        return
    try:
        with open(settings.app.mcp_log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as exc:  # pragma: no cover - best effort logging
        logging.error("Failed to log MCP traffic: %s", exc)


# Create a FastAPI application instance
app = FastAPI(
    title="Axon Backend",
    description="The backend service for the Axon project, handling API requests and WebSocket connections.",
    version="0.1.0",
)
app.add_middleware(
    RateLimiterMiddleware,
    limit=settings.app.rate_limit_per_minute,
    token=settings.app.api_token,
)

# Instantiate the handlers
memory_handler = MemoryHandler()
goal_tracker = GoalTracker(
    db_uri=settings.database.postgres_uri if service_status.postgres else None,
    notifier=Notifier(),
)
llm_router = LLMRouter()
mcp_handler = MCPHandler()
pasteback_handler = PastebackHandler(memory_handler)
profile_manager = UserProfileManager()
reminder_manager = ReminderManager(Notifier(), cast(MemoryLike, memory_handler))
session_tracker = SessionTracker()
speaker_manager = SpeakerEmbeddingManager()
mcp_metrics = MCPMetrics()
doc_tracker = DocSourceTracker()
github_auto_commit = GitHubAutoCommit(mcp_router=mcp_router)
markdown_sync = MarkdownQdrantSync()


@app.on_event("startup")
def startup_event() -> None:
    preload(memory_handler)
    load_plugins()
    logging.info(f"Plugins loaded: {list(AVAILABLE_PLUGINS.keys())}")
    goal_tracker.start_deferred_prompting("default_thread", interval_seconds=3600)


@app.on_event("shutdown")
def shutdown_event():
    memory_handler.close_connection()
    goal_tracker.stop_deferred_prompting()
    logging.info("Application shutdown: Database connection closed.")


@app.get("/")
async def read_root():
    return {"message": "Axon backend is running and connected to memory."}


@app.get("/mcp/tools")
async def list_mcp_tools():
    tools = {}
    for name in mcp_router.list_tools():
        tools[name] = {"available": mcp_router.check_tool(name)}
    return {"tools": tools}


@app.get("/models")
async def list_models():
    """Return available local models."""
    return {"models": [settings.llm.default_local_model, "z-ai/glm-4.5-air:free"]}


@app.post("/sessions/login")
async def login(identity: str, thread_id: str | None = None):
    """Create a new session for the given identity."""
    token, tid = session_tracker.create_session(identity, thread_id)
    return {"token": token, "thread_id": tid, "identity": identity}


@app.get("/sessions/qr/{token}")
async def session_qr(token: str):
    """Return a QR code image for a session token."""
    img = qrcode.make(token)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/sessions/{token}/memory")
async def session_memory(token: str, tag: str | None = None, domain: str | None = None):
    """List memory facts for the session associated with the token."""
    session = session_tracker.resolve(token)
    if not session:
        raise HTTPException(status_code=404, detail="invalid token")
    identity, thread_id = session
    facts = memory_handler.list_facts(thread_id, tag, domain)
    return {
        "identity": identity,
        "thread_id": thread_id,
        "facts": [
            {
                "key": key,
                "value": val,
                "identity": ident,
                "locked": locked,
                "tags": tags,
            }
            for key, val, ident, locked, tags in facts
        ],
    }


@app.get("/memory/{thread_id}")
async def list_memory(thread_id: str, tag: str | None = None, domain: str | None = None):
    facts = memory_handler.list_facts(thread_id, tag, domain)
    return {
        "facts": [
            {
                "key": key,
                "value": val,
                "identity": ident,
                "locked": locked,
                "tags": tags,
            }
            for key, val, ident, locked, tags in facts
        ]
    }


@app.post("/memory/{thread_id}")
async def add_memory(
    thread_id: str,
    key: str,
    value: str,
    identity: str | None = None,
    tags: str | None = None,
    domain: str | None = None,
):
    tag_list = [t for t in tags.split(",") if t] if tags else None
    memory_handler.add_fact(thread_id, key, value, identity, domain=domain, tags=tag_list)
    return {"status": "ok"}


@app.put("/memory/{thread_id}")
async def update_memory(
    thread_id: str,
    key: str,
    value: str,
    identity: str | None = None,
    tags: str | None = None,
    domain: str | None = None,
):
    tag_list = [t for t in tags.split(",") if t] if tags else None
    memory_handler.update_fact(thread_id, key, value, identity, domain=domain, tags=tag_list)
    return {"status": "ok"}


@app.delete("/memory/{thread_id}/{key}")
async def delete_memory(thread_id: str, key: str):
    deleted = memory_handler.delete_fact(thread_id, key)
    return {"deleted": deleted}


@app.delete("/memory/{thread_id}")
async def delete_memory_bulk(thread_id: str, domain: str | None = None, tag: str | None = None):
    """Delete multiple facts by thread, optionally filtered."""
    deleted = memory_handler.delete_facts(thread_id, domain=domain, tag=tag)
    return {"deleted": deleted}


@app.post("/memory/{thread_id}/{key}/lock")
async def lock_memory(thread_id: str, key: str, locked: bool = True):
    changed = memory_handler.set_lock(thread_id, key, locked)
    return {"locked": changed}


@app.get("/domains/{thread_id}")
async def list_domains(thread_id: str):
    """List all unique domains used in a thread."""
    facts = memory_handler.list_facts(thread_id)
    domains = set()
    for _, _, _, _, tags in facts:
        # Extract domain from tags if present
        for tag in tags:
            if tag.startswith("domain:"):
                domains.add(tag.split(":", 1)[1])
    # Also check the scope field via repository
    all_records = memory_handler.repo.store.search("", scope=thread_id)
    for rec in all_records:
        if hasattr(rec, "scope") and rec.scope and rec.scope != thread_id:
            domains.add(rec.scope)
    return {"domains": sorted(domains)}


@app.get("/domains/{thread_id}/stats")
async def domain_stats(thread_id: str):
    """Get statistics per domain for a thread."""
    from collections import defaultdict

    stats: dict[str, int] = defaultdict(int)
    all_records = memory_handler.repo.store.search("")

    for rec in all_records:
        scope = getattr(rec, "scope", None)
        if scope:
            stats[scope] += 1

    return {
        "domains": [{"name": domain, "count": count} for domain, count in sorted(stats.items())]
    }


@app.post("/reminders/{thread_id}")
async def add_reminder(thread_id: str, message: str, delay: int = 60):
    key = reminder_manager.schedule(message, delay, thread_id)
    return {"key": key}


@app.get("/reminders/{thread_id}")
async def list_reminders(thread_id: str):
    reminders = reminder_manager.list_reminders(thread_id)
    return {"reminders": reminders}


@app.delete("/reminders/{thread_id}/{key}")
async def delete_reminder(thread_id: str, key: str):
    deleted = reminder_manager.delete_reminder(thread_id, key)
    return {"deleted": deleted}


@app.post("/goals/{thread_id}")
async def add_goal(thread_id: str, text: str, identity: str | None = None):
    goal_tracker.add_goal(thread_id, text, identity)
    return {"status": "ok"}


@app.get("/goals/{thread_id}")
async def list_goals(thread_id: str):
    goals = goal_tracker.list_goals(thread_id)
    return {
        "goals": [
            {
                "id": g_id,
                "text": text,
                "completed": done,
                "identity": ident,
                "deferred": deferred,
                "priority": priority,
                "deadline": deadline,
            }
            for g_id, text, done, ident, deferred, priority, deadline in goals
        ]
    }


@app.get("/goals/{thread_id}/deferred")
async def list_deferred(thread_id: str):
    goals = goal_tracker.list_deferred_goals(thread_id)
    return {
        "goals": [
            {
                "id": g_id,
                "text": text,
                "completed": done,
                "identity": ident,
                "deferred": deferred,
                "priority": priority,
                "deadline": deadline,
            }
            for g_id, text, done, ident, deferred, priority, deadline in goals
        ]
    }


@app.delete("/goals/{thread_id}")
async def delete_goals(thread_id: str):
    """Delete all goals for a thread."""
    deleted = goal_tracker.delete_goals(thread_id)
    return {"deleted": deleted}


@app.get("/profiles/{identity}")
async def get_profile(identity: str):
    profile = profile_manager.get_profile(identity)
    return profile or {}


@app.post("/profiles/{identity}")
async def set_profile(
    identity: str,
    persona: str = "assistant",
    tone: str = "neutral",
    email: str | None = None,
):
    profile_manager.set_profile(identity, persona=persona, tone=tone, email=email)
    return {"status": "ok"}


@app.get("/plugins")
async def list_plugins():
    """List all loaded plugins with their permissions and status."""
    from axon.plugins.loader import PluginLoader

    loader = PluginLoader()
    loader.discover()

    plugins_info = []
    for _name, manifest in loader.manifests.items():
        plugins_info.append(
            {
                "name": manifest.name,
                "version": manifest.version,
                "description": manifest.description,
                "permissions": [p.value for p in manifest.permissions],
                "entrypoint": manifest.entrypoint,
            }
        )
    return {"plugins": plugins_info}


@app.get("/plugins/{name}")
async def get_plugin_info(name: str):
    """Get detailed information about a specific plugin."""
    from axon.plugins.loader import PluginLoader

    loader = PluginLoader()
    loader.discover()

    if name not in loader.manifests:
        raise HTTPException(status_code=404, detail="Plugin not found")

    manifest = loader.manifests[name]
    plugin = loader.plugins.get(name)

    info = {
        "name": manifest.name,
        "version": manifest.version,
        "description": manifest.description,
        "permissions": [p.value for p in manifest.permissions],
        "entrypoint": manifest.entrypoint,
        "config_schema": manifest.config_schema,
        "loaded": plugin is not None,
    }

    if plugin:
        info["description_details"] = plugin.describe()  # type: ignore[assignment]

    return info


@app.post("/plugins/{name}/execute")
async def execute_plugin(name: str, data: dict):
    """Execute a plugin with given data."""
    from axon.plugins.loader import PluginLoader

    loader = PluginLoader()
    loader.discover()

    if name not in loader.plugins:
        raise HTTPException(status_code=404, detail="Plugin not found or not loaded")

    try:
        result = loader.execute(name, data)
        return {"status": "success", "result": result}
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/speakers/register")
async def register_speaker(identity: str, audio_data: str):
    """Register a speaker voice profile.

    Args:
        identity: Speaker identity
        audio_data: Base64-encoded audio data
    """
    import base64

    try:
        audio_bytes = base64.b64decode(audio_data)
        profile = speaker_manager.register_speaker(identity, audio_bytes)
        return {
            "status": "success",
            "identity": profile.identity,
            "num_samples": profile.num_samples,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/speakers/identify")
async def identify_speaker(audio_data: str, threshold: float = 0.7):
    """Identify a speaker from audio sample.

    Args:
        audio_data: Base64-encoded audio data
        threshold: Minimum similarity threshold (0.0 to 1.0)
    """
    import base64

    try:
        audio_bytes = base64.b64decode(audio_data)
        identity, confidence = speaker_manager.identify_speaker(audio_bytes, threshold)
        return {"identity": identity, "confidence": confidence}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/speakers")
async def list_speakers():
    """List all registered speakers."""
    speakers = speaker_manager.list_speakers()
    return {"speakers": speakers}


@app.delete("/speakers/{identity}")
async def delete_speaker(identity: str):
    """Remove a speaker profile."""
    removed = speaker_manager.remove_speaker(identity)
    if not removed:
        raise HTTPException(status_code=404, detail="Speaker not found")
    return {"status": "success", "identity": identity}


@app.get("/mcp/metrics")
async def get_mcp_metrics():
    """Get MCP server performance metrics."""
    return mcp_metrics.get_all_servers_stats()


@app.get("/mcp/metrics/{server_name}")
async def get_server_metrics(server_name: str):
    """Get metrics for a specific MCP server."""
    stats = mcp_metrics.get_server_stats(server_name)
    if stats.get("total_calls", 0) == 0:
        raise HTTPException(status_code=404, detail="Server not found or no metrics")
    return stats


@app.get("/mcp/health")
async def get_mcp_health():
    """Get overall MCP health summary."""
    return mcp_metrics.get_health_summary()


@app.post("/mcp/metrics/export")
async def export_mcp_metrics(output_path: str = "data/mcp_metrics_report.md"):
    """Export MCP metrics as markdown report."""
    mcp_metrics.export_metrics_report(output_path)
    return {"status": "success", "path": output_path}


@app.get("/docs/sources")
async def list_doc_sources(category: str | None = None):
    """List tracked documentation sources."""
    sources = doc_tracker.list_sources(category=category)
    return {"sources": sources}


@app.post("/docs/sources/track")
async def track_doc_source(
    url: str, title: str | None = None, category: str | None = None, metadata: dict | None = None
):
    """Track a documentation source URL."""
    doc_tracker.track_source(url, title, category, metadata)
    return {"status": "success", "url": url}


@app.get("/docs/sources/stats")
async def get_doc_stats():
    """Get documentation source statistics."""
    return doc_tracker.get_statistics()


@app.get("/docs/sources/chart/{chart_type}")
async def get_doc_chart(chart_type: str, limit: int = 10):
    """Get chart data for documentation sources."""
    return doc_tracker.generate_chart_data(chart_type, limit)


@app.post("/docs/sources/export")
async def export_doc_report(output_path: str = "data/doc_sources_report.md"):
    """Export documentation sources as markdown report."""
    doc_tracker.export_markdown_report(output_path)
    return {"status": "success", "path": output_path}


@app.post("/markdown/sync/to-qdrant")
async def sync_markdown_to_qdrant(note_name: str | None = None):
    """Sync markdown notes to Qdrant vector store."""
    count = markdown_sync.sync_markdown_to_qdrant(note_name)
    return {"status": "success", "synced_count": count}


@app.post("/markdown/sync/to-markdown")
async def sync_qdrant_to_markdown(identity: str | None = None):
    """Sync Qdrant vectors to markdown files."""
    count = markdown_sync.sync_qdrant_to_markdown(identity)
    return {"status": "success", "exported_count": count}


@app.get("/markdown/sync/status")
async def get_sync_status():
    """Get markdown-Qdrant sync status."""
    return markdown_sync.get_sync_status()


@app.post("/markdown/sync/auto")
async def auto_sync_markdown():
    """Automatically sync in both directions."""
    return markdown_sync.auto_sync()


@app.get("/markdown/search")
async def search_markdown_notes(query: str, limit: int = 5):
    """Search markdown notes semantically."""
    results = markdown_sync.search_notes(query, limit)
    return {"query": query, "results": results}


@app.post("/github/auto-commit")
async def create_auto_commit(files: list[str], message: str, branch: str | None = None):
    """Auto-commit files via GitHub MCP."""
    result = github_auto_commit.create_patch(files, message, branch)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@app.post("/github/commit-diff")
async def commit_current_diff(message: str, auto_stage: bool = True):
    """Commit current diff via GitHub MCP."""
    result = github_auto_commit.create_patch_from_diff(message, auto_stage)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


@app.post("/github/auto-commit-memory")
async def auto_commit_memory(frequency: str = "daily"):
    """Auto-commit memory store changes."""
    result = github_auto_commit.auto_commit_memory_changes(frequency=frequency)
    return result


@app.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    identity: str = "default_user",
    session_token: str | None = None,
):
    await websocket.accept()
    if session_token:
        resolved = session_tracker.resolve(session_token)
        if resolved:
            identity, thread_id = resolved
        else:
            session_token, thread_id = session_tracker.create_session(identity)
    else:
        session_token, thread_id = session_tracker.create_session(identity)
    await websocket.send_json({"type": "session", "token": session_token})
    logging.info(f"Client connected to WebSocket for thread_id: {thread_id} as {identity}")

    try:
        while True:
            raw = await websocket.receive_text()
            logging.info(f"Received message: '{raw}'")
            log_traffic({"direction": "in", "timestamp": time.time(), "data": raw})

            selected_model = settings.llm.default_local_model
            data = raw
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict) and "text" in parsed:
                    data = parsed["text"]
                    selected_model = parsed.get("model", selected_model)
            except json.JSONDecodeError:
                pass

            # Automatically log goal-related messages
            goal_tracker.detect_and_add_goal(thread_id, data, identity=identity)

            response_message = ""
            remember_match = re.match(r"remember (.*) is (.*)", data, re.IGNORECASE)

            mcp_data = None
            try:
                mcp_data = json.loads(data)
            except Exception:
                pass

            if isinstance(mcp_data, dict) and mcp_data.get("type") == "pasteback":
                pasteback_handler.store(
                    thread_id,
                    mcp_data.get("prompt", ""),
                    mcp_data.get("response", ""),
                    mcp_data.get("model", "gpt"),
                )
                response_message = "Pasteback stored."
            elif isinstance(mcp_data, dict) and mcp_handler.parse_message(mcp_data):
                try:
                    result = mcp_handler.handle_message(mcp_data)
                    response_message = json.dumps(result["output"])
                    ts = int(time.time())
                    memory_handler.add_fact(
                        thread_id,
                        f"{result['source']}_{ts}",
                        result["summary"],
                        identity=result["source"],
                        tags=[
                            f"source:{result['source']}",
                            f"confidence:{result['confidence']:.2f}",
                        ],
                    )
                except Exception as e:
                    response_message = f"MCP error: {e}"
            elif remember_match:
                key = remember_match.group(1).strip()
                value = remember_match.group(2).strip()
                memory_handler.add_fact(thread_id, key, value)
                response_message = f"OK, I'll remember that {key} is {value}."

            elif "what is" in data.lower():
                key_match = re.search(r"what is (.*)\?", data, re.IGNORECASE)
                key = (
                    key_match.group(1).strip()
                    if key_match
                    else data.lower().replace("what is", "").strip()
                )
                fact = memory_handler.get_fact(thread_id, key)
                if fact:
                    response_message = f"You told me that {key} is {fact}."
                else:
                    response_message = f"I don't have a memory for '{key}'."
            else:
                logging.info("No command recognized. Routing to LLM.")
                profile = profile_manager.get_profile(identity)
                persona = profile.get("persona") if profile else None
                tone = profile.get("tone") if profile else None
                response_message = llm_router.get_response(
                    data,
                    model=selected_model,
                    persona=persona,
                    tone=tone,
                )

            logging.info(f"Sending response: '{response_message}'")
            log_traffic({"direction": "out", "timestamp": time.time(), "data": response_message})
            await websocket.send_text(response_message)

    except WebSocketDisconnect:
        logging.info("Client disconnected.")
    except Exception:
        # --- NEW: Detailed Error Logging ---
        # This will print the full error traceback to your terminal
        logging.error("An error occurred in the WebSocket:", exc_info=True)
    finally:
        await websocket.close()
        logging.info("WebSocket connection closed.")
