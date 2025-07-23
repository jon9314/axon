from memory.memory_handler import MemoryHandler


class DummyCursor:
    def __init__(self):
        self.queries = []
        self.fetchall_result = []
        self.rowcount = 0

    def execute(self, query, params=None):
        self.queries.append((str(query).strip(), params))

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


def test_add_fact_with_domain(monkeypatch):
    cur = DummyCursor()
    conn = DummyConn(cur)
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: conn)
    handler = MemoryHandler(db_uri="postgresql://ignore")
    handler.add_fact("t1", "k", "v", domain="work")
    query, params = cur.queries[-1]
    assert "INSERT INTO facts" in query
    assert params[-1] == "work"


def test_list_facts_domain(monkeypatch):
    cur = DummyCursor()
    cur.fetchall_result = []
    conn = DummyConn(cur)
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: conn)
    handler = MemoryHandler(db_uri="postgresql://ignore")
    handler.list_facts("t1", domain="work")
    query, params = cur.queries[-1]
    assert "domain = %s" in query
    assert params[-1] == "work"


def test_delete_facts_domain(monkeypatch):
    cur = DummyCursor()
    conn = DummyConn(cur)
    monkeypatch.setattr("psycopg2.connect", lambda *a, **k: conn)
    handler = MemoryHandler(db_uri="postgresql://ignore")
    handler.delete_facts("t1", domain="work")
    query, params = cur.queries[-1]
    assert "DELETE FROM facts" in query
    assert "domain=%s" in query
    assert params[-1] == "work"
