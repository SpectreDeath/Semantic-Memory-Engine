import json
import logging
from typing import Any

from src.core.plugin_base import BasePlugin

logger = logging.getLogger("LawnmowerMan.Monitoring")

try:
    from src.utils.performance import PerformanceMonitor as PM
except ImportError:
    PM = None


def PerformanceMonitor(plugin_id=None):
    if PM is None:
        return None
    return PM(plugin_id=plugin_id or "default")


try:
    from src.utils.alerts import AlertManager
except ImportError:
    AlertManager = None

try:
    from src.utils.log_utils import LogAnalyzer
except ImportError:
    LogAnalyzer = None

try:
    from src.utils.check_db import DatabaseAuditor
except ImportError:
    DatabaseAuditor = None


class MonitoringExtension(BasePlugin):
    """
    System Monitoring Extension for SME.
    Provides performance monitoring, alert management, log analysis, and database auditing.
    """

    def __init__(self, manifest: dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.performance = PerformanceMonitor() if PerformanceMonitor else None
        self.alerts = AlertManager() if AlertManager else None
        self.logs = LogAnalyzer() if LogAnalyzer else None
        self.db_audit = DatabaseAuditor() if DatabaseAuditor else None

    async def on_startup(self):
        logger.info(f"[{self.plugin_id}] System Monitoring extension activated.")

    async def on_ingestion(self, raw_data: str, metadata: dict[str, Any]):
        return {"status": "processed", "plugin": self.plugin_id}

    def get_tools(self):
        return [
            self.monitor_performance,
            self.manage_alerts,
            self.analyze_logs,
            self.audit_database,
        ]

    async def monitor_performance(self, metric: str = "all", duration: int = 60) -> str:
        """Monitor system performance metrics."""
        if not self.performance:
            return json.dumps({"error": "PerformanceMonitor not available"})
        try:
            result = self.performance.monitor(metric, duration)
            return json.dumps({"metric": metric, "duration": duration, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def manage_alerts(self, action: str, alert_config: dict = None) -> str:
        """Manage alerts (create, dismiss, list, configure)."""
        if not self.alerts:
            return json.dumps({"error": "AlertManager not available"})
        try:
            result = self.alerts.manage(action, alert_config)
            return json.dumps({"action": action, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def analyze_logs(self, log_path: str, filter_pattern: str = None) -> str:
        """Analyze log files for patterns and anomalies."""
        if not self.logs:
            return json.dumps({"error": "LogAnalyzer not available"})
        try:
            result = self.logs.analyze(log_path, filter_pattern)
            return json.dumps({"log_path": log_path, "filter": filter_pattern, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def audit_database(self, check_type: str = "full") -> str:
        """Perform database health and integrity checks."""
        if not self.db_audit:
            return json.dumps({"error": "DatabaseAuditor not available"})
        try:
            result = self.db_audit.audit(check_type)
            return json.dumps({"check_type": check_type, "result": result})
        except Exception as e:
            return json.dumps({"error": str(e)})


def register_extension(manifest: dict[str, Any], nexus_api: Any):
    return MonitoringExtension(manifest, nexus_api)
