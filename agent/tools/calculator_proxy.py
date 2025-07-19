import os
import requests
from agent.plugin_loader import plugin

BASE_URL = os.environ.get("CALC_MCP_URL", "http://localhost:9003")

@plugin(
    name="calculator",
    description="Perform calculations via MCP",
    usage="calculator(command='evaluate', expr='2+2')"
)
def calculator(command: str, **kwargs):
    if command == "evaluate":
        resp = requests.get(f"{BASE_URL}/evaluate", params=kwargs)
    elif command == "percent":
        resp = requests.get(f"{BASE_URL}/percent", params=kwargs)
    else:
        return f"Unknown command {command}"
    resp.raise_for_status()
    return resp.json()
