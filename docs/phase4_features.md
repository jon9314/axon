# Phase 4 Features: Remote Model & API Tooling

This document describes the Phase 4 enhancements to Axon, focusing on controlled cloud integration and enhanced user experience features.

## Overview

Phase 4 adds optional cloud integration with strict user consent requirements, along with quality-of-life improvements for working with remote LLMs and creating reminders. All cloud features require explicit manual consent before making any external requests.

Key features:
- Hosted proxy with manual consent system
- Source annotation tracking for pasted responses
- Natural language date parsing
- Text-to-speech and audio notifications

## Table of Contents

1. [Hosted Proxy with Consent](#hosted-proxy-with-consent)
2. [Source Annotation Tracking](#source-annotation-tracking)
3. [Natural Language Date Parsing](#natural-language-date-parsing)
4. [Text-to-Speech & Audio Notifications](#text-to-speech--audio-notifications)
5. [API Reference](#api-reference)
6. [Security Considerations](#security-considerations)

---

## Hosted Proxy with Consent

### Overview

The hosted proxy system enables controlled access to cloud LLM providers (OpenAI, Anthropic, Google, etc.) with **mandatory user consent** before any external requests. This ensures users maintain full control over data sharing and API usage.

### Implementation

Location: `agent/hosted_proxy.py`

```python
class HostedProxyClient:
    """Client for hosted LLM proxy with manual consent requirements."""

    def __init__(
        self,
        consent_db_path: str = "data/proxy_consent.json",
        proxy_url: str | None = None,
    ) -> None:
        """Initialize hosted proxy client."""
```

### Features

#### Consent Management

**Persistent Consent**: Stored on disk, survives restarts
```python
# Grant persistent consent
proxy.grant_consent(
    user_id="alice",
    provider="openai",
    session_only=False  # Persisted to disk
)
```

**Session-Only Consent**: Valid for current session only
```python
# Grant temporary consent
proxy.grant_consent(
    user_id="alice",
    provider="anthropic",
    session_only=True  # Not persisted
)
```

**Provider-Specific or Universal**:
```python
# Consent for specific provider
proxy.grant_consent("alice", "openai")

# Consent for all providers
proxy.grant_consent("alice", "openai", all_providers=True)
```

#### Consent Checks

All proxy calls automatically check for consent:

```python
# This will raise PermissionError if consent not granted
try:
    response = proxy.call_with_consent(
        user_id="alice",
        provider="openai",
        prompt="Explain quantum computing",
        model="gpt-4",
        max_tokens=1000
    )
except PermissionError:
    print("Consent not granted - ask user for permission first")
```

#### Consent Revocation

```python
# Revoke persistent consent
proxy.revoke_consent("alice", session_only=False)

# Revoke session consent only
proxy.revoke_consent("alice", session_only=True)
```

### Usage Examples

#### Basic Workflow

```python
from agent.hosted_proxy import HostedProxyClient

# Initialize client
proxy = HostedProxyClient()

# Check consent status
status = proxy.get_consent_status("alice")
if not status["granted"]:
    # Request consent through UI
    proxy.grant_consent("alice", "openai")

# Make request (requires consent)
response = proxy.call_with_consent(
    user_id="alice",
    provider="openai",
    prompt="What is machine learning?",
    model="gpt-4-turbo"
)
```

#### Consent Workflow with UI

```python
# In your UI/CLI code:
def request_user_consent(user_id, provider):
    """Ask user for consent via UI."""
    answer = input(f"Grant access to {provider} for user {user_id}? (y/n): ")

    if answer.lower() == "y":
        session_only = input("Session only? (y/n): ").lower() == "y"
        proxy.grant_consent(user_id, provider, session_only=session_only)
        return True

    return False

# Usage
if not proxy.request_consent("alice", "openai"):
    if request_user_consent("alice", "openai"):
        response = proxy.call_with_consent(...)
```

### API Endpoints

#### POST /proxy/consent/grant
Grant consent for hosted proxy usage.

**Request:**
```json
{
  "user_id": "alice",
  "provider": "openai",
  "session_only": false,
  "all_providers": false
}
```

**Response:**
```json
{
  "status": "granted",
  "user_id": "alice",
  "provider": "openai"
}
```

#### POST /proxy/consent/revoke
Revoke consent.

**Request:**
```json
{
  "user_id": "alice",
  "session_only": false
}
```

#### GET /proxy/consent/{user_id}
Get consent status for user.

**Response:**
```json
{
  "granted": true,
  "timestamp": "2025-01-21T14:30:00Z",
  "session_only": false,
  "providers": ["openai"]
}
```

#### GET /proxy/consents
List all consent records.

**Response:**
```json
{
  "consents": {
    "alice": {
      "granted": true,
      "providers": ["openai"],
      "session_only": false
    },
    "bob": {
      "granted": true,
      "providers": ["*"],
      "session_only": true
    }
  }
}
```

#### POST /proxy/call
Call hosted proxy (requires consent).

**Request:**
```json
{
  "user_id": "alice",
  "provider": "openai",
  "prompt": "Explain quantum computing",
  "model": "gpt-4",
  "max_tokens": 1000,
  "temperature": 0.7
}
```

**Response (currently placeholder):**
```json
{
  "status": "consent_granted_but_not_implemented",
  "message": "Hosted proxy call would be made here with user consent",
  "user_id": "alice",
  "provider": "openai"
}
```

---

## Source Annotation Tracking

### Overview

Enhanced pasteback handler that tracks detailed source information for responses pasted from cloud LLMs, including model, provider, cost, token usage, and custom metadata.

### Implementation

Location: `agent/pasteback_handler.py`

```python
class SourceAnnotation:
    """Metadata about the source of a pasted response."""

    def __init__(
        self,
        model: str,
        provider: str | None = None,
        timestamp: str | None = None,
        url: str | None = None,
        cost: float | None = None,
        tokens: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Create source annotation."""
```

### Features

#### Automatic Provider Detection

The system automatically infers the provider from model names:

```python
annotation = SourceAnnotation(model="gpt-4-turbo")
print(annotation.provider)  # "openai"

annotation = SourceAnnotation(model="claude-3-opus")
print(annotation.provider)  # "anthropic"

annotation = SourceAnnotation(model="gemini-pro")
print(annotation.provider)  # "google"
```

#### Rich Metadata Tracking

Track comprehensive information about cloud LLM usage:

```python
annotation = SourceAnnotation(
    model="gpt-4-turbo",
    provider="openai",
    url="https://chat.openai.com/c/abc123",
    cost=0.03,  # USD
    tokens=1500,
    metadata={
        "conversation_id": "abc123",
        "temperature": 0.7,
        "top_p": 0.9
    }
)
```

#### Storage and Retrieval

```python
handler = PastebackHandler(memory_handler)

# Store with full annotation
handler.store_with_metadata(
    thread_id="session_1",
    prompt="Explain neural networks",
    response="Neural networks are...",
    model="gpt-4-turbo",
    provider="openai",
    url="https://chat.openai.com/c/123",
    cost=0.05,
    tokens=2000,
    metadata={"quality_rating": 5}
)

# Retrieve annotated responses
responses = handler.get_annotated_responses("session_1", memory_handler)
for r in responses:
    print(f"Model: {r['source'].model}")
    print(f"Provider: {r['source'].provider}")
    print(f"Cost: ${r['source'].cost}")
    print(f"Response: {r['response']}")
```

### Usage Examples

#### Basic Usage

```python
from agent.pasteback_handler import PastebackHandler, SourceAnnotation
from memory.memory_handler import MemoryHandler

memory = MemoryHandler()
handler = PastebackHandler(memory)

# Create annotation
annotation = SourceAnnotation(
    model="gpt-4",
    provider="openai",
    cost=0.03,
    tokens=500
)

# Store pasted response
handler.store(
    thread_id="my_session",
    prompt="What is AI?",
    response="AI is artificial intelligence...",
    model="gpt-4",
    source_annotation=annotation
)
```

#### Convenience Method

```python
# Shorthand for common use case
handler.store_with_metadata(
    thread_id="my_session",
    prompt="What is machine learning?",
    response="Machine learning is...",
    model="gpt-4-turbo",
    url="https://chat.openai.com/c/abc",
    cost=0.05,
    tokens=1200
)
```

#### Cost Tracking

```python
# Track total costs
responses = handler.get_annotated_responses("my_session", memory)
total_cost = sum(r["source"].cost or 0 for r in responses)
print(f"Total API costs: ${total_cost:.2f}")

# Track by provider
from collections import defaultdict
costs_by_provider = defaultdict(float)
for r in responses:
    provider = r["source"].provider
    cost = r["source"].cost or 0
    costs_by_provider[provider] += cost

for provider, cost in costs_by_provider.items():
    print(f"{provider}: ${cost:.2f}")
```

### API Endpoints

#### POST /pasteback/store
Store pasted response with source annotations.

**Request:**
```json
{
  "thread_id": "session_1",
  "prompt": "Explain quantum computing",
  "response": "Quantum computing uses...",
  "model": "gpt-4-turbo",
  "provider": "openai",
  "url": "https://chat.openai.com/c/123",
  "cost": 0.05,
  "tokens": 2000,
  "metadata": {"conversation_id": "123"}
}
```

**Response:**
```json
{
  "status": "stored",
  "thread_id": "session_1"
}
```

#### GET /pasteback/responses/{thread_id}
Retrieve annotated responses.

**Response:**
```json
{
  "responses": [
    {
      "key": "cloud_response_1234567890",
      "response": "Quantum computing uses...",
      "source": {
        "model": "gpt-4-turbo",
        "provider": "openai",
        "timestamp": "2025-01-21T14:30:00Z",
        "url": "https://chat.openai.com/c/123",
        "cost": 0.05,
        "tokens": 2000,
        "metadata": {"conversation_id": "123"}
      }
    }
  ]
}
```

---

## Natural Language Date Parsing

### Overview

Parse human-readable date expressions into timestamps for creating reminders and scheduling events.

### Implementation

Location: `agent/date_parser.py`

```python
class NaturalDateParser:
    """Parse natural language date expressions into timestamps."""

    def __init__(self, base_time: datetime | None = None) -> None:
        """Initialize parser with optional base time."""
```

### Supported Expressions

#### Relative Time
- "in 2 hours"
- "in 30 minutes"
- "in 5 days"
- "in 3 weeks"

#### Named Days
- "tomorrow"
- "today at 3pm"
- "tonight"
- "yesterday"

#### Specific Times
- "3pm"
- "14:30"
- "9:00 AM"
- "2:45 PM"

#### Weekdays
- "next Monday"
- "Friday"
- "this Thursday at 10am"

#### Absolute Dates
- "December 25"
- "March 15, 2026"
- "Jan 1st"
- "2025-06-01" (ISO format)

### Usage Examples

#### Basic Parsing

```python
from agent.date_parser import NaturalDateParser

parser = NaturalDateParser()

# Parse various expressions
result = parser.parse("tomorrow at 3pm")
print(f"Timestamp: {result.timestamp}")
print(f"DateTime: {result.datetime_obj}")
print(f"Confidence: {result.confidence}")
print(f"Components: {result.components}")
```

#### Creating Reminders

```python
# Parse date and create reminder
text = "remind me tomorrow at 3pm"
date_text = "tomorrow at 3pm"

result = parser.parse(date_text)
if result:
    reminder_manager.set_reminder(
        thread_id="session_1",
        message="Your reminder",
        time=result.timestamp
    )
```

#### Duration Parsing

```python
# Parse durations
seconds = parser.parse_duration("2 hours and 30 minutes")
print(f"Duration: {seconds} seconds")  # 9000

# Use for relative reminders
parser.parse_duration("1 day")  # 86400 seconds
```

#### Batch Processing

```python
# Process multiple date expressions
expressions = [
    "tomorrow at 3pm",
    "next Friday",
    "in 2 hours",
    "December 25 at 9am"
]

for expr in expressions:
    result = parser.parse(expr)
    if result:
        print(f"{expr} -> {result.datetime_obj.isoformat()}")
    else:
        print(f"Could not parse: {expr}")
```

### API Endpoints

#### POST /date/parse
Parse natural language date expression.

**Request:**
```json
{
  "text": "tomorrow at 3pm"
}
```

**Response:**
```json
{
  "timestamp": 1737558000,
  "datetime": "2025-01-22T15:00:00+00:00",
  "original_text": "tomorrow at 3pm",
  "confidence": 0.95,
  "components": {
    "type": "named_day",
    "day": "tomorrow",
    "hour": 15,
    "minute": 0
  }
}
```

#### POST /date/parse-duration
Parse duration expression.

**Request:**
```json
{
  "text": "2 hours and 30 minutes"
}
```

**Response:**
```json
{
  "duration_seconds": 9000,
  "original_text": "2 hours and 30 minutes"
}
```

#### POST /reminders/create-with-nlp
Create reminder using natural language.

**Request:**
```json
{
  "thread_id": "session_1",
  "text": "tomorrow at 3pm",
  "message": "Call dentist"
}
```

**Response:**
```json
{
  "status": "created",
  "timestamp": 1737558000,
  "datetime": "2025-01-22T15:00:00+00:00",
  "message": "Call dentist"
}
```

### Parsing Accuracy

The parser provides confidence scores for each parse result:

- **0.95+**: High confidence (exact matches like "tomorrow", "in X hours")
- **0.85-0.94**: Good confidence (weekdays, specific times)
- **0.80-0.84**: Moderate confidence (complex expressions)

```python
result = parser.parse("tomorrow at 3pm")
if result.confidence > 0.9:
    # High confidence - use directly
    create_reminder(result.timestamp)
else:
    # Lower confidence - confirm with user
    confirm_with_user(result)
```

---

## Text-to-Speech & Audio Notifications

### Overview

TTS capabilities for speaking agent responses and audio notification alerts for reminders and events.

### Implementation

Location: `agent/audio_notifier.py`

### Supported TTS Engines

1. **pyttsx3** (local, offline)
2. **gTTS** (Google TTS, requires internet)
3. **System TTS** (platform-specific)
   - macOS: `say` command
   - Windows: PowerShell speech synthesis
   - Linux: `espeak` or `festival`

### Features

#### Text-to-Speech

```python
from agent.audio_notifier import TTSEngine

# Initialize TTS engine
tts = TTSEngine(
    engine="auto",  # Automatically selects best available
    rate=175,       # Words per minute
    volume=0.9      # 0.0 to 1.0
)

# Speak text
tts.speak("Hello, this is Axon speaking", blocking=True)

# Non-blocking speech
tts.speak("Processing your request", blocking=False)
```

#### Voice Selection

```python
# List available voices
voices = tts.list_voices()
for voice in voices:
    print(voice)

# Set specific voice
tts.set_voice("com.apple.speech.synthesis.voice.samantha")
```

#### Audio Notifications

```python
from agent.audio_notifier import AudioNotifier

# Initialize notifier
notifier = AudioNotifier(sounds_dir="data/sounds")

# Play notification sound
notifier.play_notification("reminder")

# Send reminder with TTS
notifier.notify_reminder(
    message="Time for your meeting",
    speak=True
)

# Send alert with urgency level
notifier.notify_alert(
    message="Critical system alert",
    urgency="critical"  # low, normal, high, critical
)
```

#### Combined Service

```python
from agent.audio_notifier import TTSNotificationService

# Initialize combined service
service = TTSNotificationService(
    tts_engine="auto",
    sounds_dir="data/sounds",
    enabled=True
)

# Speak agent response
service.speak_response("Your request has been processed")

# Send notification with speech
service.notify_with_speech(
    message="Reminder: Team meeting in 5 minutes",
    sound="reminder"
)

# Enable/disable on the fly
service.set_enabled(False)  # Silence all notifications
```

### Usage Examples

#### Reminder Notifications

```python
# When reminder triggers
def on_reminder_trigger(reminder):
    service = TTSNotificationService(enabled=True)

    # Play sound and speak message
    service.notify_with_speech(
        message=reminder.message,
        sound="reminder"
    )
```

#### Agent Response Reading

```python
# Speak agent responses
def send_response_with_tts(response_text, tts_enabled=False):
    if tts_enabled:
        service = TTSNotificationService(enabled=True)
        service.speak_response(response_text, blocking=False)

    return response_text
```

#### Custom Sound Files

Place `.wav` files in `data/sounds/`:
- `default.wav` - Default notification
- `reminder.wav` - Reminder sound
- `alert.wav` - Normal alert
- `urgent.wav` - High priority alert
- `critical.wav` - Critical alert

```python
notifier = AudioNotifier(sounds_dir="data/sounds")
notifier.play_notification("custom_sound")  # Plays custom_sound.wav
```

### API Endpoints

#### POST /tts/speak
Speak text using TTS.

**Request:**
```json
{
  "text": "Hello from Axon",
  "blocking": false
}
```

**Response:**
```json
{
  "success": true,
  "text": "Hello from Axon"
}
```

#### POST /tts/notify
Send notification with TTS.

**Request:**
```json
{
  "message": "Reminder: Team meeting",
  "sound": "reminder"
}
```

**Response:**
```json
{
  "status": "sent",
  "message": "Reminder: Team meeting"
}
```

#### POST /tts/enable
Enable or disable TTS service.

**Request:**
```json
{
  "enabled": true
}
```

**Response:**
```json
{
  "status": "enabled"
}
```

#### GET /tts/status
Get TTS service status.

**Response:**
```json
{
  "enabled": true
}
```

---

## API Reference

### Complete Endpoint List

#### Hosted Proxy
- `POST /proxy/consent/grant` - Grant consent
- `POST /proxy/consent/revoke` - Revoke consent
- `GET /proxy/consent/{user_id}` - Get consent status
- `GET /proxy/consents` - List all consents
- `POST /proxy/call` - Call proxy (requires consent)

#### Source Annotations
- `POST /pasteback/store` - Store annotated response
- `GET /pasteback/responses/{thread_id}` - Get annotated responses

#### Date Parsing
- `POST /date/parse` - Parse natural language date
- `POST /date/parse-duration` - Parse duration
- `POST /reminders/create-with-nlp` - Create reminder with NLP

#### Text-to-Speech
- `POST /tts/speak` - Speak text
- `POST /tts/notify` - Send notification with TTS
- `POST /tts/enable` - Enable/disable TTS
- `GET /tts/status` - Get TTS status

---

## Security Considerations

### Hosted Proxy Security

1. **Consent Requirement**: All proxy calls require explicit user consent
2. **Consent Persistence**: Consent records stored locally in `data/proxy_consent.json`
3. **Revocation**: Users can revoke consent at any time
4. **Session Isolation**: Session-only consent doesn't persist across restarts
5. **Provider Specificity**: Can grant consent per-provider or universally

### Best Practices

```python
# Always check consent before UI operations
def request_cloud_llm(user_id, provider, prompt):
    """Request cloud LLM with consent check."""
    if not proxy.request_consent(user_id, provider):
        # Show consent dialog to user
        if not show_consent_dialog(user_id, provider):
            raise PermissionError("User denied consent")

        # Grant consent based on user choice
        proxy.grant_consent(user_id, provider, session_only=True)

    # Now safe to make request
    return proxy.call_with_consent(user_id, provider, prompt)
```

### Data Privacy

- All consent records stored locally
- No automatic cloud requests without consent
- Source annotations stored in local memory only
- No telemetry or tracking of cloud usage

---

## Performance Considerations

### Date Parsing

- **Average parse time**: <1ms for simple expressions
- **Complex expressions**: 1-5ms
- **Memory overhead**: Minimal (~1KB per parser instance)

### TTS Performance

- **pyttsx3**: Fastest, no network required
- **gTTS**: Requires internet, 200-500ms latency
- **System TTS**: Varies by platform, generally fast

### Recommendations

1. **Cache parsed dates** for repeated expressions
2. **Use non-blocking TTS** for UI responsiveness
3. **Prefer pyttsx3** for offline/low-latency needs
4. **Batch date parsing** when processing multiple reminders

---

## Future Enhancements

Potential Phase 4 extensions:

- **Smart consent expiration** (time-based, usage-based)
- **Cost budgets** per user/provider
- **Advanced date parsing** (recurring events, complex ranges)
- **Voice cloning** for personalized TTS
- **Multi-language support** for date parsing
- **Notification channels** (email, SMS, push)

---

**Last Updated**: 2025-01-21
**Phase**: 4
**Status**: Complete
