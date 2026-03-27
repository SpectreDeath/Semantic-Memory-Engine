"""
Statistical Watermark Decoder Extension Plugin

Main plugin entry point that integrates the Statistical Watermark Decoder extension
with the SME system.
"""

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from .governor_integration import (
        CPUUsageLevel,
        GovernorStatus,
        StethoGovernorIntegration,
        create_stetho_governor_hook,
        safe_detect_watermark_pulse,
    )
    from .statistical_watermark_decoder import (
        StatisticalWatermarkDecoder,
        WatermarkDetection,
        detect_watermark_pulse,
    )
except ImportError:
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from governor_integration import (
        CPUUsageLevel,
        GovernorStatus,
        StethoGovernorIntegration,
        create_stetho_governor_hook,
        safe_detect_watermark_pulse,
    )
    from statistical_watermark_decoder import (
        StatisticalWatermarkDecoder,
        detect_watermark_pulse,
    )


class StatisticalWatermarkDecoderPlugin:
    """Main plugin class for the Statistical Watermark Decoder extension."""

    def __init__(self):
        self.name = "Statistical Watermark Decoder Extension"
        self.version = "1.0.0"
        self.description = "Detects invisible unicode markers and analyzes token frequency patterns for watermark detection"

        # Plugin configuration
        self.config = {
            'z_score_threshold': 2.0,  # Threshold for significant Z-Scores
            'confidence_threshold': 0.5,  # Minimum confidence score for watermark detection
            'governor_integration': True,  # Enable Governor status checking
            'cpu_monitoring': True,  # Enable CPU usage monitoring
            'safe_mode': True,  # Use safe wrapper that checks Governor and CPU status
            'log_detailed_results': True
        }

        # State tracking
        self.is_active = False
        self.governor_integration = StethoGovernorIntegration()

    def activate(self) -> bool:
        """Activate the Statistical Watermark Decoder plugin."""
        try:
            print(f"🔍 Activating {self.name} v{self.version}")
            print(f"Description: {self.description}")

            # Initialize Governor integration
            if self.config.get('governor_integration', True):
                print("✅ Governor integration enabled")

            # Initialize CPU monitoring
            if self.config.get('cpu_monitoring', True):
                print("✅ CPU monitoring enabled")

            self.is_active = True
            print(f"✅ {self.name} activated successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to activate {self.name}: {e}")
            return False

    def deactivate(self) -> bool:
        """Deactivate the Statistical Watermark Decoder plugin."""
        try:
            print(f"🔍 Deactivating {self.name}")

            self.is_active = False
            print(f"✅ {self.name} deactivated successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to deactivate {self.name}: {e}")
            return False

    def get_status(self) -> dict[str, Any]:
        """Get current plugin status."""
        return {
            'name': self.name,
            'version': self.version,
            'is_active': self.is_active,
            'config': self.config,
            'governor_status': self.governor_integration.get_status_info()
        }

    def configure(self, **kwargs) -> bool:
        """Configure the plugin."""
        try:
            # Update configuration
            for key, value in kwargs.items():
                if key in self.config:
                    self.config[key] = value

            print(f"✅ {self.name} configuration updated")
            return True

        except Exception as e:
            print(f"❌ Failed to configure {self.name}: {e}")
            return False

    def get_tools(self) -> dict[str, Callable]:
        """Get available tools provided by this plugin."""
        tools = {}

        if self.config.get('safe_mode', True):
            # Use safe wrapper that checks Governor status and CPU usage
            tools['detect_watermark_pulse'] = self._create_safe_detection_tool()
        else:
            # Use direct detection function
            tools['detect_watermark_pulse'] = self._create_direct_detection_tool()

        return tools

    def _create_safe_detection_tool(self) -> Callable:
        """Create the safe detection tool with Governor and CPU status checking."""
        def safe_detection_tool(text: str) -> dict[str, Any]:
            """
            Safe watermark detection tool that checks Governor status and CPU usage.

            Args:
                text: Text to analyze for watermarks.

            Returns:
                Dictionary containing detection results.
            """
            print("🔍 Statistical Watermark Decoder: Starting safe detection")

            # Use safe wrapper that checks Governor and CPU status
            result = safe_detect_watermark_pulse(text, self.governor_integration)
            return json.dumps(result)

        return safe_detection_tool

    def _create_direct_detection_tool(self) -> Callable:
        """Create the direct detection tool without Governor checking."""
        def direct_detection_tool(text: str) -> dict[str, Any]:
            """
            Direct watermark detection tool without Governor status checking.

            Args:
                text: Text to analyze for watermarks.

            Returns:
                Dictionary containing detection results.
            """
            print("🔍 Statistical Watermark Decoder: Starting direct detection")

            # Use direct detection function
            result = detect_watermark_pulse(text)
            return json.dumps(result)

        return direct_detection_tool

    def get_hooks(self) -> dict[str, Callable]:
        """Get available hooks provided by this plugin."""
        return {
            'governor_status_check': create_stetho_governor_hook()
        }

    def get_events(self) -> list[str]:
        """Get list of events this plugin can handle."""
        return [
            'governor_status_changed',
            'cpu_usage_changed',
            'detection_started',
            'detection_completed',
            'watermark_detected'
        ]

    def handle_event(self, event_name: str, **kwargs) -> Any:
        """Handle plugin-specific events."""
        if event_name == 'governor_status_changed':
            new_status = kwargs.get('status', 'UNKNOWN')
            print(f"📊 Governor status changed to: {new_status}")

            # Update our Governor integration
            if new_status == "NORMAL":
                self.governor_integration._governor_status = GovernorStatus.NORMAL
            elif new_status == "WARNING":
                self.governor_integration._governor_status = GovernorStatus.WARNING
            elif new_status == "CRITICAL":
                self.governor_integration._governor_status = GovernorStatus.CRITICAL
            else:
                self.governor_integration._governor_status = GovernorStatus.UNKNOWN

            self.governor_integration._last_status_check = kwargs.get('timestamp')

            return {'status_updated': True, 'new_status': new_status}

        elif event_name == 'cpu_usage_changed':
            cpu_level = kwargs.get('cpu_level', 'UNKNOWN')
            print(f"💻 CPU usage level changed to: {cpu_level}")

            # Update our CPU usage tracking
            if cpu_level == "LOW":
                self.governor_integration._cpu_usage_level = CPUUsageLevel.LOW
            elif cpu_level == "MEDIUM":
                self.governor_integration._cpu_usage_level = CPUUsageLevel.MEDIUM
            elif cpu_level == "HIGH":
                self.governor_integration._cpu_usage_level = CPUUsageLevel.HIGH
            else:
                self.governor_integration._cpu_usage_level = CPUUsageLevel.UNKNOWN

            return {'cpu_level_updated': True, 'new_level': cpu_level}

        elif event_name == 'detection_started':
            print("🔍 Watermark detection started")
            return {'detection_started': True}

        elif event_name == 'detection_completed':
            result = kwargs.get('result', {})
            print(f"✅ Watermark detection completed. Status: {result.get('status', 'unknown')}")
            return {'detection_completed': True}

        elif event_name == 'watermark_detected':
            watermark_info = kwargs.get('watermark_info', {})
            print(f"🚨 Watermark detected: {watermark_info}")
            return {'watermark_handled': True}

        return {'event_handled': False}

    def get_decoder_instance(self) -> StatisticalWatermarkDecoder:
        """Get an instance of the StatisticalWatermarkDecoder for advanced usage."""
        return StatisticalWatermarkDecoder()


# Create global plugin instance
statistical_watermark_decoder_plugin = StatisticalWatermarkDecoderPlugin()


def get_plugin() -> StatisticalWatermarkDecoderPlugin:
    """Get the global Statistical Watermark Decoder plugin instance."""
    return statistical_watermark_decoder_plugin


def register_extension(manifest: dict, nexus_api: Any) -> StatisticalWatermarkDecoderPlugin:
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return statistical_watermark_decoder_plugin


# Export for use by the extension system
__all__ = ['StatisticalWatermarkDecoderPlugin', 'get_plugin', 'register_extension', 'statistical_watermark_decoder_plugin']
