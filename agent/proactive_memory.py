"""Periodic surfacing of relevant past context."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from typing import Iterable, Protocol

from .notifier import Notifier


class MemorySource(Protocol):
    def list_facts(
        self, thread_id: str, tag: str | None = None, domain: str | None = None
    ) -> list[tuple[str, str, str | None, bool, list[str]]]: ...


class GoalSource(Protocol):
    def list_goals(
        self, thread_id: str
    ) -> Iterable[tuple[int, str, bool, str | None, bool, int, datetime | None]]: ...


class ProactiveMemory:
    """Surface stale reminders or deferred goals at intervals."""

    def __init__(
        self,
        memory_handler: MemorySource,
        goal_tracker: GoalSource,
        notifier: Notifier | None = None,
    ) -> None:
        self.memory_handler = memory_handler
        self.goal_tracker = goal_tracker
        self.notifier = notifier or Notifier()
        self._timer: threading.Timer | None = None

    def _scan(self, thread_id: str, interval: float) -> None:
        now = time.time()
        messages: list[str] = []
        # check memory for overdue reminders or tagged ideas
        for _key, value, ident, _locked, tags in self.memory_handler.list_facts(
            thread_id
        ):
            if ident == "reminder":
                try:
                    data = json.loads(value)
                except Exception:
                    continue
                when = data.get("time")
                if when is not None and when <= now:
                    msg = data.get("message")
                    if msg:
                        messages.append(msg)
            elif set(tags) & {"idea", "todo", "promise"}:
                messages.append(value)
        # check goals for deferred or past-due items
        for (
            _gid,
            text,
            completed,
            _ident,
            deferred,
            _prio,
            deadline,
        ) in self.goal_tracker.list_goals(thread_id):
            if completed:
                continue
            if deferred or (deadline and deadline <= datetime.now()):
                messages.append(text)
        if messages:
            summary = "; ".join(messages)
            self.notifier.notify("Reminder", summary)
        self.start(thread_id, interval)

    def start(self, thread_id: str, interval_seconds: float = 1800) -> None:
        """Begin periodic proactive scans."""
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(
            interval_seconds, self._scan, args=(thread_id, interval_seconds)
        )
        self._timer.daemon = True
        self._timer.start()

    def stop(self) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None
