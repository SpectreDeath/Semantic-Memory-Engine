import logging
from prometheus_client import start_http_server, Counter, Histogram, Gauge
import os

logger = logging.getLogger(__name__)

class MetricsManager:
    """
    Handles Prometheus metrics for the Lawnmower Man gateway.
    """
    
    def __init__(self, port: int = 8000):
        self.port = port
        self.enabled = os.environ.get("SME_METRICS_ENABLED", "true").lower() == "true"
        
        if self.enabled:
            # Defined metrics
            self.tool_calls_total = Counter(
                "lawnmower_tool_calls_total", 
                "Total number of MCP tool calls",
                ["tool_name", "category"]
            )
            
            self.tool_errors_total = Counter(
                "lawnmower_tool_errors_total", 
                "Total number of failed tool calls",
                ["tool_name", "error_type"]
            )
            
            self.tool_latency_seconds = Histogram(
                "lawnmower_tool_latency_seconds",
                "Tool execution latency in seconds",
                ["tool_name"]
            )
            
            self.active_sessions = Gauge(
                "lawnmower_active_sessions",
                "Number of currently active sessions"
            )
            
            self.system_health = Gauge(
                "lawnmower_system_health",
                "Overall system health status (1=healthy, 0=degraded, -1=down)"
            )

    def start(self):
        """Start the Prometheus metrics server."""
        if self.enabled:
            try:
                start_http_server(self.port)
                logger.info(f"Prometheus metrics exporter started on port {self.port}")
            except Exception as e:
                logger.error(f"Failed to start Prometheus server: {e}")
        else:
            logger.info("Prometheus metrics disabled via environment")

    def track_call(self, tool_name: str, category: str):
        if self.enabled:
            self.tool_calls_total.labels(tool_name=tool_name, category=category).inc()

    def track_error(self, tool_name: str, error_type: str):
        if self.enabled:
            self.tool_errors_total.labels(tool_name=tool_name, error_type=error_type).inc()

    def observe_latency(self, tool_name: str, seconds: float):
        if self.enabled:
            self.tool_latency_seconds.labels(tool_name=tool_name).observe(seconds)

    def set_active_sessions(self, count: int):
        if self.enabled:
            self.active_sessions.set(count)

    def set_health(self, status: str):
        if self.enabled:
            val = 1 if status == "healthy" else (0 if status == "degraded" else -1)
            self.system_health.set(val)

_metrics_manager = None

def get_metrics_manager() -> MetricsManager:
    global _metrics_manager
    if _metrics_manager is None:
        _metrics_manager = MetricsManager()
    return _metrics_manager
