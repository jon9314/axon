# Axon Development Roadmap: Phase 1 – Core Scaffold

This document breaks down **Phase 1** of Axon into detailed engineering tasks. Each item includes goals, file-level responsibilities, dependencies, configuration, and validation steps.

---

## 📦 Phase 1 Overview – MVP Core

Goal: Create the foundation of a local-first, memory-capable, MCP-aware AI agent.

---

### 1.1 – Project Bootstrap & Config System

**Description:** Sets up CLI parser, environment variable loading, and YAML-based config layer.

**File(s):**

- `main.py`
- `config/settings.yaml`
- `.env` + `.env.example`
- `agent/config_loader.py`

**Dependencies:**

- `python-dotenv`
- `PyYAML`

**Settings/Config:**

```yaml
project_name: axon
startup_mode: cli  # or 'web' or 'headless'
memory:
  engine: postgres
  vector: qdrant
```

**Validation:**

- Run `python main.py --cli` → CLI starts cleanly
- Print loaded config to stdout for sanity check

**Status:** TODO

**Optional Enhancements:**

- Add schema validation for `settings.yaml`

---

### 1.2 – CLI, Web, and Headless Startup Modes

**Description:** Enables launching Axon in 3 modes via CLI.

**File(s):**

- `main.py`

**Dependencies:**

- `argparse`
- `uvicorn` (for web mode)

**Validation:**

- `python main.py --cli`
- `python main.py --web`
- `python main.py --headless`

**Status:** TODO

**Optional:**

- Implement TUI CLI using the Textual library

---

### 1.3 – Memory Handler: Structured Memory (PostgreSQL)

**Description:** Enables storing and retrieving structured memory entries (facts, user info, goals).

**File(s):**

- `memory/memory_handler.py`

**Dependencies:**

- `asyncpg` or `psycopg2`
- Postgres service in Docker

**Settings:**

```yaml
postgres:
  host: db
  port: 5432
  database: axon
  user: axon
  password: axonpass
```

**Validation:**

- Insert + retrieve a sample fact via CLI call

**Status:** TODO

**Optional Enhancements:**

- Add scoped memory per chat/thread
- Add `locked: true` flag

---

### 1.4 – Vector Store Integration (Qdrant)

**Description:** Enables semantic memory search with Qdrant.

**File(s):**

- `memory/vector_store.py`

**Dependencies:**

- `qdrant-client`
- Qdrant service in Docker

**Settings:**

```yaml
qdrant:
  host: qdrant
  port: 6333
  collection: axon_memory
```

**Validation:**

- Embed text → store → retrieve top-N vector hits

**Status:** TODO

**Optional:**

- Add hybrid scoring (recency + similarity) and expose a confidence metric in `LLMRouter`

---

### 1.5 – LLM Routing (Local-First)

**Description:** Directs queries to local models via Ollama. Suggests cloud prompt when needed.

**File(s):**

- `agent/llm_router.py`

**Dependencies:**

- Ollama running locally

**Behavior:**

- Tries: DeepSeek → Qwen → Mistral
- If fails: Suggests Claude/GPT with prompt + pasteback wait

**Validation:**

- Confirm local model used unless flagged
- Paste Claude result and store reply in memory

**Status:** TODO

**Optional:**

- Add model confidence scoring to route smarter later

---

### 1.6 – MCP Handler: Internal Protocol Support

**Description:** Supports MCP-wrapped messages for input/output, enabling future server interop.

**File(s):**

- `agent/mcp_handler.py`

**Responsibilities:**

- Parse incoming messages into: sender, intent, domain, timestamp, content
- Convert internal memory into MCP format

**Validation:**

- Load and format a test payload with MCP fields

**Status:** TODO

**Optional:**

- Introduce `mcp_mode` option in `settings.yaml`
- Log all MCP-formatted traffic to a JSON file

---

### 1.7 – Preloaded Memory

**Description:** Load sample facts and MCP-wrapped entries for testing.

**File(s):**

- `memory/preload.py`
- `data/initial_memory.yaml`

**Content:**

- Fact: “Jonathan enjoys black coffee.”
- MCP note: “Remind me to insulate the attic.”

**Validation:**

- Preloads appear in memory viewer and retrieval tests

**Status:** TODO

**Optional:**

- Extend preload entries for identity or domain-specific facts

---

### 1.8 – FastAPI Backend Scaffold

**Description:** REST and WebSocket API for chat and memory access.

**File(s):**

- `backend/api.py`

**Endpoints:**

- `POST /chat`
- `GET /memory`
- `WS /stream`

**Status:** TODO

**Optional:**

- Implement rate limiting
- Optional authentication hooks

---

### 1.9 – React Frontend Scaffold

**Description:** Basic UI with split-pane: chat + memory threads

**File(s):**

- `frontend/`

**Stack:**

- React + Vite + shadcn/ui

**Status:** TODO

**Optional:**

- Memory editing panel
- Model selector dropdown in the UI

---

### 1.10 – Docker Compose Stack

**Description:** Container setup for full system

**File(s):**

- `docker-compose.yml`

**Services:**

- `axon-backend`
- `axon-frontend`
- `qdrant`
- `postgres`

**Validation:**

- `docker compose up --build` brings up all services

**Status:** TODO

---

### 1.11 – CI / Formatting Hooks

**Description:** Lint/type-check automation with GitHub Actions

**File(s):**

- `.github/workflows/ci.yml`

**Tools:**

- `ruff`
- `mypy`

**Status:** TODO

---

## ✅ Phase 1 Completion Criteria

- CLI, Web, and Headless modes operational
- Local LLM responding via Ollama
- Memory system functional (both structured + vector)
- MCP-ready messages parsed and displayed
- Preloaded content appears in memory
- UI loads with React + FastAPI working end-to-end

---

Next: Phase 2 – Scoped Memory, Plugin Loader, Goal Tracker

