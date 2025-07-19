# Axon Development Roadmap: Phase 15 – Persona Awareness, Contextual Voice Switching, and Tone Matching

This document outlines **Phase 15** of the Axon agent system. This stage introduces adaptive communication styles, allowing the agent to personalize its voice and tone based on context, speaker, and intent.

---

## 🧠 15.1 – Persona Detection & Identity Tagging
**Goal:** Enable Axon to recognize user identities and adjust context accordingly.

**Design:**
- Implement user profiles scoped by identity (e.g., `jonathan`, `cary`, `agent`)
- Maintain tagged speaker info in conversation and memory logs
- Infer identity from chat structure, prefixes, or active session

**Features:**
- Dynamic loading of identity-based preferences
- Memory entries tagged by speaker for disambiguation
- Session switching or shared contexts (e.g., joint planning)

---

## 🗣 15.2 – Voice Style & Contextual Switching
**Goal:** Let Axon change its communication tone based on situation.

**Modes:**
- **Assistant mode:** Informative and directive (“Here’s the answer, would you like to continue?”)
- **Partner mode:** Cooperative and open-ended (“We could go three ways here—thoughts?”)
- **Researcher mode:** Analytical and neutral (“Given X, Y is supported by memory Z.”)

**Triggers:**
- Type of task (planning vs coding vs decision making)
- Speaker preferences
- Contextual memory

**Implementation:**
- Style directives via internal tags (e.g., `@voice:partner`)
- Optional override per chat or plugin

---

## 🎯 15.3 – Tone Matching and Social Awareness
**Goal:** Improve user comfort and communication efficiency.

**Tactics:**
- Match formality and emotional tone of user inputs
- Detect and respond to frustration, confusion, or enthusiasm
- Support “mood-based” adjustments (e.g., short + to the point if rushed)

**Examples:**
- You: “Ugh I just want a quick answer.” → Axon: “Got it. Answer is: 14.”
- You: “This is exciting!” → Axon: “It really is! Let’s dig in.”

---

## ✅ Phase 15 Completion Criteria
- Agent adjusts communication style based on context and preferences
- User identity tagging active in memory and logs
- Supports Assistant, Partner, and Researcher voice modes
- Agent matches tone in real time and adapts accordingly

---

Next: Phase 16 – Reminder System, Calendar Integration, and Proactive Notifications

