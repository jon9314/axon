import os
import requests
from agent.plugin_loader import plugin

BASE_URL = os.environ.get("FILESYSTEM_MCP_URL", "http://localhost:9001")

@plugin(
    name="filesystem",
    description="Interact with local filesystem via MCP",
    usage="filesystem(command='read', path='file.txt')"
)
def filesystem(command: str, path: str = "", content: str | None = None):
    if command == "list":
        resp = requests.get(f"{BASE_URL}/list", params={"path": path})
    elif command == "read":
        resp = requests.get(f"{BASE_URL}/read", params={"path": path})
    elif command == "write":
        resp = requests.post(f"{BASE_URL}/write", params={"path": path}, json={"content": content or ""})
    elif command == "exists":
        resp = requests.get(f"{BASE_URL}/exists", params={"path": path})
    else:
        return f"Unknown command {command}"
    resp.raise_for_status()
    return resp.json()
