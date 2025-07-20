# Customising Models

LLM calls are routed through `agent.llm_router.LLMRouter`. The router builds a
`qwen_agent.agents.Assistant` using the open‑source **Qwen3** model and all
registered tools. When the input is very long or the local call fails the router
returns a JSON payload suggesting a cloud model instead.

The default model used by the backend is configured in `config/settings.yaml` under `llm.default_local_model`. Update this value to switch models globally.

To change the model you can pass a different model name when creating
`LLMRouter` in `backend/main.py` or update `settings.llm.default_local_model`.

Example `settings.yaml` snippet:

```yaml
llm:
  default_local_model: "mistral:7b"
```

Restart the backend after changing settings so the new model is loaded.

