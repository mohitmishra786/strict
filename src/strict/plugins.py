"""Plugin System for Strict.

Allows dynamic loading and management of plugins to extend functionality.
"""

from __future__ import annotations

import importlib
import inspect
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Base class for all plugins.

    Plugins must implement the setup and teardown methods.
    """

    def __init__(self) -> None:
        """Initialize plugin."""
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.description = "Base plugin"
        self.enabled: bool = True

    @abstractmethod
    async def setup(self) -> None:
        """Initialize the plugin.

        Called when the plugin is loaded.
        """
        pass

    @abstractmethod
    async def teardown(self) -> None:
        """Clean up the plugin.

        Called when the plugin is unloaded.
        """
        pass

    def get_info(self) -> dict[str, Any]:
        """Get plugin information.

        Returns:
            Dictionary with plugin metadata.
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "enabled": self.enabled,
        }


class ProcessorPlugin(Plugin):
    """Base class for processor plugins.

    Processor plugins add new LLM or computation processors.
    """

    @abstractmethod
    async def process(self, input_data: str, **kwargs: Any) -> str:
        """Process input data.

        Args:
            input_data: Input to process.
            **kwargs: Additional processing parameters.

        Returns:
            Processed output.
        """
        pass


class ValidatorPlugin(Plugin):
    """Base class for validator plugins.

    Validator plugins add new validation capabilities.
    """

    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate data.

        Args:
            data: Data to validate.

        Returns:
            True if valid, False otherwise.
        """
        pass


class FilterPlugin(Plugin):
    """Base class for signal filter plugins.

    Filter plugins add new signal processing filters.
    """

    @abstractmethod
    def apply_filter(self, signal_data: list[float], sample_rate: float) -> list[float]:
        """Apply filter to signal data.

        Args:
            signal_data: Signal samples.
            sample_rate: Sample rate in Hz.

        Returns:
            Filtered signal data.
        """
        pass


class PluginManager:
    """Manages plugin lifecycle and registration.

    Plugins can be loaded from modules or instantiated directly.
    """

    def __init__(self) -> None:
        """Initialize plugin manager."""
        self.plugins: dict[str, Plugin] = {}
        self.hooks: dict[str, list[Callable]] = {}

    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin instance.

        Args:
            plugin: Plugin instance to register.
        """
        if plugin.name in self.plugins:
            logger.warning(f"Plugin {plugin.name} already registered, skipping")
            return

        self.plugins[plugin.name] = plugin
        logger.info(f"Registered plugin: {plugin.name}")

    def unregister_plugin(self, name: str) -> None:
        """Unregister a plugin by name.

        Args:
            name: Plugin name to unregister.
        """
        if name in self.plugins:
            del self.plugins[name]
            logger.info(f"Unregistered plugin: {name}")

    def get_plugin(self, name: str) -> Plugin | None:
        """Get a plugin by name.

        Args:
            name: Plugin name.

        Returns:
            Plugin instance or None if not found.
        """
        return self.plugins.get(name)

    def list_plugins(self) -> list[dict[str, Any]]:
        """List all registered plugins.

        Returns:
            List of plugin information dictionaries.
        """
        return [plugin.get_info() for plugin in self.plugins.values()]

    async def load_plugin_from_module(
        self, module_path: str, class_name: str
    ) -> Plugin | None:
        """Load a plugin from a Python module.

        Args:
            module_path: Python module path (e.g., 'myapp.plugins.custom').
            class_name: Name of the plugin class in the module.

        Returns:
            Loaded plugin instance or None if loading failed.
        """
        try:
            module = importlib.import_module(module_path)
            plugin_class = getattr(module, class_name)

            if not inspect.issubclass(plugin_class, Plugin):
                logger.error(f"{class_name} is not a subclass of Plugin")
                return None

            plugin = plugin_class()
            await plugin.setup()
            self.register_plugin(plugin)

            return plugin

        except Exception as e:
            logger.error(f"Failed to load plugin {module_path}.{class_name}: {e}")
            return None

    async def load_plugins_from_directory(self, directory: Path) -> list[Plugin]:
        """Load all plugins from a directory.

        Args:
            directory: Directory containing plugin modules.

        Returns:
            List of loaded plugins.
        """
        loaded = []

        for plugin_file in directory.glob("*_plugin.py"):
            module_name = plugin_file.stem

            try:
                module = importlib.import_module(f"{directory.stem}.{module_name}")

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, Plugin) and obj is not Plugin:
                        plugin = obj()
                        await plugin.setup()
                        self.register_plugin(plugin)
                        loaded.append(plugin)

            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {e}")

        return loaded

    async def setup_all(self) -> None:
        """Setup all registered plugins."""
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    await plugin.setup()
                except Exception as e:
                    logger.error(f"Failed to setup plugin {plugin.name}: {e}")

    async def teardown_all(self) -> None:
        """Teardown all registered plugins."""
        for plugin in self.plugins.values():
            try:
                await plugin.teardown()
            except Exception as e:
                logger.error(f"Failed to teardown plugin {plugin.name}: {e}")

    def register_hook(self, hook_name: str, callback: Callable) -> None:
        """Register a callback for a specific hook.

        Args:
            hook_name: Name of the hook.
            callback: Callback function.
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []

        self.hooks[hook_name].append(callback)
        logger.debug(f"Registered callback for hook: {hook_name}")

    async def execute_hook(self, hook_name: str, *args: Any, **kwargs: Any) -> None:
        """Execute all callbacks registered for a hook.

        Args:
            hook_name: Name of the hook.
            *args: Positional arguments to pass to callbacks.
            **kwargs: Keyword arguments to pass to callbacks.
        """
        if hook_name not in self.hooks:
            return

        for callback in self.hooks[hook_name]:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Hook callback failed for {hook_name}: {e}")


# Global plugin manager instance
plugin_manager = PluginManager()
