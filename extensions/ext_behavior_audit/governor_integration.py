"""
Governor Integration for Rhetorical Behavior Audit

Handles integration with the Governor system to ensure text-only scans
run on CPU to keep the GPU free for rnj-1 operations.
"""

import logging
import json
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime

# Configure logging for governor integration
logger = logging.getLogger('behavior_audit.governor_integration')
logger.setLevel(logging.INFO)

# Create file handler for governor integration events
governor_handler = logging.FileHandler('behavior_audit_governor_integration_events.log')
governor_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
governor_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(governor_handler)


class GovernorStatus(Enum):
    """Governor status levels."""
    NORMAL = "NORMAL"      # Green - Safe to run text analysis
    WARNING = "WARNING"    # Yellow - Caution, may have resource constraints
    CRITICAL = "CRITICAL"  # Red - High resource usage, avoid heavy operations
    UNKNOWN = "UNKNOWN"    # Status unknown


class GPUUsageLevel(Enum):
    """GPU usage levels for resource monitoring."""
    LOW = "LOW"           # GPU usage < 30%
    MEDIUM = "MEDIUM"     # GPU usage 30-70%
    HIGH = "HIGH"         # GPU usage > 70%
    UNKNOWN = "UNKNOWN"


class BehaviorAuditGovernorIntegration:
    """Handles integration with the Governor system for safe text analysis."""
    
    def __init__(self):
        self._governor_status = GovernorStatus.UNKNOWN
        self._gpu_usage_level = GPUUsageLevel.UNKNOWN
        self._last_status_check = None
        self._analysis_count = 0
        self._total_analysis_time = 0.0
        
    def get_governor_status(self) -> GovernorStatus:
        """
        Get current Governor status.
        
        This method should be implemented to query the actual Governor system.
        For now, it returns a mock status or can be overridden by subclasses.
        """
        # TODO: Implement actual Governor status querying
        # This is a placeholder that should be replaced with actual Governor integration
        
        try:
            # Try to import and query Governor status
            # This is a mock implementation - replace with actual Governor integration
            from src.core.governor import Governor  # This may not exist in current structure
            
            governor = Governor.get_instance()
            status = governor.get_status()
            
            if status == "NORMAL":
                return GovernorStatus.NORMAL
            elif status == "WARNING":
                return GovernorStatus.WARNING
            elif status == "CRITICAL":
                return GovernorStatus.CRITICAL
            else:
                return GovernorStatus.UNKNOWN
                
        except ImportError:
            # Governor not available, assume NORMAL for testing
            logger.warning("Governor system not available, assuming NORMAL status")
            return GovernorStatus.NORMAL
        except Exception as e:
            logger.error(f"Failed to get Governor status: {e}")
            return GovernorStatus.UNKNOWN
    
    def get_gpu_usage_level(self) -> GPUUsageLevel:
        """
        Get current GPU usage level.
        
        This method should be implemented to query actual GPU usage.
        For now, it returns a mock status or can be overridden by subclasses.
        """
        # TODO: Implement actual GPU usage monitoring
        # This is a placeholder that should be replaced with actual GPU monitoring
        
        try:
            # Try to import and query GPU usage
            # This is a mock implementation - replace with actual GPU monitoring
            import psutil
            
            # For CPU-bound operations, we want to ensure GPU is available for rnj-1
            # We'll assume GPU usage is LOW if we can't actually measure it
            return GPUUsageLevel.LOW
                
        except ImportError:
            # psutil not available, assume LOW for testing
            logger.warning("GPU monitoring not available, assuming LOW usage")
            return GPUUsageLevel.LOW
        except Exception as e:
            logger.error(f"Failed to get GPU usage: {e}")
            return GPUUsageLevel.UNKNOWN
    
    def is_safe_to_analyze(self) -> bool:
        """
        Check if it's safe to run rhetorical analysis based on Governor status and GPU usage.
        
        Returns:
            True if safe to analyze (Governor status is NORMAL and GPU usage is LOW/MEDIUM), False otherwise.
        """
        governor_status = self.get_governor_status()
        gpu_usage = self.get_gpu_usage_level()
        
        self._governor_status = governor_status
        self._gpu_usage_level = gpu_usage
        self._last_status_check = datetime.now()
        
        # Safe conditions: Governor NORMAL and GPU usage not HIGH (to keep GPU free for rnj-1)
        is_safe = (governor_status == GovernorStatus.NORMAL and 
                  gpu_usage in [GPUUsageLevel.LOW, GPUUsageLevel.MEDIUM])
        
        if is_safe:
            logger.info(f"Safe to analyze: Governor={governor_status.value}, GPU={gpu_usage.value}")
        else:
            logger.warning(f"Analysis blocked: Governor={governor_status.value}, GPU={gpu_usage.value}")
        
        return is_safe
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get current status information."""
        return {
            'governor_status': self._governor_status.value,
            'gpu_usage_level': self._gpu_usage_level.value,
            'last_status_check': self._last_status_check.isoformat() if self._last_status_check else None,
            'analysis_count': self._analysis_count,
            'total_analysis_time': self._total_analysis_time,
            'is_safe_to_analyze': self.is_safe_to_analyze()
        }
    
    def record_analysis(self, analysis_time: float):
        """Record analysis execution for monitoring."""
        self._analysis_count += 1
        self._total_analysis_time += analysis_time
        
        logger.info(f"Analysis completed in {analysis_time:.2f}s. Total analyses: {self._analysis_count}")


def safe_audit_rhetorical_behavior(text: str, 
                                  governor_check: Optional[BehaviorAuditGovernorIntegration] = None) -> Dict[str, Any]:
    """
    Safe wrapper for audit_rhetorical_behavior that checks Governor status and GPU usage.
    
    Args:
        text: Text to analyze for rhetorical anomalies.
        governor_check: BehaviorAuditGovernorIntegration instance to use for status checking.
        
    Returns:
        Dictionary containing analysis results or error information.
    """
    if governor_check is None:
        governor_check = BehaviorAuditGovernorIntegration()
    
    # Check if it's safe to run the analysis
    if not governor_check.is_safe_to_analyze():
        status_info = governor_check.get_status_info()
        
        warning_message = (
            f"[ANALYSIS BLOCKED - GOVERNOR: {status_info['governor_status']}, "
            f"GPU: {status_info['gpu_usage_level']}] Rhetorical behavior analysis skipped for safety."
        )
        
        logger.warning(warning_message)
        print(f"⚠️  {warning_message}")
        
        return {
            'sentiment_volatility': 0.0,
            'type_token_ratio': 0.0,
            'lexical_diversity_score': 0.0,
            'emphatic_qualifiers_count': 0,
            'non_contracted_denials_count': 0,
            'synthetic_repetitiveness_score': 0.0,
            'deceptive_indicators': [],
            'anomaly_detected': False,
            'confidence_score': 0.0,
            'timestamp': datetime.now().isoformat(),
            'status': 'ANALYSIS_BLOCKED_DUE_TO_RESOURCE_CONSTRAINTS',
            'governor_status': status_info['governor_status'],
            'gpu_usage_level': status_info['gpu_usage_level'],
            'reason': 'Governor status not NORMAL or GPU usage too high (rnj-1 needs GPU)'
        }
    
    # Import the actual analysis function
    try:
        from .rhetorical_behavior_audit import audit_rhetorical_behavior
        import time
        
        # Record analysis start time
        start_time = time.time()
        
        # Run the actual analysis
        result = audit_rhetorical_behavior(text)
        
        # Record analysis completion
        analysis_time = time.time() - start_time
        governor_check.record_analysis(analysis_time)
        
        return result
        
    except ImportError as e:
        logger.error(f"Failed to import analysis function: {e}")
        return {
            'sentiment_volatility': 0.0,
            'type_token_ratio': 0.0,
            'lexical_diversity_score': 0.0,
            'emphatic_qualifiers_count': 0,
            'non_contracted_denials_count': 0,
            'synthetic_repetitiveness_score': 0.0,
            'deceptive_indicators': [],
            'anomaly_detected': False,
            'confidence_score': 0.0,
            'timestamp': datetime.now().isoformat(),
            'status': 'ANALYSIS_FAILED_TO_IMPORT',
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Analysis execution failed: {e}")
        return {
            'sentiment_volatility': 0.0,
            'type_token_ratio': 0.0,
            'lexical_diversity_score': 0.0,
            'emphatic_qualifiers_count': 0,
            'non_contracted_denials_count': 0,
            'synthetic_repetitiveness_score': 0.0,
            'deceptive_indicators': [],
            'anomaly_detected': False,
            'confidence_score': 0.0,
            'timestamp': datetime.now().isoformat(),
            'status': 'ANALYSIS_EXECUTION_FAILED',
            'error': str(e)
        }


def safe_audit_rhetorical_behavior_tool(text: str, 
                                     governor_check: Optional[BehaviorAuditGovernorIntegration] = None) -> str:
    """Tool wrapper that returns a JSON string."""
    result = safe_audit_rhetorical_behavior(text, governor_check)
    return json.dumps(result, indent=2)


def create_behavior_audit_governor_hook() -> Callable:
    """
    Create a hook function that can be used by the Governor system.
    
    This function returns a hook that can be registered with the Governor
    to monitor status changes and take appropriate action.
    """
    governor_integration = BehaviorAuditGovernorIntegration()
    
    def behavior_audit_governor_status_hook(status: str, **kwargs) -> Dict[str, Any]:
        """
        Hook function called by Governor when status changes.
        
        Args:
            status: New Governor status.
            **kwargs: Additional status information.
            
        Returns:
            Dictionary with hook execution results.
        """
        try:
            # Update our status tracking
            if status == "NORMAL":
                governor_integration._governor_status = GovernorStatus.NORMAL
            elif status == "WARNING":
                governor_integration._governor_status = GovernorStatus.WARNING
            elif status == "CRITICAL":
                governor_integration._governor_status = GovernorStatus.CRITICAL
            else:
                governor_integration._governor_status = GovernorStatus.UNKNOWN
            
            governor_integration._last_status_check = datetime.now()
            
            # Log the status change
            logger.info(f"Behavior Audit Governor status changed to: {status}")
            print(f"📊 Behavior Audit Governor status updated: {status}")
            
            # Take action based on status
            if status == "CRITICAL":
                print("🚨 Behavior Audit Governor reports CRITICAL status - text analysis blocked")
            elif status == "WARNING":
                print("⚠️  Behavior Audit Governor reports WARNING status - proceed with caution")
            elif status == "NORMAL":
                print("✅ Behavior Audit Governor reports NORMAL status - text analysis safe")
            
            return {
                'status': 'hook_executed',
                'new_governor_status': status,
                'timestamp': datetime.now().isoformat(),
                'action_taken': 'status_updated'
            }
            
        except Exception as e:
            logger.error(f"Behavior Audit Governor status hook failed: {e}")
            return {
                'status': 'hook_failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    return behavior_audit_governor_status_hook


# Export the main functions for use by the extension system
__all__ = [
    'safe_audit_rhetorical_behavior',
    'safe_audit_rhetorical_behavior_tool',
    'BehaviorAuditGovernorIntegration', 
    'GovernorStatus',
    'GPUUsageLevel',
    'create_behavior_audit_governor_hook'
]