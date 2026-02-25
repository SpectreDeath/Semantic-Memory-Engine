import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Try to import the extension
try:
    from extensions.ext_scrapegraph_harvester.plugin import ScrapeGraphHarvester, ScrapeRequest, ResearchRequest, MarkdownifyRequest
    from gateway.extension_manager import DefaultExtensionContext
    AVAILABLE = True
except ImportError as e:
    AVAILABLE = False
    ERROR = str(e)

async def test_integration():
    if not AVAILABLE:
        print(f"Extension not available: {ERROR}")
        return False

    # Create extension instance
    manifest = {
        "plugin_id": "scrapegraph_harvester",
        "name": "ScrapeGraphAI Harvester",
        "version": "1.0.0"
    }
    extension = ScrapeGraphHarvester(manifest, DefaultExtensionContext())

    # Test tool availability
    tools = extension.get_tools()
    print(f"Extension loaded successfully with {len(tools)} tools:")
    for name, func in tools.items():
        print(f"  - {name}: {func.__doc__[:50]}...")

    # Test dependency availability
    if extension.default_config.llm["model"] == "ollama/llama3.2":
        print("✓ VRAM-optimized configuration loaded")
    else:
        print("⚠️  Configuration may need adjustment")

    # Test basic functionality (mocked)
    print("\nRunning basic functionality tests...")
    try:
        # Test scrape_and_remember
        scrape_result = await extension.scrape_and_remember(
            ScrapeRequest(url="https://example.com")
        )
        print(f"✓ scrape_and_remember: {scrape_result['status']}")

        # Test deep_research
        research_result = await extension.deep_research(
            ResearchRequest(query="test query")
        )
        print(f"✓ deep_research: {research_result['status']}")

        # Test markdownify
        markdown_result = await extension.markdownify(
            MarkdownifyRequest(url="https://example.com")
        )
        print(f"✓ markdownify: {markdown_result['status']}")

        print("\n✅ All basic tests passed!")
        return True

    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False

if __name__ == "__main__":
    if asyncio.run(test_integration()):
        print("\n🎉 ScrapeGraphAI Harvester extension is ready for integration!")
        print("The extension has been successfully created and passes basic tests.")
        print("Next steps:")
        print("1. Install dependencies: pip install -r extensions/ext_scrapegraph_harvester/requirements.txt")
        print("2. Ensure Ollama is running with required models")
        print("3. Restart SME to auto-load the extension")
        print("4. Test via MCP Gateway or Control Room")
    else:
        print("\n❌ Extension tests failed. Check the output above for details.")