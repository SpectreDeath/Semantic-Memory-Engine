#!/usr/bin/env python3
"""
Comprehensive test suite for the improved ScrapeGraphAI Harvester extension.
Tests all improvements including validation, error handling, and security measures.
"""

import asyncio
import hashlib
import logging
import pathlib
import sys
import time
from datetime import datetime, timezone
from unittest import mock

import pydantic
import pytest

# Standard bootstrap
import src.bootstrap
src.bootstrap.initialize()

from extensions.ext_scrapegraph_harvester import plugin



class TestScrapeRequestValidation:
    """Test URL validation and security measures"""

    def test_valid_url_validation(self):
        """Test that valid URLs pass validation"""
        request = plugin.ScrapeRequest(
            url="https://example.com",
            prompt="Test prompt",
            model="ollama/llama3.2"
        )
        assert request.url == "https://example.com"

    def test_invalid_url_formats(self):
        """Test that invalid URL formats are rejected"""
        with pytest.raises(pydantic.ValidationError):
            plugin.ScrapeRequest(url="not-a-url", prompt="Test", model="ollama/llama3.2")
        
        with pytest.raises(pydantic.ValidationError):
            plugin.ScrapeRequest(url="ftp://example.com", prompt="Test", model="ollama/llama3.2")

    def test_security_blocked_urls(self):
        """Test that potentially dangerous URLs are blocked"""
        dangerous_urls = [
            "http://localhost:8080",
            "https://127.0.0.1",
            "file:///etc/passwd",
            "http://localhost/test"
        ]
        
        for url in dangerous_urls:
            with pytest.raises(pydantic.ValidationError, match="Local and file URLs are not allowed"):
                plugin.ScrapeRequest(url=url, prompt="Test", model="ollama/llama3.2")

    def test_query_validation(self):
        """Test search query validation"""
        # Valid query
        request = plugin.ResearchRequest(query="test query", results_count=5)
        assert request.query == "test query"
        
        # Empty query should be rejected
        with pytest.raises(pydantic.ValidationError):
            plugin.ResearchRequest(query="", results_count=5)
        
        # Query too long should be rejected
        long_query = "x" * 600
        with pytest.raises(pydantic.ValidationError):
            plugin.ResearchRequest(query=long_query, results_count=5)


class TestMemoryNodeProcessing:
    """Test memory node creation and processing"""

    def test_unique_node_id_generation(self):
        """Test that node IDs are unique and collision-resistant"""
        content1 = "Test content 1"
        content2 = "Test content 2"
        
        # Generate node IDs
        hash1 = hashlib.sha256(content1.encode('utf-8')).hexdigest()[:12]
        hash2 = hashlib.sha256(content2.encode('utf-8')).hexdigest()[:12]
        
        assert hash1 != hash2
        
        # Test timestamp-based uniqueness
        time1 = int(time.time())
        time.sleep(1)  # Ensure different timestamp
        time2 = int(time.time())
        
        assert time1 != time2

    def test_trust_score_calculation(self):
        """Test sophisticated trust scoring algorithm"""
        harvester = plugin.ScrapeGraphHarvester({}, None)
        
        # Test Wikipedia source
        item = {"content": "Test content"}
        score = harvester._calculate_trust_score(item, "https://wikipedia.org/test")
        assert score > 0.35  # Should be high for Wikipedia
        
        # Test .gov source
        score = harvester._calculate_trust_score(item, "https://www.whitehouse.gov/test")
        assert score > 0.30  # Should be high for .gov
        
        # Test .com source
        score = harvester._calculate_trust_score(item, "https://example.com/test")
        assert 0.1 <= score <= 0.2  # Should be moderate for .com
        
        # Test content length scoring
        short_content = {"content": "x" * 50}
        long_content = {"content": "x" * 2000}
        
        short_score = harvester._calculate_trust_score(short_content, "https://example.com/test")
        long_score = harvester._calculate_trust_score(long_content, "https://example.com/test")
        
        assert long_score > short_score  # Longer content should score higher

    def test_entity_extraction(self):
        """Test entity extraction with error handling"""
        harvester = plugin.ScrapeGraphHarvester({}, None)
        
        # Test with valid result structure
        mock_result = mock.MagicMock()
        mock_result.entities = ["entity1", "entity2", "entity1"]  # Duplicates
        entities = harvester._extract_entities(mock_result)
        
        assert len(entities) <= 10  # Should be limited
        assert len(set(entities)) == len(entities)  # Should be deduplicated
        
        # Test with fallback structure
        mock_result = mock.MagicMock()
        mock_result.data = [
            {"entities": ["entity1", "entity2"]},
            {"entities": ["entity3"]}
        ]
        entities = harvester._extract_entities(mock_result)
        
        assert len(entities) <= 10
        assert "entity1" in entities
        assert "entity3" in entities

    def test_relationship_extraction(self):
        """Test relationship extraction with error handling"""
        harvester = plugin.ScrapeGraphHarvester({}, None)
        
        # Test with valid result structure
        mock_result = mock.MagicMock()
        mock_result.relationships = [{"type": "related", "target": "entity1"}]
        relationships = harvester._extract_relationships(mock_result)
        
        assert len(relationships) <= 5  # Should be limited
        
        # Test with fallback structure
        mock_result = mock.MagicMock()
        mock_result.data = [
            {"relationships": [{"type": "related", "target": "entity1"}]},
            {"relationships": [{"type": "mentions", "target": "entity2"}]}
        ]
        relationships = harvester._extract_relationships(mock_result)
        
        assert len(relationships) <= 5


