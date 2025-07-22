from fastapi.testclient import TestClient
from backend.main import app
from agent.mcp_router import mcp_router


def test_list_mcp_tools_endpoint(monkeypatch):
    mcp_router.tools = {"echo": {"transport": "http", "url": "http://testserver"}}

    class DummyResp:
        status_code = 200
    monkeypatch.setattr("agent.mcp_router.requests.get", lambda url, timeout=2: DummyResp())

    client = TestClient(app)
    resp = client.get("/mcp/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tools"]["echo"]["available"] is True
