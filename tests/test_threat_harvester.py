"""
Unit Tests for ThreatIntelligenceHarvester
==========================================
Tests ThreatIntelligenceHarvester IOC extraction and VIndexOverlay injection.
"""

from __future__ import annotations

import pytest

from gateway.threat_harvester import ThreatIntelligenceHarvester
from gateway.vindex_overlay import VIndexOverlay


class TestThreatIntelligenceHarvester:
    """Test ThreatIntelligenceHarvester IOC extraction and semantic index injection."""

    def test_harvest_threat_iocs_extraction_and_vindex_injection(self):
        vindex = VIndexOverlay()
        harvester = ThreatIntelligenceHarvester(vindex_overlay=vindex)
        sample_feed = (
            "Detected malicious activity from IP 192.168.1.100 and 10.0.0.1. "
            "File payload hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855. "
            "Ransom payment requested to BTC wallet bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh. "
            "C2 server operating at malic-domain.onion."
        )

        res = harvester.harvest_threat_iocs(raw_text=sample_feed, source_id="darkweb_feed_01")

        assert res["status"] == "success"
        assert res["source_id"] == "darkweb_feed_01"
        assert "ipv4" in res["iocs_found"]
        assert "sha256" in res["iocs_found"]
        assert "btc_wallet" in res["iocs_found"]
        assert res["total_iocs"] >= 4
        assert res["triplets_created"] >= 12

        # Verify injection into VIndexOverlay
        match_triplets = vindex._find_relevant_triplets("192.168.1.100")
        assert len(match_triplets) > 0
        assert match_triplets[0].subject == "192.168.1.100"
