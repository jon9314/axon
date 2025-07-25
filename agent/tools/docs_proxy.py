import os
from typing import Any

import requests
from qwen_agent.tools.base import BaseTool, register_tool

from agent.plugin_loader import plugin

BASE_URL = os.environ.get("DOCS_MCP_URL", "http://localhost:9006")


@register_tool("docs")
class DocsProxy(BaseTool):
    """Retrieve Python documentation via MCP."""

    description = "Retrieve Python documentation via MCP"
    parameters = [
        {
            "name": "topic",
            "type": "string",
            "description": "Python topic or module name",
            "required": True,
        }
    ]

    def __init__(self, cfg: Any | None = None):
        super().__init__(cfg)
        self.base_url = os.environ.get("DOCS_MCP_URL", "http://localhost:9006")

    def call(self, params: Any, **kwargs):
        args = self._verify_json_format_args(params)
        resp = requests.get(f"{self.base_url}/get", params={"topic": args["topic"]})
        resp.raise_for_status()
        return resp.json()


@plugin(
    name="docs",
    description="Retrieve Python documentation via MCP",
    usage="docs(topic='asyncio')",
)
def docs(topic: str):
    tool = DocsProxy()
    return tool.call({"topic": topic})
