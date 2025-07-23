from fastapi.testclient import TestClient
from mcp_servers.filesystem_server import app as fs_app
from mcp_servers.time_server import app as time_app
from mcp_servers.calculator_server import app as calc_app
from mcp_servers.markdown_backup_server import app as md_app
from mcp_servers.github_server import app as gh_app
from agent.tools.github_proxy import GitHubProxy
from agent.tools.filesystem_proxy import FilesystemProxy
from agent.tools.time_proxy import TimeProxy
from agent.tools.calculator_proxy import CalculatorProxy
from agent.tools.markdown_backup_proxy import MarkdownBackupProxy
import subprocess
import requests


def make_mock(client: TestClient):
    def get(url, params=None, **kwargs):
        path = url.split("/")[-1]
        return client.get(f"/{path}", params=params)

    def post(url, params=None, json=None, **kwargs):
        path = url.split("/")[-1]
        return client.post(f"/{path}", params=params, json=json)

    return get, post


def test_filesystem_proxy(monkeypatch, tmp_path):
    client = TestClient(fs_app)
    get, post = make_mock(client)
    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(requests, "post", post)

    proxy = FilesystemProxy()
    file_path = tmp_path / "note.txt"
    result = proxy.call({"command": "write", "path": str(file_path), "content": "hi"})
    assert result["status"] == "ok"
    result = proxy.call({"command": "read", "path": str(file_path)})
    assert result["content"] == "hi"


def test_time_proxy(monkeypatch):
    client = TestClient(time_app)
    get, _ = make_mock(client)
    monkeypatch.setattr(requests, "get", get)
    proxy = TimeProxy()
    result = proxy.call({"command": "duration", "start": 1, "end": 4})
    assert result["seconds"] == 3


def test_calculator_proxy(monkeypatch):
    client = TestClient(calc_app)
    get, _ = make_mock(client)
    monkeypatch.setattr(requests, "get", get)
    proxy = CalculatorProxy()
    result = proxy.call({"command": "evaluate", "expr": "2+3"})
    assert result["result"] == 5


def test_markdown_backup_proxy(monkeypatch, tmp_path):
    # ensure markdown dir uses tmp
    client = TestClient(md_app)
    get, post = make_mock(client)
    monkeypatch.setattr(requests, "get", get)
    monkeypatch.setattr(requests, "post", post)
    proxy = MarkdownBackupProxy()
    result = proxy.call({"command": "save", "name": "n1", "content": "hello"})
    assert result["status"] == "ok"
    result = proxy.call({"command": "get", "name": "n1"})
    assert result["content"] == "hello"


def test_github_proxy(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init"], check=True)
    file = repo / "file.txt"
    file.write_text("data", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "file.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True)

    client = TestClient(gh_app)
    get, _ = make_mock(client)
    monkeypatch.setattr(requests, "get", get)
    proxy = GitHubProxy()

    result = proxy.call({"command": "list", "repo_path": str(repo)})
    assert "file.txt" in result["files"]
    result = proxy.call({"command": "read", "repo_path": str(repo), "file": "file.txt"})
    assert result["content"] == "data"
