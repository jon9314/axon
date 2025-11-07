# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Axon is a local-first AI agent with a **plugin architecture**, **memory capabilities**, and multiple interfaces (CLI, TUI, Web). The stack is:
- **Backend**: FastAPI (Python 3.11-3.13) with Qwen-Agent for tool-calling
- **Frontend**: React + TypeScript (Vite)
- **Databases**: PostgreSQL (goals), Qdrant (vectors), Redis (rate-limiting), JSON file (memory)
- **MCP Servers**: Microservices for specialized tools (filesystem, time, calculator, etc.)

## Build, Run, and Test Commands

### Development Setup

```bash
# Backend
poetry install                          # Install core dependencies
poetry install --with dev               # Include dev tools
poetry install --with calendar,postgres,vector,notify  # Optional features

# Frontend
cd frontend
npm install

# Pre-commit hooks
pre-commit install
git config core.hooksPath git-hooks     # Enforces commit message format
```

### Running the Application

```bash
# Backend (standalone)
python main.py web                      # Start FastAPI on localhost:8000

# Frontend (standalone)
cd frontend
npm run dev                             # Start Vite on localhost:5173

# Docker Compose (recommended for full stack)
cp .env.example .env
docker compose up --build               # Frontend: :3000, Backend: :8000

# MCP servers (if running manually)
python -m mcp_servers                   # Ports 9001-9008
```

### Testing and Linting

```bash
# Run all pre-commit hooks
pre-commit run --all-files              # Runs ruff, black, mypy, eslint, tsc, pytest

# Backend tests
pytest                                  # All tests
pytest -x -q                            # Stop on first failure, quiet
pytest tests/test_memory.py             # Single test file
pytest tests/test_memory.py::test_name  # Single test

# Backend linting
ruff check .                            # Lint
ruff check . --fix                      # Auto-fix
black .                                 # Format
mypy .                                  # Type check

# Frontend linting
cd frontend
npm run lint                            # ESLint
npm run type-check                      # TypeScript check
npm run build                           # Production build
```

### CLI Commands

```bash
python main.py cli                      # Interactive chat
python main.py tui                      # Text UI
python main.py plugins reload           # List/reload plugins
python main.py remember "key" "value"   # Add memory
python main.py remind "text" --delay 30 # Reminder in 30s
python main.py import-profiles config/user_prefs.yaml
python main.py set-profile jon --persona partner --tone informal
python main.py voice-shell              # Voice interface (optional deps)
python main.py settings-schema          # Export config JSON schema
```

## Architecture

### Backend Architecture (FastAPI)

**Entry point**: `backend/main.py` (980 lines)

**Service Initialization Pattern**: All handlers/managers are instantiated at module level as singletons and shared across requests:
- `MemoryHandler` - Memory CRUD with thread/identity scoping
- `GoalTracker` - PostgreSQL-backed goal tracking
- `LLMRouter` - Routes LLM requests to Qwen-Agent
- `MCPHandler` - MCP protocol message handling
- `ReminderManager` - Scheduled reminders
- `SessionTracker` - Session/auth tokens
- `UserProfileManager` - Persona/tone preferences
- Additional: `PastebackHandler`, `SpeakerEmbeddingManager`, `MCPMetrics`, `DocSourceTracker`, `GitHubAutoCommit`, `MarkdownQdrantSync`, `HostedProxyClient`, `NaturalDateParser`, `TTSNotificationService`

**Health Checking**: At startup, `check_service_health()` probes PostgreSQL, Qdrant, and Redis. Services track status in `service_status` dict for graceful degradation.

**Middleware**:
- `RateLimiterMiddleware` - Redis-backed or in-memory fallback
- Optional token authentication via `api_token` in settings

**API Endpoints** (grouped by domain):
- `/memory/*` - CRUD, lock/unlock, domain filtering
- `/sessions/*` - Login, QR codes, session tokens
- `/goals/*` - CRUD, deferred goals
- `/profiles/*` - User preferences
- `/plugins/*` - Discovery, info, execution
- `/reminders/*` - Schedule, list
- `/mcp/*` - Tool listing, health, metrics
- `/docs/*` - Documentation tracking
- `/markdown/*` - Markdown/Qdrant sync
- `/github/*` - Auto-commit
- `/proxy/*`, `/pasteback/*`, `/date/*`, `/tts/*` - Phase 4 cloud integration
- `/ws/chat` - WebSocket for real-time chat

