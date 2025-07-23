# Axon

Axon is a local-first AI agent with simple memory capabilities.

## Quick start

```bash
# start backend API from the repository root
python main.py web

# start frontend dev server
cd frontend
npm install
npm run dev
```

The backend listens on `localhost:8000` and the frontend (Vite) runs on `localhost:5173` by default. Edit memory via the sidebar in the UI.

Plugins can be added by dropping Python files into the `plugins/` directory.
Run `python main.py cli` to load plugins (hot reloaded each launch). Each
plugin provides metadata such as name, description, and usage via the
`@plugin` decorator.

To store a fact without using the UI, you can run:

```bash
python main.py remember "topic" "fact"
```
This writes the key/value pair directly to Axon's memory.

Goals can be stored via the `/goals/{thread_id}` API for simple task tracking.
Ideas that sound vague ("someday I might...") are marked as **deferred** and
can be listed via `/goals/{thread_id}/deferred`.

## Docker Compose

The repository includes a `docker-compose.yml` for running Axon and its
dependencies in containers. This setup also launches the MCP helper servers so
they are available automatically.

```bash
# build and start all services
cp .env.example .env  # configure environment variables if needed
docker compose up --build
```

The frontend will be available on `http://localhost:3000` and the backend on
`http://localhost:8000`.

## Remote model fallback

Axon can suggest prompts for hosted models like GPT-4o or Claude when the local
LLM appears inadequate. The UI displays the suggested model and a short reason
explaining why the remote model fits the request. Copy the prompt shown in the
UI, run it in your browser, then paste the response back and press **Submit** to
store the result in memory. For quick manual pasting you can run
`python scripts/clipboard_watch.py` to monitor your clipboard or invoke
`python main.py clipboard-monitor`.

The clipboard monitor relies on optional packages `pyperclip` and `keyboard`.
Install them via `pip install pyperclip keyboard` if missing.


## Documentation

- [docs/plugins.md](docs/plugins.md) explains how to create new plugins.
- [docs/mcp_setup.md](docs/mcp_setup.md) covers running the MCP helper services.
- [docs/models.md](docs/models.md) shows how to change the default model.

Example local configuration files are available in `.env.example` and `config/settings.example.yaml`.

## Qwen-Agent

Axon depends on [Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) to provide
tool-calling capabilities. The Qwen-Agent repository includes several usage
examples such as the **Qwen3 Tool-call Demo** found in
`examples/assistant_qwen3.py`.

See [docs/models.md](docs/models.md) for instructions on running Qwen3 with
reasoning enabled and how to pass the recommended `generate_cfg` settings.

## Roadmap progress

Phases 0 through 3.9 have been completed. Core MCP servers are stable and the GitHub service is partially implemented. See [phases/roadmap.md](phases/roadmap.md) for progress on additional secondary servers.

