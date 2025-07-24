from __future__ import annotations

import platform
from typing import Any

from pydantic import BaseModel
from qwen_agent.tools.base import BaseTool, register_tool

from axon.plugins.base import Plugin


class EmptyInput(BaseModel):
    pass


class InfoOutput(BaseModel):
    text: str


@register_tool("get_os_version")
class GetOSVersion(BaseTool):
    """Return the host operating system version."""

    description = "Return the host operating system version"
    parameters: list[Any] = []

    def call(self, params: dict, **kwargs) -> str:
        self._verify_json_format_args(params)
        return f"The current OS is: {platform.system()} {platform.release()}"


class SystemInfoPlugin(Plugin[EmptyInput, InfoOutput]):
    """Plugin returning OS information."""

    input_model = EmptyInput
    output_model = InfoOutput

    def load(self, config: BaseModel | None) -> None:  # pragma: no cover - simple
        return

    def describe(self) -> dict[str, str]:
        return {"name": self.manifest.name, "description": self.manifest.description}

    def execute(self, data: EmptyInput) -> InfoOutput:
        tool = GetOSVersion()
        return InfoOutput(text=tool.call({}))


PLUGIN_CLASS = SystemInfoPlugin
