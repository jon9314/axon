### Phase 2 Features

This document describes the features implemented in Phase 2 of Axon development, focused on memory enrichment and plugin management.

## Domain Scoping in Memory

Memory entries can now be organized by domain for better categorization and filtering.

### Domain Management API

#### List Domains
```bash
GET /domains/{thread_id}
```

Returns all unique domains used in a thread:
```json
{
  "domains": ["personal", "project", "health", "finance", "learning"]
}
```

#### Domain Statistics
```bash
GET /domains/{thread_id}/stats
```

Returns fact counts per domain:
```json
{
  "domains": [
    {"name": "personal", "count": 15},
    {"name": "project", "count": 8},
    {"name": "health", "count": 5}
  ]
}
```

### Domain Filtering

Filter memory operations by domain:

```python
# Add fact to specific domain
POST /memory/{thread_id}?domain=personal

# List facts in domain
GET /memory/{thread_id}?domain=project

# Delete all facts in domain
DELETE /memory/{thread_id}?domain=health
```

### Usage Examples

```python
from memory.memory_handler import MemoryHandler

handler = MemoryHandler()

# Add facts to different domains
handler.add_fact("user1", "budget", "$3000", domain="finance")
handler.add_fact("user1", "exercise_goal", "10k steps", domain="health")
handler.add_fact("user1", "project_deadline", "2025-12-01", domain="project")

# List facts by domain
finance_facts = handler.list_facts("user1", domain="finance")
health_facts = handler.list_facts("user1", domain="health")

# Delete entire domain
handler.delete_facts("user1", domain="finance")
```

## Permission Scoping for Plugins

Plugins now have comprehensive permission enforcement to control access to sensitive operations.

### Permission Types

```python
from axon.plugins.permissions import Permission

Permission.FS_READ       # Read filesystem
Permission.FS_WRITE      # Write filesystem
Permission.NET_HTTP      # Network HTTP requests
Permission.PROCESS_SPAWN # Spawn subprocesses
```

### Plugin Permission Declaration

In plugin manifest (`plugin_name.yaml`):

```yaml
name: file_writer
version: "1.0"
description: Write content to files
entrypoint: file_writer:FileWriterPlugin
permissions:
  - fs.write  # Required permission
```

### Permission Enforcement in Plugins

```python
from axon.plugins.base import Plugin
from axon.plugins.permissions import Permission

class FileWriterPlugin(Plugin):
    def load(self, config):
        # Check permission during load
        if Permission.FS_WRITE not in self.permissions:
            raise PermissionError("FS_WRITE required")

    def execute(self, data):
        # Enforce at runtime
        self.require(Permission.FS_WRITE)

        # Safe to perform file operations
        path.write_text(data.content)
```

### Permission Deny List

Restrict plugins from using certain permissions:

```python
from axon.plugins.loader import PluginLoader
from axon.plugins.permissions import Permission

# Prevent any plugin from spawning processes
loader = PluginLoader(deny={Permission.PROCESS_SPAWN})
loader.discover()

# Plugins requesting PROCESS_SPAWN will have it stripped
```

### Plugin Management API

#### List All Plugins
```bash
GET /plugins
```

Returns all plugins with their permissions:
```json
{
  "plugins": [
    {
      "name": "file_writer",
      "version": "1.0",
      "description": "Write content to files",
      "permissions": ["fs.write"],
      "entrypoint": "file_writer:FileWriterPlugin"
    }
  ]
}
```

#### Get Plugin Details
```bash
GET /plugins/{name}
```

Returns detailed plugin information including config schema.

#### Execute Plugin
```bash
POST /plugins/{name}/execute
{
  "path": "/tmp/test.txt",
  "content": "Hello, World!"
}
```

Returns execution result or permission error (403).

### Permission Error Handling

```python
try:
    loader.execute("file_writer", {"path": "/etc/passwd", "content": "hack"})
except PermissionError as e:
    print(f"Permission denied: {e}")
```

