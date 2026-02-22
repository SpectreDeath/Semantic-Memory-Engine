"""
Governor Integration for Cross-Modal Auditor

Handles integration with the Governor system to ensure audits only run
when Governor status is NORMAL (Green) to avoid OOM conditions.
"""

import logging
import json
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime

# Configure logging for governor integration
logger = logging.getLogger('mirror_test.governor_integration')
logger.setLevel(logging.INFO)

# Create file handler for governor integration events
governor_handler = logging.FileHandler('governor_integration_events.log')
governor_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
governor_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(governor_handler)


class GovernorStatus(Enum):
    """Governor status levels."""
    NORMAL = "NORMAL"      # Green - Safe to run audits
    WARNING = "WARNING"    # Yellow - Caution, may have resource constraints
    CRITICAL = "CRITICAL"  # Red - High resource usage, avoid heavy operations
    UNKNOWN = "UNKNOWN"    # Status unknown


class GovernorIntegration:
    """Handles integration with the Governor system for safe audit execution."""
    
    def __init__(self):
        self._governor_status = GovernorStatus.UNKNOWN
        self._last_status_check = None
        self._audit_count = 0
        self._total_audit_time = 0.0
        
    def get_governor_status(self) -> GovernorStatus:
        """
        Get current Governor status.
        
        This method should be implemented to query the actual Governor system.
        For now, it returns a mock status or can be overridden by subclasses.
        """
        # TODO: Implement actual Governor status querying
        # This is a placeholder that should be replaced with actual Governor integration
        
        # For demonstration, we'll check if we can access Governor status
        # In a real implementation, this would query the Governor's status endpoint
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
    
    def is_safe_to_audit(self) -> bool:
        """
        Check if it's safe to run cross-modal audits based on Governor status.
        
        Returns:
            True if safe to audit (Governor status is NORMAL), False otherwise.
        """
        current_status = self.get_governor_status()
        self._governor_status = current_status
        self._last_status_check = datetime.now()
        
        is_safe = current_status == GovernorStatus.NORMAL
        
        if is_safe:
            logger.info(f"Governor status: {current_status.value} - Safe to audit")
        else:
            logger.warning(f"Governor status: {current_status.value} - Audit blocked for safety")
        
        return is_safe
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get current status information."""
        return {
            'governor_status': self._governor_status.value,
            'last_status_check': self._last_status_check.isoformat() if self._last_status_check else None,
            'audit_count': self._audit_count,
            'total_audit_time': self._total_audit_time,
            'is_safe_to_audit': self.is_safe_to_audit()
        }
    
    def record_audit(self, audit_time: float):
        """Record audit execution for monitoring."""
        self._audit_count += 1
        self._total_audit_time += audit_time
        
        logger.info(f"Audit completed in {audit_time:.2f}s. Total audits: {self._audit_count}")


def safe_audit_multimodal_sync(image_path: str, prompt: str, 
                              threshold: float = 65.0,
                              governor_check: Optional[GovernorIntegration] = None) -> Dict[str, Any]:
    """
    Safe wrapper for audit_multimodal_sync that checks Governor status.
    
    Args:
        image_path: Path to the image file.
        prompt: Text prompt describing the image.
        threshold: Sync score threshold for hallucination detection.
        governor_check: GovernorIntegration instance to use for status checking.
        
    Returns:
        Dictionary containing audit results or error information.
    """
    if governor_check is None:
        governor_check = GovernorIntegration()
    
    # Check if it's safe to run the audit
    if not governor_check.is_safe_to_audit():
        status_info = governor_check.get_status_info()
        
        warning_message = (
            f"[AUDIT BLOCKED - GOVERNOR STATUS: {status_info['governor_status']}] "
            f"Cross-modal audit skipped for safety. Image: {image_path}"
        )
        
        logger.warning(warning_message)
        print(f"⚠️  {warning_message}")
        
        return {
            'sync_score': 0.0,
            'hallucination_detected': False,  # No hallucination detected due to blocked audit
            'severity': 'BLOCKED',
            'detected_keywords': [],
            'missing_keywords': [],
            'timestamp': datetime.now().isoformat(),
            'status': 'AUDIT_BLOCKED_DUE_TO_RESOURCE_CONSTRAINTS',
            'governor_status': status_info['governor_status'],
            'reason': 'Governor status is not NORMAL (Green)'
        }
    
    # Import the actual audit function
    try:
        from .cross_modal_auditor import audit_multimodal_sync
        import time
        
        # Record audit start time
        start_time = time.time()
        
        # Run the actual audit
        result = audit_multimodal_sync(image_path, prompt, threshold)
        
        # Record audit completion
        audit_time = time.time() - start_time
        governor_check.record_audit(audit_time)
        
        return result
        
    except ImportError as e:
        logger.error(f"Failed to import audit function: {e}")
        return {
            'sync_score': 0.0,
            'hallucination_detected': False,
            'severity': 'ERROR',
            'detected_keywords': [],
            'missing_keywords': [],
            'timestamp': datetime.now().isoformat(),
            'status': 'AUDIT_FAILED_TO_IMPORT',
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Audit execution failed: {e}")
        return {
            'sync_score': 0.0,
            'hallucination_detected': False,
            'severity': 'ERROR',
            'detected_keywords': [],
            'missing_keywords': [],
            'timestamp': datetime.now().isoformat(),
            'status': 'AUDIT_EXECUTION_FAILED',
            'error': str(e)
        }


def safe_audit_multimodal_sync_tool(image_path: str, prompt: str, 
                                 threshold: float = 65.0,
                                 governor_check: Optional[GovernorIntegration] = None) -> str:
    """Tool wrapper that returns a JSON string."""
    result = safe_audit_multimodal_sync(image_path, prompt, threshold, governor_check)
    return json.dumps(result, indent=2)


def create_governor_aware_hook() -> Callable:
    """
    Create a hook function that can be used by the Governor system.
    
    This function returns a hook that can be registered with the Governor
    to monitor status changes and take appropriate action.
    """
    governor_integration = GovernorIntegration()
    
    def governor_status_hook(status: str, **kwargs) -> Dict[str, Any]:
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
            logger.info(f"Governor status changed to: {status}")
            print(f"📊 Governor status updated: {status}")
            
            # Take action based on status
            if status == "CRITICAL":
                print("🚨 Governor reports CRITICAL status - heavy operations blocked")
            elif status == "WARNING":
                print("⚠️  Governor reports WARNING status - proceed with caution")
            elif status == "NORMAL":
                print("✅ Governor reports NORMAL status - operations safe")
            
            return {
                'status': 'hook_executed',
                'new_governor_status': status,
                'timestamp': datetime.now().isoformat(),
                'action_taken': 'status_updated'
            }
            
        except Exception as e:
            logger.error(f"Governor status hook failed: {e}")
            return {
                'status': 'hook_failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    return governor_status_hook


# Export the main functions for use by the extension system
__all__ = [
    'safe_audit_multimodal_sync',
    'safe_audit_multimodal_sync_tool',
    'GovernorIntegration', 
    'GovernorStatus',
    'create_governor_aware_hook'
]