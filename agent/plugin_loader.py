# axon/agent/plugin_loader.py

import os
import importlib.util
from typing import Dict, Callable

# This dictionary will hold our loaded plugin functions
AVAILABLE_PLUGINS: Dict[str, Callable] = {}

def load_plugins():
    """
    Scans the 'plugins' directory, imports Python files as modules,
    and registers any functions decorated with @plugin.
    """
    plugin_dir = os.path.join(os.path.dirname(__file__), '..', 'plugins')
    if not os.path.exists(plugin_dir):
        print(f"Plugins directory not found at {plugin_dir}. Creating it.")
        os.makedirs(plugin_dir)
        return

    for filename in os.listdir(plugin_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            plugin_path = os.path.join(plugin_dir, filename)
            module_name = f"plugins.{filename[:-3]}"

            try:
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                if spec and spec.loader:
                    plugin_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(plugin_module)
                    print(f"Successfully loaded plugin: {filename}")
                else:
                    print(f"Could not create spec for plugin: {filename}")
            except Exception as e:
                print(f"Failed to load plugin {filename}: {e}")

def plugin(name: str):
    """
    A decorator to register a function as a plugin.
    """
    def decorator(func: Callable):
        global AVAILABLE_PLUGINS
        print(f"Registering plugin: '{name}'")
        AVAILABLE_PLUGINS[name] = func
        return func
    return decorator