"""
Rhetorical Behavior Audit Extension Plugin

Main plugin entry point that integrates the Rhetorical Behavior Audit extension
with the SME system.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

try:
    from .rhetorical_behavior_audit import audit_rhetorical_behavior, RhetoricalBehaviorAuditor, RhetoricalAnalysis
    from .provenance_profiler import profile_rhetorical_motive, profile_rhetorical_motive_async, ProvenanceProfiler, ProvenanceProfile
    from .governor_integration import (
        safe_audit_rhetorical_behavior,
        BehaviorAuditGovernorIntegration,
        GovernorStatus,
        GPUUsageLevel,
        create_behavior_audit_governor_hook
    )
except ImportError:
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from rhetorical_behavior_audit import audit_rhetorical_behavior, RhetoricalBehaviorAuditor, RhetoricalAnalysis
    from provenance_profiler import profile_rhetorical_motive, profile_rhetorical_motive_async, ProvenanceProfiler, ProvenanceProfile
    from governor_integration import (
        safe_audit_rhetorical_behavior,
        BehaviorAuditGovernorIntegration,
        GovernorStatus,
        GPUUsageLevel,
        create_behavior_audit_governor_hook
    )


class RhetoricalBehaviorAuditPlugin:
    """Main plugin class for the Rhetorical Behavior Audit extension."""
    
    def __init__(self):
        self.name = "Rhetorical Behavior Audit Extension"
        self.version = "1.0.0"
        self.description = "Analyzes text for rhetorical anomalies including sentiment volatility, synthetic repetitiveness, and deceptive language patterns"
        
        # Plugin configuration
        self.config = {
            'sentiment_threshold': 0.5,  # Threshold for high sentiment volatility
            'ttr_threshold': 0.5,        # Threshold for low lexical diversity
            'emphatic_threshold': 2,     # Minimum emphatic qualifiers to flag
            'governor_integration': True,  # Enable Governor status checking
            'gpu_monitoring': True,      # Enable GPU usage monitoring
            'cpu_only_mode': True,       # Ensure CPU-only operation for GPU conservation
            'log_detailed_results': True
        }
        
        # State tracking
        self.is_active = False
        self.governor_integration = BehaviorAuditGovernorIntegration()
        
    def activate(self) -> bool:
        """Activate the Rhetorical Behavior Audit plugin."""
        try:
            print(f"🔍 Activating {self.name} v{self.version}")
            print(f"Description: {self.description}")
            
            # Initialize Governor integration
            if self.config.get('governor_integration', True):
                print("✅ Governor integration enabled")
            
            # Initialize GPU monitoring
            if self.config.get('gpu_monitoring', True):
                print("✅ GPU monitoring enabled (to keep GPU free for rnj-1)")
            
            # Verify CPU-only operation
            if self.config.get('cpu_only_mode', True):
                print("✅ CPU-only mode enforced (GPU conservation for rnj-1)")
            
            self.is_active = True
            print(f"✅ {self.name} activated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to activate {self.name}: {e}")
            return False
    
    def deactivate(self) -> bool:
        """Deactivate the Rhetorical Behavior Audit plugin."""
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
        
        if self.config.get('cpu_only_mode', True):
            # Use safe wrapper that checks Governor status and GPU usage
            tools['audit_rhetorical_behavior'] = self._create_safe_audit_tool()
        else:
            # Use direct audit function
            tools['audit_rhetorical_behavior'] = self._create_direct_audit_tool()
        
        # Add Provenance Profiler tool
        tools['profile_rhetorical_motive'] = self._create_provenance_profiler_tool()
        
        return tools
    
    def _create_safe_audit_tool(self) -> Callable:
        """Create the safe audit tool with Governor and GPU status checking."""
        def safe_audit_tool(text: str) -> Dict[str, Any]:
            """
            Safe rhetorical behavior audit tool that checks Governor status and GPU usage.
            
            Args:
                text: Text to analyze for rhetorical anomalies.
                
            Returns:
                Dictionary containing audit results.
            """
            print(f"🔍 Rhetorical Behavior Audit: Starting safe analysis")
            
            # Use safe wrapper that checks Governor and GPU status
            return safe_audit_rhetorical_behavior(text, self.governor_integration)
        
        return safe_audit_tool
    
    def _create_direct_audit_tool(self) -> Callable:
        """Create the direct audit tool without Governor checking."""
        def direct_audit_tool(text: str) -> Dict[str, Any]:
            """
            Direct rhetorical behavior audit tool without Governor status checking.
            
            Args:
                text: Text to analyze for rhetorical anomalies.
                
            Returns:
                Dictionary containing audit results.
            """
            print(f"🔍 Rhetorical Behavior Audit: Starting direct analysis")
            
            # Use direct audit function
            return audit_rhetorical_behavior(text)
        
        return direct_audit_tool
    
    def get_hooks(self) -> Dict[str, Callable]:
        """Get available hooks provided by this plugin."""
        return {
            'governor_status_check': create_behavior_audit_governor_hook()
        }
    
    def get_events(self) -> List[str]:
        """Get list of events this plugin can handle."""
        return [
            'governor_status_changed',
            'gpu_usage_changed',
            'audit_started',
            'audit_completed',
            'rhetorical_anomaly_detected',
            'provenance_profile_started',
            'provenance_profile_completed',
            'commercial_policy_profile_detected'
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
        
        elif event_name == 'gpu_usage_changed':
            gpu_level = kwargs.get('gpu_level', 'UNKNOWN')
            print(f"💻 GPU usage level changed to: {gpu_level}")
            
            # Update our GPU usage tracking
            if gpu_level == "LOW":
                self.governor_integration._gpu_usage_level = GPUUsageLevel.LOW
            elif gpu_level == "MEDIUM":
                self.governor_integration._gpu_usage_level = GPUUsageLevel.MEDIUM
            elif gpu_level == "HIGH":
                self.governor_integration._gpu_usage_level = GPUUsageLevel.HIGH
            else:
                self.governor_integration._gpu_usage_level = GPUUsageLevel.UNKNOWN
            
            return {'gpu_level_updated': True, 'new_level': gpu_level}
        
        elif event_name == 'audit_started':
            print("🔍 Rhetorical behavior audit started")
            return {'audit_started': True}
        
        elif event_name == 'audit_completed':
            result = kwargs.get('result', {})
            print(f"✅ Rhetorical behavior audit completed. Status: {result.get('status', 'unknown')}")
            return {'audit_completed': True}
        
        elif event_name == 'rhetorical_anomaly_detected':
            anomaly_info = kwargs.get('anomaly_info', {})
            print(f"🚨 Rhetorical anomaly detected: {anomaly_info}")
            return {'anomaly_handled': True}
        
        elif event_name == 'provenance_profile_started':
            print("🔍 Provenance profiling started")
            return {'profile_started': True}
        
        elif event_name == 'provenance_profile_completed':
            result = kwargs.get('result', {})
            print(f"✅ Provenance profiling completed. Status: {result.get('status', 'unknown')}")
            return {'profile_completed': True}
        
        elif event_name == 'commercial_policy_profile_detected':
            profile_info = kwargs.get('profile_info', {})
            print(f"🚨 Commercial policy profile detected: {profile_info}")
            return {'profile_handled': True}
        
        return {'event_handled': False}
    
    def _create_provenance_profiler_tool(self) -> Callable:
        """Create the Provenance Profiler tool with background thread execution."""
        def provenance_profiler_tool(text: str, async_mode: bool = True) -> Dict[str, Any]:
            """
            Provenance profiler tool that analyzes rhetorical motives and commercial policy-aligned LLM patterns.
            
            Args:
                text: Text to analyze for rhetorical motives.
                async_mode: Whether to run in background thread (default: True).
                
            Returns:
                Dictionary containing profiling results.
            """
            print(f"🔍 Provenance Profiler: Starting analysis")
            
            if async_mode:
                # Run on background thread to avoid blocking main inference
                def callback(result):
                    print(f"✅ Background profiling completed. Status: {result.get('status', 'unknown')}")
                    if result.get('profile_detected', False):
                        print(f"🚨 Commercial policy profile detected: {result.get('confidence_score', 0.0)}")
                
                thread = profile_rhetorical_motive_async(text, callback)
                return {
                    'status': 'BACKGROUND_PROFILING_STARTED',
                    'thread_id': thread.ident,
                    'message': 'Provenance profiling started in background thread'
                }
            else:
                # Run synchronously
                return profile_rhetorical_motive(text)
        
        return provenance_profiler_tool
    
    def get_auditor_instance(self) -> RhetoricalBehaviorAuditor:
        """Get an instance of the RhetoricalBehaviorAuditor for advanced usage."""
        return RhetoricalBehaviorAuditor()
    
    def get_profiler_instance(self) -> ProvenanceProfiler:
        """Get an instance of the ProvenanceProfiler for advanced usage."""
        return ProvenanceProfiler()


# Create global plugin instance
rhetorical_behavior_audit_plugin = RhetoricalBehaviorAuditPlugin()


def get_plugin() -> RhetoricalBehaviorAuditPlugin:
    """Get the global Rhetorical Behavior Audit plugin instance."""
    return rhetorical_behavior_audit_plugin


def register_extension(manifest: dict, nexus_api: Any) -> RhetoricalBehaviorAuditPlugin:
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return rhetorical_behavior_audit_plugin


# Export for use by the extension system
__all__ = ['RhetoricalBehaviorAuditPlugin', 'get_plugin', 'rhetorical_behavior_audit_plugin', 'register_extension']