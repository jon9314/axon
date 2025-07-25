from starlette.testclient import TestClient

from agent.mcp_router import MCPRouter
from mcp_servers.time_server import app as time_app


def test_load_and_list(tmp_path):
    config = tmp_path / "servers.yaml"
    config.write_text(
        """
- name: time
  transport: http
  url: http://testserver
"""
    )
    router = MCPRouter(config_path=str(config))
    assert router.list_tools() == ["time"]
    info = router.get_tool("time")
    assert info["url"] == "http://testserver"


def test_call_http(monkeypatch):
    client = TestClient(time_app)

    def fake_get(url, params=None, **kwargs):
        path = url.split("/")[-1]
        return client.get(f"/{path}", params=params)

    monkeypatch.setattr("requests.get", fake_get)

    router = MCPRouter()
    router.tools = {"time": {"transport": "http", "url": "http://unused"}}
    result = router.call("time", {"command": "now"})
    assert "timestamp" in result
