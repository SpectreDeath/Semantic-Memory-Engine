"""
Governor Integration for Statistical Watermark Decoder

Handles integration with the Governor system to ensure watermark detection
only runs when CPU isn't already pegged by Ghost-Trap's persistence scans.
"""

import logging
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime

# Configure logging for governor integration
logger = logging.getLogger('stetho_scan.governor_integration')
logger.setLevel(logging.INFO)

# Create file handler for governor integration events
governor_handler = logging.FileHandler('stetho_governor_integration_events.log')
governor_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
governor_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(governor_handler)


class GovernorStatus(Enum):
    """Governor status levels."""
    NORMAL = "NORMAL"      # Green - Safe to run watermark detection
    WARNING = "WARNING"    # Yellow - Caution, may have resource constraints
    CRITICAL = "CRITICAL"  # Red - High resource usage, avoid heavy operations
    UNKNOWN = "UNKNOWN"    # Status unknown


class CPUUsageLevel(Enum):
    """CPU usage levels for resource monitoring."""
    LOW = "LOW"           # CPU usage < 50%
    MEDIUM = "MEDIUM"     # CPU usage 50-80%
    HIGH = "HIGH"         # CPU usage > 80%
    UNKNOWN = "UNKNOWN"


class StethoGovernorIntegration:
    """Handles integration with the Governor system for safe watermark detection."""
    
    def __init__(self):
        self._governor_status = GovernorStatus.UNKNOWN
        self._cpu_usage_level = CPUUsageLevel.UNKNOWN
        self._last_status_check = None
        self._detection_count = 0
        self._total_detection_time = 0.0
        
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
    
    def get_cpu_usage_level(self) -> CPUUsageLevel:
        """
        Get current CPU usage level.
        
        This method should be implemented to query actual CPU usage.
        For now, it returns a mock status or can be overridden by subclasses.
        """
        # TODO: Implement actual CPU usage monitoring
        # This is a placeholder that should be replaced with actual CPU monitoring
        
        try:
            # Try to import and query CPU usage
            # This is a mock implementation - replace with actual CPU monitoring
            import psutil
            
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent < 50:
                return CPUUsageLevel.LOW
            elif cpu_percent < 80:
                return CPUUsageLevel.MEDIUM
            else:
                return CPUUsageLevel.HIGH
                
        except ImportError:
            # psutil not available, assume MEDIUM for testing
            logger.warning("psutil not available, assuming MEDIUM CPU usage")
            return CPUUsageLevel.MEDIUM
        except Exception as e:
            logger.error(f"Failed to get CPU usage: {e}")
            return CPUUsageLevel.UNKNOWN
    
    def is_safe_to_detect(self) -> bool:
        """
        Check if it's safe to run watermark detection based on Governor status and CPU usage.
        
        Returns:
            True if safe to detect (Governor status is NORMAL and CPU usage is LOW/MEDIUM), False otherwise.
        """
        governor_status = self.get_governor_status()
        cpu_usage = self.get_cpu_usage_level()
        
        self._governor_status = governor_status
        self._cpu_usage_level = cpu_usage
        self._last_status_check = datetime.now()
        
        # Safe conditions: Governor NORMAL and CPU usage not HIGH
        is_safe = (governor_status == GovernorStatus.NORMAL and 
                  cpu_usage in [CPUUsageLevel.LOW, CPUUsageLevel.MEDIUM])
        
        if is_safe:
            logger.info(f"Safe to detect: Governor={governor_status.value}, CPU={cpu_usage.value}")
        else:
            logger.warning(f"Detection blocked: Governor={governor_status.value}, CPU={cpu_usage.value}")
        
        return is_safe
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get current status information."""
        return {
            'governor_status': self._governor_status.value,
            'cpu_usage_level': self._cpu_usage_level.value,
            'last_status_check': self._last_status_check.isoformat() if self._last_status_check else None,
            'detection_count': self._detection_count,
            'total_detection_time': self._total_detection_time,
            'is_safe_to_detect': self.is_safe_to_detect()
        }
    
    def record_detection(self, detection_time: float):
        """Record detection execution for monitoring."""
        self._detection_count += 1
        self._total_detection_time += detection_time
        
        logger.info(f"Detection completed in {detection_time:.2f}s. Total detections: {self._detection_count}")


def safe_detect_watermark_pulse(text: str, 
                               governor_check: Optional[StethoGovernorIntegration] = None) -> Dict[str, Any]:
    """
    Safe wrapper for detect_watermark_pulse that checks Governor status and CPU usage.
    
    Args:
        text: Text to analyze for watermarks.
        governor_check: StethoGovernorIntegration instance to use for status checking.
        
    Returns:
        Dictionary containing detection results or error information.
    """
    if governor_check is None:
        governor_check = StethoGovernorIntegration()
    
    # Check if it's safe to run the detection
    if not governor_check.is_safe_to_detect():
        status_info = governor_check.get_status_info()
        
        warning_message = (
            f"[DETECTION BLOCKED - GOVERNOR: {status_info['governor_status']}, "
            f"CPU: {status_info['cpu_usage_level']}] Watermark detection skipped for safety."
        )
        
        logger.warning(warning_message)
        print(f"⚠️  {warning_message}")
        
        return {
            'has_invisible_markers': False,
            'z_score_analysis': {},
            'provider_signature': None,
            'confidence_score': 0.0,
            'detected_markers': [],
            'timestamp': datetime.now().isoformat(),
            'status': 'DETECTION_BLOCKED_DUE_TO_RESOURCE_CONSTRAINTS',
            'governor_status': status_info['governor_status'],
            'cpu_usage_level': status_info['cpu_usage_level'],
            'reason': 'Governor status not NORMAL or CPU usage too high'
        }
    
    # Import the actual detection function
    try:
        from .statistical_watermark_decoder import detect_watermark_pulse
        import time
        
        # Record detection start time
        start_time = time.time()
        
        # Run the actual detection
        result = detect_watermark_pulse(text)
        
        # Record detection completion
        detection_time = time.time() - start_time
        governor_check.record_detection(detection_time)
        
        return result
        
    except ImportError as e:
        logger.error(f"Failed to import detection function: {e}")
        return {
            'has_invisible_markers': False,
            'z_score_analysis': {},
            'provider_signature': None,
            'confidence_score': 0.0,
            'detected_markers': [],
            'timestamp': datetime.now().isoformat(),
            'status': 'DETECTION_FAILED_TO_IMPORT',
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Detection execution failed: {e}")
        return {
            'has_invisible_markers': False,
            'z_score_analysis': {},
            'provider_signature': None,
            'confidence_score': 0.0,
            'detected_markers': [],
            'timestamp': datetime.now().isoformat(),
            'status': 'DETECTION_EXECUTION_FAILED',
            'error': str(e)
        }


def create_stetho_governor_hook() -> Callable:
    """
    Create a hook function that can be used by the Governor system.
    
    This function returns a hook that can be registered with the Governor
    to monitor status changes and take appropriate action.
    """
    governor_integration = StethoGovernorIntegration()
    
    def stetho_governor_status_hook(status: str, **kwargs) -> Dict[str, Any]:
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
            logger.info(f"Stetho Governor status changed to: {status}")
            print(f"📊 Stetho Governor status updated: {status}")
            
            # Take action based on status
            if status == "CRITICAL":
                print("🚨 Stetho Governor reports CRITICAL status - watermark detection blocked")
            elif status == "WARNING":
                print("⚠️  Stetho Governor reports WARNING status - proceed with caution")
            elif status == "NORMAL":
                print("✅ Stetho Governor reports NORMAL status - watermark detection safe")
            
            return {
                'status': 'hook_executed',
                'new_governor_status': status,
                'timestamp': datetime.now().isoformat(),
                'action_taken': 'status_updated'
            }
            
        except Exception as e:
            logger.error(f"Stetho Governor status hook failed: {e}")
            return {
                'status': 'hook_failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    return stetho_governor_status_hook


# Export the main functions for use by the extension system
__all__ = [
    'safe_detect_watermark_pulse', 
    'StethoGovernorIntegration', 
    'GovernorStatus',
    'CPUUsageLevel',
    'create_stetho_governor_hook'
]