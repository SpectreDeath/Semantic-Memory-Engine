"""
Ghost Trap Extension Plugin

Main plugin entry point that integrates the Ghost Trap extension
with the SME system.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

try:
    from .persistence_monitor import (
        hook_governor_task_execution,
        ghost_monitor,
        get_monitoring_status
    )
    from .ghost_detector import scan_for_ghosts, GhostDetector, GhostFile
except ImportError:
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from persistence_monitor import (
        hook_governor_task_execution,
        ghost_monitor,
        get_monitoring_status
    )
    from ghost_detector import scan_for_ghosts, GhostDetector, GhostFile


class GhostTrapPlugin:
    """Main plugin class for the Ghost Trap extension."""
    
    def __init__(self):
        self.name = "Ghost Trap Extension"
        self.version = "1.0.0"
        self.description = "Monitors for potential self-replication events and unauthorized file creation"
        
        # Plugin configuration
        self.config = {
            'size_threshold_mb': 100,
            'recursive_scan': True,
            'detailed_reports': True,
            'monitoring_enabled': True
        }
        
        # State tracking
        self.is_active = False
        
    def activate(self) -> bool:
        """Activate the Ghost Trap plugin."""
        try:
            print(f"🛡️  Activating {self.name} v{self.version}")
            print(f"Description: {self.description}")
            
            # Initialize monitoring if enabled
            if self.config.get('monitoring_enabled', True):
                ghost_monitor.start_monitoring()
                print("✅ Persistence monitoring activated")
            
            self.is_active = True
            print(f"✅ {self.name} activated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to activate {self.name}: {e}")
            return False
    
    def deactivate(self) -> bool:
        """Deactivate the Ghost Trap plugin."""
        try:
            print(f"🛡️  Deactivating {self.name}")
            
            # Stop monitoring
            ghost_monitor.stop_monitoring()
            print("✅ Persistence monitoring deactivated")
            
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
            'monitoring_status': get_monitoring_status(),
            'config': self.config
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
        return {
            'scan_for_ghosts': self._create_scan_tool()
        }
    
    def _create_scan_tool(self) -> Callable:
        """Create the scan_for_ghosts tool with current configuration."""
        def scan_tool(project_root: Optional[str] = None, 
                     size_threshold_mb: Optional[int] = None,
                     recursive: Optional[bool] = None,
                     detailed_report: Optional[bool] = None) -> Dict[str, Any]:
            """
            Scan for ghost files in the project.
            
            Args:
                project_root: Root directory to scan. If None, uses current working directory.
                size_threshold_mb: Minimum file size in MB to consider as suspicious.
                recursive: Whether to scan subdirectories recursively.
                detailed_report: Whether to print a detailed report.
                
            Returns:
                Dictionary containing scan results and summary.
            """
            # Use configuration defaults if not provided
            scan_config = {
                'project_root': project_root or os.getcwd(),
                'size_threshold_mb': size_threshold_mb or self.config['size_threshold_mb'],
                'recursive': recursive if recursive is not None else self.config['recursive_scan'],
                'detailed_report': detailed_report if detailed_report is not None else self.config['detailed_reports']
            }
            
            print(f"🔍 Ghost Trap: Starting scan with config: {scan_config}")
            return scan_for_ghosts(**scan_config)
        
        return scan_tool
    
    def get_hooks(self) -> Dict[str, Callable]:
        """Get available hooks provided by this plugin."""
        return {
            'governor_task_execution': hook_governor_task_execution
        }
    
    def get_events(self) -> List[str]:
        """Get list of events this plugin can handle."""
        return [
            'task_execution_started',
            'task_execution_completed',
            'file_created',
            'ghost_detected'
        ]
    
    def handle_event(self, event_name: str, **kwargs) -> Any:
        """Handle plugin-specific events."""
        if event_name == 'task_execution_started':
            if self.config.get('monitoring_enabled', True):
                ghost_monitor.start_monitoring()
                return {'monitoring_started': True}
        
        elif event_name == 'task_execution_completed':
            if self.config.get('monitoring_enabled', True):
                ghost_monitor.stop_monitoring()
                return {'monitoring_stopped': True}
        
        elif event_name == 'file_created':
            file_path = kwargs.get('file_path', '')
            if file_path and self._is_suspicious_file(file_path):
                print(f"⚠️  Suspicious file created: {file_path}")
                return {'suspicious_file_detected': True}
        
        elif event_name == 'ghost_detected':
            # Handle when a ghost file is detected
            ghost_info = kwargs.get('ghost_info', {})
            print(f"👻 Ghost detected: {ghost_info}")
            return {'ghost_handled': True}
        
        return {'event_handled': False}
    
    def _is_suspicious_file(self, file_path: str) -> bool:
        """Check if a newly created file is suspicious."""
        path = Path(file_path)
        
        # Check if it's a target extension
        if path.suffix.lower() not in {'.bin', '.json'}:
            return False
        
        # Check if it's in a hidden directory
        if ghost_monitor._is_hidden_directory(str(path)):
            return True
        
        # Check file size if it exists
        try:
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > self.config['size_threshold_mb']:
                return True
        except OSError:
            pass
        
        return False


# Create global plugin instance
ghost_trap_plugin = GhostTrapPlugin()


def get_plugin() -> GhostTrapPlugin:
    """Get the global Ghost Trap plugin instance."""
    return ghost_trap_plugin


def register_extension(manifest: dict, nexus_api: Any) -> GhostTrapPlugin:
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return ghost_trap_plugin


# Export for use by the extension system
__all__ = ['GhostTrapPlugin', 'get_plugin', 'ghost_trap_plugin', 'register_extension']