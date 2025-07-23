from fastapi.testclient import TestClient
from backend.main import app, memory_handler, goal_tracker


def test_delete_memory_bulk(monkeypatch):
    monkeypatch.setattr(memory_handler, "delete_facts", lambda *a, **k: 5)
    client = TestClient(app)
    resp = client.delete("/memory/t1")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": 5}


def test_delete_goals(monkeypatch):
    monkeypatch.setattr(goal_tracker, "delete_goals", lambda *a, **k: 2)
    client = TestClient(app)
    resp = client.delete("/goals/t1")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": 2}
