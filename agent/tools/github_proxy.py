import os
from typing import Any

import requests
from qwen_agent.tools.base import BaseTool, register_tool

from agent.plugin_loader import plugin

BASE_URL = os.environ.get("GITHUB_MCP_URL", "http://localhost:9005")


@register_tool("github")
class GitHubProxy(BaseTool):
    """Read GitHub repository files via MCP."""

    description = "Read or write GitHub repository files via MCP"
    parameters = [
        {
            "name": "command",
            "type": "string",
            "description": "Operation to perform: list, read or write",
            "required": True,
        },
        {"name": "repo_path", "type": "string", "description": "Local repo path"},
        {"name": "file", "type": "string", "description": "File path when reading or writing"},
        {"name": "content", "type": "string", "description": "File content when writing"},
        {"name": "message", "type": "string", "description": "Commit message when writing"},
    ]

    def __init__(self, cfg: Any | None = None):
        super().__init__(cfg)
        self.base_url = os.environ.get("GITHUB_MCP_URL", "http://localhost:9005")

    def call(self, params: Any, **kwargs):
        args = self._verify_json_format_args(params)
        command = args["command"]
        repo_path = args.get("repo_path", "")
        if command == "list":
            resp = requests.get(f"{self.base_url}/list", params={"repo_path": repo_path})
        elif command == "read":
            resp = requests.get(
                f"{self.base_url}/read",
                params={"repo_path": repo_path, "file": args.get("file")},
            )
        elif command == "write":
            resp = requests.post(
                f"{self.base_url}/write",
                params={
                    "repo_path": repo_path,
                    "file": args.get("file"),
                    "message": args.get("message", "update"),
                },
                json={"content": args.get("content", "")},
            )
        else:
            return f"Unknown command {command}"
        resp.raise_for_status()
        return resp.json()


@plugin(
    name="github",
    description="Read or write GitHub repository files via MCP",
    usage="github(command='list', repo_path='path')",
)
def github(command: str, **kwargs):
    tool = GitHubProxy()
    params = {"command": command, **kwargs}
    return tool.call(params)
