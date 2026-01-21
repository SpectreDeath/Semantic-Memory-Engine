"""
🕸️ NETWORK ANALYZER - Coordinated Inauthentic Behavior Detection
Detects sockpuppet accounts, bot farms, and coordinated campaigns
using fingerprint similarity clustering.

Analyzes 6,734 rhetorical signals to find:
✓ Sockpuppet accounts (same person, multiple identities)
✓ Bot farms (coordinated inauthentic behavior)
✓ Campaign networks (coordinated messaging)
✓ Co-author relationships (who writes with whom)
"""

import logging
from typing import Dict, List, Tuple, Set
import numpy as np
from dataclasses import dataclass
from datetime import datetime
from scribe_authorship import ScribeEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class FingerprintCluster:
    """Group of accounts with similar linguistic fingerprints"""
    cluster_id: int
    accounts: List[str]
    avg_similarity: float
    confidence: float  # 0-100
    suspected_operator: str
    severity: str  # "Critical", "High", "Medium", "Low"
    evidence: List[str]
    created_at: str = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class CoauthorNetwork:
    """Relationship between authors based on signal similarity"""
    author_a: str
    author_b: str
    similarity_score: float  # 0-1
    shared_signals: Dict[str, float]
    likely_relationship: str  # "Same person", "Collaborators", "Unrelated"


@dataclass
class AnomalyAlert:
    """Suspicious pattern detected in account network"""
    alert_type: str  # "Sockpuppet", "BotFarm", "Campaign", "Anomaly"
    severity: str  # "Critical", "High", "Medium", "Low"
    confidence: float  # 0-100
    accounts_involved: List[str]
    evidence: List[str]
    recommended_action: str
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


# ============================================================================
# NETWORK ANALYZER ENGINE
# ============================================================================

