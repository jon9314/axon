from __future__ import annotations

import time

from pydantic import BaseModel
from qwen_agent.tools.base import BaseTool, register_tool

from axon.plugins.base import Plugin

try:  # pragma: no cover - optional deps
    import keyboard
    import pyperclip
except Exception:  # pragma: no cover - optional deps
    pyperclip = None
    keyboard = None


class MonitorInput(BaseModel):
    seconds: int = 15


class MonitorOutput(BaseModel):
    items: list[str]


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

    def call(self, params: dict, **kwargs) -> list[str] | str:
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


class ClipboardMonitorPlugin(Plugin[MonitorInput, MonitorOutput]):
    """Plugin wrapper for clipboard monitoring."""

    input_model = MonitorInput
    output_model = MonitorOutput

    def load(self, config: BaseModel | None) -> None:  # pragma: no cover - simple
        return

    def describe(self) -> dict[str, str]:
        return {"name": self.manifest.name, "description": self.manifest.description}

    def execute(self, data: MonitorInput) -> MonitorOutput:
        tool = ClipboardMonitor()
        result = tool.call({"seconds": data.seconds})
        if isinstance(result, list):
            return MonitorOutput(items=result)
        return MonitorOutput(items=[result])


PLUGIN_CLASS = ClipboardMonitorPlugin
