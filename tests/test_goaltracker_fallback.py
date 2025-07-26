from agent.goal_tracker import GoalTracker
from axon.utils.health import service_status


def test_goaltracker_no_postgres(monkeypatch):
    monkeypatch.setattr(service_status, "postgres", False)
    tracker = GoalTracker(db_uri="postgresql://ignore")
    tracker.add_goal("t1", "do things")
    assert not tracker.detect_and_add_goal("t1", "I want to run")  # NOTE: disabled
    assert tracker.list_goals("t1") == []
    assert tracker.list_deferred_goals("t1") == []
    tracker.complete_goal(1)
    assert tracker.delete_goals("t1") == 0
    tracker.start_deferred_prompting("t1", interval_seconds=0.01)
    assert tracker._prompt_timer is None
    tracker.stop_deferred_prompting()