### Example: File Writer Plugin

Complete example demonstrating permission enforcement:

```python
# plugins/file_writer.py
from axon.plugins.base import Plugin
from axon.plugins.permissions import Permission
from pydantic import BaseModel
from pathlib import Path

class FileWriteInput(BaseModel):
    path: str
    content: str

class FileWriteOutput(BaseModel):
    success: bool
    message: str
    bytes_written: int

class FileWriterPlugin(Plugin[FileWriteInput, FileWriteOutput]):
    input_model = FileWriteInput
    output_model = FileWriteOutput

    def load(self, config):
        if Permission.FS_WRITE not in self.permissions:
            raise PermissionError("FileWriterPlugin requires FS_WRITE")

    def describe(self):
        return {
            "name": self.manifest.name,
            "permissions_required": "fs.write"
        }

    def execute(self, data):
        self.require(Permission.FS_WRITE)  # Runtime check

        try:
            file_path = Path(data.path)
            bytes_written = file_path.write_text(data.content)
            return FileWriteOutput(
                success=True,
                message=f"Wrote to {data.path}",
                bytes_written=bytes_written
            )
        except Exception as e:
            return FileWriteOutput(
                success=False,
                message=str(e),
                bytes_written=0
            )
```

```yaml
# plugins/file_writer.yaml
name: file_writer
version: "1.0"
description: Write content to files with permission enforcement
entrypoint: file_writer:FileWriterPlugin
permissions:
  - fs.write
```

## Speaker Embedding (Optional)

Voice-based speaker identification using embeddings for hands-free identity tracking.

### Features

- **Voice Registration**: Register speaker profiles from audio samples
- **Speaker Identification**: Identify speakers from voice with confidence scores
- **Running Average**: Multiple samples improve accuracy over time
- **Persistence**: Export/import speaker profiles
- **Graceful Degradation**: Works without numpy (placeholder mode)

### Speaker Embedding Manager

```python
from memory.speaker_embedding import SpeakerEmbeddingManager

# Initialize manager
manager = SpeakerEmbeddingManager(embedding_dim=128)

# Register a speaker
audio_data = load_audio_file("alice_sample.wav")
profile = manager.register_speaker("alice", audio_data)

# Identify speaker from new audio
unknown_audio = load_audio_file("mystery_speaker.wav")
identity, confidence = manager.identify_speaker(unknown_audio, threshold=0.7)

if identity:
    print(f"Speaker: {identity} (confidence: {confidence:.2f})")
else:
    print("Unknown speaker")
```

### API Endpoints

#### Register Speaker
```bash
POST /speakers/register
{
  "identity": "alice",
  "audio_data": "base64_encoded_audio"
}
```

Returns:
```json
{
  "status": "success",
  "identity": "alice",
  "num_samples": 1
}
```

#### Identify Speaker
```bash
POST /speakers/identify
{
  "audio_data": "base64_encoded_audio",
  "threshold": 0.7
}
```

Returns:
```json
{
  "identity": "alice",
  "confidence": 0.89
}
```

#### List Speakers
```bash
GET /speakers
```

Returns:
```json
{
  "speakers": ["alice", "bob", "charlie"]
}
```

#### Delete Speaker
```bash
DELETE /speakers/{identity}
```

### Advanced Usage

#### Multiple Sample Registration

Improves accuracy by averaging embeddings:

```python
# Register initial sample
manager.register_speaker("alice", audio_sample_1)

# Add more samples (updates profile)
manager.register_speaker("alice", audio_sample_2)
manager.register_speaker("alice", audio_sample_3)

# Profile now has num_samples = 3 with averaged embedding
```

#### Profile Persistence

```python
# Export profiles
profiles = manager.export_profiles()
save_to_file("speaker_profiles.json", profiles)

# Import profiles
loaded_profiles = load_from_file("speaker_profiles.json")
manager.import_profiles(loaded_profiles)
```

