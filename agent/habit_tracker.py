# axon/agent/habit_tracker.py
"""Recognize recurring goals as habits."""

from __future__ import annotations

import re
import threading

from memory.memory_handler import MemoryHandler

from .goal_tracker import GoalTracker
from .notifier import Notifier


class HabitTracker:
    """Analyze goal history to detect routine habits."""

    def __init__(
        self,
        goal_tracker: GoalTracker,
        memory_handler: MemoryHandler,
        notifier: Notifier | None = None,
    ) -> None:
        self.goal_tracker = goal_tracker
        self.memory_handler = memory_handler
        self.notifier = notifier or Notifier()
        self._timer: threading.Timer | None = None

    @staticmethod
    def _slug(text: str) -> str:
        return re.sub(r"\W+", "_", text.strip().lower())

    def _find_habits(self, thread_id: str) -> list[tuple[str, str]]:
        """Return pairs of (weekday, normalized text) that repeat."""
        goals = self.goal_tracker.list_goals(thread_id)
        counts: dict[tuple[str, str], int] = {}
        for _gid, text, _done, _ident, _deferred, _prio, deadline in goals:
            if deadline is None:
                continue
            weekday = deadline.strftime("%A")
            norm = text.strip().lower()
            counts[(weekday, norm)] = counts.get((weekday, norm), 0) + 1
        habits = []
        for (weekday, norm), count in counts.items():
            if count >= 2:
                habits.append((weekday, norm))
        return habits

    def update_habits(self, thread_id: str) -> None:
        """Analyze goals and store detected habits in memory."""
        for weekday, norm in self._find_habits(thread_id):
            key = f"habit_{weekday}_{self._slug(norm)}"
            value = f"{norm} on {weekday}"
            self.memory_handler.add_fact(
                thread_id,
                key,
                value,
                tags=["routine"],
            )

    def summarize_habits(self, thread_id: str) -> str:
        entries = self.memory_handler.list_facts(thread_id, tag="routine")
        summaries: list[str] = []
        for _key, value, _ident, _locked, _tags in entries:
            summaries.append(value)
        return "; ".join(summaries)

    def _notify_summary(self, thread_id: str, interval: float) -> None:
        self.update_habits(thread_id)
        summary = self.summarize_habits(thread_id)
        if summary:
            self.notifier.notify("Habit summary", summary)
        self.start_summary(thread_id, interval)

    def start_summary(self, thread_id: str, interval_seconds: float = 86400) -> None:
        """Begin periodic habit summaries."""
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(
            interval_seconds,
            self._notify_summary,
            args=(thread_id, interval_seconds),
        )
        self._timer.daemon = True
        self._timer.start()

    def stop_summary(self) -> None:
        if self._timer:
            self._timer.cancel()
            self._timer = None