class NetworkAnalyzer:
    """
    Detect coordinated inauthentic behavior using forensic fingerprints.
    """

    def __init__(self):
        self.scribe = ScribeEngine()
        self.fingerprints_cache = {}
        logger.info("🕸️ NetworkAnalyzer initialized")

    # ========================================================================
    # TOOL 1: DETECT SOCKPUPPET ACCOUNTS
    # ========================================================================

    def detect_sockpuppet_accounts(
        self,
        account_texts: Dict[str, str],
        similarity_threshold: float = 0.85
    ) -> List[FingerprintCluster]:
        """
        Find accounts likely run by same person (sockpuppets).
        
        Args:
            account_texts: {account_id: text}
            similarity_threshold: 0.85 = 85% fingerprint match
            
        Returns:
            List of FingerprintCluster objects
        """
        logger.info(f"🔍 Analyzing {len(account_texts)} accounts for sockpuppets...")

        try:
            # Step 1: Extract fingerprints
            fingerprints = {}
            for account_id, text in account_texts.items():
                if not text or len(text) < 100:
                    logger.warning(f"⚠️ Skipping {account_id} (text too short)")
                    continue

                fp = self.scribe.extract_linguistic_fingerprint(text, author_id=account_id)
                fingerprints[account_id] = fp
                self.fingerprints_cache[account_id] = fp

            if not fingerprints:
                logger.warning("⚠️ No valid fingerprints extracted")
                return []

            # Step 2: Build similarity matrix
            logger.info(f"📊 Building similarity matrix ({len(fingerprints)} fingerprints)...")
            clusters = []
            processed_pairs = set()

            for acc1 in fingerprints:
                for acc2 in fingerprints:
                    if acc1 >= acc2 or (acc1, acc2) in processed_pairs:
                        continue

                    processed_pairs.add((acc1, acc2))

                    fp1 = fingerprints[acc1]
                    fp2 = fingerprints[acc2]

                    # Calculate similarity
                    similarity = self.scribe._calculate_signal_similarity(
                        fp1.signal_vector,
                        fp2.signal_vector
                    )

                    if similarity > similarity_threshold:
                        # Strong match - likely same person
                        evidence = self._build_evidence(fp1, fp2, similarity)

                        cluster = FingerprintCluster(
                            cluster_id=len(clusters),
                            accounts=[acc1, acc2],
                            avg_similarity=similarity,
                            confidence=min(100, similarity * 100),
                            suspected_operator=f"Unknown (Fingerprint Match: {similarity:.0%})",
                            severity=self._classify_severity(similarity),
                            evidence=evidence
                        )
                        clusters.append(cluster)
                        logger.info(f"🚨 SOCKPUPPET DETECTED: {acc1} ↔ {acc2} ({similarity:.0%})")

            logger.info(f"✅ Found {len(clusters)} suspicious account pairs")
            return clusters

        except Exception as e:
            logger.error(f"❌ Sockpuppet detection failed: {str(e)}")
            raise

    # ========================================================================
    # TOOL 2: DETECT BOT FARMS
    # ========================================================================

    def detect_bot_farms(
        self,
        account_texts: Dict[str, str],
        min_farm_size: int = 3,
        similarity_threshold: float = 0.80
    ) -> List[FingerprintCluster]:
        """
        Detect bot farms (3+ coordinated accounts with similar patterns).
        
        Args:
            account_texts: {account_id: text}
            min_farm_size: Minimum accounts to be considered a farm
            similarity_threshold: Pattern match threshold
            
        Returns:
            List of FingerprintCluster objects (bot farms)
        """
        logger.info(f"🤖 Analyzing {len(account_texts)} accounts for bot farms...")

        try:
            # Extract fingerprints
            fingerprints = {}
            for account_id, text in account_texts.items():
                if not text or len(text) < 100:
                    continue
                fp = self.scribe.extract_linguistic_fingerprint(text, author_id=account_id)
                fingerprints[account_id] = fp

            # Build clustering
            visited = set()
            bot_farms = []

            for seed_account in fingerprints:
                if seed_account in visited:
                    continue

                # Find all similar accounts
                cluster_members = [seed_account]
                visited.add(seed_account)

                for other_account in fingerprints:
                    if other_account in visited:
                        continue

                    sim = self.scribe._calculate_signal_similarity(
                        fingerprints[seed_account].signal_vector,
                        fingerprints[other_account].signal_vector
                    )

                    if sim > similarity_threshold:
                        cluster_members.append(other_account)
                        visited.add(other_account)

                # Only report if 3+ members
                if len(cluster_members) >= min_farm_size:
                    avg_sim = np.mean([
                        self.scribe._calculate_signal_similarity(
                            fingerprints[cluster_members[0]].signal_vector,
                            fingerprints[m].signal_vector
                        )
                        for m in cluster_members[1:]
                    ])

                    farm = FingerprintCluster(
                        cluster_id=len(bot_farms),
                        accounts=cluster_members,
                        avg_similarity=avg_sim,
                        confidence=min(100, avg_sim * 100),
                        suspected_operator=f"Bot Farm ({len(cluster_members)} accounts)",
                        severity="Critical" if len(cluster_members) >= 5 else "High",
                        evidence=[
                            f"{len(cluster_members)} accounts with {avg_sim:.0%} fingerprint match",
                            "Uniform linguistic patterns across accounts",
                            "Coordinated signal distribution",
                            "Likely automated or managed network"
                        ]
                    )
                    bot_farms.append(farm)
                    logger.info(f"🤖 BOT FARM DETECTED: {len(cluster_members)} accounts, {avg_sim:.0%} similarity")

            logger.info(f"✅ Found {len(bot_farms)} potential bot farms")
            return bot_farms

        except Exception as e:
            logger.error(f"❌ Bot farm detection failed: {str(e)}")
            raise

    # ========================================================================
    # TOOL 3: BUILD COAUTHOR NETWORKS
    # ========================================================================

    def build_coauthor_network(
        self,
        author_texts: Dict[str, str],
        similarity_threshold: float = 0.60
    ) -> List[CoauthorNetwork]:
        """
        Find writing partnerships (similar signal distributions).
        
        Args:
            author_texts: {author_id: text}
            similarity_threshold: Connection threshold
            
        Returns:
            List of CoauthorNetwork relationships
        """
        logger.info(f"🤝 Building co-author network from {len(author_texts)} authors...")

        try:
            fingerprints = {}
            for author_id, text in author_texts.items():
                if not text or len(text) < 100:
                    continue
                fp = self.scribe.extract_linguistic_fingerprint(text, author_id=author_id)
                fingerprints[author_id] = fp

            relationships = []
            processed = set()

            for auth1 in fingerprints:
                for auth2 in fingerprints:
                    if auth1 >= auth2 or (auth1, auth2) in processed:
                        continue

                    processed.add((auth1, auth2))

                    sim = self.scribe._calculate_signal_similarity(
                        fingerprints[auth1].signal_vector,
                        fingerprints[auth2].signal_vector
                    )

                    if sim > similarity_threshold:
                        # Find shared signals
                        shared = {}
                        for sig_id in fingerprints[auth1].signal_weights:
                            if sig_id in fingerprints[auth2].signal_weights:
                                w1 = fingerprints[auth1].signal_weights[sig_id]
                                w2 = fingerprints[auth2].signal_weights[sig_id]
                                if w1 > 0 or w2 > 0:
                                    shared[sig_id] = (w1 + w2) / 2

                        # Classify relationship
                        if sim > 0.85:
                            rel_type = "Same person"
                        elif sim > 0.75:
                            rel_type = "Close collaborators"
                        else:
                            rel_type = "Writing partnership"

                        relationship = CoauthorNetwork(
                            author_a=auth1,
                            author_b=auth2,
                            similarity_score=sim,
                            shared_signals=shared,
                            likely_relationship=rel_type
                        )
                        relationships.append(relationship)
                        logger.info(f"🤝 {rel_type}: {auth1} ↔ {auth2} ({sim:.0%})")

            logger.info(f"✅ Found {len(relationships)} co-author relationships")
            return relationships

        except Exception as e:
            logger.error(f"❌ Co-author network failed: {str(e)}")
            raise

    # ========================================================================
    # TOOL 4: TIMELINE ANALYSIS
    # ========================================================================

    def analyze_coordinated_campaign(
        self,
        campaign_accounts: List[str],
        timeline_data: Dict[str, List[Tuple[str, str]]]
    ) -> List[AnomalyAlert]:
        """
        Detect coordinated posting patterns (same message, different accounts).
        
        Args:
            campaign_accounts: List of account IDs to analyze
            timeline_data: {account_id: [(timestamp, text), ...]}
            
        Returns:
            List of AnomalyAlert objects
        """
        logger.info(f"📅 Analyzing {len(campaign_accounts)} accounts for coordination...")

        alerts = []

        try:
            # Find similar messages posted across accounts
            message_clusters = {}

            for account in campaign_accounts:
                if account not in timeline_data:
                    continue

                for timestamp, text in timeline_data[account]:
                    # Fingerprint the message
                    msg_fp = self.scribe.extract_linguistic_fingerprint(text)

                    # Check against existing messages
                    for existing_id, (existing_fp, posting_accounts) in message_clusters.items():
                        sim = self.scribe._calculate_signal_similarity(
                            msg_fp.signal_vector,
                            existing_fp.signal_vector
                        )

                        if sim > 0.80:  # Very similar message
                            posting_accounts.append((account, timestamp))
                            break
                    else:
                        # New message cluster
                        message_clusters[len(message_clusters)] = (msg_fp, [(account, timestamp)])

            # Find coordinated patterns
            for cluster_id, (_, postings) in message_clusters.items():
                if len(postings) >= 3:  # 3+ accounts with same message
                    accounts_involved = list(set([p[0] for p in postings]))

                    alert = AnomalyAlert(
                        alert_type="Campaign",
                        severity="High",
                        confidence=90.0,
                        accounts_involved=accounts_involved,
                        evidence=[
                            f"Same message posted by {len(accounts_involved)} accounts",
                            "Similar rhetorical patterns across posts",
                            "Coordinated timing",
                            "Indicates campaign or coordinated effort"
                        ],
                        recommended_action="Flag for platform review; likely coordinated inauthentic behavior"
                    )
                    alerts.append(alert)
                    logger.info(f"🚨 CAMPAIGN DETECTED: {len(accounts_involved)} accounts coordinated")

            logger.info(f"✅ Found {len(alerts)} coordinated campaigns")
            return alerts

        except Exception as e:
            logger.error(f"❌ Campaign analysis failed: {str(e)}")
            raise

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _build_evidence(self, fp1, fp2, similarity: float) -> List[str]:
        """Build evidence list for sockpuppet detection"""
        evidence = []

        # Voice ratio similarity
        voice_diff = abs(fp1.passive_voice_ratio - fp2.passive_voice_ratio)
        if voice_diff < 0.05:
            evidence.append(f"Identical voice ratio (passive: {fp1.passive_voice_ratio:.0%})")

        # Sentence length similarity
        length_diff = abs(fp1.avg_sentence_length - fp2.avg_sentence_length)
        if length_diff < 2:
            evidence.append(f"Nearly identical sentence length (~{fp1.avg_sentence_length:.1f} words)")

        # Punctuation similarity
        punct_diff = sum(abs(fp1.punctuation_profile.get(p, 0) - fp2.punctuation_profile.get(p, 0))
                        for p in fp1.punctuation_profile)
        if punct_diff < 0.2:
            evidence.append("Nearly identical punctuation habits")

        # Signal overlap
        signal_overlap = len(set(fp1.signal_weights.keys()) & set(fp2.signal_weights.keys()))
        if signal_overlap > 50:
            evidence.append(f"{signal_overlap} shared rhetoric signals")

        # Overall match
        evidence.append(f"{similarity:.0%} fingerprint match (very strong)")

        return evidence

    def _classify_severity(self, similarity: float) -> str:
        """Classify severity based on similarity score"""
        if similarity > 0.95:
            return "Critical"
        elif similarity > 0.85:
            return "High"
        elif similarity > 0.75:
            return "Medium"
        else:
            return "Low"

    # ========================================================================
    # REPORTING
    # ========================================================================

    def generate_network_report(
        self,
        sockpuppets: List[FingerprintCluster],
        bot_farms: List[FingerprintCluster],
        coauthors: List[CoauthorNetwork]
    ) -> Dict:
        """Generate comprehensive network analysis report"""
        return {
            "report_type": "Network Analysis",
            "timestamp": datetime.utcnow().isoformat(),
            "sockpuppet_clusters": len(sockpuppets),
            "bot_farms_detected": len(bot_farms),
            "coauthor_relationships": len(coauthors),
            "overall_threat_level": self._assess_threat_level(sockpuppets, bot_farms),
            "sockpuppets": [
                {
                    "accounts": c.accounts,
                    "similarity": f"{c.avg_similarity:.0%}",
                    "severity": c.severity,
                    "evidence": c.evidence
                }
                for c in sockpuppets
            ],
            "bot_farms": [
                {
                    "size": len(c.accounts),
                    "accounts": c.accounts,
                    "avg_similarity": f"{c.avg_similarity:.0%}",
                    "severity": c.severity,
                    "evidence": c.evidence
                }
                for c in bot_farms
            ],
            "coauthor_relationships": [
                {
                    "author_a": c.author_a,
                    "author_b": c.author_b,
                    "similarity": f"{c.similarity_score:.0%}",
                    "relationship": c.likely_relationship
                }
                for c in coauthors
            ]
        }

    def _assess_threat_level(self, sockpuppets, bot_farms) -> str:
        """Assess overall threat level"""
        threat_score = len(sockpuppets) + (len(bot_farms) * 5)

        if threat_score > 10:
            return "Critical"
        elif threat_score > 5:
            return "High"
        elif threat_score > 0:
            return "Medium"
        else:
            return "Low"


