"""Tests for ext_social_intel extension modules."""

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from extensions.ext_social_intel.api_manager import (
    APIConfig,
    PlatformType,
    RateLimiter,
    SocialMediaAPIManager,
)
from extensions.ext_social_intel.campaign_detector import (
    AmplificationNetwork,
    BotPattern,
    CampaignDetector,
    CoordinationPattern,
    RiskAssessment,
)
from extensions.ext_social_intel.content_moderator import (
    ContentModerator,
    ModerationResult,
    UserModerationProfile,
)
from extensions.ext_social_intel.plugin import SocialIntelligenceCrawler
from extensions.ext_social_intel.sentiment_analyzer import (
    SentimentAnalyzer,
    SentimentCorrelation,
    SentimentResult,
    SentimentTrend,
)

# ============================================================
# Phase 1: Data classes and simple initialization tests
# ============================================================


class TestPlatformType:
    """Tests for PlatformType enum."""

    def test_platform_type_values(self):
        assert PlatformType.TWITTER.value == "twitter"
        assert PlatformType.REDDIT.value == "reddit"
        assert PlatformType.FACEBOOK.value == "facebook"
        assert PlatformType.YOUTUBE.value == "youtube"
        assert PlatformType.TIKTOK.value == "tiktok"


class TestAPIConfig:
    """Tests for APIConfig dataclass."""

    def test_api_config_creation(self):
        config = APIConfig(
            platform=PlatformType.TWITTER,
            api_key="test_key",
            api_secret="secret",
            access_token="token",
            access_token_secret="token_secret",
            client_id="client",
            client_secret="client_secret",
            rate_limit=300,
            rate_window=900,
        )
        assert config.platform == PlatformType.TWITTER
        assert config.api_key == "test_key"
        assert config.enabled is True

    def test_api_config_disabled(self):
        config = APIConfig(
            platform=PlatformType.REDDIT,
            api_key=None,
            api_secret=None,
            access_token=None,
            access_token_secret=None,
            client_id=None,
            client_secret=None,
            rate_limit=60,
            rate_window=60,
            enabled=False,
        )
        assert config.enabled is False


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_rate_limiter_init(self):
        limiter = RateLimiter(PlatformType.TWITTER, 300, 900)
        assert limiter.platform == PlatformType.TWITTER
        assert limiter.max_requests == 300
        assert limiter.window_seconds == 900
        assert limiter.requests == []

    @pytest.mark.asyncio
    async def test_acquire_below_limit(self):
        limiter = RateLimiter(PlatformType.TWITTER, 10, 60)
        result = await limiter.acquire()
        assert result is True
        assert len(limiter.requests) == 1


class TestSentimentResult:
    """Tests for SentimentResult dataclass."""

    def test_sentiment_result_creation(self):
        result = SentimentResult(
            text="positive text",
            sentiment_score=0.8,
            sentiment_label="positive",
            confidence=0.9,
            language="en",
            bias_indicators=["emotional_manipulation"],
            entities=["Alice"],
            keywords=["test"],
        )
        assert result.sentiment_score == 0.8
        assert result.sentiment_label == "positive"


