"""
Verification Tests for Phase 6 - Silicon Brain
==============================================

Tests for KnowledgeGraph, IntelligenceReports, and OverlapDiscovery modules.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import ToolFactory, KnowledgeGraph, IntelligenceReports, OverlapDiscovery

class TestPhase6Intelligence:
    """Test suite for Phase 6 intelligence components."""
    
    @pytest.fixture
    def sample_text(self):
        return """
        Albert Einstein was a theoretical physicist who developed the theory of relativity. 
        He worked in Princeton at the Institute for Advanced Study. 
        Einstein's work has had a profound impact on science, though he expressed 
        concerns about the technological applications of nuclear physics. 
        The world remembers him as a symbol of human intelligence.
        """

    def test_knowledge_graph_build(self, sample_text):
        """Test building a graph from text."""
        kg = ToolFactory.create_knowledge_graph(reset=True)
        kg.build_from_text(sample_text)
        
        summary = kg.get_summary()
        assert summary["node_count"] > 0
        assert summary["edge_count"] > 0
        
        mermaid = kg.to_mermaid()
        assert "Albert_Einstein" in mermaid
        assert "graph LR" in mermaid

    def test_intelligence_briefing(self, sample_text):
        """Test generating a narrative report."""
        ir = ToolFactory.create_intelligence_reports(reset=True)
        report = ir.generate_briefing(sample_text, title="Einstein Report")
        
        assert report.title == "Einstein Report"
        assert len(report.key_points) > 0
        assert "polarity" in report.sentiment_overview
        
        md = ir.to_markdown(report)
        assert "# Einstein Report" in md
        assert "Executive Summary" in md

    def test_overlap_discovery_initialization(self):
        """Test that OverlapDiscovery initializes correctly."""
        od = ToolFactory.create_overlap_discovery(reset=True)
        assert od is not None
        assert od.semantic_db is not None

    def test_factory_registry(self):
        """Verify all Phase 6 tools are in the factory."""
        assert hasattr(ToolFactory, 'create_knowledge_graph')
        assert hasattr(ToolFactory, 'create_intelligence_reports')
        assert hasattr(ToolFactory, 'create_overlap_discovery')
        
    def test_graph_export_json(self, sample_text):
        """Test JSON export for D3 integration."""
        kg = ToolFactory.create_knowledge_graph(reset=True)
        kg.build_from_text(sample_text)
        
        js_data = kg.to_json()
        assert '"nodes":' in js_data
        assert '"links":' in js_data

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
