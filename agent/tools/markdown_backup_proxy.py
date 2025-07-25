import os
from typing import Any

import requests
from qwen_agent.tools.base import BaseTool, register_tool

from agent.plugin_loader import plugin

BASE_URL = os.environ.get("MARKDOWN_MCP_URL", "http://localhost:9004")


@register_tool("markdown_backup")
class MarkdownBackupProxy(BaseTool):
    """Save and retrieve markdown notes via MCP."""

    description = "Save and retrieve markdown notes via MCP"
    parameters = [
        {
            "name": "command",
            "type": "string",
            "description": "Operation to perform: save, get or search",
            "required": True,
        },
        {
            "name": "name",
            "type": "string",
            "description": "Note name",
        },
        {
            "name": "content",
            "type": "string",
            "description": "Markdown content when saving",
        },
        {
            "name": "query",
            "type": "string",
            "description": "Search query",
        },
    ]

    def __init__(self, cfg: Any | None = None):
        super().__init__(cfg)
        self.base_url = os.environ.get("MARKDOWN_MCP_URL", "http://localhost:9004")

    def call(self, params: Any, **kwargs):
        args = self._verify_json_format_args(params)
        command = args["command"]
        if command == "save":
            resp = requests.post(
                f"{self.base_url}/save",
                params={"name": args.get("name")},
                json={"content": args.get("content", "")},
            )
        elif command == "get":
            resp = requests.get(f"{self.base_url}/get", params={"name": args.get("name")})
        elif command == "search":
            resp = requests.get(f"{self.base_url}/search", params={"query": args.get("query", "")})
        else:
            return f"Unknown command {command}"
        resp.raise_for_status()
        return resp.json()


@plugin(
    name="markdown_backup",
    description="Save and retrieve markdown notes via MCP",
    usage="markdown_backup(command='save', name='note', content='text')",
)
def markdown_backup(command: str, **kwargs):
    tool = MarkdownBackupProxy()
    kwargs = {"command": command, **kwargs}
    return tool.call(kwargs)
