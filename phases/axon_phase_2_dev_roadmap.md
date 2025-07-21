# Axon Development Roadmap: Phase 2 – Memory Expansion, Plugin System, Goal Tracking

This document breaks down **Phase 2** of Axon into detailed engineering tasks for extending structured memory, introducing scoped identity tracking, goal logging, and implementing a reloadable plugin system.

---

## 📦 Phase 2 Overview – Memory & Skills Expansion

Goal: Improve memory fidelity, allow user-driven expansion, and introduce the plugin loader with context awareness.

---

### 2.1 – Memory Scoping by Thread and Identity

**Description:** Supports contextual memory per chat thread or user.

**File(s):**

- `memory/memory_handler.py`
- `agent/context_manager.py`

**Dependencies:**

- PostgreSQL memory tables must include `thread_id`, `identity`

**Settings:**

```yaml
memory:
  scope_by_thread: true
  scope_by_identity: true
```

**Validation:**

- Save/retrieve memory by user and thread
- Ensure irrelevant facts aren’t retrieved between contexts

**Status:** Done

**Optional:**

- Add per-domain scoping (e.g., "work", "personal")

---

### 2.2 – Memory Edit, Delete, and Lock Support

**Description:** Adds UI/API and backend support for memory item updates.

**File(s):**

- `memory/memory_handler.py`
- `frontend/components/MemoryViewer.tsx`
- `backend/api.py`

**Validation:**

- Mark items as `locked: true` to prevent deletion
- Edit content in UI or via CLI
- Delete by ID

**Status:** Done

**Optional:**

- Support mass delete by context

---

### 2.3 – Plugin Loader (Folder-Based)

**Description:** Allows plugins to be added by dropping Python files into a folder.

**File(s):**

- `plugins/`
- `agent/plugin_loader.py`

**Responsibilities:**

- Discover all `.py` files in `plugins/`
- Validate interface (e.g., `Plugin.run()`)
- Load metadata: name, description, permissions

**Validation:**

- Load sample plugin with console output
- List loaded plugins from CLI

**Status:** Done

**Optional:**

- Hot-reload plugins while running

---

### 2.4 – Plugin Access to Memory & API

**Description:** Allows plugins to retrieve/store memory and optionally call APIs.

**File(s):**

- `agent/plugin_context.py`

**Config:**

```yaml
plugins:
  allow_memory_access: true
  allow_external_apis: true
```

**Validation:**

- Sample plugin retrieves a memory item and sends a mocked API request

**Status:** Done

**Optional:**

- Add permission scoping (per-plugin)

---

### 2.5 – Long-Term Goal Logging

**Description:** Automatically logs statements that represent long-term goals or future actions.

**File(s):**

- `agent/goal_tracker.py`

**Responsibilities:**

- Parse statements like “I want to…” or “Remind me to…”
- Store in dedicated table or memory type `goal`

**Validation:**

- Submit test utterance and verify it's logged

**Status:** Done

**Optional:**

- Add priority and deadline fields

---

### 2.6 – Deferred Idea Logging

**Description:** Captures unacted thoughts or half-formed plans.

**File(s):**

- `agent/goal_tracker.py`

**Responsibilities:**

- Detect vague or non-actionable input (“someday I might…”)
- Tag as `deferred`

**Validation:**

- Capture and retrieve deferred ideas in UI/API

**Status:** Done

**Optional:**

- Add option to re-prompt user about old ideas

---

### 2.7 – Identity Recognition & Multi-Person Chat

**Description:** Tracks and logs user identities by name or message source.

**File(s):**

- `agent/context_manager.py`

**Settings:**

```yaml
identity_tracking: true
```

**Validation:**

- Track who said what in multi-person sessions
- Ensure memory entries reflect correct `identity`

**Status:** Done

**Optional:**

- Add speaker embedding matching (future ML enhancement)

---

### 2.8 – MCP Identity Tag Support

**Description:** Ensures memory entries from MCP sources retain their origin (e.g., "from Filesystem", "from GitHub")

**File(s):**

- `agent/mcp_handler.py`

**Validation:**

- Load MCP-wrapped memory payload and tag source properly

**Status:** Done

**Optional:**

- Allow plugin-based identity enrichment

---

## ✅ Phase 2 Completion Criteria

- Memory can be scoped, edited, deleted, and locked
- Plugins load from folder and optionally call APIs or memory
- Long-term and deferred ideas logged automatically
- User and thread identities handled throughout

---

Next: Phase 3 – MCP Server Integration (Filesystem, Time, Calculator, etc.)

