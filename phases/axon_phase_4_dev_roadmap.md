# Axon Development Roadmap: Phase 4 – Cloud Fallback & Calendar Integration

This document outlines **Phase 4** of Axon: cloud prompt routing without direct API usage, manual pasteback handling, and local-first calendar/reminder system integration.

---

## 📦 Phase 4 Overview – Cloud-Aware, Still Local-First

Goal: Empower Axon to assist with external model use (GPT-4o, Claude) and time-based task management without giving up control.

Cloud LLMs are **never called automatically**. Instead, Axon:

- Detects task complexity that may exceed local models
- Generates a copyable prompt
- Waits for user to paste response back into the chat interface

---

## ☁️ Smart Cloud Prompting (Phase 4.1–4.4)

### 4.1 – Fallback Prompt Generator

**Description:** Generates Claude/GPT-style prompt when local model is insufficient

**File(s):**

- `agent/llm_router.py`
- `agent/fallback_prompt.py`

**Behavior:**

- Tag conversation as "cloud-suggested" if context exceeds confidence threshold
- Present user with prefilled prompt
- Wait for pasteback reply

**Validation:**

- Simulate local model refusal → trigger fallback suggestion

**Status:** DONE

**Optional:**

- Suggest model name (e.g., "Claude Sonnet" or "GPT-4o")

---

### 4.2 – Pasteback Workflow (Manual API-Free Inference)

**Description:** Allows users to paste cloud model output into chat

**File(s):**

- `frontend/components/Chat.tsx`
- `agent/pasteback_handler.py`

**Validation:**

- Copy > paste cycle tested in full
- Memory stores both original prompt and pasted result

**Status:** DONE

**Optional:**

 - Tag pasted responses with `source:gpt` or `source:claude`

---

### 4.3 – Model Suggestions + Explanation

**Description:** Adds lightweight model selector logic to explain fallback reason

**File(s):**

- `agent/llm_router.py`

**Logic:**

- “This might be better suited for Claude because it involves nuanced summarization.”
- Include model links: Claude.ai, ChatGPT, Poe

**Status:** DONE

---

### 4.4 – Clipboard Watcher (Optional Utility Plugin)

**Description:** Background tool detects clipboard updates to auto-paste when desired

**File(s):**

- `plugins/clipboard_monitor.py`

**Dependencies:**

- `pyperclip`, `keyboard`

**Validation:**

- Prompt + paste within 15s triggers memory log

**Status:** DONE

---

## 📅 Local Calendar Integration (Phase 4.5–4.7)

### 4.5 – Reminder Scheduler

**Description:** Parses time-based tasks and stores with datetime

**File(s):**

- `agent/scheduler.py`
- `memory/memory_handler.py`

**Format:**

```yaml
- type: reminder
  content: "Doctor appointment at 2PM"
  datetime: "2025-07-20T14:00:00"
```

**Validation:**

- Schedule + retrieve reminder

**Status:** DONE

**Optional:**

 - Natural-language date parsing such as "next Thursday"

---

### 4.6 – Reminder Notification Engine

**Description:** Background job to trigger notifications

**File(s):**

- `agent/notifier.py`
- `frontend/components/ReminderBell.tsx`

**Notification Types:**

- UI banner
- Console log

**Status:** DONE

**Optional:**

 - Provide text-to-speech or audio notifications

---

### 4.7 – External Calendar Export

**Description:** Implement `calendar_exporter.py` to generate `.ics` files or a CalDAV-compatible feed

**File(s):**

- `agent/calendar_exporter.py`

**Optional Integration:**

- Google Calendar via manual sync or `.ics`

**Status:** DONE

---

## ✅ Phase 4 Completion Criteria

- Axon suggests cloud model prompts with justification
- Pasteback workflow stores both prompt and result
- Reminders can be scheduled and trigger alerts
- Calendar entries exportable if needed

---

Next: Phase 5 – Identity Adaptation, Scheduling Personalization, and Mobile/Voice Expansion

