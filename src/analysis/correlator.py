"""
📈 TREND CORRELATOR - Link Trending Topics to Authors
Identifies which authors are driving specific trends by correlating
trending topic mentions with author fingerprints.

Uses Scribe + Loom output to:
✓ Identify trending topics
✓ Find articles mentioning trends
✓ Attribute to likely authors
✓ Timeline analysis (when did trend start?)
✓ Campaign detection (coordinated promotion)
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from scribe_authorship import ScribeEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class TrendDriver:
    """Author identified as driving a trend"""
    author_id: str
    author_name: str
    trend_topic: str
    attribution_score: float  # 0-100
    article_count: int
    first_mention: str
    last_mention: str
    aggregate_signal_strength: Dict[str, float]
    estimated_reach: int  # Estimated readers/followers
    role: str  # "Primary Driver", "Amplifier", "Adopter"


@dataclass
class TrendAnalysis:
    """Complete analysis of a trending topic"""
    topic: str
    trend_start_date: str
    trend_intensity: float  # 0-100
    primary_drivers: List[TrendDriver]
    amplifiers: List[TrendDriver]
    article_count: int
    unique_authors: int
    estimated_total_reach: int
    coordinated_promotion: bool
    coordination_confidence: float


@dataclass
class InfluenceChain:
    """Chain of how a trend spreads author-to-author"""
    trend_topic: str
    chain_length: int
    influencers: List[Tuple[str, float]]  # (author, timestamp)
    estimated_spread_velocity: str  # "Rapid", "Moderate", "Slow"
    amplification_factor: float


# ============================================================================
# TREND CORRELATOR ENGINE
# ============================================================================

class TrendCorrelator:
    """
    Correlate trending topics with author fingerprints to identify trend drivers.
    """

    def __init__(self):
        self.scribe = ScribeEngine()
        logger.info("📈 TrendCorrelator initialized")

    # ========================================================================
    # TOOL 1: IDENTIFY TREND DRIVERS
    # ========================================================================

    def identify_trend_drivers(
        self,
        trend_topic: str,
        article_data: List[Dict],  # [{author_id, text, timestamp, url}, ...]
        min_attribution_score: float = 70.0
    ) -> TrendAnalysis:
        """
        Find which authors are driving a specific trend.
        
        Args:
            trend_topic: The trending topic (e.g., "AI Regulation")
            article_data: List of articles with {author_id, text, timestamp, url}
            min_attribution_score: Minimum confidence to list as driver
            
        Returns:
            TrendAnalysis with identified drivers
        """
        logger.info(f"📈 Analyzing trend: {trend_topic}")

        try:
            # Step 1: Extract fingerprints from all articles
            author_fingerprints = {}
            author_article_count = {}
            author_timestamps = {}

            for article in article_data:
                author_id = article['author_id']
                text = article['text']
                timestamp = article['timestamp']

                if len(text) < 200:
                    continue

                # Extract fingerprint
                fp = self.scribe.extract_linguistic_fingerprint(text, author_id=author_id)

                if author_id not in author_fingerprints:
                    author_fingerprints[author_id] = []
                    author_article_count[author_id] = 0
                    author_timestamps[author_id] = []

                author_fingerprints[author_id].append(fp)
                author_article_count[author_id] += 1
                author_timestamps[author_id].append(timestamp)

            logger.info(f"✅ Extracted {len(author_fingerprints)} unique authors")

            # Step 2: Calculate aggregate signal strength per author
            author_scores = {}
            author_signals = {}

            for author_id, fingerprints in author_fingerprints.items():
                # Aggregate signal weights
                agg_signals = {}
                for fp in fingerprints:
                    for sig_id, weight in fp.signal_weights.items():
                        if sig_id not in agg_signals:
                            agg_signals[sig_id] = []
                        agg_signals[sig_id].append(weight)

                # Average signals
                avg_signals = {sig_id: np.mean(weights) for sig_id, weights in agg_signals.items()}
                author_signals[author_id] = avg_signals

                # Calculate strength (consistency + intensity)
                consistency = np.std([fp.lexical_diversity for fp in fingerprints])
                intensity = np.mean([fp.lexical_diversity for fp in fingerprints])
                article_count = len(fingerprints)

                # Composite score: consistency (40%), intensity (40%), volume (20%)
                score = (
                    (1 - consistency) * 40 +  # More consistent = higher
                    intensity * 40 +
                    min(100, article_count * 10) * 20 / 100
                )

                author_scores[author_id] = score

            # Step 3: Classify roles (Primary, Amplifier, Adopter)
            sorted_authors = sorted(author_scores.items(), key=lambda x: x[1], reverse=True)
            primary_threshold = np.percentile([s for _, s in sorted_authors], 75)
            amplifier_threshold = np.percentile([s for _, s in sorted_authors], 50)

            drivers = []
            amplifiers = []

            for author_id, score in sorted_authors:
                if score < min_attribution_score:
                    continue

                timestamps = sorted(author_timestamps[author_id])
                first_mention = timestamps[0] if timestamps else ""
                last_mention = timestamps[-1] if timestamps else ""

                driver = TrendDriver(
                    author_id=author_id,
                    author_name=author_id,  # Would be enriched with actual name
                    trend_topic=trend_topic,
                    attribution_score=score,
                    article_count=author_article_count[author_id],
                    first_mention=first_mention,
                    last_mention=last_mention,
                    aggregate_signal_strength=author_signals[author_id],
                    estimated_reach=author_article_count[author_id] * 1000,  # Placeholder
                    role=self._classify_role(score, primary_threshold, amplifier_threshold)
                )

                if driver.role == "Primary Driver":
                    drivers.append(driver)
                    logger.info(f"🎯 PRIMARY DRIVER: {author_id} ({score:.1f}%)")
                else:
                    amplifiers.append(driver)

            # Step 4: Check for coordinated promotion
            coordinated = self._detect_coordination(sorted_authors[:3], author_fingerprints)

            analysis = TrendAnalysis(
                topic=trend_topic,
                trend_start_date=min(author_timestamps[a] for a in author_fingerprints if author_timestamps[a]),
                trend_intensity=np.mean([s for _, s in sorted_authors[:5]]),
                primary_drivers=drivers,
                amplifiers=amplifiers[:5],  # Top 5 amplifiers
                article_count=len(article_data),
                unique_authors=len(author_fingerprints),
                estimated_total_reach=sum(author_article_count.values()) * 1000,
                coordinated_promotion=coordinated['detected'],
                coordination_confidence=coordinated['confidence']
            )

            logger.info(f"✅ Trend analysis complete: {len(drivers)} drivers, {len(amplifiers)} amplifiers")
            return analysis

        except Exception as e:
            logger.error(f"❌ Trend driver identification failed: {str(e)}")
            raise

    # ========================================================================
    # TOOL 2: TRACE INFLUENCE CHAIN
    # ========================================================================

    def trace_influence_chain(
        self,
        trend_topic: str,
        article_data: List[Dict],  # Sorted by timestamp
        max_chain_length: int = 10
    ) -> InfluenceChain:
        """
        Trace how a trend spreads author-to-author over time.
        
        Args:
            trend_topic: Trending topic
            article_data: Articles in chronological order
            max_chain_length: Maximum influencers to track
            
        Returns:
            InfluenceChain showing spread pattern
        """
        logger.info(f"🔗 Tracing influence chain for: {trend_topic}")

        try:
            if not article_data:
                return InfluenceChain(trend_topic, 0, [], "None", 0)

            # Sort by timestamp
            article_data = sorted(article_data, key=lambda x: x['timestamp'])

            influencers = []
            fingerprints_by_author = {}

            for article in article_data:
                author_id = article['author_id']
                text = article['text']
                timestamp = article['timestamp']

                if len(text) < 200:
                    continue

                # Get or create fingerprint for this author
                if author_id not in fingerprints_by_author:
                    fp = self.scribe.extract_linguistic_fingerprint(text, author_id=author_id)
                    fingerprints_by_author[author_id] = fp

                # If this is the first mention or different author, add to chain
                if not influencers or influencers[-1][0] != author_id:
                    # Check if similar to previous author (indicating amplification)
                    if influencers:
                        prev_fp = fingerprints_by_author[influencers[-1][0]]
                        curr_fp = fingerprints_by_author[author_id]
                        similarity = self.scribe._calculate_signal_similarity(
                            prev_fp.signal_vector,
                            curr_fp.signal_vector
                        )
                    else:
                        similarity = 1.0  # First in chain

                    influencers.append((author_id, timestamp))

                if len(influencers) >= max_chain_length:
                    break

            # Calculate spread velocity
            if len(influencers) > 1:
                time_diffs = []
                for i in range(1, len(influencers)):
                    # Parse timestamps (simplified)
                    diff = 1  # Placeholder
                    time_diffs.append(diff)

                avg_diff = np.mean(time_diffs) if time_diffs else 0
                if avg_diff < 1:
                    velocity = "Rapid"
                    amplification = len(influencers)
                elif avg_diff < 3:
                    velocity = "Moderate"
                    amplification = len(influencers) * 0.6
                else:
                    velocity = "Slow"
                    amplification = len(influencers) * 0.3
            else:
                velocity = "None"
                amplification = 0

            chain = InfluenceChain(
                trend_topic=trend_topic,
                chain_length=len(influencers),
                influencers=influencers,
                estimated_spread_velocity=velocity,
                amplification_factor=amplification
            )

            logger.info(f"✅ Influence chain: {len(influencers)} authors, {velocity} spread")
            return chain

        except Exception as e:
            logger.error(f"❌ Influence chain tracing failed: {str(e)}")
            raise

    # ========================================================================
    # TOOL 3: DETECT COORDINATED CAMPAIGNS
    # ========================================================================

    def detect_campaign_patterns(
        self,
        trend_topic: str,
        article_data: List[Dict],
        similarity_threshold: float = 0.75
    ) -> Dict:
        """
        Detect coordinated promotion patterns (multiple authors pushing same narrative).
        
        Args:
            trend_topic: Topic to analyze
            article_data: Articles with full content
            similarity_threshold: Message similarity threshold
            
        Returns:
            Campaign pattern analysis
        """
        logger.info(f"🎯 Analyzing campaign patterns for: {trend_topic}")

        try:
            if not article_data:
                return {"detected": False, "patterns": []}

            # Group articles by timeframe (e.g., same day)
            timeframe_groups = {}
            for article in article_data:
                timestamp = article['timestamp']
                timeframe = timestamp[:10]  # Date only

                if timeframe not in timeframe_groups:
                    timeframe_groups[timeframe] = []
                timeframe_groups[timeframe].append(article)

            # Find coordinated patterns
            patterns = []
            for timeframe, articles in timeframe_groups.items():
                if len(articles) < 3:
                    continue

                # Check message similarity across authors
                fingerprints = {}
                for article in articles:
                    author_id = article['author_id']
                    text = article['text']

                    if author_id not in fingerprints:
                        fp = self.scribe.extract_linguistic_fingerprint(text)
                        fingerprints[author_id] = fp

                # Find pairs with high similarity
                coordinated_pairs = []
                for i, auth1 in enumerate(list(fingerprints.keys())):
                    for auth2 in list(fingerprints.keys())[i+1:]:
                        sim = self.scribe._calculate_signal_similarity(
                            fingerprints[auth1].signal_vector,
                            fingerprints[auth2].signal_vector
                        )

                        if sim > similarity_threshold:
                            coordinated_pairs.append((auth1, auth2, sim))

                if len(coordinated_pairs) >= 2:
                    pattern = {
                        "date": timeframe,
                        "authors_involved": list(set(sum([(a, b) for a, b, _ in coordinated_pairs], ()))),
                        "coordinated_pairs": len(coordinated_pairs),
                        "avg_similarity": np.mean([s for _, _, s in coordinated_pairs]),
                        "confidence": "High" if len(coordinated_pairs) >= 3 else "Medium"
                    }
                    patterns.append(pattern)
                    logger.info(f"🎯 Campaign pattern detected on {timeframe}")

            result = {
                "detected": len(patterns) > 0,
                "patterns": patterns,
                "confidence": "High" if len(patterns) >= 2 else ("Medium" if patterns else "Low")
            }

            logger.info(f"✅ Campaign analysis complete: {len(patterns)} patterns detected")
            return result

        except Exception as e:
            logger.error(f"❌ Campaign detection failed: {str(e)}")
            return {"detected": False, "patterns": [], "error": str(e)}

    # ========================================================================
    # REPORTING
    # ========================================================================

    def generate_trend_report(self, analysis: TrendAnalysis) -> Dict:
        """Generate comprehensive trend analysis report"""
        return {
            "report_type": "Trend Analysis",
            "timestamp": datetime.utcnow().isoformat(),
            "topic": analysis.topic,
            "trend_start": analysis.trend_start_date,
            "trend_intensity": f"{analysis.trend_intensity:.0f}%",
            "total_articles": analysis.article_count,
            "unique_authors": analysis.unique_authors,
            "estimated_reach": analysis.estimated_total_reach,
            "primary_drivers": [
                {
                    "author": d.author_id,
                    "score": f"{d.attribution_score:.1f}%",
                    "articles": d.article_count,
                    "reach": d.estimated_reach,
                    "first_mention": d.first_mention
                }
                for d in analysis.primary_drivers
            ],
            "amplifiers": [
                {
                    "author": a.author_id,
                    "score": f"{a.attribution_score:.1f}%",
                    "articles": a.article_count
                }
                for a in analysis.amplifiers[:5]
            ],
            "coordinated_promotion": "Yes" if analysis.coordinated_promotion else "No",
            "coordination_confidence": f"{analysis.coordination_confidence:.0f}%"
        }

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _classify_role(self, score: float, primary_threshold: float, amplifier_threshold: float) -> str:
        """Classify author role based on contribution score"""
        if score >= primary_threshold:
            return "Primary Driver"
        elif score >= amplifier_threshold:
            return "Amplifier"
        else:
            return "Adopter"

    def _detect_coordination(self, top_authors, fingerprints) -> Dict:
        """Detect if top authors are coordinated"""
        if len(top_authors) < 2:
            return {"detected": False, "confidence": 0}

        similarities = []
        for i, (auth1, _) in enumerate(top_authors):
            for auth2, _ in top_authors[i+1:]:
                if auth1 in fingerprints and auth2 in fingerprints:
                    fps1 = fingerprints[auth1]
                    fps2 = fingerprints[auth2]

                    for fp1 in fps1[:1]:  # First article only
                        for fp2 in fps2[:1]:
                            sim = self.scribe._calculate_signal_similarity(
                                fp1.signal_vector,
                                fp2.signal_vector
                            )
                            similarities.append(sim)

        if similarities:
            avg_sim = np.mean(similarities)
            return {
                "detected": avg_sim > 0.75,
                "confidence": min(100, avg_sim * 100)
            }
        else:
            return {"detected": False, "confidence": 0}


# ============================================================================
# MCP TOOL FUNCTIONS
# ============================================================================

def identify_trend_drivers_tool(trend_topic: str, articles: List[Dict]) -> Dict:
    """MCP Tool: Identify authors driving a trend"""
    correlator = TrendCorrelator()
    analysis = correlator.identify_trend_drivers(trend_topic, articles)

    return {
        "status": "success",
        "trend": trend_topic,
        "primary_drivers": len(analysis.primary_drivers),
        "amplifiers": len(analysis.amplifiers),
        "drivers": [
            {
                "author_id": d.author_id,
                "score": round(d.attribution_score, 1),
                "articles": d.article_count,
                "reach": d.estimated_reach
            }
            for d in analysis.primary_drivers
        ],
        "coordinated": analysis.coordinated_promotion,
        "coordination_confidence": round(analysis.coordination_confidence, 1)
    }


def trace_influence_tool(trend_topic: str, articles: List[Dict]) -> Dict:
    """MCP Tool: Trace influence chain"""
    correlator = TrendCorrelator()
    chain = correlator.trace_influence_chain(trend_topic, articles)

    return {
        "status": "success",
        "trend": trend_topic,
        "chain_length": chain.chain_length,
        "influencers": chain.influencers,
        "spread_velocity": chain.estimated_spread_velocity,
        "amplification": round(chain.amplification_factor, 2)
    }


if __name__ == "__main__":
    print("\n" + "="*80)
    print("📈 TREND CORRELATOR DEMO")
    print("="*80 + "\n")

    print("✅ TREND CORRELATOR READY")
    print("="*80 + "\n")
