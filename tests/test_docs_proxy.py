import requests
from fastapi.testclient import TestClient

from agent.tools.docs_proxy import DocsProxy
from mcp_servers.docs_server import app as docs_app


def make_mock(client: TestClient):
    def get(url, params=None, **kwargs):
        path = url.split("/")[-1]
        return client.get(f"/{path}", params=params)

    return get


def test_docs_proxy(monkeypatch):
    client = TestClient(docs_app)
    monkeypatch.setattr(requests, "get", make_mock(client))
    proxy = DocsProxy()
    result = proxy.call({"topic": "math"})
    assert "math" in result["content"]