class TestSentimentAnalyzer:
    """Tests for SentimentAnalyzer class."""

    def test_sentiment_analyzer_init(self):
        analyzer = SentimentAnalyzer()
        assert analyzer.bias_lexicon is not None
        assert analyzer.sentiment_lexicon is not None
        assert "political_bias" in analyzer.bias_lexicon

    def test_clean_text(self):
        analyzer = SentimentAnalyzer()
        text = "Check out this https://example.com link and @user"
        cleaned = analyzer._clean_text(text)
        assert "https://" not in cleaned
        assert "@" not in cleaned
        assert cleaned.islower()

    def test_detect_language(self):
        analyzer = SentimentAnalyzer()
        lang = analyzer._detect_language("any text")
        assert lang == "en"

    def test_calculate_sentiment_score_positive(self):
        analyzer = SentimentAnalyzer()
        score = analyzer._calculate_sentiment_score("this is great and amazing")
        assert score > 0

    def test_calculate_sentiment_score_negative(self):
        analyzer = SentimentAnalyzer()
        score = analyzer._calculate_sentiment_score("this is terrible and awful")
        assert score < 0

    def test_calculate_sentiment_score_neutral(self):
        analyzer = SentimentAnalyzer()
        score = analyzer._calculate_sentiment_score("the standard everyday text")
        assert -0.1 <= score <= 0.1

    def test_calculate_confidence(self):
        analyzer = SentimentAnalyzer()
        confidence = analyzer._calculate_confidence("great amazing wonderful", 0.5)
        assert 0.0 <= confidence <= 1.0

    def test_detect_bias_indicators_conspiracy(self):
        analyzer = SentimentAnalyzer()
        indicators = analyzer._detect_bias_indicators("they control everything")
        assert "conspiracy_indicators" in indicators

    def test_detect_bias_indicators_absolutist(self):
        analyzer = SentimentAnalyzer()
        indicators = analyzer._detect_bias_indicators("always and never always")
        assert "absolutist_language" in indicators

    def test_extract_entities_hashtag(self):
        analyzer = SentimentAnalyzer()
        entities = analyzer._extract_entities("Check out #awesome #topic")
        assert "#awesome" in entities or "#topic" in entities

    def test_extract_keywords(self):
        analyzer = SentimentAnalyzer()
        keywords = analyzer._extract_keywords("This is a test message for keywords")
        assert isinstance(keywords, list)

    def test_calculate_trend_direction_increasing(self):
        analyzer = SentimentAnalyzer()
        scores = [0.1, 0.3, 0.5, 0.7]
        direction = analyzer._calculate_trend_direction(scores)
        assert direction == "increasing"

    def test_calculate_trend_direction_decreasing(self):
        analyzer = SentimentAnalyzer()
        scores = [0.7, 0.5, 0.3, 0.1]
        direction = analyzer._calculate_trend_direction(scores)
        assert direction == "decreasing"

    def test_calculate_trend_direction_stable(self):
        analyzer = SentimentAnalyzer()
        scores = [0.3, 0.31, 0.32, 0.3]
        direction = analyzer._calculate_trend_direction(scores)
        assert direction == "stable"


class TestCampaignDetector:
    """Tests for CampaignDetector class."""

    def test_campaign_detector_init(self):
        detector = CampaignDetector()
        assert detector.bot_detection_rules is not None
        assert detector.coordination_thresholds is not None

    def test_initialize_bot_rules(self):
        detector = CampaignDetector()
        assert "posting_frequency" in detector.bot_detection_rules

    def test_initialize_coordination_thresholds(self):
        detector = CampaignDetector()
        assert detector.coordination_thresholds["time_correlation"] == 0.7

    def test_calculate_text_similarity(self):
        detector = CampaignDetector()
        similarity = detector._calculate_text_similarity("hello world", "hello earth")
        assert 0.0 <= similarity <= 1.0

    def test_calculate_coordination_score(self):
        detector = CampaignDetector()
        score = detector._calculate_coordination_score(0.5, 0.6, 0.7, 0.4)
        assert 0.0 <= score <= 1.0


class TestContentModerator:
    """Tests for ContentModerator class."""

    def test_content_moderator_init(self):
        moderator = ContentModerator()
        assert moderator.nsfw_lexicon is not None
        assert moderator.spam_patterns is not None

    def test_load_nsfw_lexicon(self):
        moderator = ContentModerator()
        assert "porn" in moderator.nsfw_lexicon

    def test_analyze_nsfw_content_clean(self):
        moderator = ContentModerator()
        score = moderator._analyze_nsfw_content("safe family friendly content")
        assert score == 0.0

    def test_analyze_nsfw_content_flagged(self):
        moderator = ContentModerator()
        score = moderator._analyze_nsfw_content("adult sexual content")
        assert score > 0

    def test_analyze_spam_content_spam(self):
        moderator = ContentModerator()
        score = moderator._analyze_spam_content("buy now click here free money!")
        assert score > 0

    def test_analyze_hate_speech_clean(self):
        moderator = ContentModerator()
        score = moderator._analyze_hate_speech("peaceful coexistence")
        assert score == 0.0

    def test_analyze_content_quality_too_short(self):
        moderator = ContentModerator()
        score = moderator._analyze_content_quality("short")
        assert score > 0

    def test_determine_moderation_level_block(self):
        moderator = ContentModerator()
        level = moderator._determine_moderation_level(0.9)
        assert level == "block"

    def test_determine_moderation_level_flag(self):
        moderator = ContentModerator()
        level = moderator._determine_moderation_level(0.65)
        assert level == "flag"

    def test_determine_moderation_level_allow(self):
        moderator = ContentModerator()
        level = moderator._determine_moderation_level(0.3)
        assert level == "allow"

    def test_get_user_profile_new(self):
        moderator = ContentModerator()
        profile = moderator._get_user_profile("new_user")
        assert profile.user_id == "new_user"
        assert profile.trust_score == 1.0

    def test_set_moderation_policy(self):
        moderator = ContentModerator()
        moderator.set_moderation_policy("nsfw_threshold", 0.8)
        assert moderator.moderation_policies["nsfw_threshold"] == 0.8


