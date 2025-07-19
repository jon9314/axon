# Axon Development Roadmap: Phase 18 – Long-Term Memory Prioritization, Forgetting Policy, and Memory Locking Controls

This document outlines **Phase 18** of the Axon agent system. The focus is on establishing mechanisms for prioritizing important information, safely forgetting outdated content, and enabling permanent memory retention when needed.

---

## 🧠 18.1 – Memory Prioritization Framework
**Goal:** Assign importance levels to memory entries to help guide retention and summarization.

**System Behavior:**
- Assign default priority (e.g., 1–5) to memory entries based on type
- Allow user-defined overrides (e.g., “this is important”)
- Higher-priority entries are retained longer, summarized later

**Example Prioritization Heuristics:**
- 🟢 Level 1: Temporary (e.g., jokes, filler text)
- 🔵 Level 3: Notes, short-term goals
- 🔴 Level 5: Permanent facts, relationships, locked ideas

---

## 🧽 18.2 – Forgetting Policy Engine
**Goal:** Keep memory efficient and relevant by gradually removing low-value or stale entries.

**Behaviors:**
- Automatic purging or summarization of low-priority, old content
- Option to simulate purging and ask user for confirmation
- Support for memory “cooldown” (review before deletion)

**Tech Notes:**
- Runs as background service
- Can log deleted/summarized content to `archive/`

---

## 🔒 18.3 – Memory Locking & Permanent Retention
**Goal:** Let users manually protect key information from being altered or forgotten.

**Features:**
- Lock individual entries (e.g., user preferences, mission-critical facts)
- Visual indicator in UI for locked memories
- Prevent deletion, summarization, or embedding overwrites

**Example:**
> “Always remember that my daughter’s name is Lila and she hates broccoli.”

---

## ✅ Phase 18 Completion Criteria
- Memory entries support `priority` and `locked` fields
- Summarization engine respects priority values
- Forgetting service simulates, confirms, or archives old content
- UI indicators and memory editing tools support locking

---

Next: Phase 19 – Memory Export, Import, and Cross-Agent Sync Support

