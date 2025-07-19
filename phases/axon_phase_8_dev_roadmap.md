# Axon Development Roadmap: Phase 8 – Notifications, Mobile Sync & Scheduling

This document outlines **Phase 8** of Axon: building out its ability to remind, notify, and coordinate tasks—locally and (optionally) across devices.

---

## 🔔 8.1 – Local Notification System

**Purpose:** Let Axon alert you to time-based or task-based events.

**Implementation Options:**

- Use system pings (via OS, if supported)
- WebSocket push to frontend
- Console print fallback (for CLI)

**Features:**

- Event type: reminder, scheduled task, deferred goal
- Trigger mode: absolute time (e.g., 2pm), relative time (e.g., 10 min), calendar-linked

**Backend module:** `notifications/dispatcher.py`

**Frontend widget:** Toast or sidebar alert

**Status:** TODO

---

## 📱 8.2 – Mobile Access & Sync (Optional Future Feature)

**Goal:** Make Axon accessible remotely or via mobile-friendly interfaces.

**Paths:**

- Build a lightweight PWA (Progressive Web App)
- Expose REST API for use with third-party mobile dashboards (e.g., Home Assistant, Tasker)
- Headless mode + webhook endpoint for receiving/sending mobile updates

**Use Cases:**

- Get reminder pings while away from desktop
- Send notes via text or voice to Axon
- Voice integration (future)

**Status:** Future Phase (Optional)

---

## 🗓 8.3 – Scheduling Engine

**Goal:** Let Axon handle calendar-like behavior, with or without calendar integration.

**Features:**

- Time parsing (e.g., “next Friday at noon”)
- Recurring task support (e.g., “every Monday at 8am”)
- Deferred goals handling (e.g., “Remind me to finish the router config later”)

**Optional:**

- Export to `.ics` or push to calendar via API (e.g., local Nextcloud, or Google/iCloud with user API key)

**Modules:**

- `scheduler/parser.py`
- `scheduler/engine.py`

**Status:** TODO

---

## 🔁 8.4 – Reminder Memory Integration

**Purpose:** Reminders should live in memory, be retrievable, and get context-linked.

**Features:**

- All reminders stored in structured memory
- Retrieval like: “What did I ask you to remind me last week?”
- Automatic promotion of forgotten tasks/goals

**Memory Fields:**

```yaml
- type: reminder
  speaker: jonathan
  time: 2025-07-14T16:00:00Z
  content: "Review home server notes."
  context: project:homelab
```

**Status:** TODO

---

## ✅ Phase 8 Completion Criteria

- Axon can issue local alerts and reminders
- Reminders are persistent, context-aware, and editable
- Scheduling engine supports basic recurrence and time parsing
- Ready for future mobile syncing layer or calendar integration

---

Next: Phase 9 – Plugin Management, Runtime Skills, and Toolchain Updates

