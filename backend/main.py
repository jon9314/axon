# axon/backend/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, List
from memory.memory_handler import MemoryHandler
from memory.preload import preload
from config.settings import settings
from agent.llm_router import LLMRouter
from agent.goal_tracker import GoalTracker
from agent.plugin_loader import load_plugins, AVAILABLE_PLUGINS
from agent.mcp_handler import MCPHandler
from agent.mcp_router import mcp_router
from agent.pasteback_handler import PastebackHandler
from typing import cast

from agent.reminder import MemoryLike, ReminderManager
from agent.notifier import Notifier
from memory.user_profile import UserProfileManager
import json
import re
import logging
import time

# --- NEW: Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter and optional token auth."""

    def __init__(self, app: FastAPI, limit: int, token: str | None) -> None:
        super().__init__(app)
        self.limit = limit
        self.token = token
        self.calls: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        if self.token and request.headers.get("X-API-Token") != self.token:
            return Response(status_code=401)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
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
memory_handler = MemoryHandler(db_uri=settings.database.postgres_uri)
goal_tracker = GoalTracker(db_uri=settings.database.postgres_uri)
llm_router = LLMRouter()
mcp_handler = MCPHandler()
pasteback_handler = PastebackHandler(memory_handler)
profile_manager = UserProfileManager(db_uri=settings.database.postgres_uri)
reminder_manager = ReminderManager(Notifier(), cast(MemoryLike, memory_handler))


@app.on_event("startup")
def startup_event() -> None:
    preload(memory_handler)
    load_plugins()
    logging.info(f"Plugins loaded: {list(AVAILABLE_PLUGINS.keys())}")


@app.on_event("shutdown")
def shutdown_event():
    memory_handler.close_connection()
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
    return {"models": [settings.llm.default_local_model, "mock-model"]}


@app.get("/memory/{thread_id}")
async def list_memory(thread_id: str, tag: str | None = None):
    facts = memory_handler.list_facts(thread_id, tag)
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
):
    tag_list = [t for t in tags.split(",") if t] if tags else None
    memory_handler.add_fact(thread_id, key, value, identity, tags=tag_list)
    return {"status": "ok"}


@app.put("/memory/{thread_id}")
async def update_memory(
    thread_id: str,
    key: str,
    value: str,
    identity: str | None = None,
    tags: str | None = None,
):
    tag_list = [t for t in tags.split(",") if t] if tags else None
    memory_handler.update_fact(thread_id, key, value, identity, tags=tag_list)
    return {"status": "ok"}


@app.delete("/memory/{thread_id}/{key}")
async def delete_memory(thread_id: str, key: str):
    deleted = memory_handler.delete_fact(thread_id, key)
    return {"deleted": deleted}


@app.post("/memory/{thread_id}/{key}/lock")
async def lock_memory(thread_id: str, key: str, locked: bool = True):
    changed = memory_handler.set_lock(thread_id, key, locked)
    return {"locked": changed}


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
            }
            for g_id, text, done, ident, deferred in goals
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
            }
            for g_id, text, done, ident, deferred in goals
        ]
    }


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


@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    thread_id = "user_session_123"
    logging.info(f"Client connected to WebSocket for thread_id: {thread_id}")

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
            goal_tracker.detect_and_add_goal(thread_id, data, identity="default_user")

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
                identity = "default_user"
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
            log_traffic(
                {"direction": "out", "timestamp": time.time(), "data": response_message}
            )
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
