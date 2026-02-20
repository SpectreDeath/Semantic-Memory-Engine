"""
Campaign Detector

Advanced pattern recognition system for detecting coordinated disinformation
campaigns across social media platforms. Uses machine learning and statistical
analysis to identify bot networks, amplification patterns, and coordinated
messaging strategies.

Key Features:
- Bot pattern detection and analysis
- Coordinated campaign identification
- Amplification network analysis
- Cross-platform coordination detection
- Risk assessment and scoring
- Temporal pattern analysis
- Geographic correlation analysis
"""

import logging
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from collections import defaultdict, Counter

logger = logging.getLogger("SME.SocialIntelligence.CampaignDetector")

@dataclass
class BotPattern:
    """Detected bot pattern."""
    pattern_type: str
    confidence: float
    indicators: List[str]
    affected_accounts: List[str]
    posting_frequency: Dict[str, int]
    content_similarity: float

@dataclass
class AmplificationNetwork:
    """Detected amplification network."""
    network_id: str
    source_accounts: List[str]
    amplification_accounts: List[str]
    target_content: List[str]
    amplification_factor: float
    network_structure: Dict[str, List[str]]
    coordination_score: float

@dataclass
class CoordinationPattern:
    """Detected coordination pattern."""
    pattern_id: str
    platforms_involved: List[str]
    keywords: List[str]
    time_correlation: float
    content_similarity: float
    account_overlap: float
    coordination_score: float
    detected_at: datetime

@dataclass
class RiskAssessment:
    """Risk assessment for detected coordination."""
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    risk_score: float
    risk_factors: List[Dict[str, Any]]
    impact_assessment: Dict[str, Any]
    recommendations: List[str]

