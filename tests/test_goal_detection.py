from agent.goal_tracker import GoalTracker


def test_detect_goal_creates_entry(monkeypatch):
    tracker = GoalTracker.__new__(GoalTracker)
    tracker.conn = object()  # NOTE: pretend DB connected
    calls = []

    def dummy_add(thread_id, text, identity=None):
        calls.append((thread_id, text, identity))

    monkeypatch.setattr(tracker, "add_goal", dummy_add)
    result = tracker.detect_and_add_goal("t1", "I want to learn Python")
    assert result is True
    assert calls == [("t1", "I want to learn Python", None)]
