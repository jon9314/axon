"""Simple in-memory reminder scheduler."""
from __future__ import annotations

import threading
from typing import Callable

from .notifier import Notifier


class ReminderManager:
    def __init__(self, notifier: Notifier | None = None) -> None:
        self.notifier = notifier or Notifier()
        self._timers: list[threading.Timer] = []

    def schedule(self, message: str, delay_seconds: int) -> None:
        timer = threading.Timer(delay_seconds, self.notifier.notify, args=("Reminder", message))
        timer.daemon = True
        timer.start()
        self._timers.append(timer)

