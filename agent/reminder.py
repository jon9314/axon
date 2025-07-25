"""Simple in-memory reminder scheduler."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Iterable
from typing import Any, Protocol

from .notifier import Notifier


class MemoryLike(Protocol):
    def add_fact(
        self,
        thread_id: str,
        key: str,
        value: str,
        identity: str | None = None,
        tags: Iterable[str] | None = None,
    ) -> None: ...

    def delete_fact(self, thread_id: str, key: str) -> bool: ...

    def list_facts(
        self, thread_id: str, tag: str | None = None, domain: str | None = None
    ) -> list[tuple[str, str, str | None, bool, list[str]]]: ...


class ReminderManager:
    def __init__(
        self, notifier: Notifier | None = None, memory_handler: MemoryLike | None = None
    ) -> None:
        self.notifier = notifier or Notifier()
        self.memory_handler = memory_handler
        self._timers: list[threading.Timer] = []

    def _trigger(self, thread_id: str, key: str, message: str) -> None:
        self.notifier.notify("Reminder", message)
        if self.memory_handler:
            self.memory_handler.delete_fact(thread_id, key)

    def schedule(self, message: str, delay_seconds: int, thread_id: str = "default_thread") -> str:
        ts = int(time.time()) + delay_seconds
        key = f"reminder_{ts}"
        if self.memory_handler:
            data = json.dumps({"message": message, "time": ts})
            self.memory_handler.add_fact(thread_id, key, data, identity="reminder")
        timer = threading.Timer(delay_seconds, self._trigger, args=(thread_id, key, message))
        timer.daemon = True
        timer.start()
        self._timers.append(timer)
        return key

    def list_reminders(self, thread_id: str) -> list[dict[str, Any]]:
        if not self.memory_handler:
            return []
        results: list[dict[str, Any]] = []
        for key, value, _ident, _locked, _tags in self.memory_handler.list_facts(thread_id):
            if key.startswith("reminder_"):
                try:
                    data = json.loads(value)
                    results.append(
                        {
                            "key": key,
                            "message": data.get("message"),
                            "time": data.get("time"),
                        }
                    )
                except Exception:
                    continue
        return results

    def delete_reminder(self, thread_id: str, key: str) -> bool:
        if self.memory_handler:
            return self.memory_handler.delete_fact(thread_id, key)
        return False
