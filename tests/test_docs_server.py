from fastapi.testclient import TestClient
from mcp_servers.docs_server import app

client = TestClient(app)


def test_get_doc():
    resp = client.get("/get", params={"topic": "math"})
    assert resp.status_code == 200
    assert "math" in resp.json()["content"]
