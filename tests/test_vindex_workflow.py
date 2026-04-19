"""
Tests for V-Index workflow gateway modules
==========================================
Note: Some tests skipped due to spacy incompatibility with Python 3.14
"""

import unittest


class TestEpistemicTrust(unittest.TestCase):
    """Test epistemic trust scoring - constants only."""

    def test_default_thresholds(self):
        """Test default threshold values."""
        from gateway.epistemic_trust import DEFAULT_TRUST_THRESHOLD, HALLUCINATION_BLOCK_THRESHOLD
        self.assertEqual(DEFAULT_TRUST_THRESHOLD, 0.6)
        self.assertEqual(HALLUCINATION_BLOCK_THRESHOLD, 0.25)


class TestGraphWalk(unittest.TestCase):
    """Test graph walk constants."""

    def test_constants_exist(self):
        """Test constants are defined."""
        from gateway.graph_walk import DEFAULT_VECTOR_SIZE
        self.assertGreater(DEFAULT_VECTOR_SIZE, 0)


if __name__ == '__main__':
    unittest.main()
