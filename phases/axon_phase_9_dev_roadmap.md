# Axon Development Roadmap: Phase 9 – Plugin System & Runtime Skills

This document outlines **Phase 9** of the Axon agent: extending its capabilities via a modular plugin architecture and dynamic runtime skill loading.

---

## 🧩 9.1 – Plugin System Core

**Goal:** Allow Axon to gain new features by dropping plugins into a designated folder.

**Folder:** `plugins/`

**Plugin Structure:**

```
plugins/
├── summarize_pdf/
│   ├── plugin.yaml
│   ├── handler.py
│   └── utils.py
```

``** example:**

```yaml
name: summarize_pdf
version: 0.1.0
entrypoint: handler.py
commands:
  - summarize_pdf
requires:
  - PyMuPDF
```

**Loader module:** `core/plugin_loader.py`

**Features:**

- Auto-discovery on boot
- Optional `reload` command
- Plugin-level error isolation

**Status:** TODO

---

## ⚙️ 9.2 – Runtime Skill Registration

**Goal:** Let plugins register new commands or augment existing behaviors.

**Implementation:**

- Plugins can call `register_command()` to define new CLI/LLM-callable commands
- Axon exposes a PluginContext object with:
  - Access to memory API
  - File and vector store I/O
  - Optional external tool wrappers

**Example command:**

```python
@register_command("summarize_pdf")
def summarize_pdf(file_path: str):
    # PDF parsing logic here
```

**Status:** TODO

---

## 🔐 9.3 – Plugin Metadata, Permissions & Logging

**Optional for MVP, but scaffoldable**

**Permissions system (future):**

- `can_modify_memory: true`
- `can_call_external_api: false`
- `can_write_files: true`

**Logging module:**

- Scoped logs per plugin (optional)
- Plugin failure recovery

**Status:** Design Phase

---

## 🔄 9.4 – Hot Reloading & Dev Tools

**Nice-to-have, not required for v1.0**

**Goal:** Support live development without restarting Axon.

**Features:**

- `reload_plugins()` admin command
- Plugin watcher (e.g., watchdog or polling loop)
- Optional: Dev dashboard showing loaded plugins & status

**Status:** Future Phase

---

## ✅ Phase 9 Completion Criteria

- Plugins can be dropped into the plugins/ directory and auto-loaded
- Commands defined in plugins are registered and callable
- Plugin system is documented and stable for v1.0 use
- Optional metadata support scaffolded for later use

---

Next: Phase 10 – Internal Task Management, Subgoals, and Reflection Engine

