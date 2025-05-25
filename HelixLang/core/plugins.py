# plugins.py

"""
HelixLang Plugin System

Manages external modules/plugins that extend HelixLang.
Supports:
- Plugin interface definition with lifecycle hooks.
- Dynamic plugin registration, discovery, loading, and unloading.
- Hooking into compilation, execution, or analysis phases.
- Isolation and metadata management for plugins.
- Safe execution and error reporting for plugins.

Plugins enable domain-specific extensions, integration with bioinformatics tools,
custom syntax, or runtime features.
"""

import importlib
import os
import sys
import traceback
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Protocol, Union

# ------------------------------
# Plugin Interface Definition
# ------------------------------

class HelixPlugin(Protocol):
    """
    Interface all HelixLang plugins must implement.
    """
    name: str
    version: str
    description: str

    def on_load(self, plugin_manager: "PluginManager") -> None:
        """
        Called when plugin is loaded.
        Can be used to register hooks or initialize state.
        """
        ...

    def on_unload(self) -> None:
        """
        Called when plugin is unloaded.
        Cleanup any resources here.
        """
        ...

    def register_hooks(self, plugin_manager: "PluginManager") -> None:
        """
        Register hooks into compilation/execution phases.
        """
        ...

# ------------------------------
# Plugin Metadata
# ------------------------------

class PluginMetadata:
    """
    Metadata container for a loaded plugin.
    """
    def __init__(self, module: ModuleType, plugin_instance: HelixPlugin):
        self.module = module
        self.instance = plugin_instance
        self.name = plugin_instance.name
        self.version = plugin_instance.version
        self.description = plugin_instance.description
        self.loaded = False


# ------------------------------
# Plugin Manager
# ------------------------------

class PluginManager:
    """
    Central manager for loading, registering, and managing plugins.
    """

    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        # List of directories to scan for plugins
        self.plugin_dirs = plugin_dirs or ["./plugins"]
        # Loaded plugins: name -> PluginMetadata
        self.plugins: Dict[str, PluginMetadata] = {}
        # Hooks registry: event_name -> list of callables
        self.hooks: Dict[str, List[Callable[..., Any]]] = {}

    def discover_plugins(self) -> List[str]:
        """
        Discover plugin modules in plugin_dirs.
        Returns a list of plugin module names (dot notation).
        Assumes plugins are Python packages or modules.
        """
        plugin_modules = []
        for directory in self.plugin_dirs:
            if not os.path.isdir(directory):
                continue
            for filename in os.listdir(directory):
                if filename.endswith(".py") and not filename.startswith("_"):
                    mod_name = filename[:-3]
                    # Compose full module path relative to plugin directory
                    full_module_name = f"plugins.{mod_name}"
                    plugin_modules.append(full_module_name)
                elif os.path.isdir(os.path.join(directory, filename)):
                    # Package plugin assumed
                    full_module_name = f"plugins.{filename}"
                    plugin_modules.append(full_module_name)
        return plugin_modules

    def load_plugin(self, module_name: str) -> bool:
        """
        Load a plugin module by name and instantiate plugin class.
        Returns True if successfully loaded, False otherwise.
        """
        if module_name in self.plugins:
            print(f"Plugin '{module_name}' already loaded.")
            return False
        try:
            module = importlib.import_module(module_name)
            # Plugin module must expose `plugin` variable or factory function
            plugin_obj = getattr(module, "plugin", None)
            if plugin_obj is None:
                raise ImportError(f"Module '{module_name}' missing required 'plugin' attribute.")

            # If plugin is a class, instantiate it
            if callable(plugin_obj):
                plugin_instance = plugin_obj()
            else:
                plugin_instance = plugin_obj

            # Check interface compliance
            if not all(hasattr(plugin_instance, attr) for attr in ("name", "version", "on_load", "on_unload", "register_hooks")):
                raise TypeError(f"Plugin '{module_name}' does not implement the required HelixPlugin interface.")

            metadata = PluginMetadata(module, plugin_instance)
            self.plugins[plugin_instance.name] = metadata

            # Call on_load lifecycle method
            plugin_instance.on_load(self)
            metadata.loaded = True

            # Register hooks
            plugin_instance.register_hooks(self)

            print(f"Loaded plugin '{plugin_instance.name}' version {plugin_instance.version}.")
            return True

        except Exception as e:
            print(f"Failed to load plugin '{module_name}': {e}")
            traceback.print_exc()
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a plugin by name.
        Calls plugin's on_unload method and removes from registry.
        """
        metadata = self.plugins.get(plugin_name)
        if metadata is None:
            print(f"Plugin '{plugin_name}' is not loaded.")
            return False
        try:
            metadata.instance.on_unload()
            del self.plugins[plugin_name]

            # Remove hooks registered by this plugin
            for event, handlers in self.hooks.items():
                self.hooks[event] = [h for h in handlers if getattr(h, "__plugin_name__", None) != plugin_name]

            print(f"Unloaded plugin '{plugin_name}'.")
            return True
        except Exception as e:
            print(f"Failed to unload plugin '{plugin_name}': {e}")
            traceback.print_exc()
            return False

    def register_hook(self, event_name: str, handler: Callable[..., Any], plugin_name: Optional[str] = None) -> None:
        """
        Register a hook (callback) for a given event.
        Hooks receive event-specific arguments.
        """
        if event_name not in self.hooks:
            self.hooks[event_name] = []

        # Tag handler with plugin_name for easy removal later
        if plugin_name:
            setattr(handler, "__plugin_name__", plugin_name)

        self.hooks[event_name].append(handler)

    def trigger_hook(self, event_name: str, *args, **kwargs) -> List[Any]:
        """
        Trigger all hooks registered to an event.
        Returns list of results from all handlers.
        """
        results = []
        for handler in self.hooks.get(event_name, []):
            try:
                result = handler(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Error in plugin hook for event '{event_name}': {e}")
                traceback.print_exc()
        return results

    def list_plugins(self) -> List[str]:
        """
        Return list of currently loaded plugin names.
        """
        return list(self.plugins.keys())

    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a plugin module by unloading and loading again.
        """
        metadata = self.plugins.get(plugin_name)
        if not metadata:
            print(f"Plugin '{plugin_name}' not loaded, cannot reload.")
            return False
        module_name = metadata.module.__name__
        self.unload_plugin(plugin_name)
        try:
            importlib.reload(metadata.module)
            return self.load_plugin(module_name)
        except Exception as e:
            print(f"Failed to reload plugin '{plugin_name}': {e}")
            traceback.print_exc()
            return False


# ------------------------------
# Example Hook Events
# ------------------------------
# Common event names to register hooks for:
#
# "before_parse" - before source code parsing
# "after_parse"  - after AST is produced
# "before_compile" - before IR generation
# "after_compile" - after IR generation
# "before_execute" - before runtime execution
# "after_execute" - after runtime execution
# "on_error" - runtime or compile error event
#
# Plugins register handlers to these events via PluginManager.register_hook
#

# ------------------------------
# Usage Example (For Reference)
# ------------------------------

if __name__ == "__main__":
    pm = PluginManager()
    print("Discovered plugins:", pm.discover_plugins())
    # Example: load all discovered plugins
    for mod in pm.discover_plugins():
        pm.load_plugin(mod)
    print("Loaded plugins:", pm.list_plugins())

