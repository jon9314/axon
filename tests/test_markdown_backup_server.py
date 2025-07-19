from fastapi.testclient import TestClient
from mcp_servers.markdown_backup_server import app, BASE_DIR
import os
import shutil

client = TestClient(app)


def setup_module(module):
    if os.path.exists(BASE_DIR):
        shutil.rmtree(BASE_DIR)
    os.makedirs(BASE_DIR)


def test_save_get_search():
    resp = client.post("/save", params={"name": "note1"}, json={"content": "hello"})
    assert resp.status_code == 200

    resp = client.get("/get", params={"name": "note1"})
    assert resp.json()["content"] == "hello"

    resp = client.get("/search", params={"query": "hell"})
    assert "note1" in resp.json()["matches"]
