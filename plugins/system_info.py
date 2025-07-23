# axon/plugins/system_info.py

import platform
from agent.plugin_loader import plugin
from qwen_agent.tools.base import BaseTool, register_tool
from typing import Any


@register_tool("get_os_version")
class GetOSVersion(BaseTool):
    """Return the host operating system version."""

    description = "Return the host operating system version"
    parameters: list[Any] = []

    def call(self, params: Any, **kwargs) -> str:
        # No parameters needed, just verify empty input
        self._verify_json_format_args(params)
        return f"The current OS is: {platform.system()} {platform.release()}"

@plugin(
    name="get_os_version",
    description="Return the host operating system version",
    usage="get_os_version()"
)
def get_os_version():
    """Return the current OS version."""
    tool = GetOSVersion()
    return tool.call({})

