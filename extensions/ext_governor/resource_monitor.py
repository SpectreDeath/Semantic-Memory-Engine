import asyncio
import threading
import time
import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("LawnmowerMan.Governor.ResourceMonitor")

class VRAMState(Enum):
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ResourceStatus:
    """Resource status information."""
    vram_usage_gb: float
    vram_threshold_gb: float
    vram_state: VRAMState
    should_delay: bool
    timestamp: datetime
    cpu_usage_percent: float = 0.0
    memory_usage_gb: float = 0.0

class VSCodeStatusBarManager:
    """
    Manages VS Code status bar integration for resource monitoring.
    This can be used by the ConnectLMStudio plugin to display resource usage.
    """
    
    def __init__(self):
        self.status_bar_items = {}
        self.update_callbacks = []
        self._lock = threading.Lock()
        
    def register_status_bar_update(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback to update VS Code status bar."""
        with self._lock:
            self.update_callbacks.append(callback)
    
    def unregister_status_bar_update(self, callback: Callable[[Dict[str, Any]], None]):
        """Unregister a status bar update callback."""
        with self._lock:
            if callback in self.update_callbacks:
                self.update_callbacks.remove(callback)
    
    def update_status_bar(self, status: ResourceStatus):
        """Update VS Code status bar with current resource status."""
        status_data = {
            "vram_usage_gb": round(status.vram_usage_gb, 2),
            "vram_threshold_gb": status.vram_threshold_gb,
            "vram_state": status.vram_state.value,
            "should_delay": status.should_delay,
            "cpu_usage_percent": round(status.cpu_usage_percent, 1),
            "memory_usage_gb": round(status.memory_usage_gb, 2),
            "timestamp": status.timestamp.isoformat()
        }
        
        # Format status bar text
        status_text = self._format_status_text(status)
        
        # Notify all registered callbacks
        with self._lock:
            for callback in self.update_callbacks:
                try:
                    callback(status_data, status_text)
                except Exception as e:
                    logger.error(f"Error updating status bar: {e}")
    
    def _format_status_text(self, status: ResourceStatus) -> str:
        """Format resource status for display in status bar."""
        vram_icon = "🟢" if status.vram_state == VRAMState.NORMAL else "🟡" if status.vram_state == VRAMState.HIGH else "🔴"
        delay_icon = "⏸️" if status.should_delay else "▶️"
        
        return f"{vram_icon} VRAM: {status.vram_usage_gb:.1f}GB | {delay_icon} {status.vram_state.value.upper()}"

class EnhancedResourceMonitor:
    """
    Enhanced resource monitor with VS Code status bar integration.
    """
    
    def __init__(self, vram_threshold_gb: float = 5.8, status_bar_manager: Optional[VSCodeStatusBarManager] = None):
        self.vram_threshold_gb = vram_threshold_gb
        self.status_bar_manager = status_bar_manager or VSCodeStatusBarManager()
        self.monitoring = False
        self.monitor_thread = None
        self.current_status: Optional[ResourceStatus] = None
        self._lock = threading.Lock()
        
        # Resource history for trend analysis
        self.resource_history = []
        self.max_history_size = 100
        
    def start_monitoring(self):
        """Start background resource monitoring."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info(f"[Governor] Enhanced resource monitoring started (VRAM threshold: {self.vram_threshold_gb}GB)")
    
    def stop_monitoring(self):
        """Stop background resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("[Governor] Enhanced resource monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            try:
                # Get current resource status
                status = self.get_current_status()
                
                # Update internal state
                with self._lock:
                    self.current_status = status
                    self.resource_history.append(status)
                    if len(self.resource_history) > self.max_history_size:
                        self.resource_history.pop(0)
                
                # Update VS Code status bar
                if self.status_bar_manager:
                    self.status_bar_manager.update_status_bar(status)
                
                # Log critical resource usage
                if status.vram_state == VRAMState.CRITICAL:
                    logger.warning(f"[Governor] VRAM usage critical: {status.vram_usage_gb:.2f}GB > {self.vram_threshold_gb}GB")
                elif status.vram_state == VRAMState.HIGH:
                    logger.info(f"[Governor] VRAM usage high: {status.vram_usage_gb:.2f}GB")
                
                time.sleep(2.0)  # Monitor every 2 seconds
                
            except Exception as e:
                logger.error(f"[Governor] Error in enhanced monitoring loop: {e}")
                time.sleep(3.0)
    
    def get_current_status(self) -> ResourceStatus:
        """Get current resource status."""
        try:
            # Try to use GPU if available
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use first GPU
                    vram_usage_gb = gpu.memoryUsed / 1024.0
                else:
                    # Fallback to CPU memory if no GPU
                    vram_usage_gb = psutil.virtual_memory().used / (1024**3)
            except ImportError:
                # GPUtil not available, use CPU memory
                vram_usage_gb = psutil.virtual_memory().used / (1024**3)
        except:
            vram_usage_gb = 0.0
        
        try:
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_usage_gb = psutil.virtual_memory().used / (1024**3)
        except:
            cpu_usage = 0.0
            memory_usage_gb = 0.0
        
        # Determine VRAM state
        if vram_usage_gb >= self.vram_threshold_gb:
            vram_state = VRAMState.CRITICAL
        elif vram_usage_gb >= (self.vram_threshold_gb * 0.8):
            vram_state = VRAMState.HIGH
        else:
            vram_state = VRAMState.NORMAL
        
        should_delay = vram_state in [VRAMState.HIGH, VRAMState.CRITICAL]
        
        return ResourceStatus(
            vram_usage_gb=vram_usage_gb,
            vram_threshold_gb=self.vram_threshold_gb,
            vram_state=vram_state,
            should_delay=should_delay,
            timestamp=datetime.now(),
            cpu_usage_percent=cpu_usage,
            memory_usage_gb=memory_usage_gb
        )
    
    def get_vram_state(self) -> VRAMState:
        """Get current VRAM state."""
        with self._lock:
            if self.current_status:
                return self.current_status.vram_state
            else:
                return VRAMState.NORMAL
    
    def should_delay_ingestion(self) -> bool:
        """Check if ingestion should be delayed due to high resource usage."""
        with self._lock:
            if self.current_status:
                return self.current_status.should_delay
            else:
                return False
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get current resource status information."""
        with self._lock:
            if self.current_status:
                status = self.current_status
                return {
                    "vram_usage_gb": round(status.vram_usage_gb, 2),
                    "vram_threshold_gb": status.vram_threshold_gb,
                    "vram_state": status.vram_state.value,
                    "should_delay": status.should_delay,
                    "cpu_usage_percent": round(status.cpu_usage_percent, 1),
                    "memory_usage_gb": round(status.memory_usage_gb, 2),
                    "timestamp": status.timestamp.isoformat()
                }
            else:
                return {
                    "vram_usage_gb": 0.0,
                    "vram_threshold_gb": self.vram_threshold_gb,
                    "vram_state": VRAMState.NORMAL.value,
                    "should_delay": False,
                    "cpu_usage_percent": 0.0,
                    "memory_usage_gb": 0.0,
                    "timestamp": datetime.now().isoformat()
                }
    
    def get_resource_trends(self) -> Dict[str, Any]:
        """Get resource usage trends from history."""
        with self._lock:
            if not self.resource_history:
                return {"error": "No history available"}
            
            # Calculate trends
            vram_values = [r.vram_usage_gb for r in self.resource_history]
            cpu_values = [r.cpu_usage_percent for r in self.resource_history]
            memory_values = [r.memory_usage_gb for r in self.resource_history]
            
            return {
                "vram_trend": {
                    "current": vram_values[-1],
                    "min": min(vram_values),
                    "max": max(vram_values),
                    "avg": sum(vram_values) / len(vram_values),
                    "history_count": len(vram_values)
                },
                "cpu_trend": {
                    "current": cpu_values[-1],
                    "min": min(cpu_values),
                    "max": max(cpu_values),
                    "avg": sum(cpu_values) / len(cpu_values),
                    "history_count": len(cpu_values)
                },
                "memory_trend": {
                    "current": memory_values[-1],
                    "min": min(memory_values),
                    "max": max(memory_values),
                    "avg": sum(memory_values) / len(memory_values),
                    "history_count": len(memory_values)
                }
            }

# Global status bar manager instance
global_status_bar_manager = VSCodeStatusBarManager()

def get_status_bar_manager() -> VSCodeStatusBarManager:
    """Get the global status bar manager instance."""
    return global_status_bar_manager

def create_enhanced_monitor(vram_threshold_gb: float = 5.8) -> EnhancedResourceMonitor:
    """Create an enhanced resource monitor with status bar integration."""
    return EnhancedResourceMonitor(vram_threshold_gb, global_status_bar_manager)