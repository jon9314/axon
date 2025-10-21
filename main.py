# axon/main.py
from __future__ import annotations

import asyncio
import logging
from typing import Optional  # noqa: F401

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
from axon.obs.logging_config import setup_logging
from axon.obs.tracer import run_tracer
from axon.plugins.loader import PluginLoader
from memory.user_profile import UserProfileManager

# Global managers used across commands
profile_manager = UserProfileManager()
reminder_manager = ReminderManager()
plugin_loader = PluginLoader()

logger = logging.getLogger(__name__)

app = typer.Typer(
    name="axon",
    help="The main entry point for the Axon project, supporting different operational modes.",
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    config: str = typer.Option("", "--config", help="Path to settings override YAML file"),  # noqa: B008
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),  # noqa: B008
    log_json: bool = typer.Option(False, "--log-json", help="JSON log output"),  # noqa: B008
) -> None:
    """Global CLI options."""
    if config:
        reload_settings(local_file=config)
    validate_or_die()
    setup_logging(getattr(logging, log_level.upper(), logging.INFO), log_json)
    summary = get_settings().pretty_dump().replace("\n", " ").strip()
    logger.info("config-loaded", extra={"summary": summary})
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
    logger.info("plugins-loaded", extra={"plugins": list(plugin_loader.plugins.keys())})


@plugins_app.command("list")
def list_plugins() -> None:
    plugin_loader.discover()
    for m in plugin_loader.manifests.values():
        perms = ",".join(p.value for p in m.permissions) or "-"
        logger.info("plugin", extra={"name": m.name, "version": m.version, "perms": perms})


@plugins_app.command("doctor")
def doctor_plugins() -> None:
    try:
        plugin_loader.discover()
        logger.info("plugin-doctor", extra={"count": len(plugin_loader.plugins)})
    except Exception as exc:
        logger.error("plugin-doctor-failed", extra={"error": str(exc)})


@plugins_app.command("run")
def run_plugin(name: str, payload: str = "{}") -> None:
    import json

    plugin_loader.discover()
    data = json.loads(payload)
    result = plugin_loader.execute(name, data)
    logger.info("plugin-result", extra={"plugin": name, "result": result})


@app.command()
def web():
    """
    Starts the FastAPI web server for the backend API and WebSocket.
    """
    logger.info("web-start")
    uvicorn.run("axon.backend.main:app", host="0.0.0.0", port=8000, reload=True)


@app.command()
def cli():
    """
    Starts the Axon agent in an interactive command-line interface (CLI) mode.
    """
    # --- NEW: Load plugins on CLI startup ---
    logger.info("loading-plugins")
    plugin_loader.discover()
    logger.info("plugins-loaded", extra={"plugins": list(plugin_loader.plugins.keys())})
    # --- END NEW ---

    logger.info("cli-start")
    logger.info("cli-help", extra={"msg": "Type 'exit' or 'quit' to stop."})
    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                logger.info("cli-exit")
                break

            # --- NEW: Check for and execute plugins ---
            if user_input in plugin_loader.plugins:
                result = plugin_loader.execute(user_input, {})
                logger.info("plugin-result", extra={"plugin": user_input, "result": result})
            else:
                # Placeholder for your agent's regular processing logic
                logger.info("agent", extra={"input": user_input})
            # --- END NEW ---

    except KeyboardInterrupt:
        logger.info("cli-stop")


