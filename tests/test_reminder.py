from agent.reminder import ReminderManager


def test_schedule(monkeypatch):
    called = []

    class DummyNotifier:
        def notify(self, title, message):
            called.append((title, message))

    rm = ReminderManager(notifier=DummyNotifier())
    rm.schedule("hi", 0)
    # wait briefly for timer
    import time
    time.sleep(0.1)
    assert called == [("Reminder", "hi")]

