from agent.proactive_memory import ProactiveMemory


class DummyMem:
    def list_facts(self, thread_id, tag=None, domain=None):
        import json

        return [
            (
                "reminder_1",
                json.dumps({"message": "do thing", "time": 0}),
                "reminder",
                False,
                [],
            ),
            ("k2", "new project", None, False, ["idea"]),
        ]


class DummyGoals:
    def list_goals(self, thread_id):
        from datetime import datetime, timedelta

        return [
            (1, "Maybe later", False, None, True, 0, None),
            (
                2,
                "Due soon",
                False,
                None,
                False,
                0,
                datetime.now() - timedelta(seconds=1),
            ),
        ]


class DummyNotifier:
    def __init__(self):
        self.calls = []

    def notify(self, title, message):
        self.calls.append((title, message))


def test_scan_collects_context(monkeypatch):
    notifier = DummyNotifier()
    mem = DummyMem()
    goals = DummyGoals()
    pm = ProactiveMemory(mem, goals, notifier=notifier)
    monkeypatch.setattr(pm, "start", lambda *a, **k: None)
    pm._scan("t1", 0)
    assert notifier.calls
    combined = notifier.calls[0][1]
    assert "do thing" in combined
    assert "Maybe later" in combined
    assert "Due soon" in combined
