from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from axon.memory import MemoryRepository


class MemoryHandler:
    """Compatibility wrapper over :class:`MemoryRepository`."""

    def __init__(self, auto_timestamp: bool = True) -> None:
        self.repo = MemoryRepository()
        self.auto_timestamp = auto_timestamp

    def _get_timestamp(self) -> str | None:
        """Get current timestamp from Time MCP if enabled."""
        if not self.auto_timestamp:
            return None

        try:
            from agent.mcp_router import mcp_router

            if mcp_router.check_tool("time"):
                result = mcp_router.call("time", {"command": "now"})
                return result.get("timestamp")
        except Exception:
            # Gracefully degrade if MCP not available
            from datetime import datetime

            try:
                from datetime import UTC  # type: ignore[attr-defined]

                return datetime.now(UTC).isoformat()
            except ImportError:
                import datetime as dt

                return dt.datetime.utcnow().isoformat() + "Z"
        return None

    def add_fact(
        self,
        thread_id: str,
        key: str,
        value: str,
        identity: str | None = None,
        domain: str | None = None,
        tags: Iterable[str] | None = None,
    ) -> None:
        metadata = {"identity": identity} if identity else {}

        # Add timestamp to metadata
        timestamp = self._get_timestamp()
        if timestamp:
            if metadata:
                metadata["created_at"] = timestamp
            else:
                metadata = {"created_at": timestamp}

        self.repo.remember_fact(
            value,
            record_id=key,
            tags=list(tags) if tags else None,
            scope=domain or thread_id,
            metadata=metadata if metadata else None,
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
        self, thread_id: str, tag: str | None = None, domain: str | None = None
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
        identity: str | None = None,
        domain: str | None = None,
        tags: Iterable[str] | None = None,
    ) -> None:
        update_fields: dict[str, Any] = {
            "content": value,
            "scope": domain or thread_id,
        }
        if tags is not None:
            update_fields["tags"] = list(tags)
        if identity is not None:
            update_fields["metadata"] = {"identity": identity}
        self.repo.store.update(key, **update_fields)

    def delete_fact(self, thread_id: str, key: str) -> bool:
        return self.repo.store.delete(key)

    def delete_facts(
        self, thread_id: str, domain: str | None = None, tag: str | None = None
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
