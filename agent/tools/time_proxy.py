import os
import requests
from agent.plugin_loader import plugin
from qwen_agent.tools.base import BaseTool, register_tool
from typing import Any

BASE_URL = os.environ.get("TIME_MCP_URL", "http://localhost:9002")


@register_tool("time")
class TimeProxy(BaseTool):
    """Access system time via MCP."""

    description = "Access system time via MCP"
    parameters = [
        {
            "name": "command",
            "type": "string",
            "description": "Operation to perform: now, timezone or duration",
            "required": True,
        },
        {
            "name": "start",
            "type": "string",
            "description": "Start time for duration command",
        },
        {
            "name": "end",
            "type": "string",
            "description": "End time for duration command",
        },
    ]

    def __init__(self, cfg: Any | None = None):
        super().__init__(cfg)
        self.base_url = os.environ.get("TIME_MCP_URL", "http://localhost:9002")

    def call(self, params: Any, **kwargs):
        args = self._verify_json_format_args(params)
        command = args["command"]
        if command == "now":
            resp = requests.get(f"{self.base_url}/now")
        elif command == "timezone":
            resp = requests.get(f"{self.base_url}/timezone")
        elif command == "duration":
            resp = requests.get(f"{self.base_url}/duration", params=args)
        else:
            return f"Unknown command {command}"
        resp.raise_for_status()
        return resp.json()

@plugin(
    name="time",
    description="Access system time via MCP",
    usage="time(command='now')"
)
def time_tool(command: str, **kwargs):
    tool = TimeProxy()
    params = {"command": command, **kwargs}
    return tool.call(params)
