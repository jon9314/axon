import os
from typing import Any

import requests
from qwen_agent.tools.base import BaseTool, register_tool

from agent.plugin_loader import plugin

BASE_URL = os.environ.get("FILESYSTEM_MCP_URL", "http://localhost:9001")


@register_tool("filesystem")
class FilesystemProxy(BaseTool):
    """Interact with the local filesystem via MCP."""

    description = "Interact with local filesystem via MCP"
    parameters = [
        {
            "name": "command",
            "type": "string",
            "description": "Operation to perform: list, read, write or exists",
            "required": True,
        },
        {
            "name": "path",
            "type": "string",
            "description": "Filesystem path",
        },
        {
            "name": "content",
            "type": "string",
            "description": "Content used when writing files",
        },
    ]

    def __init__(self, cfg: Any | None = None):
        super().__init__(cfg)
        self.base_url = os.environ.get("FILESYSTEM_MCP_URL", "http://localhost:9001")

    def call(self, params: Any, **kwargs):
        args = self._verify_json_format_args(params)
        command = args["command"]
        path = args.get("path", "")
        content = args.get("content")
        if command == "list":
            resp = requests.get(f"{self.base_url}/list", params={"path": path})
        elif command == "read":
            resp = requests.get(f"{self.base_url}/read", params={"path": path})
        elif command == "write":
            resp = requests.post(
                f"{self.base_url}/write", params={"path": path}, json={"content": content or ""}
            )
        elif command == "exists":
            resp = requests.get(f"{self.base_url}/exists", params={"path": path})
        else:
            return f"Unknown command {command}"
        resp.raise_for_status()
        return resp.json()


@plugin(
    name="filesystem",
    description="Interact with local filesystem via MCP",
    usage="filesystem(command='read', path='file.txt')",
)
def filesystem(command: str, path: str = "", content: str | None = None):
    tool = FilesystemProxy()
    return tool.call({"command": command, "path": path, "content": content})
