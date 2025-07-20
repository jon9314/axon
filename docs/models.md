# Customising Models

LLM calls are routed through `agent.llm_router.LLMRouter`. By default the router targets a local Ollama server and falls back to prompting for a cloud model when the input is very long.

The default model used by the backend is configured in `config/settings.yaml` under `llm.default_local_model`. Update this value to switch models globally.

To point the router at a different server you can pass the `server_url` when creating `LLMRouter` in `backend/main.py` or set the environment variable `OLLAMA_URL` and modify the code accordingly.

Example `settings.yaml` snippet:

```yaml
llm:
  default_local_model: "mistral:7b"
```

Restart the backend after changing settings so the new model is loaded.

