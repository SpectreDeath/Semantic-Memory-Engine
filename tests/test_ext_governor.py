"""Tests for ext_governor (Governor) extension resource monitor."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from extensions.ext_governor.plugin import (
    Governor,
    IngestionTask,
    ResourceMonitor,
    create_plugin,
    register_extension,
)
from extensions.ext_governor.resource_monitor import (
    EnhancedResourceMonitor,
    ResourceStatus,
    VRAMState,
    VSCodeStatusBarManager,
    create_enhanced_monitor,
    get_status_bar_manager,
)


class TestVRAMState:
    """Tests for VRAMState enum."""

    def test_vram_state_values(self):
        assert VRAMState.NORMAL.value == "normal"
        assert VRAMState.HIGH.value == "high"
        assert VRAMState.CRITICAL.value == "critical"


class TestResourceStatus:
    """Tests for ResourceStatus dataclass."""

    def test_resource_status_creation(self):
        status = ResourceStatus(
            vram_usage_gb=5.0,
            vram_threshold_gb=5.8,
            vram_state=VRAMState.NORMAL,
            should_delay=False,
            timestamp=datetime.now(),
        )
        assert status.vram_usage_gb == 5.0
        assert status.vram_state == VRAMState.NORMAL
        assert status.cpu_usage_percent == 0.0  # default

    def test_resource_status_full(self):
        status = ResourceStatus(
            vram_usage_gb=6.0,
            vram_threshold_gb=5.8,
            vram_state=VRAMState.CRITICAL,
            should_delay=True,
            timestamp=datetime.now(),
            cpu_usage_percent=75.5,
            memory_usage_gb=12.3,
        )
        assert status.should_delay is True


class TestVSCodeStatusBarManager:
    """Tests for VSCodeStatusBarManager class."""

    def test_status_bar_manager_init(self):
        manager = VSCodeStatusBarManager()
        assert manager.status_bar_items == {}
        assert manager.update_callbacks == []

    def test_register_callback(self):
        manager = VSCodeStatusBarManager()
        callback = MagicMock()
        manager.register_status_bar_update(callback)
        assert callback in manager.update_callbacks

    def test_unregister_callback(self):
        manager = VSCodeStatusBarManager()
        callback = MagicMock()
        manager.register_status_bar_update(callback)
        manager.unregister_status_bar_update(callback)
        assert callback not in manager.update_callbacks

    def test_update_status_bar(self):
        manager = VSCodeStatusBarManager()
        callback = MagicMock()
        manager.register_status_bar_update(callback)
        status = ResourceStatus(
            vram_usage_gb=3.0,
            vram_threshold_gb=5.8,
            vram_state=VRAMState.NORMAL,
            should_delay=False,
            timestamp=datetime.now(),
        )
        manager.update_status_bar(status)
        callback.assert_called_once()

    def test_format_status_text_normal(self):
        manager = VSCodeStatusBarManager()
        status = ResourceStatus(
            vram_usage_gb=3.0,
            vram_threshold_gb=5.8,
            vram_state=VRAMState.NORMAL,
            should_delay=False,
            timestamp=datetime.now(),
        )
        text = manager._format_status_text(status)
        assert "🟢" in text
        assert "NORMAL" in text

    def test_format_status_text_high(self):
        manager = VSCodeStatusBarManager()
        status = ResourceStatus(
            vram_usage_gb=5.0,
            vram_threshold_gb=5.8,
            vram_state=VRAMState.HIGH,
            should_delay=True,
            timestamp=datetime.now(),
        )
        text = manager._format_status_text(status)
        assert "🟡" in text
        assert "HIGH" in text

    def test_format_status_text_critical(self):
        manager = VSCodeStatusBarManager()
        status = ResourceStatus(
            vram_usage_gb=6.0,
            vram_threshold_gb=5.8,
            vram_state=VRAMState.CRITICAL,
            should_delay=True,
            timestamp=datetime.now(),
        )
        text = manager._format_status_text(status)
        assert "🔴" in text
        assert "CRITICAL" in text


class TestEnhancedResourceMonitor:
    """Tests for EnhancedResourceMonitor class."""

    @pytest.fixture
    def monitor(self):
        with patch("extensions.ext_governor.resource_monitor.psutil") as mock_psutil:
            mock_psutil.cpu_percent.return_value = 50.0
            mock_psutil.virtual_memory.return_value = MagicMock(used=4 * 1024**3)
            yield EnhancedResourceMonitor(vram_threshold_gb=5.8)

    def test_monitor_initialization(self, monitor):
        assert monitor.vram_threshold_gb == 5.8
        assert monitor.monitoring is False

    def test_start_monitoring(self, monitor):
        monitor.start_monitoring()
        assert monitor.monitoring is True
        monitor.stop_monitoring()

    def test_stop_monitoring(self, monitor):
        monitor.start_monitoring()
        monitor.stop_monitoring()
        assert monitor.monitoring is False

    def test_get_vram_state_normal(self, monitor):
        state = monitor.get_vram_state()
        assert state == VRAMState.NORMAL

    def test_should_delay_ingestion(self, monitor):
        result = monitor.should_delay_ingestion()
        assert result is False

    def test_get_status_info(self, monitor):
        info = monitor.get_status_info()
        assert "vram_usage_gb" in info
        assert "vram_state" in info

    def test_get_resource_trends_empty(self, monitor):
        trends = monitor.get_resource_trends()
        assert "error" in trends

    def test_get_resource_trends_with_history(self, monitor):
        status = ResourceStatus(
            vram_usage_gb=4.0,
            vram_threshold_gb=5.8,
            vram_state=VRAMState.NORMAL,
            should_delay=False,
            timestamp=datetime.now(),
            cpu_usage_percent=50.0,
            memory_usage_gb=8.0,
        )
        monitor.resource_history = [status]
        trends = monitor.get_resource_trends()
        assert "vram_trend" in trends
        assert trends["vram_trend"]["avg"] == 4.0


class TestGlobalFunctions:
    """Tests for module-level functions."""

    def test_get_status_bar_manager(self):
        manager = get_status_bar_manager()
        assert isinstance(manager, VSCodeStatusBarManager)

    def test_create_enhanced_monitor(self):
        with patch("extensions.ext_governor.resource_monitor.psutil"):
            monitor = create_enhanced_monitor(vram_threshold_gb=6.0)
            assert isinstance(monitor, EnhancedResourceMonitor)
            assert monitor.vram_threshold_gb == 6.0


class TestPluginResourceMonitor:
    """Tests for plugin.py ResourceMonitor class."""

    @pytest.fixture
    def mock_psutil(self):
        with patch("extensions.ext_governor.plugin.psutil") as mock_psutil:
            mock_psutil.virtual_memory.return_value = MagicMock(used=4 * 1024**3)
            mock_psutil.cpu_percent.return_value = 50.0
            yield mock_psutil

    def test_resource_monitor_init_with_threshold(self, mock_psutil):
        monitor = ResourceMonitor(vram_threshold_gb=6.0)
        assert monitor.vram_threshold_gb == 6.0

    def test_resource_monitor_init_adaptive(self, mock_psutil):
        with patch("extensions.ext_governor.plugin.HAS_NVML", False):
            monitor = ResourceMonitor()
            assert monitor.vram_threshold_gb == 5.8

    def test_get_vram_usage_gb_nvidia(self, mock_psutil):
        mock_pynvml = MagicMock()
        mock_pynvml.nvmlInit.return_value = None
        mock_pynvml.nvmlDeviceGetHandleByIndex.return_value = MagicMock()
        mock_pynvml.nvmlDeviceGetMemoryInfo.return_value = MagicMock(used=4 * 1024**3)
        mock_pynvml.nvmlShutdown.return_value = None
        with patch("extensions.ext_governor.plugin.HAS_NVML", True):
            with patch("extensions.ext_governor.plugin.pynvml", mock_pynvml, create=True):
                monitor = ResourceMonitor(vram_threshold_gb=6.0)
                usage = monitor.get_vram_usage_gb()
                assert usage > 0

    def test_get_vram_usage_gb_fallback(self, mock_psutil):
        with patch("extensions.ext_governor.plugin.HAS_NVML", False):
            monitor = ResourceMonitor(vram_threshold_gb=6.0)
            usage = monitor.get_vram_usage_gb()
            assert usage > 0

    def test_get_vram_state(self, mock_psutil):
        monitor = ResourceMonitor(vram_threshold_gb=6.0)
        # Need to use the VRAMState from the same module
        from extensions.ext_governor.plugin import VRAMState as PluginVRAMState

        state = monitor.get_vram_state()
        assert state == PluginVRAMState.NORMAL

    def test_should_delay_ingestion(self, mock_psutil):
        monitor = ResourceMonitor(vram_threshold_gb=6.0)
        assert monitor.should_delay_ingestion() is False


class TestGovernorPlugin:
    """Tests for Governor plugin class."""

    @pytest.fixture
    def mock_nexus(self):
        nexus = MagicMock()
        nexus.nexus = MagicMock()
        nexus.nexus.execute.return_value = None
        return nexus

    @pytest.fixture
    def mock_psutil(self):
        with patch("extensions.ext_governor.plugin.psutil") as mock_psutil:
            mock_psutil.virtual_memory.return_value = MagicMock(used=4 * 1024**3)
            mock_psutil.cpu_percent.return_value = 50.0
            yield mock_psutil

    @pytest.fixture
    def governor(self, mock_nexus, mock_psutil):
        with patch("extensions.ext_governor.plugin.HAS_NVML", False):
            manifest = {"name": "test_governor", "version": "1.0"}
            return Governor(manifest, mock_nexus)

    def test_governor_init(self, governor):
        assert governor.vram_threshold_gb == 5.8
        assert governor.max_queue_size == 100

    def test_governor_get_tools(self, governor):
        tools = governor.get_tools()
        assert len(tools) == 5

    @pytest.mark.asyncio
    async def test_on_ingestion(self, governor):
        result = await governor.on_ingestion("test_data", {"key": "value"})
        assert result["status"] == "queued"

    @pytest.mark.asyncio
    async def test_get_resource_status(self, governor):
        status = await governor.get_resource_status()
        data = json.loads(status)
        assert "vram_usage_gb" in data

    @pytest.mark.asyncio
    async def test_get_governor_stats(self, governor):
        stats = await governor.get_governor_stats()
        data = json.loads(stats)
        assert "total_tasks" in data

    @pytest.mark.asyncio
    async def test_get_queue_status(self, governor):
        status = await governor.get_queue_status()
        data = json.loads(status)
        assert "current_size" in data

    @pytest.mark.asyncio
    async def test_set_vram_threshold(self, governor):
        result = await governor.set_vram_threshold(7.0)
        data = json.loads(result)
        assert data["status"] == "success"
        assert data["new_threshold_gb"] == 7.0

    @pytest.mark.asyncio
    async def test_clear_queue(self, governor):
        result = await governor.clear_queue()
        data = json.loads(result)
        assert data["status"] == "success"

    def test_register_plugins(self, governor):
        governor.register_plugins(sda_plugin=MagicMock(), apb_plugin=MagicMock())
        assert governor.sda_plugin is not None
        assert governor.apb_plugin is not None

    @pytest.mark.asyncio
    async def test_on_startup(self, governor):
        await governor.on_startup()
        assert governor.resource_monitor.monitoring is True

    @pytest.mark.asyncio
    async def test_on_shutdown(self, governor):
        await governor.on_startup()
        await governor.on_shutdown()
        assert governor.resource_monitor.monitoring is False


class TestPluginFactory:
    """Tests for plugin factory functions."""

    @pytest.fixture
    def mock_nexus(self):
        nexus = MagicMock()
        nexus.nexus = MagicMock()
        return nexus

    def test_create_plugin(self, mock_nexus):
        with patch("extensions.ext_governor.plugin.HAS_NVML", False):
            with patch("extensions.ext_governor.plugin.psutil"):
                manifest = {"name": "test_governor"}
                plugin = create_plugin(manifest, mock_nexus)
                assert isinstance(plugin, Governor)

    def test_register_extension(self, mock_nexus):
        with patch("extensions.ext_governor.plugin.HAS_NVML", False):
            with patch("extensions.ext_governor.plugin.psutil"):
                manifest = {"name": "test_governor"}
                plugin = register_extension(manifest, mock_nexus)
                assert isinstance(plugin, Governor)
