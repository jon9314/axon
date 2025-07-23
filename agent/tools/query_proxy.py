import os
import requests
from agent.plugin_loader import plugin
from qwen_agent.tools.base import BaseTool, register_tool
from typing import Any

BASE_URL = os.environ.get("QUERY_MCP_URL", "http://localhost:9007")


@register_tool("query")
class QueryProxy(BaseTool):
    """Run SQL queries on CSV files via MCP."""

    description = "Run SQL queries on CSV files via MCP"
    parameters = [
        {"name": "path", "type": "string", "description": "CSV file path", "required": True},
        {"name": "sql", "type": "string", "description": "SQL query to execute", "required": True},
    ]

    def __init__(self, cfg: Any | None = None):
        super().__init__(cfg)
        self.base_url = os.environ.get("QUERY_MCP_URL", "http://localhost:9007")

    def call(self, params: Any, **kwargs):
        args = self._verify_json_format_args(params)
        resp = requests.post(
            f"{self.base_url}/query",
            params={"path": args["path"]},
            json={"sql": args["sql"]},
        )
        resp.raise_for_status()
        return resp.json()


@plugin(
    name="query",
    description="Run SQL queries on CSV files via MCP",
    usage="query(path='data.csv', sql='SELECT * FROM data')",
)
def query(path: str, sql: str):
    tool = QueryProxy()
    return tool.call({"path": path, "sql": sql})
