from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .json_store import JSONFileMemoryStore
from .models import MemoryRecord, ProfileRecord, ReminderRecord

_DEFAULT_PATH = Path("data/memory_store.json")
_store: JSONFileMemoryStore | None = None


def get_store() -> JSONFileMemoryStore:
    global _store
    if _store is None:
        _DEFAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
        _store = JSONFileMemoryStore(str(_DEFAULT_PATH))
    return _store


class MemoryRepository:
    """Convenience wrapper around :class:`MemoryStore`."""

    def __init__(self, store: JSONFileMemoryStore | None = None) -> None:
        self.store = store or get_store()

    def remember_fact(
        self,
        content: str,
        *,
        record_id: str | None = None,
        tags: list[str] | None = None,
        scope: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        rec = MemoryRecord(
            id=record_id or str(uuid4()),
            content=content,
            tags=tags or [],
            scope=scope,
            metadata=metadata,
        )
        return self.store.put(rec)

    def get_profile(self, identity: str) -> ProfileRecord | None:
        for rec in self.store.search("", scope=identity):
            if isinstance(rec, ProfileRecord):
                return rec
        return None

    def list_reminders_due(self, before: datetime) -> list[ReminderRecord]:
        results: list[ReminderRecord] = []
        for rec in self.store.search(""):
            if isinstance(rec, ReminderRecord) and rec.due_at <= before:
                results.append(rec)
        return results
