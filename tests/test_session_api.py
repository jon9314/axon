from fastapi.testclient import TestClient

from backend.main import app, memory_handler, session_tracker


class DummyMem:
    def list_facts(self, thread_id, tag=None, domain=None):
        return [("k", "v", "alice", False, [])]


def test_login_and_memory(monkeypatch):
    monkeypatch.setattr(memory_handler, "list_facts", DummyMem().list_facts)
    # reset sessions for isolated test
    session_tracker._sessions.clear()
    client = TestClient(app)
    resp = client.post("/sessions/login", params={"identity": "alice"})
    assert resp.status_code == 200
    data = resp.json()
    token = data["token"]
    thread_id = data["thread_id"]
    resp = client.get(f"/sessions/{token}/memory")
    assert resp.status_code == 200
    m = resp.json()
    assert m["identity"] == "alice"
    assert m["thread_id"] == thread_id
    assert m["facts"][0]["key"] == "k"
