from fastapi.testclient import TestClient
from mcp_servers.query_server import app as query_app
from agent.tools.query_proxy import QueryProxy
import requests


def make_mock(client: TestClient):
    def post(url, params=None, json=None, **kwargs):
        path = url.split("/")[-1]
        return client.post(f"/{path}", params=params, json=json)

    return post


def test_query_proxy(monkeypatch, tmp_path):
    csv_file = tmp_path / "data.csv"
    csv_file.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    client = TestClient(query_app)
    monkeypatch.setattr(requests, "post", make_mock(client))
    proxy = QueryProxy()
    result = proxy.call({"path": str(csv_file), "sql": "SELECT COUNT(*) FROM data"})
    assert result["rows"][0][0] == 2
