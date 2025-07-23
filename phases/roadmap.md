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

### Phase 1 Enhancements (Planned)
- [ ] TUI-based CLI interface
- [ ] Hybrid vector scoring and LLM confidence metrics
- [ ] `mcp_mode` setting and JSON traffic logs
- [ ] Domain-aware preload entries
- [ ] Backend rate limiting and optional auth
- [ ] Model selector dropdown in the UI

---

## 🧠 Phase 2: Memory & Plugin Enrichment
**Goal:** Scoped memory, plugin loader, goal tracking

- [x] Memory scoping (per thread, per identity)
- [x] Edit/delete/lock memory entries
- [x] Plugin system with hot-reload + metadata config
- [x] Structured long-term goal tracking
- [x] Manual note tagging + identity recognition
- [x] Add support for CLI input memory injection

### Phase 2 Improvements (Planned)
- [ ] Domain scoping in memory tables and API
- [ ] Mass deletion endpoints and CLI plugin reload
- [ ] Permission scoping for plugins
- [ ] Goal priority and deadline fields
- [ ] Periodic prompts for deferred goals
- [ ] Optional speaker-embedding logic

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

### Phase 3 Additions (Planned)
- [ ] Timestamp new memory entries via Time MCP
- [ ] Sync markdown notes with Qdrant
- [ ] Auto-commit patches via GitHub tooling
- [ ] Capture documentation source URLs and show charts
- [ ] Record MCP latency/failure metrics

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

- [ ] Identity tracking across sessions (you vs. family vs. guest)
- [ ] Model persona shaping based on context (assistant/partner/researcher)
- [ ] Voice adaptation (tone, formality, role-specific)
- [ ] Calendar and scheduling integration
- [ ] Notification system for reminders
- [ ] Mobile UI or TUI wrapper (optional)

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

