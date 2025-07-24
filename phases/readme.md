# Axon: Local-First AI Agent with Hybrid Memory and MCP Support

Axon is a modular, local-first AI agent designed to learn, remember, and adapt through structured and vector memory. It supports context-aware conversations, file parsing, plugin loading, and Model Context Protocol (MCP) integration. Built with privacy and extensibility in mind, Axon gives you full control—no forced cloud API calls, no vendor lock-in.

---

## 🔧 Features

- **Local LLM-first execution** via Ollama (DeepSeek, Qwen, Mistral)
- **Cloud assist prompts** (manual Claude/GPT workflows, no API keys required)
- **Structured memory** (PostgreSQL) for facts, identity, task tracking
- **Vector memory** (Qdrant) for semantic retrieval using hybrid ranking
- **Multi-threaded chat sessions** with scoped memory
- **MCP-ready** (Filesystem, Time, Calculator, Docs, GitHub integrations planned)
- **Plugin system** with hot-reload support
- **FastAPI backend** and **React frontend** with split-pane view
- **CLI, Web, and Headless modes**
- **.env and YAML-based config layers**
- **Type-checked (mypy), linted (ruff)**
- **CI/CD hooks for linting/formatting via GitHub Actions**

---

## 🏁 Quick Start

```bash
# Clone and set up
git clone https://github.com/your-username/axon.git
cd axon
cp .env.example .env

# Start with Docker
docker compose up --build

# Or start CLI mode only
python main.py --cli
```

---

## 📁 Project Structure (Partial)

```
axon/
├── main.py
├── config/
│   └── settings.yaml
├── memory/
│   ├── memory_handler.py
│   └── vector_store.py
├── plugins/
│   └── example_plugin.py
├── agent/
│   ├── llm_router.py
│   ├── planner.py
│   └── mcp_handler.py
├── frontend/  (React)
├── backend/   (FastAPI)
├── .env.example
├── docker-compose.yml
└── README.md
```

---

## 🧠 Model Behavior

- **Defaults to local LLM** via Ollama
- If task exceeds local model capabilities, agent:
  1. Suggests model (e.g., Claude Sonnet, GPT-4o)
  2. Generates exact prompt
  3. Waits for user to paste in output

---

## 📦 Tech Stack

- Python 3.11+
- React + Vite (frontend)
- FastAPI (backend)
- PostgreSQL (structured memory)
- Qdrant (vector memory)
- Docker + Docker Compose
- mypy, ruff, GitHub Actions

---

## 🧭 Project Roadmap

See `ROADMAP.md`.

---

## 🔐 License

MIT License (see [LICENSE](../LICENSE))

