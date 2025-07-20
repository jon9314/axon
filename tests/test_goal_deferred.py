from agent.goal_tracker import GoalTracker

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
    cur = DummyCursor()
    conn = DummyConn(cur)
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: conn)
    tracker = GoalTracker(db_uri="postgresql://ignore")
    tracker.add_goal("t1", "Someday I might travel")
    insert_query, params = cur.queries[-1]
    assert "INSERT INTO goals" in insert_query
    assert params == ("t1", None, "Someday I might travel", True)


def test_list_deferred(monkeypatch):
    cur = DummyCursor()
    cur.fetchall_result = [(1, "Someday I might travel", False, None, True)]
    conn = DummyConn(cur)
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: conn)
    tracker = GoalTracker(db_uri="postgresql://ignore")
    goals = tracker.list_deferred_goals("t1")
    assert goals == cur.fetchall_result
