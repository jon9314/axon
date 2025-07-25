import requests
from fastapi.testclient import TestClient

from mcp_servers.wolframalpha_server import app

client = TestClient(app)


class DummyResponse:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status
        self.text = ""

    def json(self):
        return self._data


def test_query(monkeypatch):
    monkeypatch.setenv("WOLFRAM_APP_ID", "demo")

    def fake_get(url, params=None, timeout=10):
        assert params["input"] == "2+2"
        return DummyResponse(
            {"queryresult": {"pods": [{"id": "Result", "subpods": [{"plaintext": "4"}]}]}}
        )

    monkeypatch.setattr(requests, "get", fake_get)
    resp = client.get("/query", params={"expression": "2+2"})
    assert resp.status_code == 200
    assert resp.json()["result"] == "4"
