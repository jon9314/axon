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

Goals can be stored via the `/goals/{thread_id}` API for simple task tracking.

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
LLM appears inadequate. The UI will display the generated prompt and provide a
text area for pasting back the remote response. Press **Submit** after pasting
to store the result in memory. For quick manual pasting you can run
`python scripts/clipboard_watch.py` to monitor your clipboard.

