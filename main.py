# axon/main.py

import asyncio
from typing import Optional

import typer
import uvicorn
from rich.console import Console
from rich.prompt import Prompt

from agent.context_manager import ContextManager
from agent.mcp_router import MCPRouter
from agent.reminder import ReminderManager
from axon.config.settings import (
    get_settings,
    reload_settings,
    schema_json,
    validate_or_die,
)
from axon.plugins.loader import PluginLoader
from memory.user_profile import UserProfileManager

# Global managers used across commands
profile_manager = UserProfileManager()
reminder_manager = ReminderManager()
plugin_loader = PluginLoader()

app = typer.Typer(
    name="axon",
    help="The main entry point for the Axon project, supporting different operational modes.",
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    config: Optional[str] = typer.Option(
        None, "--config", help="Path to settings override YAML file"
    ),
) -> None:
    """Global CLI options."""
    if config:
        reload_settings(local_file=config)
    validate_or_die()
    summary = get_settings().pretty_dump().replace("\n", " ").strip()
    typer.echo(f"Config loaded: {summary}")
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("settings-schema")
def settings_schema_cmd() -> None:
    """Emit JSON schema for the config."""
    typer.echo(schema_json())


plugins_app = typer.Typer(help="Plugin management commands")
app.add_typer(plugins_app, name="plugins")


@plugins_app.command("reload")
def reload_plugins_cmd() -> None:
    """Reload plugins from disk and display the available set."""
    plugin_loader.discover()
    print(f"Plugins loaded: {list(plugin_loader.plugins.keys())}")


@plugins_app.command("list")
def list_plugins() -> None:
    plugin_loader.discover()
    for m in plugin_loader.manifests.values():
        perms = ",".join(p.value for p in m.permissions) or "-"
        print(f"{m.name} {m.version} {perms}")


@plugins_app.command("doctor")
def doctor_plugins() -> None:
    try:
        plugin_loader.discover()
        print(f"{len(plugin_loader.plugins)} plugins ok")
    except Exception as exc:
        print(f"Plugin validation failed: {exc}")


@plugins_app.command("run")
def run_plugin(name: str, payload: str = "{}") -> None:
    import json

    plugin_loader.discover()
    data = json.loads(payload)
    result = plugin_loader.execute(name, data)
    print(result)


@app.command()
def web():
    """
    Starts the FastAPI web server for the backend API and WebSocket.
    """
    print("Starting web server...")
    uvicorn.run("axon.backend.main:app", host="0.0.0.0", port=8000, reload=True)


@app.command()
def cli():
    """
    Starts the Axon agent in an interactive command-line interface (CLI) mode.
    """
    # --- NEW: Load plugins on CLI startup ---
    print("Loading plugins...")
    plugin_loader.discover()
    print(f"Plugins loaded: {list(plugin_loader.plugins.keys())}")
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
            if user_input in plugin_loader.plugins:
                result = plugin_loader.execute(user_input, {})
                print(f"Plugin '{user_input}': {result}")
            else:
                # Placeholder for your agent's regular processing logic
                print(f"Agent: I would process '{user_input}' now.")
            # --- END NEW ---

    except KeyboardInterrupt:
        print("\nExiting CLI mode.")


@app.command()
def tui() -> None:
    """Simple text-based UI using Rich."""
    console = Console()
    console.print("[bold magenta]Axon TUI mode. Type 'quit' to exit.[/bold magenta]")
    plugin_loader.discover()
    while True:
        try:
            user_input = Prompt.ask("[cyan]You[/cyan]")
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in {"quit", "exit"}:
            break
        if user_input in plugin_loader.plugins:
            result = plugin_loader.execute(user_input, {})
            console.print(f"[green]Plugin {user_input}:[/green] {result}")
        else:
            console.print(f"[yellow]Agent[/yellow]: I would process '{user_input}' now.")


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
            await asyncio.sleep(2)  # Simulate doing work
            count += 1

    try:
        asyncio.run(background_task())
    except KeyboardInterrupt:
        print("\nStopping headless mode.")
    finally:
        print("Headless mode finished.")


@app.command()
def set_profile(
    identity: str,
    persona: str = "assistant",
    tone: str = "neutral",
    email: Optional[str] = None,
) -> None:
    """Create or update a user profile."""
    profile_manager.set_profile(identity, persona=persona, tone=tone, email=email)
    print(f"Profile saved for {identity}.")


@app.command("import-profiles")
def import_profiles(path: str = "config/user_prefs.yaml") -> None:
    """Load default profiles from a YAML file."""
    profile_manager.load_from_yaml(path)
    print(f"Profiles imported from {path}.")


@app.command()
def remind(message: str, delay: int = 60, thread_id: str = "cli_thread") -> None:
    """Schedule a reminder in seconds."""
    reminder_manager.schedule(message, delay, thread_id)
    print(f"Reminder set in {delay} seconds: {message}")


@app.command("clipboard-monitor")
def clipboard_monitor_cmd(seconds: int = 15) -> None:
    """Run the clipboard monitor plugin."""
    result = plugin_loader.execute("clipboard_monitor", {"seconds": seconds})
    print(result)


@app.command("voice-shell")
def voice_shell_cmd(timeout: float = 0.0) -> None:
    """Start the hands-free voice shell plugin."""
    t = timeout if timeout > 0 else None
    plugin_loader.discover()
    plugin_loader.execute("voice_shell", {"timeout": t})


@app.command()
def remember(
    topic: str, fact: str, thread_id: str = "cli_thread", identity: str = "cli_user"
) -> None:
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
