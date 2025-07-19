# Axon Development Roadmap: Phase 10 – Internal Task Management, Subgoals, and Reflection Engine

This document defines **Phase 10** of the Axon agent system, focused on enabling internal planning, goal tracking, subtask execution, and self-reflection mechanisms.

---

## 🧠 10.1 – Task Management Core

**Goal:** Track active goals, user-defined tasks, and agent-generated subtasks.

**Modules:**

- `task_manager.py` (new)
- `memory/tasks/` (if persistent YAML/JSON)
- PostgreSQL task table (if using DB)

**Features:**

- Add/edit/remove tasks
- Mark as complete/deferred
- Attach metadata (created\_by, context, due\_date)

**Command Examples:**

```
add_task("Finish insulation plan by Monday")
list_tasks(context="home_project")
```

**Status:** Planned

---

## 🧠 10.2 – Subgoal Generation

**Goal:** Break high-level user goals into manageable steps.

**Trigger Types:**

- Manually requested: `generate_subgoals("Build a greenhouse")`
- Auto-triggered when a task is added with "large" context

**Example Output:**

```yaml
parent: Build a greenhouse
subgoals:
  - Measure available space
  - Choose materials
  - Draft design
```

**Output Location:** Embedded in structured memory and optionally linked to MCP payloads

**Status:** MVP feature

---

## 🔁 10.3 – Reflection Engine

**Goal:** Enable Axon to review its own actions, improve strategies, and correct errors

**Types of Reflection:**

- Summary-based (“What did I help with today?”)
- Outcome review (“Which reminders were ignored?”)
- LLM-assisted self-assessment (prompt-based introspection)

**Frequency:**

- Daily summaries (if configured)
- Triggered on milestone completion or failure

**Outputs Stored In:**

- `logs/reflections/`
- Memory entries with tag: `reflection`

**Prompting Example:**

```
Today, Axon completed 3 tasks and missed 1.
Reason for missed task: ambiguous time setting.
Suggested fix: ask for time confirmation next time.
```

**Status:** Early concept

---

## 📘 10.4 – Optional UI Enhancements

**Features:**

- Task list sidebar or overlay
- Status chips (Active / Completed / Deferred)
- Reflection viewer (view past entries)

**Future Phase:** not needed for backend functionality

---

## ✅ Phase 10 Completion Criteria

- Axon can manage user tasks with CRUD operations
- Subgoals are generatable for complex tasks
- Reflection module produces basic logs of success/failure
- Optional hooks for goal/summary viewing in UI

---

Next: Phase 11 – Vector Search Upgrades, Summarization Memory, and Cross-Thread Recall