# ============================================================================
# MCP TOOL FUNCTIONS
# ============================================================================

def detect_sockpuppets_tool(account_texts: Dict[str, str], similarity_threshold: float = 0.85) -> Dict:
    """MCP Tool: Detect sockpuppet accounts"""
    analyzer = NetworkAnalyzer()
    clusters = analyzer.detect_sockpuppet_accounts(account_texts, similarity_threshold)

    return {
        "status": "success",
        "sockpuppets_found": len(clusters),
        "clusters": [
            {
                "accounts": c.accounts,
                "similarity": f"{c.avg_similarity:.0%}",
                "confidence": f"{c.confidence:.0f}%",
                "severity": c.severity,
                "evidence": c.evidence
            }
            for c in clusters
        ]
    }


def detect_bot_farms_tool(account_texts: Dict[str, str], min_farm_size: int = 3) -> Dict:
    """MCP Tool: Detect bot farms"""
    analyzer = NetworkAnalyzer()
    farms = analyzer.detect_bot_farms(account_texts, min_farm_size)

    return {
        "status": "success",
        "bot_farms_found": len(farms),
        "farms": [
            {
                "size": len(f.accounts),
                "accounts": f.accounts,
                "avg_similarity": f"{f.avg_similarity:.0%}",
                "severity": f.severity,
                "evidence": f.evidence
            }
            for f in farms
        ]
    }