class CampaignDetector:
    """
    Advanced pattern recognition system for detecting coordinated disinformation
    campaigns across social media platforms.
    """
    
    def __init__(self):
        self.bot_detection_rules = self._initialize_bot_rules()
        self.coordination_thresholds = self._initialize_coordination_thresholds()
        self.amplification_patterns = self._initialize_amplification_patterns()
        self.temporal_analyzer = self._initialize_temporal_analyzer()
        
        logger.info("Campaign Detector initialized")

    def _initialize_bot_rules(self) -> Dict[str, Any]:
        """Initialize bot detection rules and patterns."""
        return {
            "posting_frequency": {
                "threshold": 10,  # posts per hour
                "window": 3600    # 1 hour in seconds
            },
            "content_similarity": {
                "threshold": 0.8,  # 80% similarity
                "min_posts": 5
            },
            "account_age": {
                "threshold": 30,  # days
                "min_activity": 100
            },
            "engagement_ratio": {
                "likes_to_posts": 0.1,  # Very low engagement
                "retweets_to_posts": 0.05
            },
            "posting_time": {
                "uniform_distribution": 0.8,  # Posts at same time
                "sleep_hours": [0, 1, 2, 3, 4, 5]  # Posts during sleep hours
            }
        }

    def _initialize_coordination_thresholds(self) -> Dict[str, float]:
        """Initialize coordination detection thresholds."""
        return {
            "time_correlation": 0.7,      # 70% time correlation
            "content_similarity": 0.6,    # 60% content similarity
            "account_overlap": 0.3,       # 30% account overlap
            "keyword_correlation": 0.8,   # 80% keyword correlation
            "amplification_factor": 5.0,  # 5x normal amplification
            "coordination_score": 0.7     # 70% overall coordination
        }

    def _initialize_amplification_patterns(self) -> Dict[str, Any]:
        """Initialize amplification pattern detection."""
        return {
            "echo_chamber": {
                "min_accounts": 10,
                "interaction_threshold": 0.8,
                "content_repetition": 0.7
            },
            "astroturfing": {
                "organic_appearance": 0.3,
                "sudden_activity": 0.8,
                "coordinated_timing": 0.7
            },
            "viral_amplification": {
                "exponential_growth": 2.0,
                "short_duration": 3600,  # 1 hour
                "high_engagement": 0.9
            }
        }

    def _initialize_temporal_analyzer(self) -> Dict[str, Any]:
        """Initialize temporal pattern analysis."""
        return {
            "burst_detection": {
                "window_size": 300,    # 5 minutes
                "threshold_multiplier": 3.0
            },
            "synchronization": {
                "time_tolerance": 60,  # 1 minute
                "min_correlated_posts": 5
            },
            "campaign_duration": {
                "min_duration": 3600,  # 1 hour
                "max_duration": 86400  # 24 hours
            }
        }

    async def analyze_coordination_patterns(self, campaign_data: Dict, 
                                          keywords: List[str]) -> Dict:
        """
        Analyze coordination patterns across platforms.
        
        Args:
            campaign_data: Data from multiple platforms
            keywords: Keywords being coordinated
            
        Returns:
            Dict containing coordination analysis results
        """
        try:
            coordination_results = []
            risk_factors = []
            
            # Analyze each platform
            for platform, data in campaign_data.items():
                if "error" not in data:
                    platform_coordination = await self._analyze_platform_coordination(
                        platform, data, keywords
                    )
                    coordination_results.append(platform_coordination)
            
            # Cross-platform coordination analysis
            cross_platform_analysis = await self._analyze_cross_platform_coordination(
                campaign_data, coordination_results
            )
            
            # Risk assessment
            risk_assessment = await self._assess_coordination_risk(
                coordination_results, cross_platform_analysis
            )
            
            return {
                "coordination_results": coordination_results,
                "cross_platform_analysis": cross_platform_analysis,
                "risk_assessment": risk_assessment,
                "detected_campaigns": self._identify_campaigns(coordination_results),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing coordination patterns: {e}")
            return {
                "error": str(e),
                "coordination_results": [],
                "cross_platform_analysis": {},
                "risk_assessment": {},
                "detected_campaigns": []
            }

    async def analyze_bot_patterns(self, platform_data: Dict) -> Dict:
        """
        Analyze bot activity patterns in platform data.
        
        Args:
            platform_data: Data from a specific platform
            
        Returns:
            Dict containing bot analysis results
        """
        try:
            posts = platform_data.get("posts", [])
            users = platform_data.get("users", {})
            
            if not posts:
                return {"bot_score": 0.0, "bot_patterns": [], "suspicious_accounts": []}
            
            # Analyze posting patterns
            posting_analysis = self._analyze_posting_patterns(posts)
            
            # Analyze content similarity
            content_analysis = self._analyze_content_similarity(posts)
            
            # Analyze account behavior
            account_analysis = self._analyze_account_behavior(posts, users)
            
            # Calculate overall bot score
            bot_score = self._calculate_bot_score(posting_analysis, content_analysis, account_analysis)
            
            # Identify bot patterns
            bot_patterns = self._identify_bot_patterns(posting_analysis, content_analysis, account_analysis)
            
            # Identify suspicious accounts
            suspicious_accounts = self._identify_suspicious_accounts(account_analysis)
            
            return {
                "bot_score": bot_score,
                "bot_patterns": bot_patterns,
                "suspicious_accounts": suspicious_accounts,
                "detailed_analysis": {
                    "posting_analysis": posting_analysis,
                    "content_analysis": content_analysis,
                    "account_analysis": account_analysis
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing bot patterns: {e}")
            return {
                "error": str(e),
                "bot_score": 0.0,
                "bot_patterns": [],
                "suspicious_accounts": []
            }

    async def analyze_amplification_network(self, platform_data: Dict) -> Dict:
        """
        Analyze amplification networks in platform data.
        
        Args:
            platform_data: Data from a specific platform
            
        Returns:
            Dict containing amplification network analysis
        """
        try:
            posts = platform_data.get("posts", [])
            
            if not posts:
                return {
                    "amplification_networks": [],
                    "amplification_score": 0.0,
                    "source_accounts": [],
                    "target_content": []
                }
            
            # Build interaction graph
            interaction_graph = self._build_interaction_graph(posts)
            
            # Identify amplification patterns
            amplification_patterns = self._identify_amplification_patterns(
                posts, interaction_graph
            )
            
            # Calculate amplification score
            amplification_score = self._calculate_amplification_score(amplification_patterns)
            
            # Identify source accounts and target content
            source_accounts = self._identify_source_accounts(amplification_patterns)
            target_content = self._identify_target_content(amplification_patterns)
            
            return {
                "amplification_networks": amplification_patterns,
                "amplification_score": amplification_score,
                "source_accounts": source_accounts,
                "target_content": target_content,
                "interaction_graph": interaction_graph
            }
            
        except Exception as e:
            logger.error(f"Error analyzing amplification network: {e}")
            return {
                "error": str(e),
                "amplification_networks": [],
                "amplification_score": 0.0,
                "source_accounts": [],
                "target_content": []
            }

    async def analyze_influence_metrics(self, handle: str, platform_data: Dict) -> Dict:
        """
        Analyze influence metrics for a specific account.
        
        Args:
            handle: Account handle
            platform_data: Data from a specific platform
            
        Returns:
            Dict containing influence analysis
        """
        try:
            posts = platform_data.get("posts", [])
            users = platform_data.get("users", {})
            
            # Get account data
            account_data = users.get(handle, {})
            
            # Analyze posting metrics
            posting_metrics = self._analyze_posting_metrics(posts, handle)
            
            # Analyze engagement metrics
            engagement_metrics = self._analyze_engagement_metrics(posts, handle)
            
            # Analyze network influence
            network_influence = self._analyze_network_influence(posts, handle)
            
            # Calculate overall influence score
            influence_score = self._calculate_influence_score(
                posting_metrics, engagement_metrics, network_influence
            )
            
            return {
                "handle": handle,
                "influence_score": influence_score,
                "posting_metrics": posting_metrics,
                "engagement_metrics": engagement_metrics,
                "network_influence": network_influence,
                "influence_type": self._classify_influence_type(influence_score, engagement_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing influence metrics for {handle}: {e}")
            return {
                "error": str(e),
                "handle": handle,
                "influence_score": 0.0,
                "posting_metrics": {},
                "engagement_metrics": {},
                "network_influence": {},
                "influence_type": "unknown"
            }

    async def analyze_cross_platform_influence(self, handle: str, 
                                             platform_data: Dict) -> Dict:
        """
        Analyze cross-platform influence patterns.
        
        Args:
            handle: Account handle
            platform_data: Data across multiple platforms
            
        Returns:
            Dict containing cross-platform influence analysis
        """
        try:
            platform_scores = {}
            total_influence = 0.0
            platform_count = 0
            
            for platform, data in platform_data.items():
                if "error" not in data:
                    influence_result = await self.analyze_influence_metrics(handle, data)
                    platform_scores[platform] = influence_result
                    total_influence += influence_result.get("influence_score", 0.0)
                    platform_count += 1
            
            if platform_count == 0:
                return {
                    "handle": handle,
                    "cross_platform_score": 0.0,
                    "platform_scores": {},
                    "influence_consistency": 0.0
                }
            
            # Calculate cross-platform metrics
            cross_platform_score = total_influence / platform_count
            influence_consistency = self._calculate_influence_consistency(platform_scores)
            
            return {
                "handle": handle,
                "cross_platform_score": cross_platform_score,
                "platform_scores": platform_scores,
                "influence_consistency": influence_consistency,
                "platform_diversity": len(platform_scores)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing cross-platform influence for {handle}: {e}")
            return {
                "error": str(e),
                "handle": handle,
                "cross_platform_score": 0.0,
                "platform_scores": {},
                "influence_consistency": 0.0
            }

    async def analyze_geographic_patterns(self, platform: str, 
                                        geo_content: List[Dict], 
                                        topic: str) -> Dict:
        """
        Analyze geographic patterns in geotagged content.
        
        Args:
            platform: Platform name
            geo_content: Geotagged content
            topic: Topic being analyzed
            
        Returns:
            Dict containing geographic pattern analysis
        """
        try:
            if not geo_content:
                return {
                    "platform": platform,
                    "topic": topic,
                    "geographic_distribution": {},
                    "anomaly_detection": {},
                    "coordination_indicators": {}
                }
            
            # Analyze geographic distribution
            geo_distribution = self._analyze_geographic_distribution(geo_content)
            
            # Detect geographic anomalies
            anomaly_detection = self._detect_geographic_anomalies(geo_distribution)
            
            # Identify coordination indicators
            coordination_indicators = self._identify_coordination_indicators(geo_content)
            
            return {
                "platform": platform,
                "topic": topic,
                "geographic_distribution": geo_distribution,
                "anomaly_detection": anomaly_detection,
                "coordination_indicators": coordination_indicators
            }
            
        except Exception as e:
            logger.error(f"Error analyzing geographic patterns for {platform}: {e}")
            return {
                "error": str(e),
                "platform": platform,
                "topic": topic,
                "geographic_distribution": {},
                "anomaly_detection": {},
                "coordination_indicators": {}
            }

    async def generate_geographic_heatmap(self, geolocation_data: Dict) -> Dict:
        """
        Generate geographic heatmap data.
        
        Args:
            geolocation_data: Geographic data from platforms
            
        Returns:
            Dict containing heatmap data
        """
        try:
            heatmap_data = {}
            
            for platform, data in geolocation_data.items():
                if "error" not in data:
                    platform_heatmap = self._generate_platform_heatmap(data)
                    heatmap_data[platform] = platform_heatmap
            
            return {
                "heatmap_data": heatmap_data,
                "global_heatmap": self._generate_global_heatmap(heatmap_data),
                "anomaly_regions": self._identify_anomaly_regions(heatmap_data)
            }
            
        except Exception as e:
            logger.error(f"Error generating geographic heatmap: {e}")
            return {
                "error": str(e),
                "heatmap_data": {},
                "global_heatmap": {},
                "anomaly_regions": []
            }

    # Private helper methods
    
    async def _analyze_platform_coordination(self, platform: str, 
                                           platform_data: Dict, 
                                           keywords: List[str]) -> Dict:
        """Analyze coordination patterns for a specific platform."""
        posts = platform_data.get("posts", [])
        
        if not posts:
            return {
                "platform": platform,
                "coordination_score": 0.0,
                "time_correlation": 0.0,
                "content_similarity": 0.0,
                "keyword_correlation": 0.0,
                "account_overlap": 0.0
            }
        
        # Analyze time correlation
        time_correlation = self._analyze_time_correlation(posts)
        
        # Analyze content similarity
        content_similarity = self._analyze_content_similarity_coordination(posts, keywords)
        
        # Analyze keyword correlation
        keyword_correlation = self._analyze_keyword_correlation(posts, keywords)
        
        # Analyze account overlap
        account_overlap = self._analyze_account_overlap(posts)
        
        # Calculate coordination score
        coordination_score = self._calculate_coordination_score(
            time_correlation, content_similarity, keyword_correlation, account_overlap
        )
        
        return {
            "platform": platform,
            "coordination_score": coordination_score,
            "time_correlation": time_correlation,
            "content_similarity": content_similarity,
            "keyword_correlation": keyword_correlation,
            "account_overlap": account_overlap,
            "posts_analyzed": len(posts)
        }

    async def _analyze_cross_platform_coordination(self, campaign_data: Dict, 
                                                 coordination_results: List[Dict]) -> Dict:
        """Analyze cross-platform coordination patterns."""
        platforms = list(campaign_data.keys())
        
        if len(platforms) < 2:
            return {
                "cross_platform_correlation": 0.0,
                "amplification_factor": 1.0,
                "synchronization_score": 0.0,
                "multi_platform_campaigns": []
            }
        
        # Calculate cross-platform correlation
        cross_platform_correlation = self._calculate_cross_platform_correlation(coordination_results)
        
        # Calculate amplification factor
        amplification_factor = self._calculate_amplification_factor(coordination_results)
        
        # Calculate synchronization score
        synchronization_score = self._calculate_synchronization_score(coordination_results)
        
        # Identify multi-platform campaigns
        multi_platform_campaigns = self._identify_multi_platform_campaigns(coordination_results)
        
        return {
            "cross_platform_correlation": cross_platform_correlation,
            "amplification_factor": amplification_factor,
            "synchronization_score": synchronization_score,
            "multi_platform_campaigns": multi_platform_campaigns,
            "platforms_involved": platforms
        }

    async def _assess_coordination_risk(self, coordination_results: List[Dict], 
                                      cross_platform_analysis: Dict) -> RiskAssessment:
        """Assess risk level of detected coordination."""
        # Calculate overall risk score
        coordination_scores = [result.get("coordination_score", 0.0) for result in coordination_results]
        cross_platform_score = cross_platform_analysis.get("cross_platform_correlation", 0.0)
        
        overall_risk_score = (np.mean(coordination_scores) + cross_platform_score) / 2
        
        # Determine risk level
        if overall_risk_score >= 0.8:
            risk_level = "CRITICAL"
        elif overall_risk_score >= 0.6:
            risk_level = "HIGH"
        elif overall_risk_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(coordination_results, cross_platform_analysis)
        
        # Generate recommendations
        recommendations = self._generate_coordination_recommendations(risk_level)
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_score=overall_risk_score,
            risk_factors=risk_factors,
            impact_assessment={},
            recommendations=recommendations
        )

    def _analyze_posting_patterns(self, posts: List[Dict]) -> Dict:
        """Analyze posting patterns for bot detection."""
        user_posts = defaultdict(list)
        
        for post in posts:
            user_id = post.get("author_id")
            if user_id:
                user_posts[user_id].append(post)
        
        analysis = {}
        
        for user_id, user_post_list in user_posts.items():
            # Calculate posting frequency
            if len(user_post_list) > 1:
                timestamps = [post.get("created_at") for post in user_post_list if post.get("created_at")]
                if len(timestamps) > 1:
                    time_diffs = []
                    for i in range(1, len(timestamps)):
                        try:
                            time_diff = abs((timestamps[i] - timestamps[i-1]).total_seconds())
                            time_diffs.append(time_diff)
                        except:
                            pass
                    
                    if time_diffs:
                        avg_interval = np.mean(time_diffs)
                        posting_frequency = 3600 / avg_interval if avg_interval > 0 else 0
                    else:
                        posting_frequency = 0
                else:
                    posting_frequency = 0
            else:
                posting_frequency = 0
            
            # Check for uniform posting times
            uniform_times = self._check_uniform_posting_times(user_post_list)
            
            analysis[user_id] = {
                "total_posts": len(user_post_list),
                "posting_frequency": posting_frequency,
                "uniform_times": uniform_times,
                "time_variance": np.var(time_diffs) if 'time_diffs' in locals() else 0
            }
        
        return analysis

    def _analyze_content_similarity(self, posts: List[Dict]) -> Dict:
        """Analyze content similarity for bot detection."""
        # Simple similarity calculation (would use more sophisticated methods in production)
        content_similarities = {}
        
        for i, post1 in enumerate(posts):
            text1 = post1.get("text", "").lower()
            similar_posts = []
            
            for j, post2 in enumerate(posts):
                if i != j:
                    text2 = post2.get("text", "").lower()
                    similarity = self._calculate_text_similarity(text1, text2)
                    
                    if similarity > self.bot_detection_rules["content_similarity"]["threshold"]:
                        similar_posts.append({
                            "post_id": post2.get("id"),
                            "similarity": similarity
                        })
            
            content_similarities[post1.get("id")] = {
                "similar_posts": similar_posts,
                "max_similarity": max([s["similarity"] for s in similar_posts]) if similar_posts else 0.0
            }
        
        return content_similarities

    def _analyze_account_behavior(self, posts: List[Dict], users: Dict) -> Dict:
        """Analyze account behavior patterns."""
        account_analysis = {}
        
        for post in posts:
            user_id = post.get("author_id")
            if user_id and user_id in users:
                user_data = users[user_id]
                
                # Calculate engagement ratios
                metrics = user_data.get("metrics", {})
                likes = metrics.get("like_count", 0)
                retweets = metrics.get("retweet_count", 0)
                followers = metrics.get("followers_count", 1)
                
                engagement_ratio = (likes + retweets) / max(followers, 1)
                
                # Check account age
                created_at = user_data.get("created_at")
                account_age = 0
                if created_at:
                    try:
                        account_age = (datetime.now() - created_at).days
                    except:
                        pass
                
                account_analysis[user_id] = {
                    "engagement_ratio": engagement_ratio,
                    "account_age": account_age,
                    "followers_count": followers,
                    "verified": user_data.get("verified", False)
                }
        
        return account_analysis

    def _calculate_bot_score(self, posting_analysis: Dict, 
                           content_analysis: Dict, 
                           account_analysis: Dict) -> float:
        """Calculate overall bot score."""
        bot_indicators = []
        
        # Check posting frequency
        for user_id, analysis in posting_analysis.items():
            if analysis["posting_frequency"] > self.bot_detection_rules["posting_frequency"]["threshold"]:
                bot_indicators.append(0.8)
        
        # Check content similarity
        for post_id, analysis in content_analysis.items():
            if analysis["max_similarity"] > self.bot_detection_rules["content_similarity"]["threshold"]:
                bot_indicators.append(0.7)
        
        # Check account behavior
        for user_id, analysis in account_analysis.items():
            if analysis["engagement_ratio"] < self.bot_detection_rules["engagement_ratio"]["likes_to_posts"]:
                bot_indicators.append(0.6)
            
            if analysis["account_age"] < self.bot_detection_rules["account_age"]["threshold"]:
                bot_indicators.append(0.5)
        
        return np.mean(bot_indicators) if bot_indicators else 0.0

    def _identify_bot_patterns(self, posting_analysis: Dict, 
                             content_analysis: Dict, 
                             account_analysis: Dict) -> List[BotPattern]:
        """Identify specific bot patterns."""
        patterns = []
        
        # High frequency posting pattern
        high_freq_users = [
            user_id for user_id, analysis in posting_analysis.items()
            if analysis["posting_frequency"] > self.bot_detection_rules["posting_frequency"]["threshold"]
        ]
        
        if high_freq_users:
            patterns.append(BotPattern(
                pattern_type="high_frequency_posting",
                confidence=0.8,
                indicators=["rapid_posting", "uniform_intervals"],
                affected_accounts=high_freq_users,
                posting_frequency={user: posting_analysis[user]["posting_frequency"] for user in high_freq_users},
                content_similarity=0.0
            ))
        
        # Content copying pattern
        similar_content = [
            post_id for post_id, analysis in content_analysis.items()
            if analysis["max_similarity"] > self.bot_detection_rules["content_similarity"]["threshold"]
        ]
        
        if similar_content:
            patterns.append(BotPattern(
                pattern_type="content_copying",
                confidence=0.7,
                indicators=["identical_content", "high_similarity"],
                affected_accounts=[],
                posting_frequency={},
                content_similarity=0.8
            ))
        
        return patterns

    def _identify_suspicious_accounts(self, account_analysis: Dict) -> List[str]:
        """Identify suspicious accounts based on behavior."""
        suspicious = []
        
        for user_id, analysis in account_analysis.items():
            risk_factors = 0
            
            if analysis["engagement_ratio"] < 0.1:
                risk_factors += 1
            
            if analysis["account_age"] < 30:
                risk_factors += 1
            
            if not analysis["verified"] and analysis["followers_count"] > 1000:
                risk_factors += 1
            
            if risk_factors >= 2:
                suspicious.append(user_id)
        
        return suspicious

    def _build_interaction_graph(self, posts: List[Dict]) -> Dict[str, List[str]]:
        """Build interaction graph for amplification analysis."""
        graph = defaultdict(list)
        
        for post in posts:
            user_id = post.get("author_id")
            retweeted_user = post.get("referenced_tweets", [{}])[0].get("author_id")
            
            if user_id and retweeted_user and user_id != retweeted_user:
                graph[retweeted_user].append(user_id)
        
        return dict(graph)

    def _identify_amplification_patterns(self, posts: List[Dict], 
                                       interaction_graph: Dict[str, List[str]]) -> List[AmplificationNetwork]:
        """Identify amplification patterns in the interaction graph."""
        patterns = []
        
        for source, amplifiers in interaction_graph.items():
            if len(amplifiers) >= self.amplification_patterns["echo_chamber"]["min_accounts"]:
                amplification_factor = len(amplifiers)
                
                patterns.append(AmplificationNetwork(
                    network_id=f"network_{source}",
                    source_accounts=[source],
                    amplification_accounts=amplifiers,
                    target_content=[],
                    amplification_factor=amplification_factor,
                    network_structure=interaction_graph,
                    coordination_score=amplification_factor / 10.0
                ))
        
        return patterns

    def _calculate_coordination_score(self, time_correlation: float, 
                                    content_similarity: float,
                                    keyword_correlation: float,
                                    account_overlap: float) -> float:
        """Calculate overall coordination score."""
        weights = [0.3, 0.3, 0.2, 0.2]  # Time, content, keyword, account weights
        scores = [time_correlation, content_similarity, keyword_correlation, account_overlap]
        
        return np.average(scores, weights=weights)

    def _identify_campaigns(self, coordination_results: List[Dict]) -> List[Dict]:
        """Identify coordinated campaigns from analysis results."""
        campaigns = []
        
        for result in coordination_results:
            if result.get("coordination_score", 0) > self.coordination_thresholds["coordination_score"]:
                campaigns.append({
                    "platform": result["platform"],
                    "coordination_score": result["coordination_score"],
                    "time_correlation": result["time_correlation"],
                    "content_similarity": result["content_similarity"]
                })
        
        return campaigns

    def _identify_risk_factors(self, coordination_results: List[Dict], 
                             cross_platform_analysis: Dict) -> List[Dict]:
        """Identify specific risk factors."""
        risk_factors = []
        
        for result in coordination_results:
            if result.get("coordination_score", 0) > 0.7:
                risk_factors.append({
                    "factor": "high_coordination",
                    "platform": result["platform"],
                    "score": result["coordination_score"],
                    "weight": 0.3
                })
        
        if cross_platform_analysis.get("amplification_factor", 1.0) > 5.0:
            risk_factors.append({
                "factor": "cross_platform_amplification",
                "amplification_factor": cross_platform_analysis["amplification_factor"],
                "weight": 0.4
            })
        
        return risk_factors

    def _generate_coordination_recommendations(self, risk_level: str) -> List[str]:
        """Generate recommendations based on risk level."""
        base_recommendations = [
            "Monitor the identified accounts and content closely",
            "Implement additional verification for high-risk accounts",
            "Consider platform-specific countermeasures"
        ]
        
        if risk_level == "CRITICAL":
            return base_recommendations + [
                "Escalate to senior management immediately",
                "Coordinate with platform moderators",
                "Prepare emergency response protocols"
            ]
        elif risk_level == "HIGH":
            return base_recommendations + [
                "Increase monitoring frequency",
                "Engage with community to counter misinformation",
                "Prepare public communication strategy"
            ]
        elif risk_level == "MEDIUM":
            return base_recommendations + [
                "Continue monitoring for escalation",
                "Document patterns for future reference"
            ]
        else:
            return base_recommendations

    # Additional helper methods for geographic and temporal analysis
    def _analyze_geographic_distribution(self, geo_content: List[Dict]) -> Dict:
        """Analyze geographic distribution of content."""
        distribution = defaultdict(int)
        
        for content in geo_content:
            country = content.get("country", "Unknown")
            city = content.get("city", "Unknown")
            
            distribution[f"{country}-{city}"] += 1
        
        return dict(distribution)

    def _detect_geographic_anomalies(self, geo_distribution: Dict) -> Dict:
        """Detect anomalies in geographic distribution."""
        # Simple anomaly detection based on distribution
        total_posts = sum(geo_distribution.values())
        anomalies = {}
        
        for location, count in geo_distribution.items():
            percentage = count / total_posts
            if percentage > 0.5:  # More than 50% from one location
                anomalies[location] = {
                    "count": count,
                    "percentage": percentage,
                    "anomaly_type": "concentration"
                }
        
        return anomalies

    def _identify_coordination_indicators(self, geo_content: List[Dict]) -> Dict:
        """Identify coordination indicators in geographic data."""
        indicators = {}
        
        # Check for synchronized posting from same locations
        location_posts = defaultdict(list)
        
        for content in geo_content:
            location = f"{content.get('country', 'Unknown')}-{content.get('city', 'Unknown')}"
            location_posts[location].append(content)
        
        for location, posts in location_posts.items():
            if len(posts) > 10:  # High volume from single location
                indicators[location] = {
                    "post_count": len(posts),
                    "indicator_type": "high_volume_location"
                }
        
        return indicators

    def _generate_platform_heatmap(self, geo_data: Dict) -> Dict:
        """Generate heatmap data for a specific platform."""
        return {
            "data": geo_data,
            "type": "geographic_heatmap",
            "platform_specific": True
        }

    def _generate_global_heatmap(self, heatmap_data: Dict) -> Dict:
        """Generate global heatmap combining all platforms."""
        global_data = defaultdict(int)
        
        for platform, data in heatmap_data.items():
            for location, count in data.get("data", {}).items():
                global_data[location] += count
        
        return {
            "data": dict(global_data),
            "type": "global_heatmap",
            "platforms_combined": list(heatmap_data.keys())
        }

    def _identify_anomaly_regions(self, heatmap_data: Dict) -> List[str]:
        """Identify regions with anomalous activity."""
        anomalies = []
        
        for platform, data in heatmap_data.items():
            platform_data = data.get("data", {})
            if platform_data:
                max_count = max(platform_data.values())
                threshold = max_count * 0.8  # 80% of max
                
                for location, count in platform_data.items():
                    if count >= threshold:
                        anomalies.append(f"{platform}-{location}")
        
        return anomalies

    # Additional helper methods for text analysis
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        # Simple Jaccard similarity for demonstration
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    def _check_uniform_posting_times(self, posts: List[Dict]) -> bool:
        """Check if posts are made at uniform time intervals."""
        if len(posts) < 3:
            return False
        
        timestamps = [post.get("created_at") for post in posts if post.get("created_at")]
        if len(timestamps) < 3:
            return False
        
        time_diffs = []
        for i in range(1, len(timestamps)):
            try:
                diff = abs((timestamps[i] - timestamps[i-1]).total_seconds())
                time_diffs.append(diff)
            except:
                pass
        
        if len(time_diffs) < 2:
            return False
        
        # Check if time differences are similar (within 10%)
        mean_diff = np.mean(time_diffs)
        std_diff = np.std(time_diffs)
        
        return std_diff / mean_diff < 0.1 if mean_diff > 0 else False

    def _analyze_time_correlation(self, posts: List[Dict]) -> float:
        """Analyze time correlation between posts."""
        # Simple time correlation analysis
        timestamps = [post.get("created_at") for post in posts if post.get("created_at")]
        
        if len(timestamps) < 2:
            return 0.0
        
        # Group posts by minute
        minute_groups = defaultdict(int)
        for timestamp in timestamps:
            minute_key = timestamp.replace(second=0, microsecond=0)
            minute_groups[minute_key] += 1
        
        # Calculate correlation based on burst patterns
        burst_count = sum(1 for count in minute_groups.values() if count > 5)
        total_minutes = len(minute_groups)
        
        return burst_count / total_minutes if total_minutes > 0 else 0.0

    def _analyze_content_similarity_coordination(self, posts: List[Dict], 
                                               keywords: List[str]) -> float:
        """Analyze content similarity for coordination detection."""
        keyword_posts = []
        for post in posts:
            text = post.get("text", "").lower()
            if any(keyword.lower() in text for keyword in keywords):
                keyword_posts.append(text)
        
        if len(keyword_posts) < 2:
            return 0.0
        
        # Calculate average similarity between keyword posts
        similarities = []
        for i, text1 in enumerate(keyword_posts):
            for j, text2 in enumerate(keyword_posts):
                if i != j:
                    similarity = self._calculate_text_similarity(text1, text2)
                    similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0.0

    def _analyze_keyword_correlation(self, posts: List[Dict], 
                                   keywords: List[str]) -> float:
        """Analyze keyword correlation in posts."""
        keyword_usage = defaultdict(int)
        
        for post in posts:
            text = post.get("text", "").lower()
            for keyword in keywords:
                if keyword.lower() in text:
                    keyword_usage[keyword.lower()] += 1
        
        if len(keyword_usage) < 2:
            return 0.0
        
        # Calculate correlation based on co-occurrence
        total_posts = len(posts)
        correlations = []
        
        keyword_list = list(keyword_usage.keys())
        for i, kw1 in enumerate(keyword_list):
            for j, kw2 in enumerate(keyword_list):
                if i != j:
                    # Simple co-occurrence correlation
                    kw1_posts = keyword_usage[kw1]
                    kw2_posts = keyword_usage[kw2]
                    correlation = min(kw1_posts, kw2_posts) / max(kw1_posts, kw2_posts)
                    correlations.append(correlation)
        
        return np.mean(correlations) if correlations else 0.0

    def _analyze_account_overlap(self, posts: List[Dict]) -> float:
        """Analyze account overlap between posts."""
        users = set()
        for post in posts:
            user_id = post.get("author_id")
            if user_id:
                users.add(user_id)
        
        # For coordination, we want to see if the same accounts are posting
        # This is a simplified version - in reality would compare across platforms
        return len(users) / len(posts) if posts else 0.0

    def _calculate_cross_platform_correlation(self, coordination_results: List[Dict]) -> float:
        """Calculate correlation between platforms."""
        if len(coordination_results) < 2:
            return 0.0
        
        scores = [result.get("coordination_score", 0.0) for result in coordination_results]
        return np.mean(scores)

    def _calculate_amplification_factor(self, coordination_results: List[Dict]) -> float:
        """Calculate amplification factor across platforms."""
        amplification_scores = []
        
        for result in coordination_results:
            time_corr = result.get("time_correlation", 0.0)
            content_sim = result.get("content_similarity", 0.0)
            amplification_scores.append(time_corr + content_sim)
        
        return np.mean(amplification_scores) * 10 if amplification_scores else 1.0

    def _calculate_synchronization_score(self, coordination_results: List[Dict]) -> float:
        """Calculate synchronization score between platforms."""
        time_correlations = [result.get("time_correlation", 0.0) for result in coordination_results]
        return np.mean(time_correlations) if time_correlations else 0.0

    def _identify_multi_platform_campaigns(self, coordination_results: List[Dict]) -> List[Dict]:
        """Identify campaigns spanning multiple platforms."""
        campaigns = []
        
        high_coordination = [
            result for result in coordination_results
            if result.get("coordination_score", 0.0) > 0.7
        ]
        
        if len(high_coordination) >= 2:
            campaigns.append({
                "campaign_id": "multi_platform_1",
                "platforms": [result["platform"] for result in high_coordination],
                "coordination_score": np.mean([result["coordination_score"] for result in high_coordination]),
                "start_time": datetime.now().isoformat()
            })
        
        return campaigns

    def _analyze_posting_metrics(self, posts: List[Dict], handle: str) -> Dict:
        """Analyze posting metrics for an account."""
        user_posts = [post for post in posts if post.get("author_id") == handle]
        
        return {
            "total_posts": len(user_posts),
            "avg_engagement": np.mean([post.get("metrics", {}).get("like_count", 0) for post in user_posts]) if user_posts else 0,
            "post_frequency": len(user_posts) / 7,  # Posts per week (simplified)
            "content_diversity": self._calculate_content_diversity(user_posts)
        }

    def _analyze_engagement_metrics(self, posts: List[Dict], handle: str) -> Dict:
        """Analyze engagement metrics for an account."""
        user_posts = [post for post in posts if post.get("author_id") == handle]
        
        engagements = []
        for post in user_posts:
            metrics = post.get("metrics", {})
            engagements.append(metrics.get("like_count", 0) + metrics.get("retweet_count", 0))
        
        return {
            "avg_engagement": np.mean(engagements) if engagements else 0,
            "engagement_rate": (np.mean(engagements) / 1000) if engagements else 0,  # Simplified
            "reach_estimate": sum(engagements) * 10 if engagements else 0,  # Simplified
            "viral_posts": sum(1 for e in engagements if e > 1000)
        }

    def _analyze_network_influence(self, posts: List[Dict], handle: str) -> Dict:
        """Analyze network influence metrics."""
        # Count mentions and retweets
        mentions = 0
        retweets = 0
        
        for post in posts:
            text = post.get("text", "")
            if f"@{handle}" in text:
                mentions += 1
            if post.get("referenced_tweets"):
                retweets += 1
        
        return {
            "mention_count": mentions,
            "retweet_count": retweets,
            "influence_network_size": mentions + retweets,
            "network_diversity": len(set(post.get("author_id") for post in posts if f"@{handle}" in post.get("text", "")))
        }

    def _calculate_influence_score(self, posting_metrics: Dict, 
                                 engagement_metrics: Dict, 
                                 network_influence: Dict) -> float:
        """Calculate overall influence score."""
        posting_score = min(posting_metrics["post_frequency"] / 10, 1.0)
        engagement_score = min(engagement_metrics["engagement_rate"], 1.0)
        network_score = min(network_influence["influence_network_size"] / 100, 1.0)
        
        return (posting_score * 0.3 + engagement_score * 0.5 + network_score * 0.2)

    def _classify_influence_type(self, influence_score: float, 
                               engagement_metrics: Dict) -> str:
        """Classify type of influence."""
        if influence_score > 0.8:
            return "mega_influencer"
        elif influence_score > 0.6:
            return "macro_influencer"
        elif influence_score > 0.4:
            return "micro_influencer"
        elif engagement_metrics["viral_posts"] > 5:
            return "viral_content_creator"
        else:
            return "regular_user"

    def _calculate_influence_consistency(self, platform_scores: Dict) -> float:
        """Calculate consistency of influence across platforms."""
        scores = [data.get("influence_score", 0.0) for data in platform_scores.values()]
        return 1.0 - (np.std(scores) / np.mean(scores)) if np.mean(scores) > 0 else 0.0