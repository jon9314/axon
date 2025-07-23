from agent.reminder import ReminderManager


def test_schedule(monkeypatch):
    called = []

    class DummyNotifier:
        def notify(self, title, message):
            called.append((title, message))

    class DummyMem:
        def __init__(self):
            self.added = []
            self.deleted = []

        def add_fact(
            self, thread_id, key, value, identity=None, domain=None, tags=None
        ):
            self.added.append((thread_id, key, value, identity))

        def delete_fact(self, thread_id, key):
            self.deleted.append((thread_id, key))
            self.added = [item for item in self.added if item[1] != key]
            return True

        def list_facts(self, thread_id, tag=None, domain=None):
            return [(k, v, None, False, []) for _, k, v, _ in self.added]

    mem = DummyMem()
    rm = ReminderManager(notifier=DummyNotifier(), memory_handler=mem)
    key = rm.schedule("hi", 0, thread_id="t1")
    # wait briefly for timer
    import time

    time.sleep(0.1)
    assert called == [("Reminder", "hi")]
    assert mem.deleted == [("t1", key)]
    assert rm.list_reminders("t1") == []
