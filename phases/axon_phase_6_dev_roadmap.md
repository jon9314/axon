# Axon Development Roadmap: Phase 6 – Tool Ecosystem & Plugin Expansion

This document outlines **Phase 6** of Axon: establishing a plugin system, enabling tools for tasks like file parsing or summarization, and expanding modularity.

---

## 🧩 Phase 6 Overview – Enabling Agent Growth

Goal: Give Axon the ability to load, manage, and run plugins that extend its capabilities without needing core rewrites.

Features introduced in this phase:

- Plugin folder discovery
- Skill registration and dynamic command exposure
- Controlled access to memory, files, and external APIs
- Safety metadata and plugin isolation practices

---

## 🔌 Plugin System Architecture (Phase 6.1–6.3)

### 6.1 – Plugin Folder Loader

**Description:** Scans `/plugins` directory for valid modules

**File(s):**

- `plugins/plugin_loader.py`
- `config/settings.yaml`

**Behavior:**

- Detect plugins with `plugin.yaml` metadata file
- Dynamically import and register supported actions

**Metadata Format (plugin.yaml):**

```yaml
name: pdf_tools
version: 0.1
author: Jonathan
permissions:
  memory: read-write
  files: read
  api: none
```

**Status:** TODO

---

### 6.2 – Command Hook Exposure

**Description:** Allows plugins to register commands with Axon dynamically

**File(s):**

- `agent/plugin_registry.py`

**Usage:**

- Plugin can call `register_command("summarize_pdf", function)`

**Validation:**

- Ensure command is callable
- Prevent name collisions

**Status:** TODO

---

### 6.3 – Permissions & Isolation Framework

**Description:** Restricts what plugins can access based on config

**File(s):**

- `agent/security.py`

**Examples:**

- `memory: read-only`
- `api: none`
- `files: write`

**Status:** TODO

**Optional:**

- Logging access attempts
- Deny-by-default mode

---

## 🛠 Built-In Tools (Phase 6.4–6.6)

### 6.4 – PDF & Markdown Tools

**Description:** Add default plugins for parsing and summarizing local `.pdf` and `.md` files

**Plugin:**

- `plugins/pdf_tools/`
- `plugins/markdown_tools/`

**Commands:**

- `summarize_pdf(file_path)`
- `extract_text(file_path)`

**Dependencies:**

- `PyMuPDF`, `markdown2`

**Status:** TODO

---

### 6.5 – Memory Modifier Tool

**Description:** Lets plugin or user adjust memory facts or add annotations

**Command:**

- `modify_fact(id, new_content)`
- `tag_memory(id, tag="important")`

**Status:** TODO

**Optional:**

- Memory diff view in UI

---

### 6.6 – External API Test Plugin

**Description:** Sample plugin that makes safe call to public API (e.g., joke, weather)

**Plugin:**

- `plugins/api_example/`

**Command:**

- `get_joke()`
- `weather(city="Akron")`

**Status:** TODO

---

## ✅ Phase 6 Completion Criteria

- Plugin system auto-discovers plugins from `/plugins`
- Plugins can safely register commands with Axon
- Built-in tools include PDF parser, markdown reader, memory modifier, and test API plugin
- All plugin access is validated and isolated per config

---

Next: Phase 7 – Multi-Identity Recognition, Custom Personas, and Dynamic Voice Styles

