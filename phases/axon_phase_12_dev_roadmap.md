# Axon Development Roadmap: Phase 12 – Goal-Aware Planning, Simulated Tools, and Execution Pathways

This document defines **Phase 12** of the Axon agent system. The focus is on building structured goal planning, simulating tool use, and defining task execution logic.

---

## 🎯 12.1 – Goal Management System

**Goal:** Track long-term and short-term goals as structured entries.

**Features:**

- Add/edit/remove goals
- Auto-tagging: `domain`, `priority`, `due_date`, `status`
- Categories: `idea`, `todo`, `research`, `build`, `deferred`

**Data Model Example:**

```yaml
- type: goal
  title: Build greenhouse automation
  domain: home
  priority: high
  due_date: 2025-08-01
  status: active
  created: 2025-07-13
```

---

## 🧠 12.2 – Simulated Tool Planning

**Goal:** Allow agent to walk through tool-based steps in dry-run mode.

**Flow:**

1. Identify task steps (LLM + memory + context)
2. Simulate each action (e.g., "I would open file X and replace line Y...")
3. Ask for user approval or modification

**Benefits:**

- Safe environment for automation planning
- Debuggable by design

---

## 🗺 12.3 – Execution Pathways

**Goal:** Define how the agent transitions from “plan” to “act.”

**Modes:**

- 🧪 Simulate: dry-run each step, request approval
- 🏁 Execute: perform approved steps with optional confirmations
- 🛑 Skip: ignore steps or log them for later

**Planner Interface:**

```python
plan_task("optimize greenhouse watering")
```

Returns:

```yaml
- step: Analyze current sensor layout
- step: Generate new watering intervals
- step: Write updated config to Home Assistant
```

---

## 🔄 12.4 – Goal Reflection Engine (optional)

**Future Upgrade:**

- Periodic review of goals
- “You started X last week. Do you want to revisit it?”
- Tag stale or abandoned goals automatically

---

## ✅ Phase 12 Completion Criteria

- Agent supports structured goals with priority, domain, and timestamps
- Simulated planning logic (tool dry runs) is implemented
- Execution modes (simulate, act, skip) supported in planner
- Hooks available for tool/plugin integration in Phase 13

---

Next: Phase 13 – Real Plugin Integration, Safe Runtime Execution, and Dynamic Toolchains

