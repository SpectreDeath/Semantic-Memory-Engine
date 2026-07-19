"""
Unit Tests for ForensicNexus & VIndex Optimization
====================================================
Tests high-throughput SQLite PRAGMAs, index creation, and VIndex caching.
"""

from __future__ import annotations

import pytest

from gateway.nexus_db import ForensicNexus
from gateway.vindex_overlay import VIndexConfig, VIndexOverlay, VIndexTriple


class TestNexusPragmas:
    """Test high-throughput PRAGMA configurations on ForensicNexus."""

    def test_nexus_pragmas_configured(self):
        nexus = ForensicNexus()
        cursor = nexus.conn.cursor()

        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode.lower() == "wal"

        cursor.execute("PRAGMA synchronous")
        sync_mode = cursor.fetchone()[0]
        # NORMAL mode is 1 in SQLite
        assert sync_mode in (1, "1", "NORMAL")

        cursor.execute("PRAGMA temp_store")
        temp_store = cursor.fetchone()[0]
        # MEMORY mode is 2 in SQLite
        assert temp_store in (2, "2", "MEMORY")

        cursor.close()

    def test_nexus_cross_db_query(self):
        nexus = ForensicNexus()
        feed = nexus.get_unified_forensic_feed(limit=5)
        assert isinstance(feed, list)


class TestVIndexOverlayCaching:
    """Test query caching in VIndexOverlay."""

    def test_vindex_caching_returns_consistent_results(self):
        config = VIndexConfig(max_triplets=5)
        overlay = VIndexOverlay(config=config)

        overlay.triple_store.append(
            VIndexTriple(subject="Alpha", relation="is_a", target="Agent", weight=1.0)
        )

        res1 = overlay._find_relevant_triplets("Alpha agent details")
        assert len(res1) == 1

        res2 = overlay._find_relevant_triplets("Alpha agent details")
        assert res1 == res2
        assert "alpha agent details" in overlay._cache

    def test_add_triplets_clears_cache(self):
        overlay = VIndexOverlay()
        overlay.triple_store.append(
            VIndexTriple(subject="Beta", relation="operates", target="Node", weight=0.9)
        )

        overlay._find_relevant_triplets("Beta operates node")
        assert len(overlay._cache) > 0

        # Simulating adding new triplets invalidates cache
        overlay.add_triplets("Gamma is connected to Delta")
        assert len(overlay._cache) == 0