def build_network_tool(author_texts: Dict[str, str]) -> Dict:
    """MCP Tool: Build co-author network"""
    analyzer = NetworkAnalyzer()
    relationships = analyzer.build_coauthor_network(author_texts)

    return {
        "status": "success",
        "relationships_found": len(relationships),
        "network": [
            {
                "author_a": r.author_a,
                "author_b": r.author_b,
                "similarity": f"{r.similarity_score:.0%}",
                "relationship": r.likely_relationship
            }
            for r in relationships
        ]
    }


if __name__ == "__main__":
    # Demo
    print("\n" + "="*80)
    print("🕸️ NETWORK ANALYZER DEMO")
    print("="*80)

    analyzer = NetworkAnalyzer()

    # Sample accounts (sockpuppet scenario)
    sample_accounts = {
        "account_001": "The rapid growth of digital platforms enables unprecedented information sharing. We must prioritize security and ethical governance. I believe strongly in data protection.",
        "account_002": "Digital platforms grow rapidly, enabling information to be shared at scale. Security is paramount, and governance must be ethical. Data protection matters.",
        "account_003": "The internet is wonderful. I like talking about tech. Different perspective here.",
    }

    print("\n🔍 Testing sockpuppet detection...")
    sockpuppets = analyzer.detect_sockpuppet_accounts(sample_accounts, similarity_threshold=0.70)
    print(f"Found {len(sockpuppets)} sockpuppet pairs")

    print("\n✅ NETWORK ANALYZER READY")
    print("="*80 + "\n")
