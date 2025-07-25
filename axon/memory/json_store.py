from __future__ import annotations

import json
import os
from pathlib import Path

from .base import MemoryStore
from .models import BaseRecord, MemoryRecord, ProfileRecord, ReminderRecord


class JSONFileMemoryStore(MemoryStore):
    """JSON file-backed memory store."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self._records: dict[str, BaseRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            typ = item.pop("record_type", "memory")
            cls = {
                "memory": MemoryRecord,
                "reminder": ReminderRecord,
                "profile": ProfileRecord,
            }.get(typ, MemoryRecord)
            rec = cls.model_validate(item)  # type: ignore[attr-defined]
            self._records[rec.id] = rec

    def _serialize(self, record: BaseRecord) -> dict:
        data = record.model_dump()
        if isinstance(record, MemoryRecord):
            data["record_type"] = "memory"
        elif isinstance(record, ReminderRecord):
            data["record_type"] = "reminder"
        elif isinstance(record, ProfileRecord):
            data["record_type"] = "profile"
        else:
            data["record_type"] = "base"
        return data

    def _save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump([self._serialize(r) for r in self._records.values()], f, default=str)
        os.replace(tmp, self.path)

    def put(self, record: BaseRecord) -> str:
        self._records[record.id] = record
        self._save()
        return record.id

    def get(self, record_id: str) -> BaseRecord | None:
        return self._records.get(record_id)

    def update(self, record_id: str, **fields) -> BaseRecord:
        rec = self._records.get(record_id)
        if rec is None:
            raise KeyError(record_id)
        if rec.locked:
            raise ValueError("record locked")
        for k, v in fields.items():
            if hasattr(rec, k):
                setattr(rec, k, v)
            else:
                if rec.metadata is None:
                    rec.metadata = {}
                rec.metadata[k] = v
        rec.updated_at = fields.get("updated_at", rec.updated_at)
        self._save()
        return rec

    def delete(self, record_id: str) -> bool:
        rec = self._records.get(record_id)
        if not rec or rec.locked:
            return False
        self._records.pop(record_id, None)
        self._save()
        return True

    def search(
        self, query: str, tags: list[str] | None = None, scope: str | None = None, limit: int = 50
    ) -> list[BaseRecord]:
        q = query.lower()
        results: list[BaseRecord] = []
        for rec in self._records.values():
            if scope and rec.scope != scope:
                continue
            if tags and not set(tags).issubset(rec.tags):
                continue
            text = ""
            if isinstance(rec, MemoryRecord):
                text = rec.content.lower()
            elif isinstance(rec, ReminderRecord):
                text = rec.content.lower()
            elif isinstance(rec, ProfileRecord):
                text = json.dumps(rec.fields).lower()
            if q in text:
                results.append(rec)
                if len(results) >= limit:
                    break
        return results

    def lock(self, record_id: str) -> None:
        rec = self._records.get(record_id)
        if rec is None:
            raise KeyError(record_id)
        rec.locked = True
        self._save()

    def unlock(self, record_id: str) -> None:
        rec = self._records.get(record_id)
        if rec is None:
            raise KeyError(record_id)
        rec.locked = False
        self._save()
