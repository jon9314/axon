"""Store remote model responses in memory with source annotations.

This module handles pasted-back responses from cloud LLMs, tracking
the source, model, timestamp, and any additional metadata.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol


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
        self.model = model
        self.provider = provider or self._infer_provider(model)
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.url = url
        self.cost = cost
        self.tokens = tokens
        self.metadata = metadata or {}

    def _infer_provider(self, model: str) -> str:
        """Infer provider from model name."""
        model_lower = model.lower()
        if "gpt" in model_lower or "openai" in model_lower:
            return "openai"
        elif "claude" in model_lower or "anthropic" in model_lower:
            return "anthropic"
        elif "gemini" in model_lower or "google" in model_lower:
            return "google"
        elif "llama" in model_lower or "meta" in model_lower:
            return "meta"
        else:
            return "unknown"

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "model": self.model,
            "provider": self.provider,
            "timestamp": self.timestamp,
            "url": self.url,
            "cost": self.cost,
            "tokens": self.tokens,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict) -> SourceAnnotation:
        """Create from dictionary."""
        return cls(
            model=data["model"],
            provider=data.get("provider"),
            timestamp=data.get("timestamp"),
            url=data.get("url"),
            cost=data.get("cost"),
            tokens=data.get("tokens"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_json(cls, json_str: str) -> SourceAnnotation:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))


class PastebackHandler:
    """Store remote model responses in memory with source annotations."""

    def __init__(self, memory_handler: MemoryLike):
        self.memory_handler = memory_handler

    def store(
        self,
        thread_id: str,
        prompt: str,
        response: str,
        model: str = "gpt",
        source_annotation: SourceAnnotation | None = None,
    ) -> None:
        """Store pasted-back response with optional source annotation.

        Args:
            thread_id: Thread identifier
            prompt: Original prompt sent to cloud LLM
            response: Response from cloud LLM
            model: Model name (e.g., "gpt-4", "claude-3")
            source_annotation: Optional detailed source information
        """
        ts = int(time.time())

        # Store prompt
        self.memory_handler.add_fact(
            thread_id,
            f"cloud_prompt_{ts}",
            prompt,
            identity=model,
            domain="cloud_interaction",
            tags=["cloud", "prompt", "remote"],
        )

        # Store response with source annotation
        if source_annotation:
            # Store annotated response
            annotated_response = {
                "response": response,
                "source": source_annotation.to_dict(),
            }
            self.memory_handler.add_fact(
                thread_id,
                f"cloud_response_{ts}",
                json.dumps(annotated_response),
                identity=model,
                domain="cloud_interaction",
                tags=["cloud", "response", "remote", "annotated", source_annotation.provider],
            )
        else:
            # Store plain response (backward compatible)
            self.memory_handler.add_fact(
                thread_id,
                f"cloud_response_{ts}",
                response,
                identity=model,
                domain="cloud_interaction",
                tags=["cloud", "response", "remote"],
            )

    def store_with_metadata(
        self,
        thread_id: str,
        prompt: str,
        response: str,
        model: str,
        provider: str | None = None,
        url: str | None = None,
        cost: float | None = None,
        tokens: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Store response with detailed metadata.

        Args:
            thread_id: Thread identifier
            prompt: Original prompt
            response: Response from cloud LLM
            model: Model name
            provider: Provider name (e.g., "openai", "anthropic")
            url: URL to conversation or API endpoint
            cost: Estimated cost in USD
            tokens: Total tokens used
            metadata: Additional metadata
        """
        annotation = SourceAnnotation(
            model=model,
            provider=provider,
            url=url,
            cost=cost,
            tokens=tokens,
            metadata=metadata,
        )
        self.store(thread_id, prompt, response, model, annotation)

    def get_annotated_responses(
        self,
        thread_id: str,
        memory_handler: MemoryLike,
    ) -> list[dict]:
        """Retrieve annotated responses from memory.

        Args:
            thread_id: Thread identifier
            memory_handler: Memory handler to read from

        Returns:
            List of annotated responses
        """
        results = []

        # Get all facts from thread
        facts = memory_handler.list_facts(thread_id, domain="cloud_interaction")

        for key, value, identity, _locked, tags in facts:
            if key.startswith("cloud_response_") and "annotated" in tags:
                try:
                    data = json.loads(value)
                    results.append(
                        {
                            "key": key,
                            "response": data.get("response", ""),
                            "source": SourceAnnotation.from_dict(data.get("source", {})),
                            "identity": identity,
                        }
                    )
                except Exception:
                    continue

        return results
