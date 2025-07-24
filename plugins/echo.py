from __future__ import annotations

from pydantic import BaseModel
from qwen_agent.tools.base import BaseTool, register_tool

from axon.plugins.base import Plugin


class EchoInput(BaseModel):
    text: str


class EchoOutput(BaseModel):
    text: str


@register_tool("echo")
class EchoTool(BaseTool):
    """Echo back the provided text"""

    description = "Echo back the provided text"
    parameters = [
        {"name": "text", "type": "string", "description": "Text to echo back", "required": True}
    ]

    def call(self, params: dict, **kwargs) -> str:
        args = self._verify_json_format_args(params)
        return args["text"]


class EchoPlugin(Plugin[EchoInput, EchoOutput]):
    """Simple echo plugin."""

    input_model = EchoInput
    output_model = EchoOutput

    def load(self, config: BaseModel | None) -> None:  # pragma: no cover - simple
        return

    def describe(self) -> dict[str, str]:
        return {"name": self.manifest.name, "description": self.manifest.description}

    def execute(self, data: EchoInput) -> EchoOutput:
        tool = EchoTool()
        return EchoOutput(text=tool.call({"text": data.text}))


PLUGIN_CLASS = EchoPlugin
