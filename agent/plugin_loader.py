# axon/agent/plugin_loader.py

import logging
import os
import importlib.util
import importlib
import sys
from dataclasses import dataclass
from typing import Dict, Callable


@dataclass
class PluginInfo:
    func: Callable
    name: str
    description: str
    usage: str


# This dictionary will hold our loaded plugin metadata
AVAILABLE_PLUGINS: Dict[str, PluginInfo] = {}


def load_plugins(hot_reload: bool = False):
    """
    Scans the 'plugins' directory, imports Python files as modules,
    and registers any functions decorated with @plugin.
    """
    plugin_dirs = [
        os.path.join(os.path.dirname(__file__), "..", "plugins"),
        os.path.join(os.path.dirname(__file__), "tools"),
    ]

    for plugin_dir in plugin_dirs:
        if not os.path.exists(plugin_dir):
            continue

        for filename in os.listdir(plugin_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                plugin_path = os.path.join(plugin_dir, filename)
                if plugin_dir.endswith("plugins"):
                    module_name = f"plugins.{filename[:-3]}"
                else:
                    module_name = f"agent.tools.{filename[:-3]}"

                try:
                    if module_name in sys.modules and hot_reload:
                        importlib.reload(sys.modules[module_name])
                    else:
                        spec = importlib.util.spec_from_file_location(
                            module_name, plugin_path
                        )
                        if spec and spec.loader:
                            plugin_module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(plugin_module)
                            sys.modules[module_name] = plugin_module
                        else:
                            logging.error(
                                "Could not create spec for plugin: %s", filename
                            )
                            continue
                    logging.info("Loaded plugin module: %s", filename)
                except (ImportError, OSError, SyntaxError, ValueError):
                    logging.exception("Failed to load plugin %s", filename)


def plugin(name: str, description: str = "", usage: str = ""):
    """A decorator to register a function as a plugin."""

    def decorator(func: Callable):
        logging.info("Registering plugin: '%s'", name)
        AVAILABLE_PLUGINS[name] = PluginInfo(
            func=func,
            name=name,
            description=description,
            usage=usage,
        )
        return func

    return decorator
