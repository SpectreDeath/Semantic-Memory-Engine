import unittest
from unittest.mock import MagicMock, patch
import json
from extensions.ext_archival_diff.scout import WaybackScout
from extensions.ext_archival_diff.analyst import ForensicAnalyst

class TestArchivalDiff(unittest.TestCase):

    def test_scout_find_divergent_snapshots(self):
        scout = WaybackScout()
        mock_history = [
            {"timestamp": "20210101000000", "digest": "hash1", "url": "url1"},
            {"timestamp": "20210201000000", "digest": "hash1", "url": "url2"},
            {"timestamp": "20210301000000", "digest": "hash2", "url": "url3"}, # Change!
        ]
        
        with patch.object(scout, 'get_snapshot_history', return_value=mock_history):
            prev, latest = scout.find_divergent_snapshots("http://test.com")
            self.assertEqual(latest['digest'], "hash2")
            self.assertEqual(prev['digest'], "hash1")
            self.assertEqual(prev['timestamp'], "20210201000000")

    def test_analyst_strip_boilerplate(self):
        analyst = ForensicAnalyst()
        html = """
        <html>
            <nav>Menu Items</nav>
            <div id="main">
                <h1>Title</h1>
                <p>This is meaningful content that should be kept.</p>
                <p>Short</p>
            </div>
            <div class="footer">Footer content</div>
            <script>console.log('test')</script>
        </html>
        """
        stripped = analyst.strip_boilerplate(html)
        self.assertIn("Title", stripped)
        self.assertIn("This is meaningful content", stripped)
        self.assertNotIn("Menu Items", stripped)
        self.assertNotIn("Footer content", stripped)
        self.assertNotIn("Short", stripped) # Filtered by length

    def test_analyst_semantic_diff(self):
        analyst = ForensicAnalyst()
        old_html = "<p>Line one</p><p>Line two</p><p>Line three</p>"
        new_html = "<p>Line one</p><p>Line three</p><p>Line four</p>"
        
        # We need to wrap them in longer strings to pass the 20-char filter in my implementation
        old_html = "<p>This is the first long line of text.</p><p>This is the second long line of text.</p>"
        new_html = "<p>This is the first long line of text.</p><p>This is a new third long line of text.</p>"
        
        diff = analyst.semantic_diff(old_html, new_html)
        self.assertEqual(len(diff['deleted_content']), 1)
        self.assertEqual(len(diff['added_content']), 1)
        self.assertIn("second", diff['deleted_content'][0])
        self.assertIn("new third", diff['added_content'][0])

if __name__ == '__main__':
    unittest.main()