**WebSocket Flow**:
```
Browser → /ws/chat → SessionTracker.resolve_session()
  → LLMRouter.get_response() → Qwen-Agent → MCP tools → Response
  → GoalTracker.detect_and_add_goal() → Send to client
```

### Frontend Architecture (React)

**Entry**: `frontend/src/main.tsx` → `App.tsx` (262 lines)

**Key Features**:
- WebSocket connection to `/ws/chat` with auto-reconnect
- Session token management (login, QR code)
- Dual interface: chat view + memory sidebar
- Memory CRUD with inline editing, lock toggle, tag management
- Model selection dropdown
- MCP quick action buttons
- Cloud model copy/paste workflow

**Deployment**: Production uses nginx (`frontend/nginx.conf`) to proxy `/api/*` and `/ws/*` to backend.

### Plugin System

**Location**: `axon/plugins/` (base, loader, manifest, permissions)

**Architecture**:
1. **Base Class** (`base.py`): `Plugin[InputT, OutputT]` with Pydantic models for type safety
2. **Discovery** (`loader.py`): Scans `plugins/*.py` + `*.yaml` pairs
3. **Manifest** (`manifest.py`): YAML metadata (name, version, permissions, config_schema)
4. **Execution**: `PluginLoader.execute(name, data)` validates I/O, enforces permissions, records metrics

**Lifecycle**:
```
discover() → load manifest → import module → instantiate plugin
  → plugin.load(config) → register with Qwen-Agent
  → execute(name, data) → validate input → plugin.execute()
  → validate output → audit log
```

**Permissions**: Enum-based (`NETWORK`, `FILESYSTEM`, etc.) with `guard()` enforcer and dry-run support.

**Creating Plugins**:
1. Create `plugins/my_plugin.py` with `Plugin[InputModel, OutputModel]` subclass
2. Create `plugins/my_plugin.yaml` with manifest
3. Implement `execute(data: InputModel) -> OutputModel`
4. Use `self.require(Permission.NETWORK)` before privileged ops

### MCP Servers (Model Context Protocol)

**Location**: `mcp_servers/` with launcher at `mcp_servers/__main__.py`

**Available Servers**:
- `filesystem_server` (9001) - File operations
- `time_server` (9002) - Timestamps, timezones
- `calculator_server` (9003) - Math evaluation
- `markdown_backup_server` (9004) - Note management
- `github_server` (9005) - Git operations
- `docs_server` (9006) - Docs fetching
- `query_server` (9007) - DB queries
- `wolframalpha_server` (9008) - Computational knowledge

**Integration**:
- Config: `config/mcp_servers.yaml` (name, transport, url)
- Router: `agent/mcp_router.py` (HTTP/stdio transports, health checking)
- Proxy tools: `agent/tools/*_proxy.py` integrate with Qwen-Agent
- Backend: `/mcp/*` endpoints, `MCPMetrics` for monitoring

### Memory System

**Storage Layers**:
1. **File**: `data/memory_store.json` via `axon/memory/json_store.py` (default)
2. **Vector**: Qdrant via `memory/vector_store.py` for semantic search
3. **Sync**: `memory/markdown_sync.py` for bidirectional markdown/vector sync

**Handler Layer**:
- `memory/memory_handler.py` - Thread/identity scoping wrapper
- `axon/memory/repository.py` - High-level CRUD API
- `axon/memory/models.py` - Pydantic models (`MemoryRecord`, `ProfileRecord`, `ReminderRecord`)

**MemoryRecord Structure**:
```python
{
  "id": str,
  "content": str,
  "tags": List[str],
  "scope": str,          # thread or domain
  "metadata": {
    "identity": str,
    "timestamp": str,    # via Time MCP
    ...
  },
  "locked": bool
}
```

### Configuration System

**Files**:
- `config/settings.yaml` - User config (auto-created from example, gitignored)
- `config/settings.example.yaml` - Template (committed)
- `config/user_prefs.yaml` - User profiles
- `config/mcp_servers.yaml` - MCP registry
- `.env` - Environment variables (database credentials, API keys)

**Config Priority** (high to low):
1. Environment variables (`AXON_*`)
2. `config/settings.yaml`
3. `config/settings.example.yaml`
4. Init settings
5. `.env` file
6. File secrets

**Nested Environment Variables**:
```bash
AXON_DATABASE__POSTGRES_URI=postgresql://...
AXON_LLM__DEFAULT_LOCAL_MODEL=qwen3:8b
```

