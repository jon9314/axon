# Writing Plugins

Axon supports simple Python plugins that can add new commands or actions. Plugins live in the `plugins/` folder and are discovered at startup.

Plugins are implemented as [Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) tools by subclassing `BaseTool` and registering with `register_tool`.

```python
from qwen_agent.tools.base import BaseTool, register_tool

@register_tool("echo")
class EchoTool(BaseTool):
    description = "Echo back the provided text"
    parameters = [
        {"name": "text", "type": "string", "description": "Text to echo", "required": True}
    ]

    def call(self, params, **kwargs):
        args = self._verify_json_format_args(params)
        return args["text"]
```

For backwards compatibility, plugins may still expose a simple function decorated with `@plugin` that calls the tool's `call()` method.

Restart the CLI (`python main.py cli`) or the web backend to load new or changed plugins. During development the loader hot‑reloads modules so edits take effect immediately.

