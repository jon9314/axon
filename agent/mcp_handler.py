# axon/agent/mcp_handler.py

import logging


class MCPHandler:
    """Handle Model Context Protocol messages and normalize results."""

    def parse_message(self, message: dict) -> bool:
        """
        Checks if a message conforms to the basic MCP protocol by looking for
        a specific key.

        Args:
            message (dict): The incoming message dictionary.

        Returns:
            bool: True if the message is an MCP message, False otherwise.
        """
        # This simple check is the first step in routing and validating
        # tool-related commands.
        is_mcp = "mcp_protocol_version" in message
        logging.debug("mcp-parse", extra={"is_mcp": is_mcp})
        return is_mcp

    def generate_message(self, tool_name: str, args: dict) -> dict:
        """
        Generates a message dictionary that conforms to the MCP protocol.

        Args:
            tool_name (str): The name of the tool to be invoked.
            args (dict): The arguments to be passed to the tool.

        Returns:
            dict: A dictionary formatted for the MCP protocol.
        """
        # This creates a standardized message format that tools can reliably parse.
        mcp_message = {"mcp_protocol_version": "1.0", "tool_name": tool_name, "arguments": args}
        logging.debug("mcp-generate", extra={"tool": tool_name})
        return mcp_message

    def _normalize(self, source: str, args: dict, output: dict) -> tuple[str, float]:
        """Convert a tool response into a human readable summary.

        Parameters
        ----------
        source: str
            Name of the MCP tool producing the output.
        args: dict
            Original arguments passed to the tool.
        output: dict
            Raw JSON output returned by the tool.

        Returns
        -------
        Tuple[str, float]
            A summary string and confidence score.
        """

        summary = ""
        confidence = 0.9

        if source == "calculator" and "result" in output:
            summary = f"Calculator result: {output['result']}"
        elif source == "time":
            if "timestamp" in output:
                summary = f"Current time is {output['timestamp']}"
            elif "timezone" in output:
                summary = f"System timezone is {output['timezone']}"
            elif "seconds" in output:
                summary = f"Duration is {output['seconds']} seconds"
        elif source == "filesystem":
            path = args.get("path", "")
            if "files" in output:
                files = ", ".join(output["files"])
                summary = f"Files in {path or '.'}: {files}"
            elif "content" in output:
                content = output["content"]
                snippet = content[:40] + ("..." if len(content) > 40 else "")
                summary = f"Read {path}: {snippet}"
            elif "status" in output:
                summary = f"Write {path}: {output['status']}"
            elif "exists" in output:
                summary = f"File {path} exists" if output["exists"] else f"File {path} missing"
        elif source == "markdown_backup":
            note = args.get("name", "")
            if "status" in output:
                summary = f"Saved markdown note {note}"
            elif "content" in output:
                summary = f"Fetched markdown note {note}"
            elif "matches" in output:
                summary = f"Found {len(output['matches'])} notes for '{args.get('query', '')}'"
        if not summary:
            confidence = 0.5
            summary = str(output)
        return summary, confidence

    def handle_message(self, message: dict):
        """Route MCP message to matching plugin and return its result."""
        if not self.parse_message(message):
            raise ValueError("Not an MCP message")

        from agent.plugin_loader import AVAILABLE_PLUGINS

        tool_name = message.get("tool_name")
        args = message.get("arguments", {})
        if tool_name not in AVAILABLE_PLUGINS:
            raise ValueError(f"Unknown tool: {tool_name}")
        plugin_info = AVAILABLE_PLUGINS[tool_name]
        output = plugin_info.func(**args)
        summary, confidence = self._normalize(tool_name, args, output)
        return {
            "source": tool_name,
            "output": output,
            "summary": summary,
            "confidence": confidence,
        }
