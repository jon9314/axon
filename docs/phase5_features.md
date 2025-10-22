# Phase 5 Features: Personalization & Pro Mode

This document describes the Phase 5 enhancements to Axon, focusing on multi-user support and adaptive interaction capabilities.

## Overview

Phase 5 adds personalization and professional-grade features to Axon, enabling:
- Multi-user identity tracking across sessions
- Adaptive persona and tone shaping based on user preferences
- Calendar and scheduling integration
- Comprehensive notification and reminder system
- Enhanced TUI interface for power users

## Table of Contents

1. [Identity Tracking](#identity-tracking)
2. [User Profile Management](#user-profile-management)
3. [Persona & Tone Shaping](#persona--tone-shaping)
4. [Calendar Integration](#calendar-integration)
5. [Notification & Reminder System](#notification--reminder-system)
6. [TUI Interface](#tui-interface)
7. [API Reference](#api-reference)
8. [Use Cases](#use-cases)

---

## Identity Tracking

### Overview

Session-based identity tracking allows multiple users (family, guests, collaborators) to maintain separate contexts and preferences.

### Implementation

Location: `agent/session_tracker.py`

```python
class SessionTracker:
    """In-memory mapping of session tokens to identity and thread."""

    def create_session(self, identity: str, thread_id: str | None = None) -> tuple[str, str]:
        """Create a new session token for an identity."""

    def resolve(self, token: str) -> tuple[str, str] | None:
        """Return the identity and thread for a token if it exists."""

    def remove(self, token: str) -> None:
        """Delete a session token."""
```

### Features

#### Session Creation

Generate secure session tokens for each user:

```python
from agent.session_tracker import SessionTracker

tracker = SessionTracker()

# Create session for user
token, thread_id = tracker.create_session(identity="alice")
print(f"Session token: {token}")
print(f"Thread ID: {thread_id}")
```

#### Session Resolution

Resolve tokens back to identity and thread:

```python
# Later, resolve session
result = tracker.resolve(token)
if result:
    identity, thread_id = result
    print(f"User: {identity}, Thread: {thread_id}")
```

#### Session Management

```python
# Remove expired session
tracker.remove(token)
```

### Usage Examples

#### WebSocket Integration

```python
@app.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    identity: str = "default_user",
    session_token: str | None = None,
):
    await websocket.accept()

    if session_token:
        resolved = session_tracker.resolve(session_token)
        if resolved:
            identity, thread_id = resolved
        else:
            session_token, thread_id = session_tracker.create_session(identity)
    else:
        session_token, thread_id = session_tracker.create_session(identity)

    # Send session info to client
    await websocket.send_json({
        "type": "session",
        "token": session_token,
        "identity": identity,
        "thread_id": thread_id
    })
```

#### Multi-User Family Setup

```python
# Create separate sessions for family members
alice_token, alice_thread = tracker.create_session("alice")
bob_token, bob_thread = tracker.create_session("bob")
guest_token, guest_thread = tracker.create_session("guest")

# Each has isolated context and memory
```

### API Endpoints

#### POST /sessions/login
Create new session for identity.

**Request:**
```json
{
  "identity": "alice"
}
```

**Response:**
```json
{
  "token": "abc123...",
  "thread_id": "alice_def456",
  "qr_code": "data:image/png;base64,..."
}
```

#### GET /sessions/{token}/memory
Get memory for session.

**Response:**
```json
{
  "facts": [
    {"key": "name", "value": "Alice Smith"},
    {"key": "preferences", "value": "..."}
  ]
}
```

---

## User Profile Management

### Overview

Persistent user profiles storing persona preferences, tone settings, and other personalization data.

### Implementation

Location: `memory/user_profile.py`

```python
class UserProfileManager:
    """Store and retrieve user profiles via the unified memory layer."""

    def set_profile(
        self,
        identity: str,
        persona: str | None = None,
        tone: str | None = None,
        email: str | None = None,
    ) -> None:
        """Set or update user profile."""

    def get_profile(self, identity: str) -> dict | None:
        """Get user profile."""

    def load_from_yaml(self, path: str = "config/user_prefs.yaml") -> None:
        """Load profiles from YAML configuration."""
```

### Features

#### Profile Creation

```python
from memory.user_profile import UserProfileManager

profile_manager = UserProfileManager()

# Set profile for user
profile_manager.set_profile(
    identity="alice",
    persona="assistant",
    tone="professional",
    email="alice@example.com"
)
```

#### Profile Retrieval

```python
# Get profile
profile = profile_manager.get_profile("alice")
if profile:
    print(f"Persona: {profile['persona']}")
    print(f"Tone: {profile['tone']}")
    print(f"Email: {profile['email']}")
```

#### YAML Configuration

Create `config/user_prefs.yaml`:

```yaml
alice:
  persona: assistant
  tone: professional
  email: alice@example.com

bob:
  persona: partner
  tone: casual
  email: bob@example.com

researcher_mode:
  persona: researcher
  tone: formal
```

Load profiles on startup:

```python
profile_manager.load_from_yaml("config/user_prefs.yaml")
```

### Usage Examples

#### Dynamic Profile Switching

```python
def handle_user_message(identity: str, message: str):
    """Handle message with user's profile preferences."""
    profile = profile_manager.get_profile(identity)

    # Use persona and tone for response shaping
    persona = profile.get("persona") if profile else "assistant"
    tone = profile.get("tone") if profile else "neutral"

    response = llm_router.get_response(
        message,
        persona=persona,
        tone=tone
    )

    return response
```

#### Profile Updates

```python
# Update specific field
profile_manager.set_profile(
    identity="alice",
    persona="researcher",  # Changed from assistant
    tone="formal"
)
```

### API Endpoints

#### GET /profiles/{identity}
Get user profile.

**Response:**
```json
{
  "identity": "alice",
  "persona": "assistant",
  "tone": "professional",
  "email": "alice@example.com"
}
```

#### POST /profiles/{identity}
Create or update user profile.

**Request:**
```json
{
  "persona": "researcher",
  "tone": "formal",
  "email": "alice@example.com"
}
```

---

## Persona & Tone Shaping

### Overview

Adaptive response shaping based on persona (assistant/partner/researcher) and tone (formal/informal/neutral).

### Implementation

Location: `agent/response_shaper.py`

```python
class ResponseShaper:
    """Apply simple stylistic transformations to model output."""

    def shape(
        self,
        text: str,
        persona: str | None = None,
        tone: str | None = None
    ) -> str:
        """Return the text adjusted for persona and tone."""
```

### Features

#### Tone Transformations

**Informal Tone:**
- "I am" → "I'm"
- "do not" → "don't"
- "cannot" → "can't"

**Formal Tone:**
- "I'm" → "I am"
- "don't" → "do not"
- "can't" → "cannot"

#### Persona Prefixes

Different personas add characteristic greetings:

```python
_PERSONA_PREFIX = {
    "partner": "Hey there,",
    "assistant": "",
    "researcher": ""
}
```

### Usage Examples

#### Basic Shaping

```python
from agent.response_shaper import ResponseShaper

shaper = ResponseShaper()

text = "I am going to help you with this task."

# Informal tone
informal = shaper.shape(text, tone="informal")
# "I'm going to help you with this task."

# Formal tone
formal = shaper.shape(text, tone="formal")
# "I am going to help you with this task."

# Partner persona
partner = shaper.shape(text, persona="partner")
# "Hey there, I am going to help you with this task."
```

#### LLM Integration

```python
def get_shaped_response(prompt: str, identity: str) -> str:
    """Get LLM response shaped by user preferences."""
    profile = profile_manager.get_profile(identity)

    # Get raw response
    response = llm_router.get_response(prompt)

    # Shape based on profile
    if profile:
        shaper = ResponseShaper()
        response = shaper.shape(
            response,
            persona=profile.get("persona"),
            tone=profile.get("tone")
        )

    return response
```

#### Length Limiting

```python
# Limit response length
shaper = ResponseShaper(max_length=280)
shaped = shaper.shape(long_text)  # Truncated to 280 chars
```

### Persona Types

**Assistant** (Default):
- Professional and helpful
- Clear and concise
- Task-oriented

**Partner**:
- Friendly and conversational
- Uses casual greetings
- More personal tone

**Researcher**:
- Formal and detailed
- Academic style
- Comprehensive responses

### Tone Options

**Neutral** (Default):
- Natural language
- Balanced formality
- Standard contractions

**Formal**:
- No contractions
- Full words
- Professional style

**Informal**:
- Heavy contractions
- Casual language
- Conversational style

---

## Calendar Integration

### Overview

Export reminders and goals as iCalendar (`.ics`) files for import into calendar applications.

### Implementation

Location: `agent/calendar_exporter.py`

```python
class CalendarExporter:
    """Generate iCalendar files from stored reminders."""

    def export(
        self,
        thread_id: str = "default_thread",
        path: str | None = None
    ) -> str:
        """Return calendar data and optionally write it to path."""
```

### Features

#### Export Reminders

```python
from agent.calendar_exporter import CalendarExporter
from memory.memory_handler import MemoryHandler

memory = MemoryHandler()
exporter = CalendarExporter(memory)

# Export reminders as ICS
ics_data = exporter.export(
    thread_id="alice_thread",
    path="reminders.ics"
)

# ics_data contains full iCalendar format
```

#### ICS Format

Generated calendar entries include:
- Event summary (reminder message)
- Start time (reminder time)
- End time (start + 1 hour)
- Standard iCalendar formatting

Example output:

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Axon//Reminder Export//EN
BEGIN:VEVENT
SUMMARY:Team meeting
DTSTART:20250122T150000Z
DTEND:20250122T160000Z
END:VEVENT
END:VCALENDAR
```

### Usage Examples

#### Batch Export

```python
# Export all user reminders
for identity in ["alice", "bob", "charlie"]:
    thread_id = f"{identity}_thread"
    exporter.export(thread_id, path=f"calendars/{identity}_reminders.ics")
```

#### Direct Import

```python
import subprocess

# Export and open in default calendar app
ics_data = exporter.export("my_thread", "temp_reminders.ics")

# macOS
subprocess.run(["open", "temp_reminders.ics"])

# Linux
subprocess.run(["xdg-open", "temp_reminders.ics"])

# Windows
subprocess.run(["start", "temp_reminders.ics"], shell=True)
```

### Requirements

Optional dependency (install if needed):

```bash
pip install icalendar
```

If not installed, calendar export will raise `RuntimeError`.

---

## Notification & Reminder System

### Overview

Comprehensive notification and reminder system with in-memory scheduling and persistence.

### Implementation

Location: `agent/reminder.py`, `agent/notifier.py`

```python
class ReminderManager:
    """Schedule and manage reminders with notifications."""

    def schedule(
        self,
        message: str,
        delay_seconds: int,
        thread_id: str = "default_thread"
    ) -> str:
        """Schedule a reminder."""

    def list_reminders(self, thread_id: str) -> list[dict]:
        """List all active reminders for thread."""

    def delete_reminder(self, thread_id: str, key: str) -> bool:
        """Cancel a reminder."""
```

### Features

#### Schedule Reminders

```python
from agent.reminder import ReminderManager
from agent.notifier import Notifier
from memory.memory_handler import MemoryHandler

notifier = Notifier()
memory = MemoryHandler()
reminder_manager = ReminderManager(notifier, memory)

# Schedule reminder for 1 hour
key = reminder_manager.schedule(
    message="Team meeting in conference room",
    delay_seconds=3600,  # 1 hour
    thread_id="alice_thread"
)

print(f"Reminder scheduled: {key}")
```

#### List Active Reminders

```python
# Get all reminders for user
reminders = reminder_manager.list_reminders("alice_thread")

for r in reminders:
    print(f"{r['key']}: {r['message']} at {r['time']}")
```

#### Cancel Reminders

```python
# Delete specific reminder
success = reminder_manager.delete_reminder("alice_thread", key)
```

#### Notification System

```python
from agent.notifier import Notifier

notifier = Notifier()

# Send notification
notifier.notify(
    title="Reminder",
    message="Meeting in 5 minutes"
)
```

### Usage Examples

#### Natural Language Reminders

Combined with Phase 4 date parsing:

```python
from agent.date_parser import NaturalDateParser

parser = NaturalDateParser()

# Parse "tomorrow at 3pm"
result = parser.parse("tomorrow at 3pm")

if result:
    # Calculate delay from now
    delay = result.timestamp - int(time.time())

    # Schedule reminder
    reminder_manager.schedule(
        message="Doctor appointment",
        delay_seconds=delay,
        thread_id="alice_thread"
    )
```

#### Persistent Storage

Reminders are automatically saved to memory and restored on restart:

```python
# Reminders stored as facts
{
    "key": "reminder_1737558000",
    "value": '{"message": "Meeting", "time": 1737558000}',
    "identity": "reminder"
}
```

### API Endpoints

#### POST /reminders/{thread_id}
Schedule a reminder.

**Request:**
```json
{
  "message": "Team meeting",
  "delay_seconds": 3600
}
```

**Response:**
```json
{
  "key": "reminder_1737558000",
  "scheduled_for": 1737558000
}
```

#### GET /reminders/{thread_id}
List all reminders.

**Response:**
```json
{
  "reminders": [
    {
      "key": "reminder_1737558000",
      "message": "Team meeting",
      "time": 1737558000
    }
  ]
}
```

#### With NLP (from Phase 4):

**POST /reminders/create-with-nlp**

```json
{
  "thread_id": "alice_thread",
  "text": "tomorrow at 3pm",
  "message": "Doctor appointment"
}
```

---

## TUI Interface

### Overview

Text-based UI for power users with full agent integration and memory display.

### Implementation

Location: `main.py` (TUI command)

```python
@app.command()
def tui(
    thread_id: str = "tui_thread",
    identity: str = "tui_user",
) -> None:
    """Enhanced text-based UI with agent integration and memory display."""
```

### Features

#### Interactive Commands

- `/memory` - Display all memory entries
- `/goals` - Show active goals
- `/quit` - Exit TUI mode
- Direct messages - Send to LLM for processing

#### Memory Display

Rich table showing:
- Key
- Value (truncated)
- Identity
- Locked status

#### Goals Display

Table showing:
- Goal ID
- Text
- Status (Done/Deferred/Active)
- Priority

### Usage Examples

#### Start TUI

```bash
python -m main tui
```

With custom identity:

```bash
python -m main tui --identity alice --thread-id alice_main
```

#### TUI Session

```
Axon TUI mode. Commands: /memory, /goals, /quit

You: /memory
┏━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┓
┃ Key  ┃ Value       ┃ Identity ┃ Locked ┃
┡━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━┩
│ name │ Alice Smith │ alice    │ ✓      │
└──────┴─────────────┴──────────┴────────┘

You: what is my name?
Agent: Your name is Alice Smith.

You: /goals
┏━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID  ┃ Text           ┃ Status   ┃ Priority ┃
┡━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 1   │ Learn Python   │ ⏳ Active│ 1        │
└─────┴────────────────┴──────────┴──────────┘
```

#### Profile Integration

TUI automatically loads user profiles:

```python
# In TUI code
profile = profile_manager.get_profile(identity)
persona = profile.get("persona") if profile else None
tone = profile.get("tone") if profile else None

response = llm_router.get_response(
    user_input,
    persona=persona,
    tone=tone
)
```

---

## API Reference

### Complete Endpoint List

#### Sessions
- `POST /sessions/login` - Create session
- `GET /sessions/qr/{token}` - Get QR code for session
- `GET /sessions/{token}/memory` - Get session memory

#### Profiles
- `GET /profiles/{identity}` - Get user profile
- `POST /profiles/{identity}` - Create/update profile

#### Reminders
- `POST /reminders/{thread_id}` - Schedule reminder
- `GET /reminders/{thread_id}` - List reminders
- `POST /reminders/create-with-nlp` - Create with natural language (Phase 4)

#### Goals (related to personalization)
- `POST /goals/{thread_id}` - Create goal
- `GET /goals/{thread_id}` - List goals
- `GET /goals/{thread_id}/deferred` - List deferred goals

---

## Use Cases

### Family Setup

```python
# Setup profiles for family members
profile_manager.set_profile("dad", persona="partner", tone="casual")
profile_manager.set_profile("mom", persona="assistant", tone="professional")
profile_manager.set_profile("kid", persona="partner", tone="informal")

# Each family member gets personalized responses
```

### Work vs Personal

```python
# Work profile - formal and structured
profile_manager.set_profile(
    "alice_work",
    persona="assistant",
    tone="formal",
    email="alice@company.com"
)

# Personal profile - casual and friendly
profile_manager.set_profile(
    "alice_personal",
    persona="partner",
    tone="informal",
    email="alice@personal.com"
)
```

### Guest Access

```python
# Temporary guest session
guest_token, guest_thread = session_tracker.create_session("guest")

# Guest has isolated context
# Can be removed when done
session_tracker.remove(guest_token)
```

### Researcher Mode

```python
# Configure for research work
profile_manager.set_profile(
    "researcher",
    persona="researcher",
    tone="formal"
)

# Responses will be formal and detailed
```

---

## Performance Considerations

### Session Tracking

- **In-Memory**: Fast O(1) lookups
- **No Persistence**: Sessions lost on restart (by design)
- **Token Security**: Cryptographically secure random tokens
- **Memory Overhead**: ~200 bytes per session

### Profile Management

- **Database-Backed**: Persistent across restarts
- **YAML Loading**: One-time load on startup
- **Update Performance**: O(1) for get/set operations
- **Storage**: Minimal (~500 bytes per profile)

### Reminder System

- **Threading**: Uses Python threading for timers
- **Persistence**: Reminders saved to memory store
- **Recovery**: Timers recreated on restart from stored data
- **Scalability**: Handles hundreds of concurrent reminders

### Response Shaping

- **Regex Performance**: O(n) where n = response length
- **Memory**: Minimal overhead
- **Latency**: <1ms for typical responses
- **Caching**: No caching (transformations are fast)

---

## Security Considerations

### Session Security

- Tokens generated with `secrets.token_urlsafe()` (256 bits)
- No predictable patterns in session IDs
- Sessions isolated by token
- No cross-session data leakage

### Profile Privacy

- Profiles stored per-identity in isolated records
- No cross-user profile access
- Email addresses stored locally only
- YAML configuration files should be protected

### Best Practices

```python
# Validate identity before creating session
def create_secure_session(identity: str, auth_token: str):
    if not validate_auth(auth_token):
        raise PermissionError("Invalid authentication")

    return session_tracker.create_session(identity)

# Remove sessions on logout
def logout(session_token: str):
    session_tracker.remove(session_token)
```

---

## Future Enhancements

Potential Phase 5 extensions:

- **Session Persistence**: Save sessions to disk for restart recovery
- **Advanced Personas**: More persona types with richer behaviors
- **Scheduling**: Recurring reminders (daily, weekly, monthly)
- **Multi-Calendar**: Export to different calendar formats
- **Voice Personas**: TTS voice selection per user
- **Profile Templates**: Pre-configured profile bundles
- **Session Analytics**: Track usage patterns per identity

---

**Last Updated**: 2025-01-22
**Phase**: 5
**Status**: Complete
