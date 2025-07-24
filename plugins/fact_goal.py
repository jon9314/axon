from typing import Any

from pydantic import BaseModel
from qwen_agent.tools.base import BaseTool, register_tool

from agent.plugin_context import context
from axon.plugins.base import Plugin


@register_tool("remember_goal")
class RememberGoal(BaseTool):
    """Store a fact and record a goal."""

    description = "Store a fact and log a goal"
    parameters = [
        {
            "name": "key",
            "type": "string",
            "description": "Fact key",
            "required": True,
        },
        {
            "name": "value",
            "type": "string",
            "description": "Fact value",
            "required": True,
        },
        {
            "name": "goal",
            "type": "string",
            "description": "Goal text to record",
            "required": True,
        },
    ]

    def call(self, params: Any, **kwargs) -> str:
        args = self._verify_json_format_args(params)
        context.add_fact(args["key"], args["value"])
        context.add_goal(args["goal"])
        return "ok"


class RememberGoalPlugin(Plugin):
    """Demo plugin that saves a fact then records a goal."""

    def load(self, config: BaseModel | None) -> None:  # pragma: no cover - no op
        return

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.manifest["name"],
            "description": self.manifest["description"],
        }

    def execute(self, data: Any) -> str:
        tool = RememberGoal()
        return tool.call(
            {
                "key": data["key"],
                "value": data["value"],
                "goal": data["goal"],
            }
        )


PLUGIN_CLASS = RememberGoalPlugin
