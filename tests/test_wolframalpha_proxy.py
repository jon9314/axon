from fastapi.testclient import TestClient
from mcp_servers.wolframalpha_server import app as wolfram_app
from agent.tools.wolframalpha_proxy import WolframAlphaProxy
import requests

class DummyResponse:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status
        self.text = ""

    def json(self):
        return self._data


def make_mock(client: TestClient):
    def get(url, params=None, **kwargs):
        if url.startswith("https://api.wolframalpha.com"):
            assert params["input"] == "2+2"
            return DummyResponse({
                "queryresult": {
                    "pods": [
                        {"id": "Result", "subpods": [{"plaintext": "4"}]}
                    ]
                }
            })
        path = url.split("/")[-1]
        return client.get(f"/{path}", params=params)

    return get


def test_wolframalpha_proxy(monkeypatch):
    client = TestClient(wolfram_app)
    monkeypatch.setenv("WOLFRAM_APP_ID", "demo")
    monkeypatch.setattr(requests, "get", make_mock(client))
    proxy = WolframAlphaProxy()

    result = proxy.call({"query": "2+2"})
    assert result["result"] == "4"
