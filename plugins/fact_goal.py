from agent.plugin_loader import plugin
from agent.plugin_context import context
from qwen_agent.tools.base import BaseTool, register_tool
from typing import Any


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


@plugin(
    name="remember_goal",
    description="Store a fact and log a goal",
    usage="remember_goal(key='topic', value='info', goal='Finish project')",
)
def remember_goal(key: str, value: str, goal: str) -> str:
    """Demo plugin that saves a fact then records a goal."""
    tool = RememberGoal()
    return tool.call({"key": key, "value": value, "goal": goal})
