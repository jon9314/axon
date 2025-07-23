from fastapi.testclient import TestClient
from mcp_servers.github_server import app
import subprocess

client = TestClient(app)


def test_list_and_read(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
    file = repo / "README.md"
    file.write_text("hello", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True)

    resp = client.get("/list", params={"repo_path": str(repo)})
    assert resp.status_code == 200
    assert "README.md" in resp.json()["files"]

    resp = client.get("/read", params={"repo_path": str(repo), "file": "README.md"})
    assert resp.json()["content"] == "hello"


def test_write(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)

    resp = client.post(
        "/write",
        params={"repo_path": str(repo), "file": "notes.txt", "message": "add"},
        json={"content": "data"},
    )
    assert resp.status_code == 200
    assert (repo / "notes.txt").read_text() == "data"
    log = subprocess.check_output([
        "git",
        "-C",
        str(repo),
        "log",
        "-1",
        "--pretty=%s",
    ], text=True).strip()
    assert log == "add"
