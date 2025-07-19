# axon/main.py

import typer
import uvicorn
import asyncio
from agent.plugin_loader import load_plugins, AVAILABLE_PLUGINS

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


if __name__ == "__main__":
    app()

