from memory.memory_handler import MemoryHandler

class DummyCursor:
    def __init__(self):
        self.queries = []
        self.fetch_result = ("v1", "alice")
    def execute(self, query, params=None):
        self.queries.append((str(query).strip(), params))
    def fetchone(self):
        return self.fetch_result
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


def test_get_fact_with_identity(monkeypatch):
    cur = DummyCursor()
    conn = DummyConn(cur)
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: conn)
    handler = MemoryHandler(db_uri="postgresql://ignore")
    value_only = handler.get_fact("t1", "k1")
    assert value_only == "v1"
    result = handler.get_fact("t1", "k1", include_identity=True)
    assert result == ("v1", "alice")
    query, params = cur.queries[-1]
    assert params == ("t1", "k1")
