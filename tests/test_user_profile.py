from memory.user_profile import UserProfileManager


class DummyCursor:
    def __init__(self):
        self.queries = []
        self.fetch_result = ("partner", "informal", "a@example.com")

    def execute(self, query, params=None):
        self.queries.append((query.strip(), params))

    def fetchone(self):
        return self.fetch_result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


class DummyConn:
    def __init__(self):
        self.cursor_obj = DummyCursor()
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        pass

    def close(self):
        self.closed = True


def test_profile_manager_round_trip(monkeypatch):
    dummy = DummyConn()
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: dummy)
    mgr = UserProfileManager(db_uri="postgresql://ignore")
    mgr.set_profile("jon", persona="partner", tone="informal", email="a@example.com")
    profile = mgr.get_profile("jon")
    assert profile["persona"] == "partner"
    assert profile["tone"] == "informal"
    assert profile["email"] == "a@example.com"
    assert not dummy.closed
    mgr.close_connection()
    assert dummy.closed

