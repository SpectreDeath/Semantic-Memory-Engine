"""
Cross-Modal Auditor Extension Plugin

Main plugin entry point that integrates the Cross-Modal Auditor extension
with the SME system.
"""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.CrossModalAuditor")

try:
    from .cross_modal_auditor import CrossModalAuditor, audit_multimodal_sync
    from .governor_integration import (
        GovernorIntegration,
        GovernorStatus,
        create_governor_aware_hook,
        safe_audit_multimodal_sync_tool,
    )
except ImportError:
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from cross_modal_auditor import CrossModalAuditor, audit_multimodal_sync
    from governor_integration import (
        GovernorIntegration,
        GovernorStatus,
        create_governor_aware_hook,
        safe_audit_multimodal_sync_tool,
    )


class CrossModalAuditorPlugin(BasePlugin):
    """
    Cross-Modal Auditor Extension Plugin.
    Validates image-text alignment using CLIP model and NLP parsing.
    
    Extends BasePlugin to comply with the SME extension contract.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.description = "Validates image-text alignment using CLIP model and NLP parsing"

        # Plugin configuration
        self.config = {
            'sync_threshold': 65.0,
            'model_name': "openai/clip-vit-base-patch32",
            'governor_integration': True,
            'safe_mode': True,
            'log_detailed_results': True
        }

        # State tracking
        self.is_active = False
        self.governor_integration = GovernorIntegration()

    async def on_startup(self) -> None:
        """
        Initialize the Cross-Modal Auditor plugin.
        """
        try:
            logger.info(f"[{self.plugin_id}] Cross-Modal Auditor initializing")
            if self.config.get('governor_integration', True):
                logger.info(f"[{self.plugin_id}] Governor integration enabled")
            self.is_active = True
            logger.info(f"[{self.plugin_id}] Cross-Modal Auditor activated successfully")
        except Exception as e:
            logger.exception(f"[{self.plugin_id}] Failed to activate: {e}")

    async def on_shutdown(self) -> None:
        """
        Clean shutdown of the Cross-Modal Auditor plugin.
        """
        try:
            self.is_active = False
            logger.info(f"[{self.plugin_id}] Cross-Modal Auditor deactivated successfully")
        except Exception as e:
            logger.exception(f"[{self.plugin_id}] Failed to deactivate: {e}")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """
        Cross-Modal Auditor does not process on_ingestion directly.
        It provides tools for multimodal auditing.
        """
        return {
            "status": "skipped",
            "reason": "Cross-Modal Auditor provides auditing tools, not direct ingestion processing"
        }

    def get_status(self) -> dict[str, Any]:
        """Get current plugin status."""
        return {
            'name': self.plugin_id,
            'version': self.manifest.get('version', '1.0.0'),
            'is_active': self.is_active,
            'config': self.config,
            'governor_status': self.governor_integration.get_status_info()
        }

    def configure(self, **kwargs: Any) -> bool:
        """Configure the plugin."""
        try:
            for key, value in kwargs.items():
                if key in self.config:
                    self.config[key] = value
            logger.info(f"[{self.plugin_id}] configuration updated")
            return True
        except Exception as e:
            logger.exception(f"[{self.plugin_id}] Failed to configure: {e}")
            return False

    def get_tools(self) -> list[Callable[..., Any]]:
        """Get available tools provided by this plugin."""
        tools: list[Callable[..., Any]] = []

        if self.config.get('safe_mode', True):
            tools.append(self._create_safe_audit_tool())
        else:
            tools.append(self._create_direct_audit_tool())

        return tools

    def _create_safe_audit_tool(self) -> Callable:
        """Create the safe audit tool with Governor status checking."""
        def safe_audit_tool(image_path: str, prompt: str,
                           threshold: float | None = None) -> dict[str, Any]:
            """
            Safe cross-modal audit tool that checks Governor status.

            Args:
                image_path: Path to the image file.
                prompt: Text prompt describing the image.
                threshold: Sync score threshold for hallucination detection.

            Returns:
                Dictionary containing audit results.
            """
            # Use configuration defaults if not provided
            audit_config = {
                'image_path': image_path,
                'prompt': prompt,
                'threshold': threshold or self.config['sync_threshold'],
                'governor_check': self.governor_integration
            }

            print(f"🔍 Cross-Modal Auditor: Starting safe audit with config: {audit_config}")
            return safe_audit_multimodal_sync_tool(**audit_config)

        return safe_audit_tool

    def _create_direct_audit_tool(self) -> Callable:
        """Create the direct audit tool without Governor checking."""
        def direct_audit_tool(image_path: str, prompt: str,
                             threshold: float | None = None) -> dict[str, Any]:
            """
            Direct cross-modal audit tool without Governor status checking.

            Args:
                image_path: Path to the image file.
                prompt: Text prompt describing the image.
                threshold: Sync score threshold for hallucination detection.

            Returns:
                Dictionary containing audit results.
            """
            # Use configuration defaults if not provided
            audit_config = {
                'image_path': image_path,
                'prompt': prompt,
                'threshold': threshold or self.config['sync_threshold']
            }

            print(f"🔍 Cross-Modal Auditor: Starting direct audit with config: {audit_config}")
            return json.dumps(audit_multimodal_sync(**audit_config), indent=2)

        return direct_audit_tool

    async def on_event(self, event_id: str, payload: dict[str, Any]) -> None:
        """
        V3.0 Event Bus Hook: Responds to system-wide events.
        """
        try:
            if event_id == 'governor_status_changed':
                new_status = payload.get('status', 'UNKNOWN')
                logger.info(f"[{self.plugin_id}] Governor status changed to: {new_status}")
                if new_status == "NORMAL":
                    self.governor_integration._governor_status = GovernorStatus.NORMAL
                elif new_status == "WARNING":
                    self.governor_integration._governor_status = GovernorStatus.WARNING
                elif new_status == "CRITICAL":
                    self.governor_integration._governor_status = GovernorStatus.CRITICAL
                else:
                    self.governor_integration._governor_status = GovernorStatus.UNKNOWN
                self.governor_integration._last_status_check = payload.get('timestamp')
            elif event_id == 'audit_started':
                logger.info(f"[{self.plugin_id}] Cross-modal audit started")
            elif event_id == 'audit_completed':
                result = payload.get('result', {})
                logger.info(f"[{self.plugin_id}] Audit completed. Status: {result.get('status', 'unknown')}")
            elif event_id == 'hallucination_detected':
                hallucination_info = payload.get('hallucination_info', {})
                logger.warning(f"[{self.plugin_id}] Multimodal hallucination detected: {hallucination_info}")
        except Exception as e:
            logger.exception(f"[{self.plugin_id}] Error handling event {event_id}: {e}")

    def get_auditor_instance(self) -> CrossModalAuditor:
        """Get an instance of the CrossModalAuditor for advanced usage."""
        return CrossModalAuditor(model_name=self.config['model_name'])


def create_plugin(manifest: dict[str, Any], nexus_api: Any) -> CrossModalAuditorPlugin:
    """Factory function to create and return a CrossModalAuditorPlugin instance."""
    return CrossModalAuditorPlugin(manifest, nexus_api)


def register_extension(manifest: dict[str, Any], nexus_api: Any) -> CrossModalAuditorPlugin:
    """Standard Lawnmower Man v3.0 extension hook; required by ExtensionManager."""
    return create_plugin(manifest, nexus_api)


# Export for use by the extension system
__all__ = ['CrossModalAuditorPlugin', 'cross_modal_auditor_plugin', 'get_plugin', 'register_extension']
