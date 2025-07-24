import time
from typing import Any

from pydantic import BaseModel
from qwen_agent.tools.base import BaseTool, register_tool

from axon.plugins.base import Plugin


@register_tool("clipboard_monitor")
class ClipboardMonitor(BaseTool):
    """Return clipboard changes detected within the given period."""

    description = "Watch clipboard for updates for a few seconds"
    parameters = [
        {
            "name": "seconds",
            "type": "integer",
            "description": "Duration to monitor clipboard",
            "required": False,
            "default": 15,
        }
    ]

    def call(self, params: Any, **kwargs):
        args = self._verify_json_format_args(params)
        seconds = int(args.get("seconds", 15))
        if not pyperclip or not keyboard:
            return "pyperclip and keyboard modules required"
        end = time.time() + seconds
        last = pyperclip.paste()
        seen: list[str] = []
        while time.time() < end:
            current = pyperclip.paste()
            if current != last:
                seen.append(current)
                last = current
            time.sleep(0.5)
        return seen


try:
    import keyboard
    import pyperclip
except Exception:  # pragma: no cover - optional dependency
    pyperclip = None
    keyboard = None


class ClipboardMonitorPlugin(Plugin):
    """Plugin wrapper for clipboard monitoring."""

    def load(self, config: BaseModel | None) -> None:  # pragma: no cover - no op
        return

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.manifest["name"],
            "description": self.manifest["description"],
        }

    def execute(self, data: Any) -> Any:
        tool = ClipboardMonitor()
        return tool.call({"seconds": data.get("seconds", 15)})


PLUGIN_CLASS = ClipboardMonitorPlugin
