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

First launch automatically copies `config/settings.example.yaml` to `config/settings.yaml` if missing. Install optional features with `poetry install --with calendar,postgres,vector,notify`.

Plugins can be added by dropping Python files into the `plugins/` directory.
Run `python main.py cli` to load plugins (hot reloaded each launch). Each
plugin provides metadata such as name, description, and usage via the
`@plugin` decorator.

## Pre-commit hooks

To run linting and tests automatically before every commit, install the
[pre-commit](https://pre-commit.com) hooks after setting up the development
environment:

```bash
poetry install --with dev
pre-commit install
```

The configured hooks execute `ruff`, `black`, `mypy`, `pytest`, `eslint` and
`tsc` so issues are caught early.

### Commit message contract

Commit messages must end with an `AI-Change-Summary` block listing the files
touched, tests run, and rationale. Install the provided `git-hooks/commit-msg`
script so Git enforces this:

```bash
git config core.hooksPath git-hooks
```

## CLI commands

Axon exposes several helper commands via `python main.py`:

```bash
# list available plugins
python main.py plugins reload

# start a simple text UI
python main.py tui

# schedule a reminder in 30 seconds
python main.py remind "take a break" --delay 30

# import profile defaults from a YAML file
python main.py import-profiles config/user_prefs.yaml

# set or update an individual profile
python main.py set-profile jon --persona partner --tone informal

# hands‑free voice shell (if optional deps are installed)
python main.py voice-shell
```

To store a fact without using the UI, you can run:

```bash
python main.py remember "topic" "fact"
```
This writes the key/value pair directly to Axon's memory.

Goals can be stored via the `/goals/{thread_id}` API for simple task tracking.
Each goal accepts optional `priority` and `deadline` fields.
Ideas that sound vague ("someday I might...") are marked as **deferred** and
trigger periodic reminder prompts. They can be listed via
`/goals/{thread_id}/deferred`.

<!-- NOTE: document optional Postgres and health endpoint -->
Axon gracefully disables goal-tracking if Postgres isn’t available. Start
Postgres to re-enable the feature. Use `GET /health` to inspect service status.

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
- [docs/api.md](docs/api.md) lists the REST endpoints.

Example configuration files are available in `.env.example`,
`config/settings.example.yaml`, and the default profiles in
`config/user_prefs.yaml`.
Axon creates `config/settings.yaml` from the example on first run if it doesn't exist.

## Qwen-Agent

Axon depends on [Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) to provide
tool-calling capabilities. The Qwen-Agent repository includes several usage
examples such as the **Qwen3 Tool-call Demo** found in
`examples/assistant_qwen3.py`.

See [docs/models.md](docs/models.md) for instructions on running Qwen3 with
reasoning enabled and how to pass the recommended `generate_cfg` settings.

## Roadmap progress

Phases 0 through 4 are complete, including manual cloud prompting and calendar export features. See [phases/roadmap.md](phases/roadmap.md) for the latest status of each phase.


## License

This project is licensed under the [MIT License](LICENSE).
Third-party package licenses are summarized in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
Run `make licenses` to regenerate this list using **pip-licenses**.
