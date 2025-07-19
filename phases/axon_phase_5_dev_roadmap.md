# Axon Development Roadmap: Phase 5 – Personalization, Identity, and Voice Adaptation

This document outlines **Phase 5** of Axon, focused on adapting the agent's behavior based on user identity, preferred tone, long-term habits, and interaction patterns. It also prepares for UI/UX expansion to voice interfaces and mobile-friendly modes.

---

## 📦 Phase 5 Overview – Adaptive Intelligence and Multimodal UX

Goal: Make Axon smarter about *who* it’s talking to and *how* it should respond, while expanding availability through better personalization and delivery.

---

## 👤 Identity & Persona Features (Phase 5.1–5.3)

### 5.1 – User Preference Memory

**Description:** Store and apply user tone, voice, and interaction preferences.

**File(s):**

- `memory/user_profile.py`
- `config/user_prefs.yaml`

**Fields:**

```yaml
jonathan:
  tone: informal
  trigger_words: ["hey axon", "yo"]
  prefers_short_responses: true
```

**Validation:**

- Apply settings dynamically based on speaker ID

**Status:** TODO

**Optional:**

- Per-domain tone control (e.g., formal at work, relaxed at home)

---

### 5.2 – Identity-Adaptive Voice/Style

**Description:** Adjust language style and structure depending on speaker

**File(s):**

- `agent/response_shaper.py`

**Behavior:**

- “You” vs. “Cary” get different styles
- Honor `user_profile` tone settings

**Validation:**

- Test same prompt from different users → different voice

**Status:** TODO

---

### 5.3 – Dynamic Memory Weighting by Identity

**Description:** Give more retrieval weight to memories relevant to the current user

**File(s):**

- `memory/vector_store.py`

**Behavior:**

- Modify Qdrant query to prioritize identity tags

**Validation:**

- Ask shared question, compare output scoped to Jonathan vs. Cary

**Status:** TODO

---

## 🎯 Long-Term Pattern Learning (Phase 5.4–5.5)

### 5.4 – Habit Recognition Engine

**Description:** Detect recurring goals or timeframes (e.g., “fasts every Mon–Fri”, “gym 3x/week”)

**File(s):**

- `agent/habit_tracker.py`

**Validation:**

- Detect pattern and summarize: “You usually fast M–F. Want to log today as a fast day?”

**Status:** TODO

**Optional:**

- Memory entries tagged with "routine"

---

### 5.5 – Auto-Surfacing Past Context

**Description:** Remind user about past promises, todos, or idle ideas

**File(s):**

- `agent/proactive_memory.py`

**Behavior:**

- Every X minutes, scan for relevant context to suggest

**Validation:**

- After 30 min, agent says “Earlier you said you might…”

**Status:** TODO

**Optional:**

- Configurable `reminder_interval`

---

## 🔔 Notification & Delivery Enhancements (Phase 5.6–5.7)

### 5.6 – Desktop and System Notifications

**Description:** Push reminders beyond UI (toast or TTS)

**File(s):**

- `agent/notifier.py`

**Platforms:**

- `plyer`, `notify-send`, or native APIs

**Status:** TODO

**Optional:**

- Use voice: Piper TTS or system-level TTS

---

### 5.7 – Voice Command Shell (CLI or Web)

**Description:** Add `OpenWakeWord` + Whisper to allow hands-free operation

**File(s):**

- `plugins/voice_shell.py`

**Dependencies:**

- `whisper`, `openwakeword`, `piper`

**Validation:**

- “Hey Axon, what’s on today?” triggers reply

**Status:** OPTIONAL

---

## 📱 Mobile & Multi-Device Readiness (Phase 5.8–5.9)

### 5.8 – Progressive Web App (PWA) Wrapper

**Description:** Mobile-friendly access to chat, memory, and reminders

**File(s):**

- `frontend/manifest.json`
- `frontend/serviceWorker.ts`

**Validation:**

- Can be added to home screen
- Works offline with basic features

**Status:** TODO

---

### 5.9 – Mobile Chat Memory Sync

**Description:** Separate device sessions retain identity and scoped memory

**File(s):**

- `agent/session_tracker.py`

**Validation:**

- Log into mobile → see matching history by user ID

**Status:** TODO

**Optional:**

- Use QR code login or access token

---

## ✅ Phase 5 Completion Criteria

- Axon adapts tone and memory to user identity
- Habit patterns logged and surfaced contextually
- Reminders can be delivered via system events or voice
- Mobile-ready UI available with offline memory access

---

Next: Phase 6 – Agent Self-Improvement, Code Evaluation, and Auto-Optimization (optional future)

