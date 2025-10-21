# Axon Roadmap: Development Phases for Local-First AI Agent

This roadmap outlines the development path for **Axon**, a modular, local-first AI agent with structured and semantic memory, plugin support, and Model Context Protocol (MCP) integration.

---

## ✅ Phase 0: Planning & Architecture Finalization (Complete)
- Define goals, LLM access policies, and agent behavior
- Decide on stack: Python, React, FastAPI, Postgres, Qdrant, Ollama
- Finalize config formats: YAML + .env
- Establish memory model: hybrid (PostgreSQL + Qdrant)
- Clarify plugin behavior, startup modes, and CLI/web/headless

---

## ✅ Phase 1: Core MVP Scaffold (Complete)
**Goal:** Local-only chat agent with working memory and UI

- [x] `main.py`: Bootloader with CLI, web, and headless modes
- [x] `settings.yaml` and `.env.example` scaffolds
- [x] `memory_handler.py`: PostgreSQL fact storage
- [x] `vector_store.py`: Qdrant connection with hybrid retrieval
- [x] `llm_router.py`: local model selector and fallback handler
- [x] `mcp_handler.py`: parse/generate MCP messages
- [x] Sample facts and MCP messages in memory
- [x] Frontend: React split-pane (chat + memory)
- [x] Backend: FastAPI API endpoints + WebSocket
- [x] Docker Compose: Postgres + Qdrant + backend + frontend
- [x] CI: GitHub Actions with mypy + ruff checks

### Phase 1 Enhancements (✅ Complete)
- [x] TUI-based CLI interface with agent integration and memory/goal display
- [x] Hybrid vector scoring and LLM confidence metrics
- [x] `mcp_mode` setting and JSON traffic logs
- [x] Domain-aware preload entries (personal, project, health, finance, learning)
- [x] Backend rate limiting and optional auth (with Redis fallback)
- [x] Model selector dropdown in the UI

---

## 🧠 Phase 2: Memory & Plugin Enrichment
**Goal:** Scoped memory, plugin loader, goal tracking

- [x] Memory scoping (per thread, per identity)
- [x] Edit/delete/lock memory entries
- [x] Plugin system with hot-reload + metadata config
- [x] Structured long-term goal tracking
- [x] Manual note tagging + identity recognition
- [x] Add support for CLI input memory injection

### Phase 2 Improvements (✅ Complete)
- [x] Domain scoping in memory tables and API (list domains, domain stats endpoints)
- [x] Mass deletion endpoints and CLI plugin reload
- [x] Permission scoping for plugins (runtime enforcement, deny list, API endpoints)
- [x] Goal priority and deadline fields
- [x] Periodic prompts for deferred goals
- [x] Optional speaker-embedding logic (voice recognition with embeddings)

---

## 🔌 Phase 3: MCP Server Integration
**Goal:** Axon connects to local MCP ecosystem

### Priority MCP Servers
- [x] **Filesystem**: browse, read, edit files
- [x] **Time**: get current timestamp for reminders
- [x] **Calculator**: offload math operations
- [x] **Basic Memory**: backup or markdown-based memory overlay

### Secondary MCP Targets
- [x] **GitHub MCP**: repo access and edits
- [x] **Context7 / DeepWiki / Docs**: documentation fetchers
- [x] **Text2SQL + Antvis**: structured querying and visualization *(basic CSV query server implemented)*
- [x] **WolframAlpha / Prolog / Logic MCPs** (optional advanced logic)

### Phase 3 Additions (✅ Complete)
- [x] Timestamp new memory entries via Time MCP (automatic with fallback)
- [x] Sync markdown notes with Qdrant (bidirectional with semantic search)
- [x] Auto-commit patches via GitHub tooling (feature branches, auto-stage)
- [x] Capture documentation source URLs and show charts (pie, bar, timeline)
- [x] Record MCP latency/failure metrics (health monitoring, percentiles, reports)

---

## ☁️ Phase 4: Remote Model & API Tooling (Optional)
**Goal:** Controlled cloud integration without automatic LLM calls

- [x] Claude/GPT model suggestion + prompt generation
- [x] UI support for paste-back workflow
- [x] Tool/plugin to watch clipboard and auto-insert output
- [ ] Optional fallback through hosted proxy (manual consent only)

### Phase 4 Extensions (Planned)
- [ ] Tag pasted responses with source annotations
- [ ] Natural-language date parsing for reminders
- [ ] Text-to-speech or audio notifications
- [x] Calendar export utility with `.ics` generation

---

## 🚀 Phase 5: Personalization & Pro Mode
**Goal:** Multi-user and adaptive interaction support

- [x] Identity tracking across sessions (you vs. family vs. guest)
- [x] Model persona shaping based on context (assistant/partner/researcher)
- [x] Voice adaptation (tone, formality, role-specific)
- [x] Calendar and scheduling integration
- [x] Notification system for reminders
- [x] Mobile UI or TUI wrapper (optional)

---

## 📚 References
- Damien Berezenko: *"I Used MCP for 3 Months: Everything You Need to Know + 24 Best Servers"*  
  [https://pub.towardsai.net/i-used-mcp-for-3-months-everything-you-need-to-know-24-best-servers-0c02f3915867](https://pub.towardsai.net/i-used-mcp-for-3-months-everything-you-need-to-know-24-best-servers-0c02f3915867)

---

## 📌 Notes
- Agent name: **Axon** (can be changed later)
- Code-first structure supports low-dependency local execution
- Cloud fallback is entirely manual and user-controlled
- This roadmap will evolve with use-case feedback and plugin growth

