from datetime import datetime

from agent.habit_tracker import HabitTracker


class DummyGoals:
    def list_goals(self, thread_id):
        return [
            (1, "Fast", False, "bob", False, 0, datetime(2024, 8, 5)),
            (2, "Fast", False, "bob", False, 0, datetime(2024, 8, 12)),
            (3, "Fast", False, "bob", False, 0, datetime(2024, 8, 13)),
        ]


class DummyMemory:
    def __init__(self):
        self.added = []

    def add_fact(self, thread_id, key, value, identity=None, domain=None, tags=None):
        self.added.append((thread_id, key, value, tags or []))

    def list_facts(self, thread_id, tag=None, domain=None):
        results = []
        for t, key, value, tags in self.added:
            if t != thread_id:
                continue
            if tag and tag not in tags:
                continue
            results.append((key, value, None, False, tags))
        return results


class DummyNotifier:
    def __init__(self):
        self.calls = []

    def notify(self, title, message):
        self.calls.append((title, message))


def test_update_habits_records_fact():
    mem = DummyMemory()
    tracker = HabitTracker(DummyGoals(), mem, notifier=DummyNotifier())
    tracker.update_habits("t1")
    assert ("t1", "habit_Monday_fast", "fast on Monday", ["routine"]) in mem.added


def test_notify_summary(monkeypatch):
    mem = DummyMemory()
    notifier = DummyNotifier()
    tracker = HabitTracker(DummyGoals(), mem, notifier=notifier)
    monkeypatch.setattr(tracker, "start_summary", lambda *a, **k: None)
    tracker._notify_summary("t1", 0)
    assert notifier.calls
    assert "fast on Monday" in notifier.calls[0][1]


def test_summarize_habits():
    mem = DummyMemory()
    tracker = HabitTracker(DummyGoals(), mem, notifier=DummyNotifier())
    tracker.update_habits("t1")
    summary = tracker.summarize_habits("t1")
    assert "fast on Monday" in summary
