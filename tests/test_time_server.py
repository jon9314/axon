from fastapi.testclient import TestClient

from mcp_servers.time_server import app

client = TestClient(app)


def test_now_and_duration():
    resp = client.get("/now")
    assert resp.status_code == 200
    assert "timestamp" in resp.json()

    resp = client.get("/duration", params={"start": 0, "end": 10})
    assert resp.json()["seconds"] == 10
