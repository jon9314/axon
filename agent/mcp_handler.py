# axon/agent/mcp_handler.py

class MCPHandler:
    """
    Handles the Master Control Program (MCP) protocol for structured
    communication between the agent and its tools.
    """
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
        is_mcp = 'mcp_protocol_version' in message
        print(f"Parsing message. Is MCP format: {is_mcp}")
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
        mcp_message = {
            "mcp_protocol_version": "1.0",
            "tool_name": tool_name,
            "arguments": args
        }
        print(f"Generated MCP message for tool '{tool_name}'")
        return mcp_message


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
        return plugin_info.func(**args)
