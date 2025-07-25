from fastapi.testclient import TestClient

from mcp_servers.calculator_server import app

client = TestClient(app)


def test_evaluate_and_percent():
    resp = client.get("/evaluate", params={"expr": "2+2"})
    assert resp.json()["result"] == 4

    resp = client.get("/percent", params={"value": 200, "percent": 10})
    assert resp.json()["result"] == 20
