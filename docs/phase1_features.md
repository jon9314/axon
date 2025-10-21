# Phase 1 Features

This document describes the features implemented in Phase 1 of Axon development.

## Enhanced TUI Mode

The Text User Interface (TUI) has been significantly enhanced with full agent integration.

### Features

- **Agent Integration**: Full LLM integration with persona and tone support
- **Memory Display**: View all memory entries with `/memory` command
- **Goal Display**: View active goals with `/goals` command
- **Plugin Support**: Execute plugins directly from TUI
- **Rich Formatting**: Tables and colored output using Rich library

### Usage

```bash
python main.py tui --identity your_name --thread-id your_thread
```

### Commands

- `/memory` - Display all memory entries for current thread
- `/goals` - Display active goals with status and priority
- `/quit` or `/exit` - Exit TUI mode
- Any other input - Send to LLM agent for processing

### Example Session

```
$ python main.py tui
Axon TUI mode. Commands: /memory, /goals, /quit
You: /memory
┌─────────────────────────────────────────────────┐
│              Memory Entries                      │
├──────────┬─────────────┬──────────┬────────────┤
│ Key      │ Value       │ Identity │ Locked     │
├──────────┼─────────────┼──────────┼────────────┤
│ user_name│ Alex        │ default  │ ✓          │
└──────────┴─────────────┴──────────┴────────────┘

You: What's the weather like?
Axon: I'll check the weather for you...
```

## LLM Confidence Metrics

LLM responses now include confidence scoring to help evaluate response quality.

### Confidence Calculation

The confidence score (0.0 to 1.0) is based on:

1. **Response Length**: Detailed responses score higher
2. **Uncertainty Markers**: Phrases like "I'm not sure" reduce confidence
3. **Structured Content**: Lists, code blocks, and formatting increase confidence
4. **Error Indicators**: Error messages reduce confidence
5. **Keyword Overlap**: Relevance to the original prompt

### API

```python
from agent.llm_router import LLMRouter

router = LLMRouter()

# Get response with confidence
response, confidence = router.get_response_with_confidence(
    prompt="Explain machine learning",
    model="openrouter/horizon-beta"
)

print(f"Response: {response}")
print(f"Confidence: {confidence:.2f}")
```

### Integration

Confidence metrics are used in:
- Hybrid vector search scoring
- Response quality assessment
- Fallback decision-making

## Improved Hybrid Vector Scoring

The vector search now uses an advanced hybrid scoring algorithm combining vector similarity with LLM confidence.

### Features

- **Configurable Weights**: Adjust vector vs. confidence importance
- **Diversity Boosting**: Penalize very similar results to promote variety
- **Normalized Scoring**: Weights are automatically normalized
- **Sorted Results**: Results ranked by hybrid score

### Default Weights

- **Vector Weight**: 0.7 (70% emphasis on semantic similarity)
- **Confidence Weight**: 0.3 (30% emphasis on LLM confidence)

### Usage

```python
from memory.vector_store import VectorStore

store = VectorStore("localhost", 6333)

results = store.hybrid_search(
    collection_name="memories",
    query_vector=[0.1, 0.2, ...],
    llm_confidence=0.85,
    limit=5,
    vector_weight=0.7,
    confidence_weight=0.3,
    diversity_boost=True
)
```

### Algorithm Details

1. Fetch initial results from vector database
2. Apply weighted combination: `score = (V_weight * vector_score) + (C_weight * llm_confidence)`
3. If diversity boost enabled, penalize results very similar to top matches
4. Sort by hybrid score descending
5. Return top N results

## Domain-Aware Memory

Memory entries now support domain categorization for better organization.

### Supported Domains

The initial memory includes examples of:

- **personal**: User preferences, personal information
- **project**: Work-related data, project details
- **health**: Fitness goals, health tracking
- **finance**: Budget, savings, financial goals
- **learning**: Educational content, courses, books

### Data Format

```yaml
facts:
  - thread_id: default_thread
    key: user_name
    value: Alex
    identity: default_user
    domain: personal

  - thread_id: default_thread
    key: project_codename
    value: Frankie
    identity: default_user
    domain: project
```

### API Usage

```python
# Add fact with domain
memory_handler.add_fact(
    thread_id="my_thread",
    key="monthly_budget",
    value="$3000",
    identity="user1",
    domain="finance"
)

# Query by domain
facts = memory_handler.list_facts(
    thread_id="my_thread",
    domain="finance"
)
```

