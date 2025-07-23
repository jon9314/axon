# axon/main.py

from typing import Optional

import typer
import uvicorn
import asyncio
from agent.plugin_loader import load_plugins, AVAILABLE_PLUGINS
from agent.mcp_router import MCPRouter
from memory.user_profile import UserProfileManager
from agent.reminder import ReminderManager
from agent.context_manager import ContextManager

# Global managers used across commands
profile_manager = UserProfileManager()
reminder_manager = ReminderManager()

app = typer.Typer(
    name="axon",
    help="The main entry point for the Axon project, supporting different operational modes."
)

@app.command()
def web():
    """
    Starts the FastAPI web server for the backend API and WebSocket.
    """
    print("Starting web server...")
    uvicorn.run(
        "axon.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

@app.command()
def cli():
    """
    Starts the Axon agent in an interactive command-line interface (CLI) mode.
    """
    # --- NEW: Load plugins on CLI startup ---
    print("Loading plugins...")
    load_plugins(hot_reload=True)
    print(f"Plugins loaded: {list(AVAILABLE_PLUGINS.keys())}")
    # --- END NEW ---
    
    print("\nStarting CLI mode...")
    print("Type 'exit' or 'quit' to stop.")
    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting CLI mode.")
                break

            # --- NEW: Check for and execute plugins ---
            if user_input in AVAILABLE_PLUGINS:
                plugin_info = AVAILABLE_PLUGINS[user_input]
                result = plugin_info.func()
                print(f"Plugin '{user_input}': {result}")
            else:
                # Placeholder for your agent's regular processing logic
                print(f"Agent: I would process '{user_input}' now.")
            # --- END NEW ---

    except KeyboardInterrupt:
        print("\nExiting CLI mode.")


@app.command()
def headless():
    """
    Runs the Axon agent in headless mode, performing a background task.
    """
    print("Running in headless mode...")

    async def background_task():
        count = 0
        while count < 5:
            print(f"Headless agent is running... (Cycle {count + 1})")
            await asyncio.sleep(2) # Simulate doing work
            count += 1

    try:
        asyncio.run(background_task())
    except KeyboardInterrupt:
        print("\nStopping headless mode.")
    finally:
        print("Headless mode finished.")


@app.command()
def set_profile(identity: str, persona: str = "assistant", tone: str = "neutral", email: Optional[str] = None) -> None:
    """Create or update a user profile."""
    profile_manager.set_profile(identity, persona=persona, tone=tone, email=email)
    print(f"Profile saved for {identity}.")


@app.command()
def remind(message: str, delay: int = 60, thread_id: str = "cli_thread") -> None:
    """Schedule a reminder in seconds."""
    reminder_manager.schedule(message, delay, thread_id)
    print(f"Reminder set in {delay} seconds: {message}")


@app.command("clipboard-monitor")
def clipboard_monitor_cmd(seconds: int = 15) -> None:
    """Run the clipboard monitor plugin."""
    from plugins.clipboard_monitor import clipboard_monitor

    result = clipboard_monitor(seconds)
    print(result)


@app.command()
def remember(topic: str, fact: str, thread_id: str = "cli_thread", identity: str = "cli_user") -> None:
    """Store a fact directly into Axon's memory."""
    cm = ContextManager(thread_id=thread_id, identity=identity)
    cm.add_fact(topic, fact)
    print(f"Remembered '{topic}' = '{fact}'.")


@app.command("mcp-tools")
def list_mcp_tools(config: str = "config/mcp_servers.yaml") -> None:
    """List registered MCP tools and check connectivity."""
    router = MCPRouter(config)
    for name in router.list_tools():
        status = "ok" if router.check_tool(name) else "unreachable"
        print(f"{name}: {status}")


if __name__ == "__main__":
    app()

