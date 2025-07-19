# Axon Development Roadmap: Phase 17 – Calendar Integration, Time-Aware Prompts, and Smart Scheduling Hooks

This document outlines **Phase 17** of the Axon agent system. Focus areas include integrating calendar support, understanding and responding to time-based prompts, and using contextual scheduling intelligence.

---

## 📅 17.1 – Calendar Integration (Local or External)
**Goal:** Enable Axon to access and interact with calendar data.

**Options:**
- Local calendar file (iCal, `.ics` format)
- External APIs (e.g., Google Calendar, Outlook via OAuth)

**Features:**
- Read upcoming events
- Add, remove, or modify events (manual approval optional)
- Link events to memory (e.g., “Meeting with Cary about attic insulation”)

---

## 🕒 17.2 – Time-Aware Prompt Handling
**Goal:** Axon should recognize and respond intelligently to time-based queries.

**Examples:**
> “What do I have scheduled tomorrow?”  
> “Remind me to check the attic next weekend.”

**System Behavior:**
- Detect date/time language
- Use memory timestamp filters
- Cross-reference calendar data when available

---

## 📆 17.3 – Smart Scheduling Hooks
**Goal:** Allow Axon to suggest times for tasks or events based on context.

**Behaviors:**
- Avoid conflicts with existing calendar items
- Suggest optimal windows (e.g., mornings, weekends)
- Ask for confirmation before writing to calendar

**Future Enhancements:**
- Learn preferred scheduling patterns over time
- Trigger reminders or follow-ups via system notification layer (Phase 8)

---

## ✅ Phase 17 Completion Criteria
- Calendar connector (local or API) in place and accessible
- Time-aware NLP parser hooked into prompt handling
- Task scheduling utility supports confirmation + context awareness
- Test coverage for various temporal prompts and scheduling use cases

---

Next: Phase 18 – Long-Term Memory Prioritization, Forgetting Policy, and Memory Locking Controls

