from agent.plugin_loader import plugin
from agent.plugin_context import context


@plugin(
    name="remember_goal",
    description="Store a fact and log a goal",
    usage="remember_goal(key='topic', value='info', goal='Finish project')",
)
def remember_goal(key: str, value: str, goal: str) -> str:
    """Demo plugin that saves a fact then records a goal."""
    context.add_fact(key, value)
    context.add_goal(goal)
    return "ok"
