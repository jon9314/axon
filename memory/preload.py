# axon/memory/preload.py

"""Load sample memory entries on startup."""

import json
import yaml
from .memory_handler import MemoryHandler


def preload(
    memory_handler: MemoryHandler, path: str = "data/initial_memory.yaml"
) -> None:
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        print("No preload file found.")
        return

    for fact in data.get("facts", []):
        memory_handler.add_fact(
            thread_id=fact.get("thread_id", "default_thread"),
            key=fact.get("key"),
            value=fact.get("value"),
            identity=fact.get("identity"),
            domain=fact.get("domain"),
        )

    for i, message in enumerate(data.get("mcp_messages", []), start=1):
        memory_handler.add_fact(
            thread_id="mcp", key=f"mcp_message_{i}", value=json.dumps(message)
        )