@app.command()
def tui(
    thread_id: str = "tui_thread",
    identity: str = "tui_user",
) -> None:
    """Enhanced text-based UI with agent integration and memory display."""
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    from agent.llm_router import LLMRouter

    console = Console()
    console.print("[bold magenta]Axon TUI mode. Commands: /memory, /goals, /quit[/bold magenta]")

    plugin_loader.discover()
    cm = ContextManager(thread_id=thread_id, identity=identity)
    llm_router = LLMRouter()

    def show_memory() -> None:
        """Display current memory entries."""
        facts = cm.memory.list_facts(thread_id)
        if not facts:
            console.print("[yellow]No memory entries found.[/yellow]")
            return
        table = Table(title="Memory Entries")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Identity", style="blue")
        table.add_column("Locked", style="red")
        for key, value, ident, locked, tags in facts:
            table.add_row(
                key,
                value[:50] + ("..." if len(value) > 50 else ""),
                ident or "-",
                "🔒" if locked else "✓",
            )
        console.print(table)

    def show_goals() -> None:
        """Display current goals if available."""
        try:
            from agent.goal_tracker import GoalTracker

            gt = GoalTracker(db_uri=get_settings().database.postgres_uri)
            goals = gt.list_goals(thread_id)
            if not goals:
                console.print("[yellow]No goals found.[/yellow]")
                return
            table = Table(title="Goals")
            table.add_column("ID", style="cyan")
            table.add_column("Text", style="green")
            table.add_column("Status", style="blue")
            table.add_column("Priority", style="magenta")
            for g_id, text, done, ident, deferred, priority, deadline in goals:
                status = "✓ Done" if done else ("⏸ Deferred" if deferred else "⏳ Active")
                table.add_row(str(g_id), text[:40], status, str(priority or "-"))
            console.print(table)
        except Exception as e:
            console.print(f"[red]Could not load goals: {e}[/red]")

    while True:
        try:
            user_input = Prompt.ask("[cyan]You[/cyan]")
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in {"/quit", "/exit", "quit", "exit"}:
            break
        elif user_input.lower() == "/memory":
            show_memory()
        elif user_input.lower() == "/goals":
            show_goals()
        elif user_input in plugin_loader.plugins:
            result = plugin_loader.execute(user_input, {})
            console.print(f"[green]Plugin {user_input}:[/green] {result}")
        else:
            # Process through LLM with profile support
            profile = profile_manager.get_profile(identity)
            persona = profile.get("persona") if profile else None
            tone = profile.get("tone") if profile else None

            with console.status("[yellow]Thinking...[/yellow]"):
                response = llm_router.get_response(
                    user_input,
                    model=get_settings().llm.default_local_model,
                    persona=persona,
                    tone=tone,
                )

            console.print(f"[yellow]Axon[/yellow]: {response}")


@app.command()
def headless(
    trace_file: str = typer.Option("", "--trace-file", help="Write trace records"),  # noqa: B008
):
    """
    Runs the Axon agent in headless mode, performing a background task.
    """
    logger.info("headless-start")

    file_path = trace_file or None

    async def background_task():
        count = 0
        while count < 5:
            with run_tracer("headless", cycle=count) as rec:
                logger.info("headless-cycle", extra={"cycle": count})
                await asyncio.sleep(2)
            if file_path:
                with open(file_path, "a") as f:
                    f.write(rec.to_json() + "\n")
            count += 1

    try:
        asyncio.run(background_task())
    except KeyboardInterrupt:
        logger.info("headless-stop")
    finally:
        logger.info("headless-finished")


@app.command()
def set_profile(
    identity: str,
    persona: str = "assistant",
    tone: str = "neutral",
    email: str = "",
) -> None:
    """Create or update a user profile."""
    profile_manager.set_profile(identity, persona=persona, tone=tone, email=email or None)
    logger.info("profile-saved", extra={"identity": identity})


@app.command("import-profiles")
def import_profiles(path: str = "config/user_prefs.yaml") -> None:
    """Load default profiles from a YAML file."""
    profile_manager.load_from_yaml(path)
    logger.info("profiles-imported", extra={"path": path})


@app.command()
def remind(message: str, delay: int = 60, thread_id: str = "cli_thread") -> None:
    """Schedule a reminder in seconds."""
    reminder_manager.schedule(message, delay, thread_id)
    logger.info("reminder-set", extra={"delay": delay, "message": message})


@app.command("clipboard-monitor")
def clipboard_monitor_cmd(seconds: int = 15) -> None:
    """Run the clipboard monitor plugin."""
    result = plugin_loader.execute("clipboard_monitor", {"seconds": seconds})
    logger.info("plugin-result", extra={"plugin": "clipboard_monitor", "result": result})


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
    logger.info("fact-remembered", extra={"topic": topic})


@app.command("mcp-tools")
def list_mcp_tools(config: str = "config/mcp_servers.yaml") -> None:
    """List registered MCP tools and check connectivity."""
    router = MCPRouter(config)
    for name in router.list_tools():
        status = "ok" if router.check_tool(name) else "unreachable"
        typer.echo(f"{name}: {status}")


if __name__ == "__main__":
    app()
