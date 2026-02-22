import os
import json
import logging
import asyncio
import threading
import time
import psutil
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from collections import deque
from dataclasses import dataclass
from enum import Enum

# NexusAPI: use self.nexus.nexus and self.nexus.get_hsm() — no gateway imports
from src.core.plugin_base import BasePlugin
from src.utils.error_handling import ErrorHandler, create_error_response, OperationContext
from src.utils.performance import get_performance_monitor, cache_result, LRUCache

logger = logging.getLogger("LawnmowerMan.Governor")

# Try to import pynvml, fallback to CPU monitoring if not available
try:
    import pynvml
    HAS_NVML = True
except ImportError:
    HAS_NVML = False
    logger.warning("[Governor] pynvml not available, falling back to CPU memory monitoring")

class VRAMState(Enum):
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class IngestionTask:
    """Represents a task in the ingestion pipeline."""
    task_id: str
    raw_data: str
    metadata: Dict[str, Any]
    timestamp: datetime
    status: str = "pending"  # pending, running, completed, delayed

class ResourceMonitor:
    """Monitors system resources, particularly VRAM usage."""
    
    def __init__(self, vram_threshold_gb: float = 5.8):
        self.vram_threshold_gb = vram_threshold_gb
        self.monitoring = False
        self.monitor_thread = None
        self.current_vram_usage = 0.0
        self.vram_history = deque(maxlen=100)  # Keep last 100 readings
        self._lock = threading.Lock()
        
    def start_monitoring(self):
        """Start background VRAM monitoring."""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            if HAS_NVML:
                try:
                    pynvml.nvmlInit()
                except Exception as e:
                    logger.warning(f"[Governor] NVML init failed: {e}")
                
        logger.info(f"[Governor] Resource monitoring started (VRAM threshold: {self.vram_threshold_gb}GB)")
    
    def stop_monitoring(self):
        """Stop background VRAM monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("[Governor] Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring:
            try:
                vram_usage = self.get_vram_usage_gb()
                with self._lock:
                    self.current_vram_usage = vram_usage
                    self.vram_history.append({
                        'timestamp': datetime.now(),
                        'vram_usage': vram_usage
                    })
                
                # Log significant changes
                if vram_usage > self.vram_threshold_gb:
                    logger.warning(f"[Governor] VRAM usage critical: {vram_usage:.2f}GB > {self.vram_threshold_gb}GB")
                
                time.sleep(1.0)  # Monitor every second
                
            except Exception as e:
                logger.error(f"[Governor] Error in monitoring loop: {e}")
                time.sleep(2.0)
    
    def get_vram_usage_gb(self) -> float:
        """Get current VRAM usage in GB."""
        try:
            if HAS_NVML:
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    return info.used / (1024 * 1024 * 1024)  # Convert bytes to GB
                except Exception as e:
                    logger.debug(f"[Governor] GPU query failed: {e}")
            
            # Fallback to CPU memory
            return psutil.virtual_memory().used / (1024**3)
        except Exception as e:
            logger.warning(f"[Governor] Could not get VRAM usage: {e}")
            return 0.0
    
    def get_vram_state(self) -> VRAMState:
        """Get current VRAM state based on usage."""
        with self._lock:
            current_usage = self.current_vram_usage
        
        if current_usage >= self.vram_threshold_gb:
            return VRAMState.CRITICAL
        elif current_usage >= (self.vram_threshold_gb * 0.8):
            return VRAMState.HIGH
        else:
            return VRAMState.NORMAL
    
    def should_delay_ingestion(self) -> bool:
        """Check if ingestion should be delayed due to high VRAM usage."""
        return self.get_vram_state() in [VRAMState.HIGH, VRAMState.CRITICAL]
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get current resource status information."""
        with self._lock:
            current_usage = self.current_vram_usage
            recent_history = list(self.vram_history)[-10:] if self.vram_history else []
        
        return {
            "vram_usage_gb": round(current_usage, 2),
            "vram_threshold_gb": self.vram_threshold_gb,
            "vram_state": self.get_vram_state().value,
            "should_delay": self.should_delay_ingestion(),
            "recent_readings": [
                {
                    "timestamp": h['timestamp'].isoformat(),
                    "vram_usage": round(h['vram_usage'], 2)
                }
                for h in recent_history
            ]
        }

