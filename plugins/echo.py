# axon/plugins/echo.py

from typing import Any

from pydantic import BaseModel
from qwen_agent.tools.base import BaseTool, register_tool

from axon.plugins.base import Plugin


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


class EchoPlugin(Plugin):
    """Simple echo plugin."""

    def load(self, config: BaseModel | None) -> None:  # pragma: no cover - no op
        return

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.manifest["name"],
            "description": self.manifest["description"],
        }

    def execute(self, data: Any) -> str:
        tool = EchoTool()
        return tool.call({"text": data["text"]})


PLUGIN_CLASS = EchoPlugin