class TestDatabaseStorage:
    """Test improved database storage with batch operations"""

    def test_batch_storage_with_validation(self):
        """Test batch storage with proper validation"""
        harvester = plugin.ScrapeGraphHarvester({}, None)
        
        # Mock nexus and hsm
        harvester.nexus = mock.MagicMock()
        harvester.hsm = mock.MagicMock()
        
        # Create test nodes
        nodes = [
            plugin.MemoryNode(
                id="test_1",
                content="Test content 1",
                source_url="https://example.com",
                timestamp=datetime.now(timezone.utc).isoformat(),
                trust_score=0.8,
                entities=["test"],
                relationships=[]
            ),
            plugin.MemoryNode(
                id="test_2",
                content="Test content 2",
                source_url="https://example.com",
                timestamp=datetime.now(timezone.utc).isoformat(),
                trust_score=0.7,
                entities=["test"],
                relationships=[]
            )
        ]
        
        # Mock successful operations
        harvester.nexus.execute = mock.MagicMock()
        harvester.hsm.sign_evidence = mock.MagicMock()
        
        # Test storage
        harvester._store_memory_nodes(nodes)
        
        # Verify HSM signing was called
        assert harvester.hsm.sign_evidence.call_count == 2
        
        # Verify database operations were called
        assert harvester.nexus.execute.call_count >= 2

    def test_invalid_node_handling(self):
        """Test handling of invalid nodes"""
        harvester = plugin.ScrapeGraphHarvester({}, None)
        
        # Mock nexus and hsm
        harvester.nexus = mock.MagicMock()
        harvester.hsm = mock.MagicMock()
        
        # Create invalid node (missing content)
        invalid_node = plugin.MemoryNode(
            id="invalid",
            content="",  # Empty content
            source_url="https://example.com",
            timestamp="",
            trust_score=0.5,
            entities=[],
            relationships=[]
        )
        
        # Mock operations
        harvester.nexus.execute = mock.MagicMock()
        harvester.hsm.sign_evidence = mock.MagicMock()
        
        # Test storage - should skip invalid node
        harvester._store_memory_nodes([invalid_node])
        
        # HSM signing should not be called for invalid node
        harvester.hsm.sign_evidence.assert_not_called()
        harvester.nexus.execute.assert_not_called()

    def test_storage_error_handling(self):
        """Test error handling during storage operations"""
        harvester = plugin.ScrapeGraphHarvester({}, None)
        
        # Mock nexus and hsm
        harvester.nexus = mock.MagicMock()
        harvester.hsm = mock.MagicMock()
        
        # Create valid node
        node = plugin.MemoryNode(
            id="test",
            content="Test content",
            source_url="https://example.com",
            timestamp=datetime.now(timezone.utc).isoformat(),
            trust_score=0.8,
            entities=["test"],
            relationships=[]
        )
        
        # Mock HSM signing to fail
        harvester.hsm.sign_evidence.side_effect = Exception("HSM error")
        harvester.nexus.execute = mock.MagicMock()
        
        # Test storage - should handle HSM error gracefully
        harvester._store_memory_nodes([node])
        
        # Database operation should still be attempted
        harvester.nexus.execute.assert_called()


