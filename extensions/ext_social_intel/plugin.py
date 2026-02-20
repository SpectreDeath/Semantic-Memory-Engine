"""
Social Media Intelligence Crawler Plugin

Main plugin class for monitoring social media platforms for disinformation patterns
and sentiment analysis. Integrates with multiple social media APIs to track
hashtag campaigns, analyze sentiment spread, and detect coordinated disinformation
campaigns across platforms.

Key Features:
- Multi-platform API integration (Twitter/X, Reddit, Facebook, YouTube, TikTok)
- Real-time hashtag campaign tracking
- Cross-platform sentiment analysis
- Coordinated campaign detection using pattern recognition
- Geolocation-based content analysis
- Rate limiting and quota management
- Content moderation and NSFW filtering
"""

import logging
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Core SME dependencies
from src.core.plugin_base import BasePlugin
from .api_manager import SocialMediaAPIManager
from .sentiment_analyzer import SentimentAnalyzer
from .campaign_detector import CampaignDetector
from .content_moderator import ContentModerator

logger = logging.getLogger("SME.SocialIntelligence")

class PlatformType(Enum):
    """Supported social media platforms."""
    TWITTER = "twitter"
    REDDIT = "reddit"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"

@dataclass
class HashtagCampaign:
    """Represents a tracked hashtag campaign."""
    hashtag: str
    platform: PlatformType
    start_time: datetime
    end_time: Optional[datetime]
    total_posts: int
    unique_users: int
    sentiment_score: float
    bot_activity_score: float
    geolocation_data: Dict[str, int]
    related_hashtags: List[str]

@dataclass
class SentimentAnalysis:
    """Represents sentiment analysis results."""
    platform: PlatformType
    topic: str
    time_window: int
    positive_sentiment: float
    negative_sentiment: float
    neutral_sentiment: float
    sentiment_trend: List[float]
    influential_posts: List[Dict]
    user_engagement: Dict[str, int]

@dataclass
class CoordinatedCampaign:
    """Represents a detected coordinated campaign."""
    campaign_id: str
    platforms_involved: List[PlatformType]
    start_time: datetime
    end_time: Optional[datetime]
    keywords: List[str]
    estimated_reach: int
    coordination_score: float
    detected_patterns: List[str]
    source_accounts: List[str]
    content_samples: List[Dict]

