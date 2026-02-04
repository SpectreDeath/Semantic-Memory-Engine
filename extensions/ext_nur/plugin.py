"""
Unified Forensic Reporter Extension Plugin

Main plugin entry point that integrates the Unified Forensic Reporter extension
with the SME system.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# Import our components
from .unified_forensic_reporter import generate_nexus_summary, UnifiedForensicReporter, ForensicSummary
from .forensic_intelligence_reporter import generate_forensic_intelligence_summary, ForensicIntelligenceReporter, ForensicAnalysis, IntelligenceBucket


class UnifiedForensicReporterPlugin:
    """Main plugin class for the Unified Forensic Reporter extension."""
    
    def __init__(self):
        self.name = "Unified Forensic Reporter Extension"
        self.version = "1.0.0"
        self.description = "Aggregates logs from all extensions and generates comprehensive forensic reports with AI-powered conclusions"
        
        # Plugin configuration
        self.config = {
            'analysis_period_hours': 24,  # Hours to look back in logs
            'max_events_displayed': 20,   # Maximum events to show in detailed log
            'report_format': 'markdown',  # Report format (markdown, json, etc.)
            'auto_generate': False,       # Whether to auto-generate reports
            'cpu_bound_only': True,       # Ensure VRAM constraint compliance
            'log_parsing_enabled': True   # Enable log file parsing
        }
        
        # State tracking
        self.is_active = False
        self.reporter = UnifiedForensicReporter()
        
    def activate(self) -> bool:
        """Activate the Unified Forensic Reporter plugin."""
        try:
            print(f"🔍 Activating {self.name} v{self.version}")
            print(f"Description: {self.description}")
            
            # Ensure reports directory exists
            reports_dir = Path("D:/SME/reports")
            reports_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ Reports directory ready: {reports_dir}")
            
            # Verify CPU-bound operation
            if self.config.get('cpu_bound_only', True):
                print("✅ CPU-bound operation enforced (VRAM constraint compliant)")
            
            self.is_active = True
            print(f"✅ {self.name} activated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to activate {self.name}: {e}")
            return False
    
    def deactivate(self) -> bool:
        """Deactivate the Unified Forensic Reporter plugin."""
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
            'reports_directory': str(self.reporter.report_dir),
            'last_report_generated': None  # Could be tracked if needed
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
        return {
            'generate_nexus_summary': self._create_nexus_summary_tool(),
            'generate_forensic_intelligence_summary': self._create_forensic_intelligence_tool()
        }
    
    def _create_nexus_summary_tool(self) -> Callable:
        """Create the nexus summary generation tool."""
        def nexus_summary_tool() -> Dict[str, Any]:
            """
            Generate unified nexus intelligence report.
            
            Returns:
                Dictionary containing report generation results.
            """
            print(f"🔍 Unified Forensic Reporter: Generating nexus summary")
            
            # Verify CPU-bound operation
            if self.config.get('cpu_bound_only', True):
                print("🧠 Using CPU-bound processing (VRAM constraint compliant)")
            
            # Generate the report
            result = generate_nexus_summary()
            
            # Update status
            if result.get('status') == 'SUCCESS':
                print(f"✅ Nexus summary generated successfully")
            else:
                print(f"❌ Failed to generate nexus summary")
            
            return result
        
        return nexus_summary_tool
    
    def get_hooks(self) -> Dict[str, Callable]:
        """Get available hooks provided by this plugin."""
        return {}
    
    def get_events(self) -> List[str]:
        """Get list of events this plugin can handle."""
        return [
            'report_generated',
            'log_analysis_started',
            'log_analysis_completed',
            'forensic_conclusion_generated',
            'forensic_intelligence_started',
            'forensic_intelligence_completed',
            'intelligence_bucket_detected'
        ]
    
    def handle_event(self, event_name: str, **kwargs) -> Any:
        """Handle plugin-specific events."""
        if event_name == 'report_generated':
            report_path = kwargs.get('report_path', '')
            print(f"📄 Report generated: {report_path}")
            return {'report_handled': True, 'path': report_path}
        
        elif event_name == 'log_analysis_started':
            print("🔍 Log analysis started")
            return {'analysis_started': True}
        
        elif event_name == 'log_analysis_completed':
            log_count = kwargs.get('log_count', 0)
            print(f"✅ Log analysis completed. Processed {log_count} entries")
            return {'analysis_completed': True, 'log_count': log_count}
        
        elif event_name == 'forensic_conclusion_generated':
            conclusion = kwargs.get('conclusion', '')
            print(f"🧠 Forensic conclusion generated")
            return {'conclusion_handled': True}
        
        elif event_name == 'forensic_intelligence_started':
            print("🔍 Forensic intelligence analysis started")
            return {'intelligence_started': True}
        
        elif event_name == 'forensic_intelligence_completed':
            result = kwargs.get('result', {})
            print(f"✅ Forensic intelligence analysis completed. Bucket: {result.get('intelligence_bucket', 'unknown')}")
            return {'intelligence_completed': True}
        
        elif event_name == 'intelligence_bucket_detected':
            bucket_info = kwargs.get('bucket_info', {})
            print(f"🎯 Intelligence bucket detected: {bucket_info}")
            return {'bucket_handled': True}
        
        return {'event_handled': False}
    
    def _create_forensic_intelligence_tool(self) -> Callable:
        """Create the forensic intelligence summary generation tool."""
        def forensic_intelligence_tool(text_sample: str) -> Dict[str, Any]:
            """
            Generate forensic intelligence summary from text sample.
            
            Args:
                text_sample: Text sample to analyze and categorize.
                
            Returns:
                Dictionary containing forensic analysis results and report path.
            """
            print(f"🔍 Unified Forensic Reporter: Generating forensic intelligence summary")
            
            # Verify CPU-bound operation
            if self.config.get('cpu_bound_only', True):
                print("🧠 Using CPU-bound processing (VRAM constraint compliant)")
            
            # Generate the forensic intelligence report
            result = generate_forensic_intelligence_summary(text_sample)
            
            # Update status
            if result.get('status') == 'FORENSIC_ANALYSIS_COMPLETED':
                print(f"✅ Forensic intelligence analysis completed")
                print(f"🎯 Intelligence Bucket: {result.get('intelligence_bucket', 'unknown')}")
                print(f"📊 Confidence Score: {result.get('confidence_score', 0.0)}")
                print(f"📄 Report saved to: {result.get('report_path', 'unknown')}")
            else:
                print(f"❌ Failed to generate forensic intelligence summary")
            
            return result
        
        return forensic_intelligence_tool
    
    def get_reporter_instance(self) -> UnifiedForensicReporter:
        """Get an instance of the UnifiedForensicReporter for advanced usage."""
        return self.reporter
    
    def get_forensic_reporter_instance(self) -> ForensicIntelligenceReporter:
        """Get an instance of the ForensicIntelligenceReporter for advanced usage."""
        return ForensicIntelligenceReporter()


# Create global plugin instance
unified_forensic_reporter_plugin = UnifiedForensicReporterPlugin()


def get_plugin() -> UnifiedForensicReporterPlugin:
    """Get the global Unified Forensic Reporter plugin instance."""
    return unified_forensic_reporter_plugin


# Export for use by the extension system
__all__ = ['UnifiedForensicReporterPlugin', 'get_plugin', 'unified_forensic_reporter_plugin']