class Governor(BasePlugin):
    """
    Governor v1.0
    Manages on_ingestion pipeline execution with resource monitoring and VRAM usage control.
    Wraps SDA, APB, and LogicAuditor in a serial queue with resource monitoring.
    """
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        
        # Configuration
        self.vram_threshold_gb = 5.8
        self.cache_clear_delay_seconds = 30
        self.max_queue_size = 100
        
        # Components to manage
        self.sda_plugin = None
        self.apb_plugin = None
        self.logic_auditor_plugin = None
        
        # Queue management
        self.ingestion_queue = asyncio.Queue(maxsize=self.max_queue_size)
        self.processing_task = None
        self.shutdown_event = asyncio.Event()
        
        # Resource monitoring
        self.resource_monitor = ResourceMonitor(self.vram_threshold_gb)
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "delayed_tasks": 0,
            "failed_tasks": 0,
            "avg_processing_time": 0.0
        }
        
        logger.info(f"[{self.plugin_id}] Governor initialized with VRAM threshold: {self.vram_threshold_gb}GB")

    async def on_startup(self):
        """
        Initialize the Governor and start monitoring.
        """
        try:
            # Initialize resource monitoring
            self.resource_monitor.start_monitoring()
            
            # Start the processing task
            self.processing_task = asyncio.create_task(self._processing_loop())
            
            # Initialize database table for governor statistics
            sql = """
                CREATE TABLE IF NOT EXISTS nexus_governor_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    vram_usage_gb REAL,
                    vram_state TEXT,
                    queue_size INTEGER,
                    total_tasks INTEGER,
                    completed_tasks INTEGER,
                    delayed_tasks INTEGER,
                    failed_tasks INTEGER
                )
            """
            self.nexus.nexus.execute(sql)
            
            logger.info(f"[{self.plugin_id}] Governor started successfully")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to start Governor: {e}")

    async def on_shutdown(self):
        """
        Clean shutdown of the Governor.
        """
        try:
            self.shutdown_event.set()
            
            if self.processing_task:
                await self.processing_task
            
            self.resource_monitor.stop_monitoring()
            
            logger.info(f"[{self.plugin_id}] Governor shutdown complete")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error during shutdown: {e}")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Governor-managed on_ingestion pipeline.
        Wraps SDA, APB, and LogicAuditor in a serial queue with resource monitoring.
        """
        task_id = f"task_{int(time.time() * 1000)}"
        
        # Create ingestion task
        task = IngestionTask(
            task_id=task_id,
            raw_data=raw_data,
            metadata=metadata,
            timestamp=datetime.now()
        )
        
        try:
            # Add to queue (will block if queue is full)
            await self.ingestion_queue.put(task)
            self.stats["total_tasks"] += 1
            
            logger.info(f"[{self.plugin_id}] Task {task_id} queued (Queue size: {self.ingestion_queue.qsize()})")
            
            # Return immediate response indicating task is queued
            return {
                "status": "queued",
                "task_id": task_id,
                "queue_position": self.ingestion_queue.qsize(),
                "resource_status": self.resource_monitor.get_status_info()
            }
            
        except asyncio.QueueFull:
            logger.warning(f"[{self.plugin_id}] Queue full, rejecting task {task_id}")
            return {
                "status": "rejected",
                "reason": "queue_full",
                "queue_size": self.ingestion_queue.qsize()
            }
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error queuing task {task_id}: {e}")
            return {
                "status": "error",
                "reason": str(e)
            }

    def get_tools(self) -> list:
        return [
            self.get_resource_status,
            self.get_governor_stats,
            self.get_queue_status,
            self.set_vram_threshold,
            self.clear_queue
        ]

    async def get_resource_status(self) -> str:
        """Get current resource status including VRAM usage."""
        try:
            status = self.resource_monitor.get_status_info()
            return json.dumps(status, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get resource status: {str(e)}"})

    async def get_governor_stats(self) -> str:
        """Get Governor statistics."""
        try:
            stats = {
                "total_tasks": self.stats["total_tasks"],
                "completed_tasks": self.stats["completed_tasks"],
                "delayed_tasks": self.stats["delayed_tasks"],
                "failed_tasks": self.stats["failed_tasks"],
                "avg_processing_time": self.stats["avg_processing_time"],
                "queue_size": self.ingestion_queue.qsize(),
                "queue_max_size": self.max_queue_size,
                "resource_monitoring": self.resource_monitor.monitoring
            }
            return json.dumps(stats, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get governor stats: {str(e)}"})

    async def get_queue_status(self) -> str:
        """Get current queue status."""
        try:
            queue_info = {
                "current_size": self.ingestion_queue.qsize(),
                "max_size": self.max_queue_size,
                "is_full": self.ingestion_queue.full(),
                "is_empty": self.ingestion_queue.empty()
            }
            return json.dumps(queue_info, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to get queue status: {str(e)}"})

    async def set_vram_threshold(self, threshold_gb: float) -> str:
        """Set VRAM threshold for delaying ingestion."""
        try:
            val = float(threshold_gb)
            self.vram_threshold_gb = val
            self.resource_monitor.vram_threshold_gb = val
            return json.dumps({
                "status": "success",
                "new_threshold_gb": val,
                "message": f"VRAM threshold set to {val}GB"
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to set VRAM threshold: {str(e)}"})

    async def clear_queue(self) -> str:
        """Clear the ingestion queue."""
        try:
            # Clear queue by getting all items
            cleared_count = 0
            while not self.ingestion_queue.empty():
                try:
                    self.ingestion_queue.get_nowait()
                    cleared_count += 1
                except asyncio.QueueEmpty:
                    break
            
            return json.dumps({
                "status": "success",
                "cleared_tasks": cleared_count,
                "message": f"Cleared {cleared_count} tasks from queue"
            }, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to clear queue: {str(e)}"})

    async def _processing_loop(self):
        """Main processing loop that handles tasks from the queue."""
        while not self.shutdown_event.is_set():
            try:
                # Check if we should process the next task
                if self.resource_monitor.should_delay_ingestion():
                    self.stats["delayed_tasks"] += 1
                    delay_seconds = self.cache_clear_delay_seconds
                    logger.info(f"[{self.plugin_id}] VRAM usage high, delaying next task for {delay_seconds}s")
                    
                    # Wait for resource levels to drop or timeout
                    await asyncio.sleep(delay_seconds)
                    continue
                
                # Get next task from queue (with timeout)
                try:
                    task = await asyncio.wait_for(
                        self.ingestion_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue  # No tasks available, continue loop
                
                # Process the task
                await self._process_task(task)
                
            except Exception as e:
                logger.error(f"[{self.plugin_id}] Error in processing loop: {e}")
                await asyncio.sleep(1.0)

    async def _process_task(self, task: IngestionTask):
        """Process a single ingestion task through the pipeline."""
        start_time = time.time()
        task.status = "running"
        
        try:
            logger.info(f"[{self.plugin_id}] Processing task {task.task_id}")
            
            # Store task start in database
            await self._store_task_start(task)
            
            # Execute the pipeline: SDA -> APB -> LogicAuditor
            results = await self._execute_pipeline(task.raw_data, task.metadata)
            
            # Mark as completed
            task.status = "completed"
            self.stats["completed_tasks"] += 1
            
            # Calculate processing time
            processing_time = time.time() - start_time
            self._update_avg_processing_time(processing_time)
            
            # Store completion in database
            await self._store_task_completion(task, results, processing_time)
            
            logger.info(f"[{self.plugin_id}] Task {task.task_id} completed in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to process task {task.task_id}: {e}")
            task.status = "failed"
            self.stats["failed_tasks"] += 1
            
            # Store failure in database
            await self._store_task_failure(task, str(e))

    async def _execute_pipeline(self, raw_data: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the SDA -> APB -> LogicAuditor pipeline."""
        pipeline_results = {
            "sda_result": None,
            "apb_result": None,
            "logic_auditor_result": None,
            "pipeline_status": "completed"
        }
        
        try:
            # 1. Execute SDA (Semantic Deception Analysis)
            if self.sda_plugin and hasattr(self.sda_plugin, 'on_ingestion'):
                sda_result = await self.sda_plugin.on_ingestion(raw_data, metadata)
                pipeline_results["sda_result"] = sda_result
                logger.debug(f"[{self.plugin_id}] SDA completed: {sda_result.get('status', 'unknown')}")
            
            # 2. Execute APB (Adversarial Pattern Breaker)
            if self.apb_plugin and hasattr(self.apb_plugin, 'on_ingestion'):
                apb_result = await self.apb_plugin.on_ingestion(raw_data, metadata)
                pipeline_results["apb_result"] = apb_result
                logger.debug(f"[{self.plugin_id}] APB completed: {apb_result.get('status', 'unknown')}")
            
            # 3. Execute LogicAuditor
            if self.logic_auditor_plugin and hasattr(self.logic_auditor_plugin, 'on_ingestion'):
                logic_result = await self.logic_auditor_plugin.on_ingestion(raw_data, metadata)
                pipeline_results["logic_auditor_result"] = logic_result
                logger.debug(f"[{self.plugin_id}] LogicAuditor completed: {logic_result.get('status', 'unknown')}")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Pipeline execution failed: {e}")
            pipeline_results["pipeline_status"] = "failed"
            pipeline_results["error"] = str(e)
        
        return pipeline_results

    async def _store_task_start(self, task: IngestionTask):
        """Store task start information in database."""
        try:
            sql = """
                INSERT INTO nexus_governor_stats 
                (timestamp, vram_usage_gb, vram_state, queue_size, total_tasks, completed_tasks, delayed_tasks, failed_tasks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            status_info = self.resource_monitor.get_status_info()
            
            self.nexus.nexus.execute(sql, (
                task.timestamp.isoformat(),
                status_info["vram_usage_gb"],
                status_info["vram_state"],
                self.ingestion_queue.qsize(),
                self.stats["total_tasks"],
                self.stats["completed_tasks"],
                self.stats["delayed_tasks"],
                self.stats["failed_tasks"]
            ))
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to store task start: {e}")

    async def _store_task_completion(self, task: IngestionTask, results: Dict[str, Any], processing_time: float):
        """Store task completion information in database."""
        try:
            # Update the existing record with completion info
            sql = """
                UPDATE nexus_governor_stats 
                SET processing_time = ?, pipeline_results = ?
                WHERE timestamp = ?
            """
            
            self.nexus.nexus.execute(sql, (
                processing_time,
                json.dumps(results),
                task.timestamp.isoformat()
            ))
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to store task completion: {e}")

    async def _store_task_failure(self, task: IngestionTask, error: str):
        """Store task failure information in database."""
        try:
            sql = """
                UPDATE nexus_governor_stats 
                SET error_message = ?
                WHERE timestamp = ?
            """
            
            self.nexus.nexus.execute(sql, (
                error,
                task.timestamp.isoformat()
            ))
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to store task failure: {e}")

    def _update_avg_processing_time(self, new_time: float):
        """Update the average processing time."""
        current_avg = self.stats["avg_processing_time"]
        completed = self.stats["completed_tasks"]
        
        if completed == 1:
            self.stats["avg_processing_time"] = new_time
        else:
            # Weighted average: (old_avg * (n-1) + new_time) / n
            self.stats["avg_processing_time"] = ((current_avg * (completed - 1)) + new_time) / completed

    def register_plugins(self, sda_plugin=None, apb_plugin=None, logic_auditor_plugin=None):
        """Register the plugins to be managed by the Governor."""
        self.sda_plugin = sda_plugin
        self.apb_plugin = apb_plugin
        self.logic_auditor_plugin = logic_auditor_plugin
        logger.info(f"[{self.plugin_id}] Registered plugins: SDA={sda_plugin is not None}, APB={apb_plugin is not None}, LogicAuditor={logic_auditor_plugin is not None}")


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return a Governor instance."""
    return Governor(manifest, nexus_api)


def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return create_plugin(manifest, nexus_api)