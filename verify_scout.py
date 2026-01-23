import os
import sys
import logging
from unittest.mock import patch, MagicMock

# Ensure src is in path
sys.path.append(os.getcwd())

from src.core.factory import ToolFactory

def test_forensic_scout():
    print("🚀 Starting Forensic Scout Verification...")
    
    # 1. Instantiate via Factory
    try:
        scout = ToolFactory.create_forensic_scout()
        print("✅ ForensicScout instance created via Factory.")
    except Exception as e:
        print(f"❌ Failed to create instance: {e}")
        sys.exit(1)
        
    # 2. Test Structure Preservation
    print("\n🏗️ Testing Structural Preservation...")
    raw_html = """
    <html>
        <body>
            <nav>Menu</nav>
            <h1>Analysis Report</h1>
            <p>First paragraph of highly relevant content.</p>
            <script>console.log('noise');</script>
            <h2>Section 1</h2>
            <p>Second paragraph with <b>bold</b> text that should remain.</p>
            <footer>Footer info</footer>
        </body>
    </html>
    """
    
    segments = scout.clean_and_segment(raw_html)
    print(f"Segments found: {len(segments)}")
    for i, seg in enumerate(segments):
        print(f"  [{i}] {seg}")
        
    assert len(segments) == 4, "Should extract H1, P1, H2, P2"
    assert "First paragraph" in segments[1]
    assert "nav" not in "".join(segments).lower()
    
    print("✅ Structure preserved, noise removed.")
    
    # 3. Test Streaming Generator
    print("\n🌊 Testing Memory-First Streaming...")
    
    # Create fake response text (large enough to chunk? Mocking small chunks for test)
    # Using 10 words per chunk limit logic inside harvest defaults to 10k, 
    # so we'll just check it yields at least one dict
    
    mock_url = "http://test.com/report"
    mock_content = "<p>Word " * 100 + "</p>" # 100 words
    
    with patch('requests.Session.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = mock_content
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        
        chunks = list(scout.harvest(mock_url, author_id="agent_smith"))
        
        print(f"Chunks yielded: {len(chunks)}")
        assert len(chunks) > 0
        first_chunk = chunks[0]
        
        print(f"Chunk Keys: {first_chunk.keys()}")
        assert "text" in first_chunk
        assert "timestamp" in first_chunk
        assert first_chunk["author_id"] == "agent_smith"
        
        print("✅ Streaming loop operational.")

    print("\n✅ Verification COMPLETE: Forensic Scout is mission-ready.")

if __name__ == "__main__":
    test_forensic_scout()
