"""
Social Media Intelligence Crawler Extension

Purpose: Monitor social media platforms for disinformation patterns and sentiment analysis
Target Platforms: Twitter/X, Reddit, Facebook, YouTube, TikTok
Key Features: Hashtag campaign tracking, sentiment analysis, coordinated campaign detection

Architecture:
    - Multi-platform API integration
    - Real-time streaming and batch processing
    - Advanced sentiment analysis with bias detection
    - Coordinated campaign pattern recognition
    - Geolocation-based content analysis
    - Rate limiting and quota management
    - Content moderation and NSFW filtering

Integration:
    Layer 0 (Harvester) → Layer 2 (Loom) → Layer 3 (Synapse) → Layer 7 (Beacon)
    
    Social media content → Harvester.fetch_semantic_markdown() → Clean content
    → Loom.distill_web_content() → Atomic facts about sentiment/trends
    → Synapse consolidation for pattern detection
    → Beacon visualization of coordinated campaigns
"""

__version__ = "1.0.0"
__author__ = "SME Team"
__description__ = "Social Media Intelligence Crawler for disinformation detection"

from .plugin import SocialIntelligenceCrawler
from .api_manager import SocialMediaAPIManager
from .sentiment_analyzer import SentimentAnalyzer
from .campaign_detector import CampaignDetector
from .content_moderator import ContentModerator

__all__ = [
    'SocialIntelligenceCrawler',
    'SocialMediaAPIManager', 
    'SentimentAnalyzer',
    'CampaignDetector',
    'ContentModerator'
]