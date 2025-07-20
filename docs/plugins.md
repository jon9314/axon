# Writing Plugins

Axon supports simple Python plugins that can add new commands or actions. Plugins live in the `plugins/` folder and are discovered at startup.

Each plugin defines a function decorated with `@plugin` from `agent.plugin_loader`. Metadata such as name, description and usage are provided to help the agent advertise available skills.

```python
# plugins/echo.py
from agent.plugin_loader import plugin

@plugin(
    name="echo",
    description="Echo back the provided text",
    usage="echo('hello')"
)
def echo(text: str) -> str:
    return text
```

Restart the CLI (`python main.py cli`) or the web backend to load new or changed plugins. During development the loader hot‑reloads modules so edits take effect immediately.

