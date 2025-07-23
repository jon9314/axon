import os
import requests
from agent.plugin_loader import plugin
from qwen_agent.tools.base import BaseTool, register_tool
from typing import Any

BASE_URL = os.environ.get("WOLFRAM_MCP_URL", "http://localhost:9008")


@register_tool("wolframalpha")
class WolframAlphaProxy(BaseTool):
    """Query WolframAlpha via MCP."""

    description = "Query WolframAlpha via MCP"
    parameters = [
        {"name": "query", "type": "string", "description": "Query expression", "required": True}
    ]

    def __init__(self, cfg: Any | None = None):
        super().__init__(cfg)
        self.base_url = os.environ.get("WOLFRAM_MCP_URL", "http://localhost:9008")

    def call(self, params: Any, **kwargs):
        args = self._verify_json_format_args(params)
        resp = requests.get(f"{self.base_url}/query", params={"expression": args["query"]})
        resp.raise_for_status()
        return resp.json()


@plugin(
    name="wolframalpha",
    description="Query WolframAlpha via MCP",
    usage="wolframalpha(query='integrate x^2')",
)
def wolframalpha(query: str):
    tool = WolframAlphaProxy()
    return tool.call({"query": query})
