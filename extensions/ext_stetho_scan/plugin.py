"""
Statistical Watermark Decoder Extension Plugin

Main plugin entry point that integrates the Statistical Watermark Decoder extension
with the SME system.
"""

import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from src.core.plugin_base import BasePlugin
    from src.utils.error_handling import ErrorHandler
except ImportError:
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from error_handling import ErrorHandler
    from plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.StethoScan")

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


class StatisticalWatermarkDecoderPlugin(BasePlugin):
    """Main plugin class for the Statistical Watermark Decoder extension."""

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.name = "Statistical Watermark Decoder Extension"
        self.version = "1.0.0"
        self.description = "Detects invisible unicode markers and analyzes token frequency patterns for watermark detection"
        self.error_handler = ErrorHandler(self.plugin_id)

        self.config = {
            "z_score_threshold": 2.0,
            "confidence_threshold": 0.5,
            "governor_integration": True,
            "cpu_monitoring": True,
            "safe_mode": True,
            "log_detailed_results": True,
        }

        self.is_active = False
        self.governor_integration = StethoGovernorIntegration()

    def activate(self) -> bool:
        try:
            logger.info("Activating %s v%s", self.name, self.version)
            if self.config.get("governor_integration", True):
                logger.info("Governor integration enabled")
            if self.config.get("cpu_monitoring", True):
                logger.info("CPU monitoring enabled")
            self.is_active = True
            logger.info("%s activated successfully", self.name)
            return True
        except Exception as e:
            logger.exception("Failed to activate %s: %s", self.name, e)
            return False

    def deactivate(self) -> bool:
        try:
            logger.info("Deactivating %s", self.name)
            self.is_active = False
            logger.info("%s deactivated successfully", self.name)
            return True
        except Exception as e:
            logger.exception("Failed to deactivate %s: %s", self.name, e)
            return False

    def get_status(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "is_active": self.is_active,
            "config": self.config,
            "governor_status": self.governor_integration.get_status_info(),
        }

    def configure(self, **kwargs) -> bool:
        try:
            for key, value in kwargs.items():
                if key in self.config:
                    self.config[key] = value
            logger.info("%s configuration updated", self.name)
            return True
        except Exception as e:
            logger.exception("Failed to configure %s: %s", self.name, e)
            return False

    def get_tools(self) -> list[Callable]:
        return [self._create_safe_detection_tool() if self.config.get("safe_mode", True) else self._create_direct_detection_tool()]

    def _create_safe_detection_tool(self) -> Callable:
        def safe_detection_tool(text: str) -> str:
            try:
                logger.info("Statistical Watermark Decoder: Starting safe detection")
                result = safe_detect_watermark_pulse(text, self.governor_integration)
                return json.dumps(result)
            except Exception as e:
                return json.dumps(self.error_handler.handle_extension_error(e, "detect_watermark_pulse", {"text_length": len(text) if text else 0}))
        return safe_detection_tool

    def _create_direct_detection_tool(self) -> Callable:
        def direct_detection_tool(text: str) -> str:
            try:
                logger.info("Statistical Watermark Decoder: Starting direct detection")
                result = detect_watermark_pulse(text)
                return json.dumps(result)
            except Exception as e:
                return json.dumps(self.error_handler.handle_extension_error(e, "detect_watermark_pulse", {"text_length": len(text) if text else 0}))
        return direct_detection_tool

    def get_hooks(self) -> dict[str, Callable]:
        return {"governor_status_check": create_stetho_governor_hook()}

    def get_events(self) -> list[str]:
        return [
            "governor_status_changed",
            "cpu_usage_changed",
            "detection_started",
            "detection_completed",
            "watermark_detected",
        ]

    def handle_event(self, event_name: str, **kwargs) -> Any:
        if event_name == "governor_status_changed":
            new_status = kwargs.get("status", "UNKNOWN")
            logger.info("Governor status changed to: %s", new_status)
            if new_status == "NORMAL":
                self.governor_integration._governor_status = GovernorStatus.NORMAL
            elif new_status == "WARNING":
                self.governor_integration._governor_status = GovernorStatus.WARNING
            elif new_status == "CRITICAL":
                self.governor_integration._governor_status = GovernorStatus.CRITICAL
            else:
                self.governor_integration._governor_status = GovernorStatus.UNKNOWN
            self.governor_integration._last_status_check = kwargs.get("timestamp")
            return {"status_updated": True, "new_status": new_status}
        elif event_name == "cpu_usage_changed":
            cpu_level = kwargs.get("cpu_level", "UNKNOWN")
            logger.info("CPU usage level changed to: %s", cpu_level)
            if cpu_level == "LOW":
                self.governor_integration._cpu_usage_level = CPUUsageLevel.LOW
            elif cpu_level == "MEDIUM":
                self.governor_integration._cpu_usage_level = CPUUsageLevel.MEDIUM
            elif cpu_level == "HIGH":
                self.governor_integration._cpu_usage_level = CPUUsageLevel.HIGH
            else:
                self.governor_integration._cpu_usage_level = CPUUsageLevel.UNKNOWN
            return {"cpu_level_updated": True, "new_level": cpu_level}
        elif event_name == "detection_started":
            logger.info("Watermark detection started")
            return {"detection_started": True}
        elif event_name == "detection_completed":
            result = kwargs.get("result", {})
            logger.info("Watermark detection completed. Status: %s", result.get("status", "unknown"))
            return {"detection_completed": True}
        elif event_name == "watermark_detected":
            watermark_info = kwargs.get("watermark_info", {})
            logger.warning("Watermark detected: %s", watermark_info)
            return {"watermark_handled": True}
        return {"event_handled": False}

    def get_decoder_instance(self) -> StatisticalWatermarkDecoder:
        return StatisticalWatermarkDecoder()


def get_plugin(manifest: dict[str, Any] | None = None, nexus_api: Any | None = None) -> StatisticalWatermarkDecoderPlugin:
    return StatisticalWatermarkDecoderPlugin(manifest or {}, nexus_api)


def register_extension(manifest: dict[str, Any], nexus_api: Any) -> StatisticalWatermarkDecoderPlugin:
    return StatisticalWatermarkDecoderPlugin(manifest, nexus_api)


__all__ = [
    "StatisticalWatermarkDecoderPlugin",
    "get_plugin",
    "register_extension",
]
