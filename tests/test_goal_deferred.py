import pytest

from agent.goal_tracker import HAS_PSYCOPG2, GoalTracker
from axon.utils.health import service_status


class DummyCursor:
    def __init__(self):
        self.queries = []
        self.fetchall_result = []

    def execute(self, query, params=None):
        self.queries.append((query.strip(), params))

    def fetchall(self):
        return self.fetchall_result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


class DummyConn:
    def __init__(self, cursor):
        self.cursor_obj = cursor

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        pass

    def close(self):
        pass


def test_add_goal_marks_deferred(monkeypatch):
    if not HAS_PSYCOPG2 or not service_status.postgres:
        pytest.skip("postgres unavailable")
    cur = DummyCursor()
    conn = DummyConn(cur)
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: conn)
    tracker = GoalTracker(db_uri="postgresql://ignore")
    tracker.add_goal("t1", "Someday I might travel")
    insert_query, params = cur.queries[-1]
    assert "INSERT INTO goals" in insert_query
    assert params == ("t1", None, "Someday I might travel", True, 0, None)


def test_list_deferred(monkeypatch):
    if not HAS_PSYCOPG2 or not service_status.postgres:
        pytest.skip("postgres unavailable")
    cur = DummyCursor()
    cur.fetchall_result = [(1, "Someday I might travel", False, None, True, 0, None)]
    conn = DummyConn(cur)
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: conn)
    tracker = GoalTracker(db_uri="postgresql://ignore")
    goals = tracker.list_deferred_goals("t1")
    assert goals == cur.fetchall_result


def test_priority_and_deadline(monkeypatch):
    if not HAS_PSYCOPG2 or not service_status.postgres:
        pytest.skip("postgres unavailable")
    from datetime import datetime

    cur = DummyCursor()
    conn = DummyConn(cur)
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: conn)
    tracker = GoalTracker(db_uri="postgresql://ignore")
    deadline = datetime(2024, 1, 1)
    tracker.add_goal("t1", "Finish project", priority=5, deadline=deadline)
    insert_query, params = cur.queries[-1]
    assert params == ("t1", None, "Finish project", False, 5, deadline)


def test_deferred_prompt(monkeypatch):
    if not HAS_PSYCOPG2 or not service_status.postgres:
        pytest.skip("postgres unavailable")
    called = []

    class DummyNotifier:
        def notify(self, title, message):
            called.append((title, message))

    cur = DummyCursor()
    cur.fetchall_result = [(1, "Maybe later", False, None, True, 0, None)]
    conn = DummyConn(cur)
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: conn)
    tracker = GoalTracker(db_uri="postgresql://ignore", notifier=DummyNotifier())
    tracker.start_deferred_prompting("t1", interval_seconds=0.05)
    import time

    time.sleep(0.1)
    tracker.stop_deferred_prompting()
    assert called