class SocialIntelligenceCrawler(BasePlugin):
    """
    Main plugin class for the Social Media Intelligence Crawler extension.
    
    This extension provides comprehensive social media monitoring capabilities
    for detecting disinformation campaigns, analyzing sentiment patterns, and
    identifying coordinated activities across multiple platforms.
    """
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        
        # Initialize core components
        self.api_manager = SocialMediaAPIManager()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.campaign_detector = CampaignDetector()
        self.content_moderator = ContentModerator()
        
        # Configuration
        self.config = self._load_config()
        self.active_campaigns: Dict[str, HashtagCampaign] = {}
        self.monitoring_tasks: List[asyncio.Task] = []
        
        logger.info(f"[{self.plugin_id}] Social Intelligence Crawler initialized")

    async def on_startup(self):
        """Initialize the social media intelligence crawler."""
        try:
            # Initialize API connections
            await self.api_manager.initialize_apis()
            
            # Load existing campaigns from database
            await self._load_active_campaigns()
            
            # Start background monitoring tasks
            self._start_monitoring_tasks()
            
            logger.info(f"[{self.plugin_id}] Social Intelligence Crawler started successfully")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to start: {e}")
            raise

    def get_tools(self) -> List[Any]:
        """Return available tools for this extension."""
        return [
            self.monitor_hashtag_campaign,
            self.analyze_sentiment_spread,
            self.detect_coordinated_campaigns,
            self.track_influencer_activity,
            self.analyze_geolocation_patterns,
            self.generate_social_media_report
        ]

    async def monitor_hashtag_campaign(self, hashtag: str, time_window: int = 24, 
                                     platforms: Optional[List[str]] = None) -> Dict:
        """
        Track hashtag usage patterns and bot activity across specified platforms.
        
        Args:
            hashtag: The hashtag to monitor (without # symbol)
            time_window: Time window in hours to analyze
            platforms: List of platforms to monitor (defaults to all configured)
            
        Returns:
            Dict containing campaign analysis results
        """
        try:
            logger.info(f"Starting hashtag campaign monitoring: #{hashtag}")
            
            # Validate and normalize hashtag
            clean_hashtag = hashtag.lstrip('#').lower()
            if not clean_hashtag:
                return {"error": "Invalid hashtag provided"}
            
            # Determine platforms to monitor
            target_platforms = platforms or list(PlatformType.__members__.keys())
            platform_types = [PlatformType[p.upper()] for p in target_platforms if p.upper() in PlatformType.__members__]
            
            # Collect data from all specified platforms
            campaign_data = {}
            total_posts = 0
            unique_users = set()
            
            for platform in platform_types:
                try:
                    platform_data = await self.api_manager.get_hashtag_data(
                        platform, clean_hashtag, time_window
                    )
                    
                    if platform_data:
                        campaign_data[platform.value] = platform_data
                        total_posts += platform_data.get('post_count', 0)
                        unique_users.update(platform_data.get('unique_users', []))
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {platform.value}: {e}")
                    campaign_data[platform.value] = {"error": str(e)}
            
            # Analyze bot activity
            bot_analysis = await self._analyze_bot_activity(campaign_data)
            
            # Analyze sentiment
            sentiment_analysis = await self._analyze_campaign_sentiment(campaign_data)
            
            # Store campaign data
            campaign = HashtagCampaign(
                hashtag=clean_hashtag,
                platform=PlatformType.TWITTER,  # Primary platform
                start_time=datetime.now(),
                end_time=None,
                total_posts=total_posts,
                unique_users=len(unique_users),
                sentiment_score=sentiment_analysis.get('overall_sentiment', 0.0),
                bot_activity_score=bot_analysis.get('bot_score', 0.0),
                geolocation_data=self._extract_geolocation_data(campaign_data),
                related_hashtags=self._extract_related_hashtags(campaign_data)
            )
            
            self.active_campaigns[clean_hashtag] = campaign
            
            # Save to database
            await self._save_campaign_data(campaign, campaign_data)
            
            result = {
                "hashtag": f"#{clean_hashtag}",
                "time_window_hours": time_window,
                "platforms_monitored": [p.value for p in platform_types],
                "total_posts": total_posts,
                "unique_users": len(unique_users),
                "bot_activity_analysis": bot_analysis,
                "sentiment_analysis": sentiment_analysis,
                "geolocation_distribution": campaign.geolocation_data,
                "related_hashtags": campaign.related_hashtags,
                "campaign_id": clean_hashtag,
                "status": "active"
            }
            
            logger.info(f"Hashtag campaign monitoring completed: #{clean_hashtag}")
            return result
            
        except Exception as e:
            logger.error(f"Error in hashtag campaign monitoring: {e}")
            return {"error": str(e), "hashtag": hashtag}

    async def analyze_sentiment_spread(self, topic: str, platforms: Optional[List[str]] = None,
                                     time_range: int = 48) -> Dict:
        """
        Analyze sentiment propagation across platforms for a given topic.
        
        Args:
            topic: Topic to analyze sentiment for
            platforms: List of platforms to analyze
            time_range: Time range in hours to analyze
            
        Returns:
            Dict containing sentiment analysis results
        """
        try:
            logger.info(f"Starting sentiment analysis for topic: {topic}")
            
            # Determine platforms
            target_platforms = platforms or list(PlatformType.__members__.keys())
            platform_types = [PlatformType[p.upper()] for p in target_platforms if p.upper() in PlatformType.__members__]
            
            sentiment_results = {}
            
            for platform in platform_types:
                try:
                    # Fetch content for topic
                    content_data = await self.api_manager.get_topic_content(
                        platform, topic, time_range
                    )
                    
                    if content_data:
                        # Analyze sentiment
                        sentiment = await self.sentiment_analyzer.analyze_platform_sentiment(
                            platform, content_data, topic
                        )
                        
                        sentiment_results[platform.value] = sentiment
                        
                except Exception as e:
                    logger.warning(f"Failed sentiment analysis for {platform.value}: {e}")
                    sentiment_results[platform.value] = {"error": str(e)}
            
            # Cross-platform sentiment correlation
            correlation_analysis = await self._analyze_sentiment_correlation(sentiment_results)
            
            # Generate trend analysis
            trend_analysis = await self._analyze_sentiment_trends(sentiment_results)
            
            result = {
                "topic": topic,
                "time_range_hours": time_range,
                "platforms_analyzed": [p.value for p in platform_types],
                "platform_sentiment": sentiment_results,
                "cross_platform_correlation": correlation_analysis,
                "sentiment_trends": trend_analysis,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Sentiment analysis completed for topic: {topic}")
            return result
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {"error": str(e), "topic": topic}

    async def detect_coordinated_campaigns(self, keywords: List[str], 
                                         time_window: int = 24,
                                         platforms: Optional[List[str]] = None) -> Dict:
        """
        Identify coordinated disinformation campaigns using pattern recognition.
        
        Args:
            keywords: List of keywords to monitor for coordination
            time_window: Time window in hours to analyze
            platforms: List of platforms to monitor
            
        Returns:
            Dict containing coordinated campaign detection results
        """
        try:
            logger.info(f"Starting coordinated campaign detection for keywords: {keywords}")
            
            # Determine platforms
            target_platforms = platforms or list(PlatformType.__members__.keys())
            platform_types = [PlatformType[p.upper()] for p in target_platforms if p.upper() in PlatformType.__members__]
            
            # Collect data across platforms
            campaign_data = {}
            for platform in platform_types:
                try:
                    platform_data = await self.api_manager.get_keyword_data(
                        platform, keywords, time_window
                    )
                    if platform_data:
                        campaign_data[platform.value] = platform_data
                except Exception as e:
                    logger.warning(f"Failed to fetch keyword data for {platform.value}: {e}")
            
            # Detect coordination patterns
            coordination_analysis = await self.campaign_detector.analyze_coordination_patterns(
                campaign_data, keywords
            )
            
            # Identify source accounts and amplification networks
            network_analysis = await self._analyze_amplification_networks(campaign_data)
            
            # Generate risk assessment
            risk_assessment = await self._assess_coordination_risk(coordination_analysis)
            
            result = {
                "keywords": keywords,
                "time_window_hours": time_window,
                "platforms_monitored": [p.value for p in platform_types],
                "coordination_analysis": coordination_analysis,
                "amplification_networks": network_analysis,
                "risk_assessment": risk_assessment,
                "detected_campaigns": coordination_analysis.get('detected_campaigns', []),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Coordinated campaign detection completed for keywords: {keywords}")
            return result
            
        except Exception as e:
            logger.error(f"Error in coordinated campaign detection: {e}")
            return {"error": str(e), "keywords": keywords}

    async def track_influencer_activity(self, influencer_handles: List[str], 
                                      time_window: int = 168) -> Dict:
        """
        Track activity and influence patterns of specific accounts.
        
        Args:
            influencer_handles: List of influencer handles to track
            time_window: Time window in hours to analyze
            
        Returns:
            Dict containing influencer activity analysis
        """
        try:
            logger.info(f"Starting influencer tracking for: {influencer_handles}")
            
            influencer_data = {}
            
            for handle in influencer_handles:
                try:
                    # Fetch influencer data across platforms
                    platform_data = await self.api_manager.get_influencer_data(
                        handle, time_window
                    )
                    
                    if platform_data:
                        # Analyze influence metrics
                        influence_metrics = await self._analyze_influence_metrics(
                            handle, platform_data
                        )
                        
                        influencer_data[handle] = {
                            "platform_data": platform_data,
                            "influence_metrics": influence_metrics
                        }
                        
                except Exception as e:
                    logger.warning(f"Failed to track influencer {handle}: {e}")
                    influencer_data[handle] = {"error": str(e)}
            
            # Cross-platform influence analysis
            cross_platform_analysis = await self._analyze_cross_platform_influence(influencer_data)
            
            result = {
                "influencers_tracked": influencer_handles,
                "time_window_hours": time_window,
                "influencer_data": influencer_data,
                "cross_platform_analysis": cross_platform_analysis,
                "tracking_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Influencer tracking completed for {len(influencer_handles)} accounts")
            return result
            
        except Exception as e:
            logger.error(f"Error in influencer tracking: {e}")
            return {"error": str(e), "influencers": influencer_handles}

    async def analyze_geolocation_patterns(self, topic: str, platforms: Optional[List[str]] = None) -> Dict:
        """
        Analyze geographic distribution and patterns of social media activity.
        
        Args:
            topic: Topic to analyze geolocation patterns for
            platforms: List of platforms to analyze
            
        Returns:
            Dict containing geolocation analysis results
        """
        try:
            logger.info(f"Starting geolocation analysis for topic: {topic}")
            
            # Determine platforms
            target_platforms = platforms or list(PlatformType.__members__.keys())
            platform_types = [PlatformType[p.upper()] for p in target_platforms if p.upper() in PlatformType.__members__]
            
            geolocation_data = {}
            
            for platform in platform_types:
                try:
                    # Fetch geotagged content
                    geo_content = await self.api_manager.get_geotagged_content(
                        platform, topic
                    )
                    
                    if geo_content:
                        # Analyze geographic patterns
                        geo_analysis = await self._analyze_geographic_patterns(
                            platform, geo_content, topic
                        )
                        
                        geolocation_data[platform.value] = geo_analysis
                        
                except Exception as e:
                    logger.warning(f"Failed geolocation analysis for {platform.value}: {e}")
                    geolocation_data[platform.value] = {"error": str(e)}
            
            # Generate geographic heatmap data
            heatmap_data = await self._generate_geographic_heatmap(geolocation_data)
            
            result = {
                "topic": topic,
                "platforms_analyzed": [p.value for p in platform_types],
                "geolocation_analysis": geolocation_data,
                "geographic_heatmap": heatmap_data,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Geolocation analysis completed for topic: {topic}")
            return result
            
        except Exception as e:
            logger.error(f"Error in geolocation analysis: {e}")
            return {"error": str(e), "topic": topic}

    async def generate_social_media_report(self, report_type: str, 
                                         parameters: Dict[str, Any]) -> Dict:
        """
        Generate comprehensive social media intelligence reports.
        
        Args:
            report_type: Type of report to generate
            parameters: Parameters for the report generation
            
        Returns:
            Dict containing the generated report
        """
        try:
            logger.info(f"Generating social media report: {report_type}")
            
            # Generate report based on type
            if report_type == "hashtag_analysis":
                result = await self._generate_hashtag_report(parameters)
            elif report_type == "sentiment_overview":
                result = await self._generate_sentiment_report(parameters)
            elif report_type == "coordination_assessment":
                result = await self._generate_coordination_report(parameters)
            elif report_type == "influencer_impact":
                result = await self._generate_influencer_report(parameters)
            elif report_type == "geographic_distribution":
                result = await self._generate_geographic_report(parameters)
            else:
                return {"error": f"Unknown report type: {report_type}"}
            
            result["report_type"] = report_type
            result["generated_at"] = datetime.now().isoformat()
            result["plugin_version"] = self.manifest.get("version", "1.0.0")
            
            logger.info(f"Social media report generated: {report_type}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating social media report: {e}")
            return {"error": str(e), "report_type": report_type}

    # Helper methods
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration for the social media crawler."""
        return {
            "rate_limits": {
                "twitter": 300,  # requests per 15 minutes
                "reddit": 60,    # requests per minute
                "facebook": 200, # requests per hour
                "youtube": 10000, # requests per day
                "tiktok": 1000   # requests per hour
            },
            "content_filters": {
                "nsfw_threshold": 0.8,
                "spam_threshold": 0.7,
                "bot_threshold": 0.6
            },
            "analysis_settings": {
                "sentiment_model": "bert-base-multilingual",
                "coordination_window": 3600,  # 1 hour
                "geolocation_precision": "city"
            }
        }

    async def _analyze_bot_activity(self, campaign_data: Dict) -> Dict:
        """Analyze bot activity patterns in campaign data."""
        bot_scores = []
        suspicious_patterns = []
        
        for platform, data in campaign_data.items():
            if "error" not in data:
                # Analyze posting patterns, account ages, engagement ratios
                bot_score = await self.campaign_detector.analyze_bot_patterns(data)
                bot_scores.append(bot_score)
                
                if bot_score > self.config["content_filters"]["bot_threshold"]:
                    suspicious_patterns.append({
                        "platform": platform,
                        "bot_score": bot_score,
                        "patterns": await self.campaign_detector.identify_suspicious_patterns(data)
                    })
        
        return {
            "bot_score": sum(bot_scores) / len(bot_scores) if bot_scores else 0.0,
            "suspicious_patterns": suspicious_patterns,
            "total_suspicious_accounts": len(suspicious_patterns)
        }

    async def _analyze_campaign_sentiment(self, campaign_data: Dict) -> Dict:
        """Analyze overall sentiment for a hashtag campaign."""
        all_content = []
        
        for platform, data in campaign_data.items():
            if "error" not in data:
                all_content.extend(data.get("posts", []))
        
        if not all_content:
            return {"overall_sentiment": 0.0, "sentiment_breakdown": {}}
        
        # Analyze sentiment across all content
        sentiment_result = await self.sentiment_analyzer.analyze_content_sentiment(all_content)
        
        return {
            "overall_sentiment": sentiment_result.get("average_sentiment", 0.0),
            "sentiment_breakdown": sentiment_result.get("sentiment_distribution", {}),
            "confidence": sentiment_result.get("confidence", 0.0)
        }

    def _extract_geolocation_data(self, campaign_data: Dict) -> Dict[str, int]:
        """Extract geographic distribution from campaign data."""
        geo_distribution = {}
        
        for platform, data in campaign_data.items():
            if "error" not in data:
                for post in data.get("posts", []):
                    location = post.get("location", "Unknown")
                    geo_distribution[location] = geo_distribution.get(location, 0) + 1
        
        return geo_distribution

    def _extract_related_hashtags(self, campaign_data: Dict) -> List[str]:
        """Extract related hashtags from campaign data."""
        related_hashtags = set()
        
        for platform, data in campaign_data.items():
            if "error" not in data:
                for post in data.get("posts", []):
                    hashtags = post.get("hashtags", [])
                    related_hashtags.update(hashtags)
        
        # Remove the main hashtag
        main_hashtag = next(iter(campaign_data.keys()), "").lower()
        related_hashtags.discard(main_hashtag)
        
        return list(related_hashtags)

    async def _analyze_sentiment_correlation(self, sentiment_results: Dict) -> Dict:
        """Analyze correlation between sentiment across platforms."""
        correlations = {}
        
        platforms = list(sentiment_results.keys())
        for i, platform1 in enumerate(platforms):
            for platform2 in platforms[i+1:]:
                if "error" not in sentiment_results[platform1] and "error" not in sentiment_results[platform2]:
                    correlation = await self.sentiment_analyzer.calculate_sentiment_correlation(
                        sentiment_results[platform1], sentiment_results[platform2]
                    )
                    correlations[f"{platform1}_{platform2}"] = correlation
        
        return {
            "platform_correlations": correlations,
            "average_correlation": sum(correlations.values()) / len(correlations) if correlations else 0.0,
            "high_correlation_pairs": [k for k, v in correlations.items() if v > 0.7]
        }

    async def _analyze_sentiment_trends(self, sentiment_results: Dict) -> Dict:
        """Analyze sentiment trends over time."""
        trends = {}
        
        for platform, data in sentiment_results.items():
            if "error" not in data:
                trend = await self.sentiment_analyzer.analyze_sentiment_trend(data)
                trends[platform] = trend
        
        return trends

    async def _analyze_amplification_networks(self, campaign_data: Dict) -> Dict:
        """Analyze amplification networks in coordinated campaigns."""
        networks = {}
        
        for platform, data in campaign_data.items():
            if "error" not in data:
                network = await self.campaign_detector.analyze_amplification_network(data)
                networks[platform] = network
        
        return networks

    async def _assess_coordination_risk(self, coordination_analysis: Dict) -> Dict:
        """Assess the risk level of detected coordination."""
        risk_factors = coordination_analysis.get("risk_factors", [])
        risk_score = sum(factor.get("weight", 0) for factor in risk_factors)
        
        risk_level = "LOW"
        if risk_score > 80:
            risk_level = "CRITICAL"
        elif risk_score > 60:
            risk_level = "HIGH"
        elif risk_score > 40:
            risk_level = "MEDIUM"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendations": await self._generate_risk_recommendations(risk_level)
        }

    async def _analyze_influence_metrics(self, handle: str, platform_data: Dict) -> Dict:
        """Analyze influence metrics for a specific account."""
        metrics = {}
        
        for platform, data in platform_data.items():
            if "error" not in data:
                metrics[platform] = await self.campaign_detector.analyze_influence_metrics(
                    handle, data
                )
        
        return metrics

    async def _analyze_cross_platform_influence(self, influencer_data: Dict) -> Dict:
        """Analyze cross-platform influence patterns."""
        cross_platform_metrics = {}
        
        for handle, data in influencer_data.items():
            if "error" not in data:
                cross_platform_metrics[handle] = await self.campaign_detector.analyze_cross_platform_influence(
                    handle, data["platform_data"]
                )
        
        return cross_platform_metrics

    async def _analyze_geographic_patterns(self, platform: PlatformType, 
                                         geo_content: List[Dict], topic: str) -> Dict:
        """Analyze geographic patterns in geotagged content."""
        return await self.campaign_detector.analyze_geographic_patterns(
            platform, geo_content, topic
        )

    async def _generate_geographic_heatmap(self, geolocation_data: Dict) -> Dict:
        """Generate geographic heatmap data."""
        heatmap = {}
        
        for platform, data in geolocation_data.items():
            if "error" not in data:
                heatmap[platform] = await self.campaign_detector.generate_geographic_heatmap(data)
        
        return heatmap

    # Report generation methods
    
    async def _generate_hashtag_report(self, parameters: Dict) -> Dict:
        """Generate hashtag analysis report."""
        hashtag = parameters.get("hashtag")
        time_window = parameters.get("time_window", 24)
        
        if not hashtag:
            return {"error": "Hashtag parameter required"}
        
        campaign_data = self.active_campaigns.get(hashtag)
        if not campaign_data:
            return {"error": f"No active campaign found for #{hashtag}"}
        
        return {
            "hashtag": f"#{hashtag}",
            "campaign_summary": {
                "total_posts": campaign_data.total_posts,
                "unique_users": campaign_data.unique_users,
                "sentiment_score": campaign_data.sentiment_score,
                "bot_activity_score": campaign_data.bot_activity_score
            },
            "geographic_distribution": campaign_data.geolocation_data,
            "related_hashtags": campaign_data.related_hashtags,
            "time_range": f"{time_window} hours"
        }

    async def _generate_sentiment_report(self, parameters: Dict) -> Dict:
        """Generate sentiment overview report."""
        topic = parameters.get("topic")
        platforms = parameters.get("platforms", [])
        
        if not topic:
            return {"error": "Topic parameter required"}
        
        return {
            "topic": topic,
            "platforms": platforms,
            "summary": "Sentiment analysis report generated",
            "details": "Full sentiment breakdown available in detailed analysis"
        }

    async def _generate_coordination_report(self, parameters: Dict) -> Dict:
        """Generate coordination assessment report."""
        keywords = parameters.get("keywords", [])
        
        if not keywords:
            return {"error": "Keywords parameter required"}
        
        return {
            "keywords": keywords,
            "summary": "Coordination assessment report generated",
            "details": "Full coordination analysis available in detailed assessment"
        }

    async def _generate_influencer_report(self, parameters: Dict) -> Dict:
        """Generate influencer impact report."""
        influencers = parameters.get("influencers", [])
        
        if not influencers:
            return {"error": "Influencers parameter required"}
        
        return {
            "influencers": influencers,
            "summary": "Influencer impact report generated",
            "details": "Full influencer analysis available in detailed report"
        }

    async def _generate_geographic_report(self, parameters: Dict) -> Dict:
        """Generate geographic distribution report."""
        topic = parameters.get("topic")
        
        if not topic:
            return {"error": "Topic parameter required"}
        
        return {
            "topic": topic,
            "summary": "Geographic distribution report generated",
            "details": "Full geographic analysis available in detailed report"
        }

    async def _generate_risk_recommendations(self, risk_level: str) -> List[str]:
        """Generate risk mitigation recommendations based on risk level."""
        recommendations = {
            "LOW": [
                "Continue monitoring for changes in activity patterns",
                "Maintain current defensive measures"
            ],
            "MEDIUM": [
                "Increase monitoring frequency",
                "Prepare response protocols",
                "Engage with community to counter misinformation"
            ],
            "HIGH": [
                "Activate incident response team",
                "Implement enhanced monitoring",
                "Coordinate with platform moderators",
                "Prepare public communication strategy"
            ],
            "CRITICAL": [
                "Immediate escalation to senior management",
                "Activate full incident response protocol",
                "Coordinate with law enforcement if necessary",
                "Implement emergency communication plan",
                "Consider platform-level countermeasures"
            ]
        }
        
        return recommendations.get(risk_level, ["Monitor situation closely"])

    async def _load_active_campaigns(self):
        """Load existing active campaigns from database."""
        # Implementation would load from database
        pass

    def _start_monitoring_tasks(self):
        """Start background monitoring tasks."""
        # Implementation would start async monitoring tasks
        pass

    async def _save_campaign_data(self, campaign: HashtagCampaign, data: Dict):
        """Save campaign data to database."""
        # Implementation would save to database
        pass

def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    """Register the Social Intelligence Crawler extension."""
    return SocialIntelligenceCrawler(manifest, nexus_api)