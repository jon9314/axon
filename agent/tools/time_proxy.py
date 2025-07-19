import os
import requests
from agent.plugin_loader import plugin

BASE_URL = os.environ.get("TIME_MCP_URL", "http://localhost:9002")

@plugin(
    name="time",
    description="Access system time via MCP",
    usage="time(command='now')"
)
def time_tool(command: str, **kwargs):
    if command == "now":
        resp = requests.get(f"{BASE_URL}/now")
    elif command == "timezone":
        resp = requests.get(f"{BASE_URL}/timezone")
    elif command == "duration":
        resp = requests.get(f"{BASE_URL}/duration", params=kwargs)
    else:
        return f"Unknown command {command}"
    resp.raise_for_status()
    return resp.json()
