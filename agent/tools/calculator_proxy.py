import os
import requests
from agent.plugin_loader import plugin
from qwen_agent.tools.base import BaseTool, register_tool
from typing import Any

BASE_URL = os.environ.get("CALC_MCP_URL", "http://localhost:9003")


@register_tool("calculator")
class CalculatorProxy(BaseTool):
    """Perform calculations via MCP."""

    description = "Perform calculations via MCP"
    parameters = [
        {
            "name": "command",
            "type": "string",
            "description": "Operation to perform: evaluate or percent",
            "required": True,
        },
        {
            "name": "expr",
            "type": "string",
            "description": "Expression to evaluate",
        },
        {
            "name": "x",
            "type": "number",
            "description": "First value for percent",
        },
        {
            "name": "y",
            "type": "number",
            "description": "Second value for percent",
        },
    ]

    def __init__(self, cfg: Any | None = None):
        super().__init__(cfg)
        self.base_url = os.environ.get("CALC_MCP_URL", "http://localhost:9003")

    def call(self, params: Any, **kwargs):
        args = self._verify_json_format_args(params)
        command = args["command"]
        if command == "evaluate":
            resp = requests.get(f"{self.base_url}/evaluate", params=args)
        elif command == "percent":
            resp = requests.get(f"{self.base_url}/percent", params=args)
        else:
            return f"Unknown command {command}"
        resp.raise_for_status()
        return resp.json()

@plugin(
    name="calculator",
    description="Perform calculations via MCP",
    usage="calculator(command='evaluate', expr='2+2')"
)
def calculator(command: str, **kwargs):
    tool = CalculatorProxy()
    params = {"command": command, **kwargs}
    return tool.call(params)
