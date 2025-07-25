"""Utility to export reminders as `.ics` calendar events."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Protocol

from icalendar import Calendar, Event


class MemoryLike(Protocol):
    def list_facts(
        self,
        thread_id: str,
        tag: str | None = None,
        domain: str | None = None,
    ) -> list[tuple[str, str, str | None, bool, Iterable[str]]]: ...


def _reminders_from_memory(memory: MemoryLike, thread_id: str) -> list[dict[str, int | str]]:
    results: list[dict[str, int | str]] = []
    for key, value, _ident, _locked, _tags in memory.list_facts(thread_id):
        if key.startswith("reminder_"):
            try:
                data = json.loads(value)
                results.append(
                    {
                        "message": data.get("message", ""),
                        "time": int(data.get("time", 0)),
                    }
                )
            except Exception:
                continue
    return results


class CalendarExporter:
    """Generate iCalendar files from stored reminders."""

    def __init__(self, memory: MemoryLike) -> None:
        self.memory = memory

    def export(self, thread_id: str = "default_thread", path: str | None = None) -> str:
        """Return calendar data and optionally write it to ``path``."""
        reminders = _reminders_from_memory(self.memory, thread_id)
        cal = Calendar()
        for item in reminders:
            event = Event()
            event.add("summary", item["message"])
            start = datetime.fromtimestamp(int(item["time"]))
            event.add("dtstart", start)
            event.add("dtend", start + timedelta(hours=1))
            cal.add_component(event)
        ics_data = cal.to_ical().decode()
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(ics_data)
        return ics_data