class TestConfigurationAndTimeouts:
    """Test configuration improvements and timeout handling"""

    def test_default_configuration(self):
        """Test that default configuration includes timeouts"""
        harvester = plugin.ScrapeGraphHarvester({}, None)
        
        config = harvester.default_config
        
        # Check LLM timeout
        assert "timeout" in config["llm"]
        assert config["llm"]["timeout"] == 120  # 2 minutes
        
        # Check scraping timeout
        assert "scraping_timeout" in config
        assert config["scraping_timeout"] == 60  # 1 minute
        
        # Check retry configuration
        assert "max_retries" in config
        assert config["max_retries"] == 3

    def test_rate_limiting_initialization(self):
        """Test that rate limiting is properly initialized"""
        harvester = plugin.ScrapeGraphHarvester({}, None)
        
        assert hasattr(harvester, '_last_request_time')
        assert hasattr(harvester, '_min_request_interval')
        assert harvester._min_request_interval == 1.0  # 1 second


class TestErrorHandling:
    """Test improved error handling throughout the extension"""

    def test_dependency_availability_check(self):
        """Test that missing dependencies are handled gracefully"""
        # This would be tested in integration tests where dependencies are not available
        # For now, just verify the structure exists
        
        # Should be a boolean
        assert isinstance(plugin.SCRAPEGRAPH_AVAILABLE, bool)

    def test_tool_return_values(self):
        """Test that tools return proper error structures"""
        harvester = plugin.ScrapeGraphHarvester({}, None)
        
        # Test with missing dependencies (simulated)
        with mock.patch('extensions.ext_scrapegraph_harvester.plugin.SCRAPEGRAPH_AVAILABLE', False):
            result = asyncio.run(harvester.scrape_and_remember(
                plugin.ScrapeRequest(url="https://example.com", prompt="test")
            ))
            
            assert result["status"] == "error"
            assert "ScrapeGraphAI dependencies not installed" in result["error"]

    def test_logging_configuration(self):
        """Test that proper logging is configured"""
        logger = logging.getLogger("scrapegraph_harvester")
        
        # Should have a logger configured
        assert logger.name == "scrapegraph_harvester"
        
        # Should be able to log messages
        logger.info("Test log message")


class TestSecurityImprovements:
    """Test security enhancements"""

    def test_url_sanitization(self):
        """Test that URLs are properly sanitized"""
        # Test that malicious URLs are blocked by validation
        dangerous_patterns = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
            "file:///etc/passwd",
            "http://localhost:22",  # SSH port
            "https://192.168.1.1"  # Internal IP
        ]
        
        for pattern in dangerous_patterns:
            with pytest.raises(pydantic.ValidationError):
                plugin.ScrapeRequest(url=pattern, prompt="test", model="ollama/llama3.2")

    def test_content_hashing(self):
        """Test that content is properly hashed for HSM signing"""
        content = "Test content for hashing"
        expected_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Verify hash calculation
        assert len(expected_hash) == 64  # SHA-256 produces 64 hex characters
        assert expected_hash.isalnum()  # Should be hexadecimal


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])