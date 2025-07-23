import time
from typing import Protocol, Iterable


class MemoryLike(Protocol):
    """Minimal interface needed from MemoryHandler."""

    def add_fact(
        self,
        thread_id: str,
        key: str,
        value: str,
        identity: str | None = None,
        domain: str | None = None,
        tags: Iterable[str] | None = None,
    ) -> None: ...


class PastebackHandler:
    """Store remote model responses in memory."""

    def __init__(self, memory_handler: MemoryLike):
        self.memory_handler = memory_handler

    def store(
        self, thread_id: str, prompt: str, response: str, model: str = "gpt"
    ) -> None:
        ts = int(time.time())
        self.memory_handler.add_fact(
            thread_id, f"cloud_prompt_{ts}", prompt, identity=model
        )
        self.memory_handler.add_fact(
            thread_id, f"cloud_response_{ts}", response, identity=model
        )
