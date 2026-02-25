#!/usr/bin/env python3
"""
Simple test script to verify ScrapeGraphAI extension can be imported
without requiring full SME infrastructure.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def test_imports():
    """Test that we can import the extension without SME dependencies"""
    print("Testing ScrapeGraphAI extension imports...")
    
    try:
        # Test pydantic imports
        from pydantic import BaseModel, Field
        from pydantic.types import constr
        print("✓ Pydantic imports successful")
        
        # Test ScrapeGraphAI imports (these will fail if not installed)
        try:
            import scrapegraphai
            from scrapegraphai.graphs import SmartScraperGraph, SearchGraph, MarkdownifyGraph
            from scrapegraphai.config import GraphConfig
            from playwright.async_api import async_playwright
            print("✓ ScrapeGraphAI imports successful")
            SCRAPEGRAPH_AVAILABLE = True
        except ImportError as e:
            print(f"⚠️  ScrapeGraphAI not available: {e}")
            SCRAPEGRAPH_AVAILABLE = False
        
        # Test our extension classes
        from extensions.ext_scrapegraph_harvester.plugin import (
            ScrapeRequest, ResearchRequest, MarkdownifyRequest, MemoryNode
        )
        print("✓ Extension classes imported successfully")
        
        # Test that we can create request objects
        scrape_req = ScrapeRequest(url="https://example.com")
        research_req = ResearchRequest(query="test query")
        markdown_req = MarkdownifyRequest(url="https://example.com")
        print("✓ Request objects created successfully")
        
        # Test MemoryNode creation
        node = MemoryNode(
            id="test_123",
            content="Test content",
            source_url="https://example.com",
            timestamp="2026-02-25T12:00:00Z",
            trust_score=0.8,
            entities=["test", "entity"],
            relationships=[{"type": "related", "target": "other"}]
        )
        print("✓ MemoryNode created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_extension_structure():
    """Test that the extension has the expected structure"""
    print("\nTesting extension structure...")
    
    try:
        # Import the main extension class
        from extensions.ext_scrapegraph_harvester.plugin import ScrapeGraphHarvester
        
        # Check that the class has the expected methods
        expected_methods = [
            'scrape_and_remember',
            'deep_research', 
            'markdownify',
            'get_tools',
            'on_startup',
            'on_ingestion'
        ]
        
        for method in expected_methods:
            if hasattr(ScrapeGraphHarvester, method):
                print(f"✓ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        print("✓ All expected methods present")
        return True
        
    except Exception as e:
        print(f"❌ Structure test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=== ScrapeGraphAI Extension Test ===\n")
    
    success = True
    success &= test_imports()
    success &= test_extension_structure()
    
    print(f"\n=== Test Results ===")
    if success:
        print("🎉 All tests passed!")
        print("\nThe ScrapeGraphAI extension has been successfully created and can be imported.")
        print("Next steps:")
        print("1. Install dependencies: pip install -r extensions/ext_scrapegraph_harvester/requirements.txt")
        print("2. Ensure Ollama is running with required models")
        print("3. Restart SME to auto-load the extension")
        print("4. Test via MCP Gateway or Control Room")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)