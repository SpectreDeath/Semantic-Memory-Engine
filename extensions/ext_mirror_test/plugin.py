"""
Cross-Modal Auditor Extension Plugin

Main plugin entry point that integrates the Cross-Modal Auditor extension
with the SME system.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

try:
    from .cross_modal_auditor import audit_multimodal_sync, CrossModalAuditor, AuditResult
    from .governor_integration import (
        safe_audit_multimodal_sync,
        GovernorIntegration,
        GovernorStatus,
        create_governor_aware_hook
    )
except ImportError:
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from cross_modal_auditor import audit_multimodal_sync, CrossModalAuditor, AuditResult
    from governor_integration import (
        safe_audit_multimodal_sync,
        GovernorIntegration,
        GovernorStatus,
        create_governor_aware_hook
    )


class CrossModalAuditorPlugin:
    """Main plugin class for the Cross-Modal Auditor extension."""
    
    def __init__(self):
        self.name = "Cross-Modal Auditor Extension"
        self.version = "1.0.0"
        self.description = "Validates image-text alignment using CLIP model and NLP parsing"
        
        # Plugin configuration
        self.config = {
            'sync_threshold': 65.0,  # Sync score threshold for hallucination detection
            'model_name': "openai/clip-vit-base-patch32",
            'governor_integration': True,  # Enable Governor status checking
            'safe_mode': True,  # Use safe wrapper that checks Governor status
            'log_detailed_results': True
        }
        
        # State tracking
        self.is_active = False
        self.governor_integration = GovernorIntegration()
        
    def activate(self) -> bool:
        """Activate the Cross-Modal Auditor plugin."""
        try:
            print(f"🔍 Activating {self.name} v{self.version}")
            print(f"Description: {self.description}")
            
            # Initialize Governor integration
            if self.config.get('governor_integration', True):
                print("✅ Governor integration enabled")
            
            self.is_active = True
            print(f"✅ {self.name} activated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to activate {self.name}: {e}")
            return False
    
    def deactivate(self) -> bool:
        """Deactivate the Cross-Modal Auditor plugin."""
        try:
            print(f"🔍 Deactivating {self.name}")
            
            self.is_active = False
            print(f"✅ {self.name} deactivated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to deactivate {self.name}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
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
    
    def get_tools(self) -> Dict[str, Callable]:
        """Get available tools provided by this plugin."""
        tools = {}
        
        if self.config.get('safe_mode', True):
            # Use safe wrapper that checks Governor status
            tools['audit_multimodal_sync'] = self._create_safe_audit_tool()
        else:
            # Use direct audit function
            tools['audit_multimodal_sync'] = self._create_direct_audit_tool()
        
        return tools
    
    def _create_safe_audit_tool(self) -> Callable:
        """Create the safe audit tool with Governor status checking."""
        def safe_audit_tool(image_path: str, prompt: str, 
                           threshold: Optional[float] = None) -> Dict[str, Any]:
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
            return safe_audit_multimodal_sync(**audit_config)
        
        return safe_audit_tool
    
    def _create_direct_audit_tool(self) -> Callable:
        """Create the direct audit tool without Governor checking."""
        def direct_audit_tool(image_path: str, prompt: str, 
                             threshold: Optional[float] = None) -> Dict[str, Any]:
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
            return audit_multimodal_sync(**audit_config)
        
        return direct_audit_tool
    
    def get_hooks(self) -> Dict[str, Callable]:
        """Get available hooks provided by this plugin."""
        return {
            'governor_status_check': create_governor_aware_hook()
        }
    
    def get_events(self) -> List[str]:
        """Get list of events this plugin can handle."""
        return [
            'governor_status_changed',
            'audit_started',
            'audit_completed',
            'hallucination_detected'
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
        
        elif event_name == 'audit_started':
            print("🔍 Cross-modal audit started")
            return {'audit_started': True}
        
        elif event_name == 'audit_completed':
            result = kwargs.get('result', {})
            print(f"✅ Cross-modal audit completed. Status: {result.get('status', 'unknown')}")
            return {'audit_completed': True}
        
        elif event_name == 'hallucination_detected':
            hallucination_info = kwargs.get('hallucination_info', {})
            print(f"🚨 Multimodal hallucination detected: {hallucination_info}")
            return {'hallucination_handled': True}
        
        return {'event_handled': False}
    
    def get_auditor_instance(self) -> CrossModalAuditor:
        """Get an instance of the CrossModalAuditor for advanced usage."""
        return CrossModalAuditor(model_name=self.config['model_name'])


# Create global plugin instance
cross_modal_auditor_plugin = CrossModalAuditorPlugin()


def get_plugin() -> CrossModalAuditorPlugin:
    """Get the global Cross-Modal Auditor plugin instance."""
    return cross_modal_auditor_plugin


def register_extension(manifest: dict, nexus_api: Any) -> CrossModalAuditorPlugin:
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return cross_modal_auditor_plugin


# Export for use by the extension system
__all__ = ['CrossModalAuditorPlugin', 'get_plugin', 'cross_modal_auditor_plugin', 'register_extension']