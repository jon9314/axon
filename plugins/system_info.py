# axon/plugins/system_info.py

import platform
from typing import Any

from pydantic import BaseModel
from qwen_agent.tools.base import BaseTool, register_tool

from axon.plugins.base import Plugin


@register_tool("get_os_version")
class GetOSVersion(BaseTool):
    """Return the host operating system version."""

    description = "Return the host operating system version"
    parameters: list[Any] = []

    def call(self, params: Any, **kwargs) -> str:
        # No parameters needed, just verify empty input
        self._verify_json_format_args(params)
        return f"The current OS is: {platform.system()} {platform.release()}"


class SystemInfoPlugin(Plugin):
    """Plugin returning OS information."""

    def load(self, config: BaseModel | None) -> None:  # pragma: no cover - no op
        return

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.manifest["name"],
            "description": self.manifest["description"],
        }

    def execute(self, data: Any) -> str:
        tool = GetOSVersion()
        return tool.call({})


PLUGIN_CLASS = SystemInfoPlugin
