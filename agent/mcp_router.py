import os
import json
import yaml
import subprocess
import requests
from typing import Any, Dict, List, Optional


class MCPRouter:
    """Registry and transport handler for MCP tools."""

    def __init__(self, config_path: str = "config/mcp_servers.yaml") -> None:
        self.tools: Dict[str, Dict[str, Any]] = {}
        if os.path.exists(config_path):
            self.load_config(config_path)

    def load_config(self, path: str) -> None:
        """Load tool info from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
        if isinstance(data, dict):
            servers = data.get("servers", [])
        else:
            servers = data
        for entry in servers:
            name = entry.get("name")
            if name:
                self.tools[name] = entry

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        return self.tools.get(name)

    def call(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a payload to the given tool using its configured transport."""
        info = self.get_tool(name)
        if not info:
            raise ValueError(f"Unknown tool: {name}")
        transport = info.get("transport")
        if transport == "http":
            url = str(info["url"]).rstrip("/")
            command = payload.get("command")
            if command:
                resp = requests.get(f"{url}/{command}", params=payload)
            else:
                resp = requests.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
        if transport == "stdio":
            cmd = info["command"]
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            stdout, stderr = proc.communicate(json.dumps(payload))
            if proc.returncode != 0:
                raise RuntimeError(stderr.strip())
            return json.loads(stdout.strip() or "{}")
        raise ValueError(f"Unsupported transport: {transport}")


# Global router instance loaded from default config
mcp_router = MCPRouter()
