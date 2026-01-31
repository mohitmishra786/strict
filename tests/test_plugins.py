"""Tests for plugin system."""

from typing import Any

import pytest

from strict.plugins import (
    FilterPlugin,
    Plugin,
    PluginManager,
    ProcessorPlugin,
    ValidatorPlugin,
    plugin_manager,
)


class MockPlugin(Plugin):
    """Mock plugin for testing."""

    def __init__(self) -> None:
        super().__init__()
        self.setup_called = False
        self.teardown_called = False

    async def setup(self) -> None:
        """Setup plugin."""
        self.setup_called = True

    async def teardown(self) -> None:
        """Teardown plugin."""
        self.teardown_called = True


class MockProcessorPlugin(ProcessorPlugin):
    """Mock processor plugin."""

    async def setup(self) -> None:
        """Setup plugin."""
        pass

    async def teardown(self) -> None:
        """Teardown plugin."""
        pass

    async def process(self, input_data: str, **kwargs: Any) -> str:
        """Process input."""
        return f"processed: {input_data}"


class MockValidatorPlugin(ValidatorPlugin):
    """Mock validator plugin."""

    async def setup(self) -> None:
        """Setup plugin."""
        pass

    async def teardown(self) -> None:
        """Teardown plugin."""
        pass

    def validate(self, data: Any) -> bool:
        """Validate data."""
        return isinstance(data, str)


class MockFilterPlugin(FilterPlugin):
    """Mock filter plugin."""

    async def setup(self) -> None:
        """Setup plugin."""
        pass

    async def teardown(self) -> None:
        """Teardown plugin."""
        pass

    def apply_filter(self, signal_data: list[float], sample_rate: float) -> list[float]:
        """Apply filter."""
        return [x * 2 for x in signal_data]


class TestPlugin:
    """Test base Plugin class."""

    @pytest.mark.asyncio
    async def test_plugin_setup(self) -> None:
        """Test plugin setup."""
        plugin = MockPlugin()
        await plugin.setup()

        assert plugin.setup_called is True

    @pytest.mark.asyncio
    async def test_plugin_teardown(self) -> None:
        """Test plugin teardown."""
        plugin = MockPlugin()
        await plugin.teardown()

        assert plugin.teardown_called is True

    def test_plugin_info(self) -> None:
        """Test getting plugin information."""
        plugin = MockPlugin()
        info = plugin.get_info()

        assert "name" in info
        assert "version" in info
        assert "description" in info
        assert "enabled" in info


class TestProcessorPlugin:
    """Test ProcessorPlugin class."""

    @pytest.mark.asyncio
    async def test_processor_plugin(self) -> None:
        """Test processor plugin process method."""
        plugin = MockProcessorPlugin()
        result = await plugin.process("test input")

        assert result == "processed: test input"


class TestValidatorPlugin:
    """Test ValidatorPlugin class."""

    def test_validator_plugin_valid(self) -> None:
        """Test validator with valid data."""
        plugin = MockValidatorPlugin()
        assert plugin.validate("string data") is True

    def test_validator_plugin_invalid(self) -> None:
        """Test validator with invalid data."""
        plugin = MockValidatorPlugin()
        assert plugin.validate(123) is False


class TestFilterPlugin:
    """Test FilterPlugin class."""

    def test_filter_plugin(self) -> None:
        """Test filter plugin."""
        plugin = MockFilterPlugin()
        result = plugin.apply_filter([1.0, 2.0, 3.0], 1000.0)

        assert result == [2.0, 4.0, 6.0]


class TestPluginManager:
    """Test PluginManager class."""

    def test_register_plugin(self) -> None:
        """Test registering a plugin."""
        manager = PluginManager()
        plugin = MockPlugin()

        manager.register_plugin(plugin)

        assert "MockPlugin" in manager.plugins
        assert manager.get_plugin("MockPlugin") is plugin

    def test_register_duplicate_plugin(self) -> None:
        """Test that duplicate plugins are not registered."""
        manager = PluginManager()
        plugin1 = MockPlugin()
        plugin2 = MockPlugin()

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)

        # Should still have only one plugin
        assert len(manager.plugins) == 1

    def test_unregister_plugin(self) -> None:
        """Test unregistering a plugin."""
        manager = PluginManager()
        plugin = MockPlugin()

        manager.register_plugin(plugin)
        manager.unregister_plugin("MockPlugin")

        assert "MockPlugin" not in manager.plugins

    def test_list_plugins(self) -> None:
        """Test listing plugins."""
        manager = PluginManager()
        plugin1 = MockPlugin()
        plugin2 = MockValidatorPlugin()  # Use ValidatorPlugin instead

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)

        plugins = manager.list_plugins()

        assert len(plugins) == 2

    @pytest.mark.asyncio
    async def test_setup_all(self) -> None:
        """Test setting up all plugins."""
        manager = PluginManager()
        plugin1 = MockPlugin()
        plugin2 = MockProcessorPlugin()  # Use a different plugin type

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)

        await manager.setup_all()

        assert plugin1.setup_called is True

    @pytest.mark.asyncio
    async def test_teardown_all(self) -> None:
        """Test tearing down all plugins."""
        manager = PluginManager()
        plugin1 = MockPlugin()
        plugin2 = MockProcessorPlugin()  # Use a different plugin type

        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)

        await manager.teardown_all()

        assert plugin1.teardown_called is True

    def test_register_hook(self) -> None:
        """Test registering a hook."""
        manager = PluginManager()
        callback_called = False

        def callback() -> None:
            nonlocal callback_called
            callback_called = True

        manager.register_hook("test_hook", callback)
        assert "test_hook" in manager.hooks

    @pytest.mark.asyncio
    async def test_execute_hook(self) -> None:
        """Test executing a hook."""
        manager = PluginManager()
        callback_called = False

        def callback() -> None:
            nonlocal callback_called
            callback_called = True

        manager.register_hook("test_hook", callback)
        await manager.execute_hook("test_hook")

        assert callback_called is True

    @pytest.mark.asyncio
    async def test_execute_hook_with_args(self) -> None:
        """Test executing hook with arguments."""
        manager = PluginManager()
        result = []

        def callback(value: int) -> None:
            result.append(value * 2)

        manager.register_hook("test_hook", callback)
        await manager.execute_hook("test_hook", 5)

        assert result == [10]

    @pytest.mark.asyncio
    async def test_execute_async_hook(self) -> None:
        """Test executing async hook callback."""
        manager = PluginManager()
        result = []

        async def async_callback(value: int) -> None:
            result.append(value * 3)

        manager.register_hook("test_hook", async_callback)
        await manager.execute_hook("test_hook", 5)

        assert result == [15]
