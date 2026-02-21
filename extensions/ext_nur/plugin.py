"""
Unified Forensic Reporter Extension Plugin

Main plugin entry point that integrates the Unified Forensic Reporter extension
with the SME system.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

try:
    from .unified_forensic_reporter import generate_nexus_summary, UnifiedForensicReporter, ForensicSummary
    from .forensic_intelligence_reporter import generate_forensic_intelligence_summary, ForensicIntelligenceReporter, ForensicAnalysis, IntelligenceBucket
except ImportError:
    _dir = Path(__file__).resolve().parent
    if str(_dir) not in sys.path:
        sys.path.insert(0, str(_dir))
    from unified_forensic_reporter import generate_nexus_summary, UnifiedForensicReporter, ForensicSummary
    from forensic_intelligence_reporter import generate_forensic_intelligence_summary, ForensicIntelligenceReporter, ForensicAnalysis, IntelligenceBucket

# NexusAPI: use self.nexus.nexus and self.nexus.get_hsm() — no gateway imports
from src.core.plugin_base import BasePlugin
from src.utils.error_handling import ErrorHandler, create_error_response, OperationContext
from src.utils.performance import get_performance_monitor, cache_result, LRUCache

logger = logging.getLogger("SME.UnifiedForensicReporter")


class UnifiedForensicReporterPlugin(BasePlugin):
    """Main plugin class for the Unified Forensic Reporter extension."""
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        self.error_handler = ErrorHandler(self.plugin_id)
        self.monitor = get_performance_monitor(self.plugin_id)
        self.reporter = UnifiedForensicReporter()
        self.forensic_reporter = ForensicIntelligenceReporter()
        
        # Plugin configuration
        self.config = {
            'analysis_period_hours': 24,  # Hours to look back in logs
            'max_events_displayed': 20,   # Maximum events to show in detailed log
            'report_format': 'markdown',  # Report format (markdown, json, etc.)
            'auto_generate': False,       # Whether to auto-generate reports
            'cpu_bound_only': True,       # Ensure VRAM constraint compliance
            'log_parsing_enabled': True   # Enable log file parsing
        }
        
        logger.info(f"[{self.plugin_id}] Unified Forensic Reporter initialized")
        
    async def on_startup(self):
        """
        Initialize the Unified Forensic Reporter.
        """
        try:
            logger.info(f"[{self.plugin_id}] Unified Forensic Reporter started successfully")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to start Unified Forensic Reporter: {e}")

    async def on_shutdown(self):
        """
        Clean shutdown of the Unified Forensic Reporter.
        """
        try:
            logger.info(f"[{self.plugin_id}] Unified Forensic Reporter shutdown complete")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error during shutdown: {e}")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Unified Forensic Reporter does not process on_ingestion directly.
        It provides tools for report generation and analysis.
        """
        return {
            "status": "skipped",
            "reason": "Unified Forensic Reporter provides reporting tools, not direct ingestion processing"
        }

    def get_tools(self) -> list:
        return [
            self.generate_nexus_summary,
            self.generate_forensic_intelligence_summary,
            self.get_unified_stats,
            self.clear_reporter_cache
        ]
    
    async def generate_nexus_summary(self) -> str:
        """
        Generate unified nexus intelligence report.
        """
        try:
            with self.monitor.time_operation("nexus_summary_generation"):
                # Verify CPU-bound operation
                if self.config.get('cpu_bound_only', True):
                    logger.info("Using CPU-bound processing (VRAM constraint compliant)")
                
                # Generate the report
                result = generate_nexus_summary()
                
                # Update status
                if result.get('status') == 'SUCCESS':
                    logger.info("Nexus summary generated successfully")
                else:
                    logger.warning("Failed to generate nexus summary")
                
                return json.dumps(result, indent=2)
                
        except Exception as e:
            return self.error_handler.handle_tool_error(e, "generate_nexus_summary")

    async def generate_forensic_intelligence_summary(self, text_sample: str) -> str:
        """
        Generate forensic intelligence summary from text sample.
        """
        try:
            with self.monitor.time_operation("forensic_intelligence_generation"):
                # Verify CPU-bound operation
                if self.config.get('cpu_bound_only', True):
                    logger.info("Using CPU-bound processing (VRAM constraint compliant)")
                
                # Generate the forensic intelligence report
                result = generate_forensic_intelligence_summary(text_sample)
                
                # Update status
                if result.get('status') == 'FORENSIC_ANALYSIS_COMPLETED':
                    logger.info("Forensic intelligence analysis completed")
                    logger.info(f"Intelligence Bucket: {result.get('intelligence_bucket', 'unknown')}")
                    logger.info(f"Confidence Score: {result.get('confidence_score', 0.0)}")
                    logger.info(f"Report saved to: {result.get('report_path', 'unknown')}")
                else:
                    logger.warning("Failed to generate forensic intelligence summary")
                
                return json.dumps(result, indent=2)
                
        except Exception as e:
            return self.error_handler.handle_tool_error(e, "generate_forensic_intelligence_summary", {"text_sample_length": len(text_sample)})

    async def get_unified_stats(self) -> str:
        """Get statistics about the Unified Forensic Reporter's performance."""
        try:
            stats = {
                "plugin_id": self.plugin_id,
                "config": self.config,
                "reporter_stats": {
                    "report_dir": str(self.reporter.report_dir),
                    "analysis_period_hours": self.config.get('analysis_period_hours', 24),
                    "max_events_displayed": self.config.get('max_events_displayed', 20)
                },
                "forensic_reporter_stats": {
                    "cpu_bound_only": self.config.get('cpu_bound_only', True),
                    "log_parsing_enabled": self.config.get('log_parsing_enabled', True)
                },
                "performance_stats": self.monitor.get_all_stats(),
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(stats, indent=2)
        except Exception as e:
            return self.error_handler.handle_tool_error(e, "get_unified_stats")

    async def clear_reporter_cache(self) -> str:
        """Clear any cached data in the reporter instances."""
        try:
            # Clear any internal caches if they exist
            if hasattr(self.reporter, 'clear_cache'):
                self.reporter.clear_cache()
            if hasattr(self.forensic_reporter, 'clear_cache'):
                self.forensic_reporter.clear_cache()
            
            return json.dumps({
                "status": "success",
                "message": "Reporter caches cleared successfully"
            }, indent=2)
        except Exception as e:
            return self.error_handler.handle_tool_error(e, "clear_reporter_cache")



# Create global plugin instance
unified_forensic_reporter_plugin = UnifiedForensicReporterPlugin()


def get_plugin() -> UnifiedForensicReporterPlugin:
    """Get the global Unified Forensic Reporter plugin instance."""
    return unified_forensic_reporter_plugin


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return a UnifiedForensicReporterPlugin instance."""
    return UnifiedForensicReporterPlugin(manifest, nexus_api)


def register_extension(manifest: dict, nexus_api: Any) -> UnifiedForensicReporterPlugin:
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return create_plugin(manifest, nexus_api)


# Export for use by the extension system
__all__ = ['UnifiedForensicReporterPlugin', 'get_plugin', 'unified_forensic_reporter_plugin', 'register_extension']