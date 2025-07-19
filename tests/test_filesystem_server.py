from fastapi.testclient import TestClient
from mcp_servers.filesystem_server import app
import os

client = TestClient(app)


def test_list_and_read_write_exists(tmp_path):
    file_path = tmp_path / "test.txt"
    # write
    resp = client.post("/write", params={"path": str(file_path)}, json={"content": "hello"})
    assert resp.status_code == 200
    # exists
    resp = client.get("/exists", params={"path": str(file_path)})
    assert resp.json()["exists"] is True
    # list
    resp = client.get("/list", params={"path": str(tmp_path)})
    assert "test.txt" in resp.json()["files"]
    # read
    resp = client.get("/read", params={"path": str(file_path)})
    assert resp.json()["content"] == "hello"
