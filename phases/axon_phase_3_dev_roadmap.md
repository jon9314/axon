# Axon Development Roadmap: Phase 3 – MCP Server Integration

This document breaks down **Phase 3** of Axon into detailed development tasks focused on integrating external Model Context Protocol (MCP) servers for enriched tool support and data context.

---

## 📦 Phase 3 Overview – External Tool Access via MCP

Goal: Integrate Axon with local MCP servers for file I/O, computation, and real-world utility.

Axon will:

- Discover and communicate with STDIO or HTTP-based MCP servers
- Route intent-tagged messages through appropriate MCP tool endpoints
- Parse and return structured results as memory entries or agent replies

---

## 🛠 Priority MCP Servers (Phase 3.1–3.4)

### 3.1 – Filesystem MCP

**Description:** Read/write access to the local filesystem via MCP.

**Files:**

- `agent/tools/filesystem_proxy.py`
- `agent/mcp_handler.py`

**Server:** [`filesystem-mcp`](https://github.com/dgbert/filesystem-mcp)

**Commands Supported:**

- `read`, `write`, `list`, `exists`

**Validation:**

- Read a `.txt` file and store its content as memory
- List files in a test directory

**Status:** DONE

**Optional:**

- Add file tagging to memory entries (`source: filesystem`)

---

### 3.2 – Time MCP

**Description:** Provides accurate timestamp and datetime utilities.

**Files:**

- `agent/tools/time_proxy.py`

**Server:** [`time-mcp`](https://github.com/dgbert/time-mcp)

**Commands Supported:**

- `now`, `timezone`, `duration_between`

**Validation:**

- Insert current timestamp into memory
- Compare time spans for reminders

**Status:** DONE

**Optional:**

 - Annotate new memory entries with timestamps

---

### 3.3 – Calculator MCP

**Description:** Handles math calculations with precision (offload from LLM).

**Files:**

- `agent/tools/calc_proxy.py`

**Server:** [`calc-mcp`](https://github.com/dgbert/calc-mcp)

**Commands Supported:**

- `evaluate`, `convert`, `percent`

**Validation:**

- Ask “what’s 12.5% of 317.6?” and receive correct structured output

**Status:** DONE

**Optional:**

- Memory tagging: `source: calculator`

---

### 3.4 – Basic Memory MCP (Markdown)

**Description:** Backup or supplement to Axon's internal Postgres memory.

**Files:**

- `agent/tools/basic_memory_proxy.py`

**Server:** [`basic-memory-mcp`](https://github.com/dgbert/basic-memory-mcp)

**Commands Supported:**

- `save_note`, `get_note`, `search_notes`

**Validation:**

- Save and retrieve a note stored via markdown file

**Status:** DONE

**Optional:**

 - Synchronize markdown notes with Qdrant for retrieval

---

## 🌐 Secondary MCP Targets (Phase 3.5+)

### 3.5 – GitHub MCP

**Description:** Programmatically read/write GitHub repositories.

**Files:**

- `agent/tools/github_proxy.py`

**Use Cases:**

- List repo files
- Edit/read specific files via commits

**Validation:**

- Pull README from a repo

**Optional:**

 - Auto-commit patches via plugin

**Status:** DONE

---

### 3.6 – Documentation MCPs (Context7, DeepWiki, MS Learn)

**Description:** Retrieve technical or structured documentation.

**Files:**

- `agent/tools/docs_proxy.py`

**Validation:**

- Ask “what is an async context manager?” → result from Context7

**Optional:**

 - Capture documentation source URLs

**Status:** DONE

---

### 3.7 – Text2SQL MCP + Antvis (Data Tools)

**Description:** Natural language querying of structured data (e.g. CSVs, DBs), and chart generation.

**Files:**

- `agent/tools/query_proxy.py`

**Validation:**

- Ask “What’s the average revenue by quarter?” on sample data

**Optional:**

 - Render query results as charts in the UI

**Status:** In Progress – CSV query server implemented

---

## 🔗 MCP Integration Infrastructure (All Tools)

### 3.8 – MCP Transport and Registry

**Description:** Core registry and router for available MCP tools.

**Files:**

- `agent/mcp_router.py`
- `config/mcp_servers.yaml`

**Format Example:**

```yaml
- name: filesystem
  transport: stdio
  command: "npx filesystem-mcp"

- name: calc
  transport: http
  url: http://localhost:1234/
```

**Validation:**

- List all running MCP tools
- Route test command from LLM to matching tool

**Optional:**

 - Record MCP latency and failure metrics in the router

**Status:** DONE

---

### 3.9 – MCP Response Normalization

**Description:** Convert tool replies into usable memory and UI outputs.

**Files:**

- `agent/mcp_handler.py`

**Validation:**

- Translate MCP response JSON to readable summaries
- Tag memory with source + confidence

**Status:** DONE

---

## ✅ Phase 3 Completion Criteria

- Axon can call MCP tools for Filesystem, Time, and Calculator
- Memory entries reflect tool output and origin
- MCP responses parsed, routed, and displayed in chat/memory views
- Config system defines MCP tools for discovery

---

Next: Phase 4 – Cloud Fallback Prompting and Calendar Integration

