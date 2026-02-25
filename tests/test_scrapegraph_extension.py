import asyncio
import unittest
from unittest.mock import patch, AsyncMock
from extensions.ext_scrapegraph_harvester.plugin import ScrapeGraphHarvester, ScrapeRequest, ResearchRequest, MarkdownifyRequest

class TestScrapeGraphHarvester(unittest.TestCase):
    def setUp(self):
        # Create a mock manifest and nexus_api
        self.manifest = {
            "plugin_id": "scrapegraph_harvester",
            "name": "ScrapeGraphAI Harvester",
            "version": "1.0.0"
        }
        self.nexus_api = None  # Will be mocked
        self.harvester = ScrapeGraphHarvester(self.manifest, self.nexus_api)

    @patch('extensions.ext_scrapegraph_harvester.SCRAPEGRAPH_AVAILABLE', False)
    def test_dependencies_not_available(self):
        """Test behavior when ScrapeGraphAI dependencies are not installed"""
        result = asyncio.run(self.harvester.scrape_and_remember(
            ScrapeRequest(url="https://example.com")
        ))
        self.assertEqual(result["status"], "error")
        self.assertIn("ScrapeGraphAI dependencies not installed", result["error"])

    @patch('extensions.ext_scrapegraph_harvester.SCRAPEGRAPH_AVAILABLE', True)
    @patch('extensions.ext_scrapegraph_harvester.SmartScraperGraph')
    def test_scrape_and_remember_success(self, mock_graph):
        """Test successful scrape_and_remember operation"""
        # Mock the graph result
        mock_result = AsyncMock()
        mock_result.run = AsyncMock(return_value=AsyncMock(data=[{"content": "Test content"}]))
        mock_graph.return_value = mock_result

        result = asyncio.run(self.harvester.scrape_and_remember(
            ScrapeRequest(url="https://example.com")
        ))

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["nodes_created"], 1)
        self.assertEqual(result["entities_extracted"], 0)  # No entities in mock data

    @patch('extensions.ext_scrapegraph_harvester.SCRAPEGRAPH_AVAILABLE', True)
    @patch('extensions.ext_scrapegraph_harvester.SearchGraph')
    def test_deep_research_success(self, mock_graph):
        """Test successful deep_research operation"""
        # Mock the graph result
        mock_result = AsyncMock()
        mock_result.run = AsyncMock(return_value=AsyncMock(results=[{
            "title": "Test Result",
            "snippet": "Test snippet",
            "url": "https://example.com",
            "content": "Test content"
        }]))
        mock_graph.return_value = mock_result

        result = asyncio.run(self.harvester.deep_research(
            ResearchRequest(query="test query")
        ))

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results_count"], 1)
        self.assertEqual(result["nodes_created"], 1)

    @patch('extensions.ext_scrapegraph_harvester.SCRAPEGRAPH_AVAILABLE', True)
    @patch('extensions.ext_scrapegraph_harvester.MarkdownifyGraph')
    def test_markdownify_success(self, mock_graph):
        """Test successful markdownify operation"""
        # Mock the graph result
        mock_result = AsyncMock()
        mock_result.run = AsyncMock(return_value=AsyncMock(markdown="# Test Markdown"))
        mock_graph.return_value = mock_result

        result = asyncio.run(self.harvester.markdownify(
            MarkdownifyRequest(url="https://example.com")
        ))

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["markdown_length"], 15)  # Length of "# Test Markdown"
        self.assertEqual(result["nodes_created"], 1)

    def test_trust_score_calculation(self):
        """Test trust score calculation logic"""
        # Test with Wikipedia (high trust)
        score1 = self.harvester._calculate_trust_score(
            {"content": "Test content"},
            "https://en.wikipedia.org/wiki/Test"
        )
        self.assertGreater(score1, 0.7)

        # Test with unknown source (neutral trust)
        score2 = self.harvester._calculate_trust_score(
            {"content": "Test content"},
            "https://unknown.com"
        )
        self.assertAlmostEqual(score2, 0.5, places=1)

        # Test with long content (higher trust)
        score3 = self.harvester._calculate_trust_score(
            {"content": "a" * 2000},
            "https://example.com"
        )
        self.assertGreater(score3, 0.5)

if __name__ == '__main__':
    unittest.main()