**Code**: `axon/config/settings.py` - Pydantic-based validation, singleton pattern with `get_settings()` / `reload_settings()`.

### Database Stack

- **PostgreSQL**: Goals, deadlines (optional, graceful degradation)
- **Qdrant**: Vector embeddings for semantic search
- **Redis**: Rate limiting, sessions (optional, in-memory fallback)
- **JSON File**: Primary memory store (`data/memory_store.json`)

All external DBs have health checks and graceful fallback.

## Key Integration Points

**Frontend → Backend**:
```
nginx :3000 → /api/* → backend :8000 (REST)
            → /ws/*  → backend :8000 (WebSocket upgrade)
```

**Backend → MCP**:
```
Backend handler → MCPRouter.call(name, payload)
  → HTTP/stdio transport → MCP server :9001-9008
  → JSON response → Handler
```

**Backend → LLM**:
```
WebSocket msg → LLMRouter.get_response()
  → Qwen-Agent Assistant → Ollama/OpenRouter API
  → Tool calls via MCP → Persona/tone shaping → WebSocket response
```

**Plugin Integration**:
```
Agent/Backend → PluginLoader.discover() → plugins/*.{py,yaml}
  → Import and instantiate → Register with Qwen-Agent
  → Available for execution
```

**Memory Flow**:
```
API/WebSocket → MemoryHandler → MemoryRepository
  → JSONFileMemoryStore → data/memory_store.json
```

**Docker Compose Stack**:
```
frontend (nginx :3000)
  ↓
backend (uvicorn :8000)
  ↓
├── postgres :5432
├── qdrant :6333/6334
├── redis :6379
└── mcp_servers :9001-9008
```

## Development Conventions

### Commit Message Format

**Required**: Commits must end with an `AI-Change-Summary` block (enforced by `git-hooks/commit-msg`):
```
feat: add voice recognition plugin

AI-Change-Summary:
Files: plugins/voice_shell.py, plugins/voice_shell.yaml
Tests: pytest tests/test_voice_shell.py
Rationale: Enable voice-activated shell commands
```

### Pre-commit Hooks

Hooks run automatically before commit (if installed):
- `ruff` + `ruff-format` - Lint and format Python
- `black` - Format Python
- `mypy` - Type check Python
- `eslint` - Lint frontend
- `tsc` - Type check frontend
- `pytest -x -q` - Run tests (stop on first failure)

### Code Style

- **Python**: Line length 100, ruff rules `["E", "F", "I", "B", "UP"]`, ignore `["E501", "UP007"]`
- **TypeScript**: ESLint with react-hooks and react-refresh plugins

### Observability

**Location**: `axon/obs/`
- `logging_config.py` - Structured logging
- `tracer.py` - Execution tracing with context managers
- `records.py` - Trace record models

**Usage**:
```python
from axon.obs.tracer import run_tracer

with run_tracer("operation_name") as tracer:
    # Execution traced, metrics captured, errors logged
    ...
```

Plugin executions are auto-traced by `PluginLoader`.

## Important Notes

### Graceful Degradation
Services (PostgreSQL, Qdrant, Redis) are optional. Backend probes health at startup and continues without unavailable services:
- No Postgres → Goals disabled
- No Qdrant → Semantic search disabled
- No Redis → In-memory rate limiting

### Session Management
WebSocket connections require session tokens from `/sessions/login`. Sessions map to `(identity, thread_id)` for scoped memory access.

### Cloud Model Workflow (Phase 4)
When local LLM is inadequate:
1. Backend suggests cloud model (GPT-4o, Claude) with reason
2. UI displays prompt for copy
3. User runs in browser, pastes response
4. Submit via `/pasteback/submit` to store in memory

### Hot Reloading
Plugins are reloaded on each CLI launch. For web mode, use Docker volume mounts or restart backend after plugin changes.

### Optional Dependencies
Install feature groups as needed:
- `--with calendar` - icalendar support
- `--with postgres` - PostgreSQL (psycopg2-binary)
- `--with vector` - Qdrant client
- `--with notify` - Desktop notifications (plyer)

### Testing Strategy
- **Backend**: `tests/` - pytest with fixtures for handlers
- **Frontend**: Type checking (`tsc`) and linting (eslint) via pre-commit
- **Integration**: Docker Compose brings up full stack for manual testing
