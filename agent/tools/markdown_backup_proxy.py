import os
import requests
from agent.plugin_loader import plugin

BASE_URL = os.environ.get("MARKDOWN_MCP_URL", "http://localhost:9004")

@plugin(
    name="markdown_backup",
    description="Save and retrieve markdown notes via MCP",
    usage="markdown_backup(command='save', name='note', content='text')"
)
def markdown_backup(command: str, **kwargs):
    if command == "save":
        resp = requests.post(f"{BASE_URL}/save", params={"name": kwargs.get("name")}, json={"content": kwargs.get("content", "")})
    elif command == "get":
        resp = requests.get(f"{BASE_URL}/get", params={"name": kwargs.get("name")})
    elif command == "search":
        resp = requests.get(f"{BASE_URL}/search", params={"query": kwargs.get("query", "")})
    else:
        return f"Unknown command {command}"
    resp.raise_for_status()
    return resp.json()
