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

## Launching Qwen3 with reasoning

When running Qwen3 locally (via Ollama or any OpenAI‑compatible API) the
Qwen-Agent README recommends enabling reasoning mode and selecting the "nous"
tool-call prompt template. Start the model with `--enable-reasoning` and choose
the DeepSeek parser:

```bash
ollama serve
ollama run qwen3:8b --enable-reasoning --reasoning-parser deepseek_r1
```

Pass the prompt template through `generate_cfg` when creating the assistant.
`config/settings.yaml` includes an example:

```yaml
llm:
  default_local_model: "qwen3:8b"
  qwen_agent_generate_cfg:
    fncall_prompt_type: "nous"
```

`LLMRouter` automatically forwards this dictionary to `qwen_agent.agents.Assistant`.

