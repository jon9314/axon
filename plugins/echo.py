# axon/plugins/echo.py

from agent.plugin_loader import plugin
from qwen_agent.tools.base import BaseTool, register_tool
from typing import Any


@register_tool("echo")
class EchoTool(BaseTool):
    """Echo back the provided text"""

    description = "Echo back the provided text"
    parameters = [
        {
            "name": "text",
            "type": "string",
            "description": "Text to echo back",
            "required": True,
        }
    ]

    def call(self, params: Any, **kwargs) -> str:
        args = self._verify_json_format_args(params)
        return args["text"]

@plugin(
    name="echo",
    description="Echo back the provided text",
    usage="echo('hello')"
)
def echo(text: str) -> str:
    tool = EchoTool()
    return tool.call({"text": text})
