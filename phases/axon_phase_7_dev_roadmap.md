# Axon Development Roadmap: Phase 7 – Identity, Personas & Voice Control

This document outlines **Phase 7** of Axon: giving the agent the ability to recognize multiple identities in conversation, adjust its tone or personality dynamically, and optionally develop a sense of continuity.

---

## 🧠 Phase 7 Overview – Making Axon Feel Personal

Goal: Axon should respond differently depending on who it’s talking to, remember preferences, and switch voices appropriately.

Key features:

- Multi-speaker identity tagging
- Contextual voice/persona switching
- User tone and style preferences
- Long-term personalization memory

---

## 👥 7.1 – Identity Recognition and Tagging

**Purpose:** Track who is speaking in a conversation (Jonathan, Cary, etc.)

**Implementation Plan:**

- Add `speaker` field to message logs and memory entries
- CLI and UI should support `--as "Cary"` or UI selector for speaker
- Auto-tagging rules (based on speaker name or session)

**Memory Entry Example:**

```yaml
type: note
speaker: cary
content: "I don’t like that playlist."
context: music
```

**Status:** TODO

---

## 🧬 7.2 – Preference Profiles (Per User)

**Goal:** Store how each user likes to be spoken to

**Fields:**

- Tone (formal, casual, playful)
- Detail level (brief vs. in-depth)
- Voice preference (assistant / partner / researcher)
- Preferred name / pronouns

**Stored In:**

- `memory/preferences/user_name.yaml`

**Used By:**

- UI display logic
- Prompt builder

**Status:** TODO

---

## 🧠 7.3 – Dynamic Voice Switching

**Goal:** Agent should adjust tone and voice based on context

**Modes:**

- Assistant: “Here’s your reminder.”
- Partner: “Let’s think through this together.”
- Researcher: “Given your data, I’d suggest X.”

**Triggers:**

- Conversation context (task type)
- Explicit override (“act like a researcher now”)
- Stored user preferences

**Optional:**

- System decides based on task classification

**Status:** TODO

---

## 🪪 7.4 – Agent Identity & Self-Awareness

**Purpose:** Allow Axon to reference itself consistently

**Examples:**

- “You can ask me to summarize PDFs.”
- “I last helped you edit `main.py` on Wednesday.”

**Features:**

- Store agent name (optional)
- Track recent actions
- Memory of past roles (e.g., “you said I’m your coding buddy”)

**Status:** TODO

---

## ✅ Phase 7 Completion Criteria

- Users can be identified and tagged in chat/memory
- Per-user preferences are stored and respected
- Agent can shift tone/style dynamically
- Agent self-references and tracks its role history

---

Next: Phase 8 – Notification Layer, Mobile Sync, and Scheduling Hooks