### Benefits

- **Organization**: Group related memories together
- **Filtering**: Retrieve only relevant domain data
- **Privacy**: Separate personal from work data
- **Analytics**: Track memory usage by domain

## MCP Mode & Traffic Logging

MCP (Model Context Protocol) mode enables detailed logging of all protocol traffic.

### Configuration

In `config/settings.yaml`:

```yaml
app:
  mcp_mode: true
  mcp_log_path: "mcp_traffic.json"
```

### Log Format

Each log entry includes:
- Direction: "in" or "out"
- Timestamp: Unix timestamp
- Data: Full message content

Example:

```json
{"direction": "in", "timestamp": 1698765432.123, "data": "user message"}
{"direction": "out", "timestamp": 1698765432.456, "data": "agent response"}
```

### Use Cases

- **Debugging**: Track exact message flow
- **Analytics**: Analyze conversation patterns
- **Auditing**: Record all interactions
- **Testing**: Replay conversations

## Backend Rate Limiting

The backend includes production-ready rate limiting with optional authentication.

### Features

- **Per-IP Rate Limiting**: Default 60 requests/minute
- **Redis Support**: Distributed rate limiting across instances
- **Memory Fallback**: Works without Redis
- **Token Authentication**: Optional API token validation

### Configuration

```yaml
app:
  rate_limit_per_minute: 60
  api_token: "your-secret-token"  # Optional
```

### Behavior

- Returns HTTP 429 when rate limit exceeded
- Returns HTTP 401 for invalid/missing token (if auth enabled)
- Sliding window: resets every 60 seconds
- Per-client IP tracking

### Testing

```bash
# Without auth
curl http://localhost:8000/

# With auth
curl -H "X-API-Token: your-secret-token" http://localhost:8000/
```

## Model Selector UI

The frontend includes a dropdown for selecting between available models.

### Available Models

Default configuration includes:
- `openrouter/horizon-beta` (default)
- `z-ai/glm-4.5-air:free` (free backup)

### Usage

1. Open the web UI at http://localhost:5173
2. Locate the model selector dropdown next to the message input
3. Select your preferred model
4. Send messages - they will use the selected model

### Adding Models

Models are configured in the backend at `backend/main.py`:

```python
@app.get("/models")
async def list_models():
    """Return available local models."""
    return {"models": [
        "openrouter/horizon-beta",
        "z-ai/glm-4.5-air:free",
        "your-new-model"
    ]}
```

And in the frontend at `frontend/src/App.tsx`:

```tsx
<select value={selectedModel} onChange={(e)=>setSelectedModel(e.target.value)}>
  <option value="openrouter/horizon-beta">openrouter/horizon-beta</option>
  <option value="z-ai/glm-4.5-air:free">z-ai/glm-4.5-air:free</option>
  <option value="your-new-model">Your New Model</option>
</select>
```

## Testing

All Phase 1 features include comprehensive test coverage:

- `tests/test_llm_confidence.py` - LLM confidence calculation
- `tests/test_hybrid_scoring.py` - Hybrid vector scoring algorithm
- `tests/test_domain_preload.py` - Domain-aware memory preload

Run tests with:

```bash
poetry run pytest tests/test_llm_confidence.py -v
poetry run pytest tests/test_hybrid_scoring.py -v
poetry run pytest tests/test_domain_preload.py -v
```

## Performance Considerations

### Memory Usage

- Domain filtering reduces query overhead
- Hybrid search fetches 2x results when diversity boosting enabled

### Rate Limiting

- Redis recommended for production (shared state across instances)
- Memory fallback sufficient for single-instance deployments

### Confidence Calculation

- O(n) complexity where n = response length
- Minimal overhead (~1ms for typical responses)

## Future Improvements

Potential Phase 1 enhancements for future consideration:

1. **TUI Improvements**
   - Split-pane live view (chat + memory)
   - Syntax highlighting for code blocks
   - Autocomplete for commands

2. **Confidence Metrics**
   - Machine learning model for confidence
   - Per-model calibration
   - Historical accuracy tracking

3. **Hybrid Scoring**
   - Adaptive weight adjustment
   - User feedback integration
   - Time-based decay for old results

4. **Domain Management**
   - Custom domain creation via UI
   - Domain-specific access controls
   - Cross-domain search

## References

- [Axon Roadmap](../phases/roadmap.md)
- [API Documentation](api.md)
- [Plugin Development](plugins.md)
- [MCP Setup](mcp_setup.md)
