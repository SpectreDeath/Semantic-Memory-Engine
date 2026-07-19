"""
ThreatIntelligenceHarvester - Real-Time Threat Intelligence IOC Harvester
==========================================================================
Extracts IOCs (IPv4, SHA256 hashes, Bitcoin wallets, domains) from threat text feeds,
converts them into semantic atomic triplets, and injects them into VIndexOverlay.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from gateway.vindex_overlay import VIndexOverlay

logger = logging.getLogger("lawnmower.threat_harvester")


class ThreatIntelligenceHarvester:
    """
    Harvester extracting threat indicators and persisting semantic triplets into VIndexOverlay.
    """

    IOC_PATTERNS = {
        "ipv4": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
        "sha256": r"\b[a-fA-F0-9]{64}\b",
        "btc_wallet": r"\b(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}\b",
        "domain": r"\b[a-zA-Z0-9.-]+\.(?:com|org|net|io|onion|ru)\b",
    }

    def __init__(self, vindex_overlay: VIndexOverlay | None = None) -> None:
        self.vindex = vindex_overlay or VIndexOverlay()

    def harvest_threat_iocs(
        self, raw_text: str, source_id: str = "darkweb_feed"
    ) -> dict[str, Any]:
        """
        Parse raw text for IOCs, construct atomic semantic triplets, and inject into VIndexOverlay.
        """
        extracted_iocs: dict[str, list[str]] = {}
        triplets: list[dict[str, str]] = []

        for ioc_type, pattern in self.IOC_PATTERNS.items():
            matches = sorted(set(re.findall(pattern, raw_text)))
            if matches:
                extracted_iocs[ioc_type] = matches
                for match in matches:
                    triplets.extend(
                        [
                            {"subject": match, "predicate": "is_a", "object": "threat_indicator"},
                            {"subject": match, "predicate": "indicator_type", "object": ioc_type},
                            {"subject": match, "predicate": "harvested_from", "object": source_id},
                        ]
                    )

        # Inject into VIndexOverlay
        for t in triplets:
            self.vindex.add_direct_triple(t["subject"], t["predicate"], t["object"])

        logger.info(
            f"ThreatIntelligenceHarvester extracted {sum(len(v) for v in extracted_iocs.values())} IOCs into {len(triplets)} triplets"
        )

        return {
            "status": "success",
            "source_id": source_id,
            "iocs_found": extracted_iocs,
            "total_iocs": sum(len(v) for v in extracted_iocs.values()),
            "triplets_created": len(triplets),
        }
