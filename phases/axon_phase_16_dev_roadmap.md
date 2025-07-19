# Axon Development Roadmap: Phase 16 – Notifications, System Pings, and Calendar-Aware Scheduling

This document outlines **Phase 16** of the Axon agent system. The focus is on delivering time-aware feedback, alerting the user to reminders or deadlines, and preparing for eventual calendar integration.

---

## 🔔 16.1 – Reminders and Time-Based Alerts

**Goal:** Let the agent set, track, and notify you of reminders.

**Features:**

- Reminder setting via chat ("Remind me to check the basement in 2 hours")
- Backend scheduler triggers message dispatch
- React UI can display banner or popup alert
- CLI shows notice upon next interaction

---

## 📆 16.2 – Calendar Hooking Logic

**Goal:** Enable agent to prepare for calendar integration.

**Features:**

- Internal format for events (title, time, location, description)
- Scaffolds support for iCal, Google Calendar, or custom sources
- Manual or AI-assisted entry from natural language

**Example:**

> “Schedule attic inspection for next Friday at 4 PM” → creates event

---

## ⏳ 16.3 – Notification Channels & Proactivity

**Goal:** Build an extensible alerting system for future growth.

**Features:**

- React-based alerts with dismiss or snooze
- CLI summary on boot if reminders exist
- Later: Email/webhook/push API support
- Agent can prompt: “Would you like me to remind you again in 30 mins?”

---

## ✅ Phase 16 Completion Criteria

- Reminder system scaffolded with basic UI + CLI outputs
- Natural language scheduling support stubbed
- Agent can store, retrieve, and notify on time-based tasks

---

Next: Phase 17 – Plugin Management, Runtime Skills, and Toolchain Updates

