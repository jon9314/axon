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

