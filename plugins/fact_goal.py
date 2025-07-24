from __future__ import annotations

from pydantic import BaseModel
from qwen_agent.tools.base import BaseTool, register_tool

from agent.plugin_context import context
from axon.plugins.base import Plugin


class GoalInput(BaseModel):
    key: str
    value: str
    goal: str


class GoalOutput(BaseModel):
    result: str


@register_tool("remember_goal")
class RememberGoal(BaseTool):
    """Store a fact and record a goal."""

    description = "Store a fact and log a goal"
    parameters = [
        {"name": "key", "type": "string", "description": "Fact key", "required": True},
        {"name": "value", "type": "string", "description": "Fact value", "required": True},
        {"name": "goal", "type": "string", "description": "Goal text to record", "required": True},
    ]

    def call(self, params: dict, **kwargs) -> str:
        args = self._verify_json_format_args(params)
        context.add_fact(args["key"], args["value"])
        context.add_goal(args["goal"])
        return "ok"


class RememberGoalPlugin(Plugin[GoalInput, GoalOutput]):
    """Demo plugin that saves a fact then records a goal."""

    input_model = GoalInput
    output_model = GoalOutput

    def load(self, config: BaseModel | None) -> None:  # pragma: no cover - simple
        return

    def describe(self) -> dict[str, str]:
        return {"name": self.manifest.name, "description": self.manifest.description}

    def execute(self, data: GoalInput) -> GoalOutput:
        tool = RememberGoal()
        result = tool.call({"key": data.key, "value": data.value, "goal": data.goal})
        return GoalOutput(result=result)


PLUGIN_CLASS = RememberGoalPlugin