# ============================================================
# Phase 2: SocialMediaAPIManager and advanced tests
# ============================================================


@pytest.mark.phase2
class TestSocialMediaAPIManager:
    """Tests for SocialMediaAPIManager class."""

    def test_api_manager_init(self):
        manager = SocialMediaAPIManager()
        assert manager.is_initialized is False
        assert len(manager.api_endpoints) == 5

    @pytest.mark.asyncio
    async def test_initialize_apis(self):
        manager = SocialMediaAPIManager()
        await manager.initialize_apis()
        assert manager.is_initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self):
        manager = SocialMediaAPIManager()
        await manager.initialize_apis()
        await manager.shutdown()
        assert manager.is_initialized is False

    def test_build_hashtag_url_twitter(self):
        manager = SocialMediaAPIManager()
        url = manager._build_hashtag_url(PlatformType.TWITTER, "test", 24)
        assert "test" in url
        assert "twitter.com" in url

    def test_build_topic_url_reddit(self):
        manager = SocialMediaAPIManager()
        url = manager._build_topic_url(PlatformType.REDDIT, "topic", 48)
        assert "topic" in url


@pytest.mark.phase2
class TestSentimentAnalyzerAsync:
    """Async tests for SentimentAnalyzer."""

    @pytest.mark.asyncio
    async def test_analyze_single_text(self):
        analyzer = SentimentAnalyzer()
        result = await analyzer._analyze_single_text("This is great!")
        assert isinstance(result, SentimentResult)

    @pytest.mark.asyncio
    async def test_analyze_platform_sentiment(self):
        analyzer = SentimentAnalyzer()
        result = await analyzer.analyze_platform_sentiment("twitter", {"posts": []}, "test")
        assert "platform" in result

    @pytest.mark.asyncio
    async def test_analyze_content_sentiment_empty(self):
        analyzer = SentimentAnalyzer()
        result = await analyzer.analyze_content_sentiment([])
        assert result["total_analyzed"] == 0


@pytest.mark.phase2
class TestContentModeratorAsync:
    """Async tests for ContentModerator."""

    @pytest.mark.asyncio
    async def test_moderate_content_empty(self):
        moderator = ContentModerator()
        result = await moderator.moderate_content({"id": "123", "text": "", "author_id": "user"})
        assert result.moderation_level == "allow"

    @pytest.mark.asyncio
    async def test_moderate_content_hate_speech(self):
        moderator = ContentModerator()
        result = await moderator.moderate_content(
            {
                "id": "123",
                "text": "I hate them and want to kill them",
                "author_id": "user",
            }
        )
        assert "hate_speech" in result.detected_issues

    @pytest.mark.asyncio
    async def test_moderate_batch(self):
        moderator = ContentModerator()
        results = await moderator.moderate_batch(
            [
                {"id": "1", "text": "safe content", "author_id": "user"},
                {"id": "2", "text": "spam buy now!", "author_id": "user"},
            ]
        )
        assert len(results) == 2


# ============================================================
# Phase 3: Plugin integration tests
# ============================================================


@pytest.mark.phase3
class TestSocialIntelligenceCrawler:
    """Tests for SocialIntelligenceCrawler plugin."""

    def test_plugin_init(self):
        manifest = {"name": "social_intel", "version": "1.0.0"}
        nexus_api = MagicMock()
        crawler = SocialIntelligenceCrawler(manifest, nexus_api)
        assert crawler.api_manager is not None
        assert crawler.sentiment_analyzer is not None

    def test_get_tools(self):
        manifest = {"name": "social_intel", "version": "1.0.0"}
        nexus_api = MagicMock()
        crawler = SocialIntelligenceCrawler(manifest, nexus_api)
        tools = crawler.get_tools()
        assert len(tools) == 6

    @pytest.mark.asyncio
    async def test_monitor_hashtag_campaign_invalid(self):
        manifest = {"name": "social_intel", "version": "1.0.0"}
        nexus_api = MagicMock()
        crawler = SocialIntelligenceCrawler(manifest, nexus_api)
        result = await crawler.monitor_hashtag_campaign("")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_generate_report_unknown_type(self):
        manifest = {"name": "social_intel", "version": "1.0.0"}
        nexus_api = MagicMock()
        crawler = SocialIntelligenceCrawler(manifest, nexus_api)
        result = await crawler.generate_social_media_report("unknown", {})
        assert "error" in result