#### Custom Threshold

Adjust recognition sensitivity:

```python
# Strict matching (fewer false positives)
identity, conf = manager.identify_speaker(audio, threshold=0.9)

# Lenient matching (fewer false negatives)
identity, conf = manager.identify_speaker(audio, threshold=0.5)
```

### Implementation Notes

The current implementation uses a placeholder embedding extraction based on audio hash. For production use, integrate with proper speaker recognition models:

**Recommended Models:**
- **SpeechBrain**: https://speechbrain.github.io/
- **pyannote.audio**: Speaker diarization and recognition
- **Resemblyzer**: Voice encoder for speaker recognition

### Example Integration

```python
# Production-ready speaker recognition
from speechbrain.pretrained import SpeakerRecognition

class ProductionSpeakerManager(SpeakerEmbeddingManager):
    def __init__(self):
        super().__init__(embedding_dim=256)
        self.model = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb"
        )

    def extract_embedding(self, audio_data):
        # Use SpeechBrain model
        embedding = self.model.encode_batch(audio_data)
        return embedding.squeeze().tolist()
```

### Security Considerations

1. **Audio Storage**: Don't store raw audio, only embeddings
2. **Threshold Tuning**: Balance security vs usability
3. **Re-enrollment**: Periodic profile updates for voice changes
4. **Multi-factor**: Combine with other authentication methods

## Testing

All Phase 2 features include comprehensive test coverage:

- `tests/test_domain_api.py` - Domain management endpoints (12 tests)
- `tests/test_permission_enforcement.py` - Permission system (9 tests)
- `tests/test_speaker_embedding.py` - Voice recognition (20 tests)

Run tests:

```bash
poetry run pytest tests/test_domain_api.py -v
poetry run pytest tests/test_permission_enforcement.py -v
poetry run pytest tests/test_speaker_embedding.py -v
```

## Performance Considerations

### Domain Scoping

- Domain filtering reduces query time for large memory stores
- Statistics endpoint caches results when possible
- Indexed by scope field for fast lookups

### Permission Enforcement

- Permission checks are O(1) set lookups
- Minimal overhead (~0.1ms per check)
- Deny list applied at load time, not runtime

### Speaker Embedding

- Embedding extraction: ~10-50ms depending on model
- Similarity comparison: O(n) where n = number of registered speakers
- Caching recommended for frequently accessed profiles

## Migration Guide

### Existing Memory Data

Domain scoping is backward compatible. Existing facts without domains continue to work:

```python
# Old code still works
handler.add_fact("thread1", "key", "value")
handler.list_facts("thread1")

# New code with domains
handler.add_fact("thread1", "key", "value", domain="personal")
handler.list_facts("thread1", domain="personal")
```

### Existing Plugins

Plugins without permission declarations default to no permissions:

```yaml
# Old plugin manifest (still works, no permissions)
name: my_plugin
version: "1.0"
entrypoint: my_plugin:MyPlugin

# New plugin manifest (with permissions)
name: my_plugin
version: "2.0"
entrypoint: my_plugin:MyPlugin
permissions:
  - fs.read
  - net.http
```

### Gradual Adoption

1. **Phase 1**: Add domain tags to new memory entries
2. **Phase 2**: Migrate existing entries to domains
3. **Phase 3**: Enable strict domain filtering

## Future Enhancements

Potential Phase 2+ improvements:

1. **Domain Hierarchies**: Support nested domains (e.g., `finance.budget.monthly`)
2. **Permission Templates**: Pre-defined permission sets for common use cases
3. **Dynamic Permissions**: Grant/revoke permissions at runtime
4. **Speaker Adaptation**: Continuous learning from verified samples
5. **Multi-speaker Detection**: Identify multiple speakers in conversation

## References

- [Axon Roadmap](../phases/roadmap.md)
- [Phase 1 Features](phase1_features.md)
- [Plugin Development](plugins.md)
- [API Documentation](api.md)
