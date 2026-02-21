"""
Governor Client - System Resource Monitoring Integration

Provides real-time system monitoring for SME extensions including:
- CPU usage tracking
- GPU memory and utilization
- RAM consumption
- Disk I/O statistics
- Process monitoring

This replaces placeholder implementations in extensions.
"""

import os
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger("lawnmower.governor")

# Try to import GPU monitoring - gracefully fallback if unavailable
try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    logger.warning("pynvml not available - GPU monitoring disabled")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available - system monitoring disabled")


@dataclass
class SystemSnapshot:
    """A point-in-time snapshot of system resources."""
    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0.0
    cpu_count: int = 0
    ram_total_mb: float = 0.0
    ram_used_mb: float = 0.0
    ram_percent: float = 0.0
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0
    gpu_available: bool = False
    gpu_count: int = 0
    gpu_memory_total_mb: float = 0.0
    gpu_memory_used_mb: float = 0.0
    gpu_utilization: float = 0.0
    gpu_temperature: float = 0.0


class Governor:
    """
    System resource governor providing real-time monitoring.
    
    Singleton pattern ensures consistent monitoring across all extensions.
    """
    
    _instance: Optional['Governor'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._nvml_initialized = False
        self._last_disk_io = None
        self._last_check_time = None
        self._snapshot_history: List[SystemSnapshot] = []
        self._max_history = 100  # Keep last 100 snapshots
        
        # Initialize NVML for GPU monitoring
        if NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self._nvml_initialized = True
                self._gpu_count = pynvml.nvmlDeviceGetCount()
                logger.info(f"Governor: NVML initialized with {self._gpu_count} GPU(s)")
            except Exception as e:
                logger.warning(f"Governor: NVML init failed: {e}")
                self._gpu_count = 0
        else:
            self._gpu_count = 0

    def get_snapshot(self) -> SystemSnapshot:
        """Get current system resource snapshot."""
        snap = SystemSnapshot()
        
        if not PSUTIL_AVAILABLE:
            return snap
        
        # CPU metrics
        snap.cpu_percent = psutil.cpu_percent(interval=0.1)
        snap.cpu_count = psutil.cpu_count()
        
        # RAM metrics
        mem = psutil.virtual_memory()
        snap.ram_total_mb = mem.total / (1024 * 1024)
        snap.ram_used_mb = mem.used / (1024 * 1024)
        snap.ram_percent = mem.percent
        
        # Disk I/O
        try:
            disk_io = psutil.disk_io_counters()
            if self._last_disk_io and self._last_check_time:
                time_delta = time.time() - self._last_check_time
                snap.disk_read_mb = (disk_io.read_bytes - self._last_disk_io.read_bytes) / (1024 * 1024) / time_delta
                snap.disk_write_mb = (disk_io.write_bytes - self._last_disk_io.write_bytes) / (1024 * 1024) / time_delta
            self._last_disk_io = disk_io
            self._last_check_time = time.time()
        except Exception as e:
            logger.debug(f"Governor: Disk I/O error: {e}")
        
        # GPU metrics
        snap.gpu_available = self._nvml_initialized
        snap.gpu_count = self._gpu_count
        
        if self._nvml_initialized and self._gpu_count > 0:
            try:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                
                # Memory
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                snap.gpu_memory_total_mb = mem_info.total / (1024 * 1024)
                snap.gpu_memory_used_mb = mem_info.used / (1024 * 1024)
                
                # Utilization
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                snap.gpu_utilization = util.gpu
                
                # Temperature
                try:
                    snap.gpu_temperature = pynvml.nvmlDeviceGetTemperature(
                        handle, pynvml.NVML_TEMPERATURE_GPU
                    )
                except:
                    pass  # Temperature may not be supported
                    
            except Exception as e:
                logger.debug(f"Governor: GPU query error: {e}")
        
        # Store in history
        self._snapshot_history.append(snap)
        if len(self._snapshot_history) > self._max_history:
            self._snapshot_history.pop(0)
        
        return snap

    def get_status(self) -> Dict[str, Any]:
        """Get formatted status for API response."""
        snap = self.get_snapshot()
        
        return {
            "governor": "active",
            "cpu": {
                "percent": round(snap.cpu_percent, 1),
                "count": snap.cpu_count
            },
            "ram": {
                "total_mb": round(snap.ram_total_mb, 0),
                "used_mb": round(snap.ram_used_mb, 0),
                "percent": round(snap.ram_percent, 1)
            },
            "disk": {
                "read_mb_s": round(snap.disk_read_mb, 2),
                "write_mb_s": round(snap.disk_write_mb, 2)
            },
            "gpu": {
                "available": snap.gpu_available,
                "count": snap.gpu_count,
                "memory_total_mb": round(snap.gpu_memory_total_mb, 0),
                "memory_used_mb": round(snap.gpu_memory_used_mb, 0),
                "utilization_percent": round(snap.gpu_utilization, 1),
                "temperature_c": round(snap.gpu_temperature, 0) if snap.gpu_temperature > 0 else None
            }
        }

    def check_limits(
        self,
        cpu_threshold: float = 80.0,
        ram_threshold: float = 80.0,
        gpu_threshold: float = 90.0
    ) -> Dict[str, bool]:
        """
        Check if any resource exceeds threshold.
        
        Returns dict with 'cpu', 'ram', 'gpu' boolean flags.
        """
        snap = self.get_snapshot()
        
        return {
            "cpu": snap.cpu_percent >= cpu_threshold,
            "ram": snap.ram_percent >= ram_threshold,
            "gpu": snap.gpu_utilization >= gpu_threshold if snap.gpu_available else False
        }

    def get_history(self, limit: int = 10) -> List[SystemSnapshot]:
        """Get recent system snapshots."""
        return self._snapshot_history[-limit:]

    def shutdown(self):
        """Clean up resources."""
        if self._nvml_initialized:
            try:
                pynvml.nvmlShutdown()
                logger.info("Governor: NVML shutdown complete")
            except Exception as e:
                logger.warning(f"Governor: NVML shutdown error: {e}")


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------
_governor: Optional[Governor] = None
_governor_lock = threading.Lock()


def get_governor() -> Governor:
    """Get the Governor singleton."""
    global _governor
    with _governor_lock:
        if _governor is None:
            _governor = Governor()
    return _governor
