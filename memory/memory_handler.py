from __future__ import annotations

from collections.abc import Iterable
from typing import Optional

from axon.memory import MemoryRepository


class MemoryHandler:
    """Compatibility wrapper over :class:`MemoryRepository`."""

    def __init__(self) -> None:
        self.repo = MemoryRepository()

    def add_fact(
        self,
        thread_id: str,
        key: str,
        value: str,
        identity: Optional[str] = None,
        domain: Optional[str] = None,
        tags: Iterable[str] | None = None,
    ) -> None:
        metadata = {"identity": identity} if identity else None
        self.repo.remember_fact(
            value,
            record_id=key,
            tags=list(tags) if tags else None,
            scope=domain or thread_id,
            metadata=metadata,
        )

    def get_fact(self, thread_id: str, key: str, include_identity: bool = False):
        rec = self.repo.store.get(key)
        if not rec or not hasattr(rec, "content"):
            return None
        if include_identity:
            ident = rec.metadata.get("identity") if rec.metadata else None
            return rec.content, ident
        return rec.content

    def list_facts(
        self, thread_id: str, tag: Optional[str] = None, domain: Optional[str] = None
    ) -> list[tuple[str, str, str | None, bool, list[str]]]:
        records = self.repo.store.search(
            "",
            tags=[tag] if tag else None,
            scope=domain or thread_id,
        )
        result = []
        for rec in records:
            if not hasattr(rec, "content"):
                continue
            ident = rec.metadata.get("identity") if rec.metadata else None
            result.append((rec.id, rec.content, ident, rec.locked, rec.tags))
        return result

    def update_fact(
        self,
        thread_id: str,
        key: str,
        value: str,
        identity: Optional[str] = None,
        domain: Optional[str] = None,
        tags: Iterable[str] | None = None,
    ) -> None:
        metadata = {"identity": identity} if identity else None
        self.repo.store.update(
            key,
            content=value,
            scope=domain or thread_id,
            tags=list(tags) if tags else [],
            metadata=metadata,
        )

    def delete_fact(self, thread_id: str, key: str) -> bool:
        return self.repo.store.delete(key)

    def delete_facts(
        self, thread_id: str, domain: Optional[str] = None, tag: Optional[str] = None
    ) -> int:
        records = self.repo.store.search(
            "",
            tags=[tag] if tag else None,
            scope=domain or thread_id,
        )
        count = 0
        for rec in records:
            if self.repo.store.delete(rec.id):
                count += 1
        return count

    def set_lock(self, thread_id: str, key: str, locked: bool) -> bool:
        if locked:
            self.repo.store.lock(key)
            return True
        # Allow unlocking previously locked records
        self.repo.store.unlock(key)
        return True

    def close_connection(self) -> None:
        pass
