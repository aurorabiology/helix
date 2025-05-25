# helixlang/plugins/__init__.py

import importlib
import os
import pkgutil
from typing import Dict, Type, Optional, List
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

# Global registry to hold all loaded plugins
_plugin_registry: Dict[str, "BasePlugin"] = {}

# Base class / interface all plugins should implement
class BasePlugin(ABC):
    name: str
    version: str

    def __init__(self):
        self.initialized = False

    @abstractmethod
    def initialize(self):
        """Initialize the plugin, prepare resources."""
        pass

    @abstractmethod
    def shutdown(self):
        """Clean up resources before unloading."""
        pass

    def on_event(self, event: str, data: dict):
        """Optional: handle runtime events."""
        pass

def register_plugin(plugin: BasePlugin):
    if plugin.name in _plugin_registry:
        logger.warning(f"Plugin '{plugin.name}' is already registered. Overwriting.")
    _plugin_registry[plugin.name] = plugin
    logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")

def get_plugin(name: str) -> Optional[BasePlugin]:
    return _plugin_registry.get(name)

def list_plugins() -> List[str]:
    return list(_plugin_registry.keys())

def discover_plugins():
    """Automatically discover and import all plugins in this package."""
    package_dir = os.path.dirname(__file__)
    for _, module_name, _ in pkgutil.iter_modules([package_dir]):
        try:
            importlib.import_module(f".{module_name}", __package__)
            logger.info(f"Discovered plugin module: {module_name}")
        except Exception as e:
            logger.error(f"Failed to import plugin '{module_name}': {e}")

# Call discovery on import to auto-register plugins
discover_plugins()
