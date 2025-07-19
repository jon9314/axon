# axon/plugins/echo.py

from agent.plugin_loader import plugin

@plugin(
    name="echo",
    description="Echo back the provided text",
    usage="echo('hello')"
)
def echo(text: str) -> str:
    return text
