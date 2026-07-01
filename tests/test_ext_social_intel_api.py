"""Additional tests for ext_social_intel API manager - full coverage."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from extensions.ext_social_intel.api_manager import (
    APIConfig,
    PlatformType,
    RateLimiter,
    SocialMediaAPIManager,
)


@pytest.mark.phase1
class TestRateLimiterFull:
    """Additional tests for RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_at_limit(self):
        limiter = RateLimiter(PlatformType.TWITTER, 2, 60)
        # Fill up to limit
        await limiter.acquire()
        await limiter.acquire()
        # Should wait and then succeed
        await limiter.acquire()
        assert len(limiter.requests) >= 1

    @pytest.mark.asyncio
    async def test_rate_limiter_clears_old(self):
        import time

        limiter = RateLimiter(PlatformType.TWITTER, 10, 1)  # 1 second window
        # Add old request
        limiter.requests.append(time.time() - 2)
        result = await limiter.acquire()
        assert result is True
        # Old request should be cleared
        assert len([r for r in limiter.requests if time.time() - r < 1]) == 1


@pytest.mark.phase1
class TestSocialMediaAPIManagerFull:
    """Additional tests for SocialMediaAPIManager class."""

    def test_api_manager_init(self):
        manager = SocialMediaAPIManager()
        assert len(manager.api_endpoints) == 5

    @pytest.mark.asyncio
    async def test_initialize_apis_exception(self):
        manager = SocialMediaAPIManager()
        with patch.object(manager, "_load_api_configs", side_effect=Exception("test error")):
            with pytest.raises(Exception):
                await manager.initialize_apis()

    @pytest.mark.asyncio
    async def test_shutdown_without_session(self):
        manager = SocialMediaAPIManager()
        await manager.shutdown()
        assert manager.is_initialized is False

    def test_get_default_headers_twitter_with_token(self):
        manager = SocialMediaAPIManager()
        config = APIConfig(
            platform=PlatformType.TWITTER,
            api_key=None,
            api_secret=None,
            access_token="token123",
            access_token_secret=None,
            client_id=None,
            client_secret=None,
            rate_limit=100,
            rate_window=60,
            enabled=True,
        )
        manager.platform_configs[PlatformType.TWITTER] = config
        headers = manager._get_default_headers(PlatformType.TWITTER)
        assert "Authorization" in headers
        assert "Bearer token123" in headers["Authorization"]

    def test_get_default_headers_reddit_with_token(self):
        manager = SocialMediaAPIManager()
        config = APIConfig(
            platform=PlatformType.REDDIT,
            api_key=None,
            api_secret=None,
            access_token="token123",
            access_token_secret=None,
            client_id=None,
            client_secret=None,
            rate_limit=100,
            rate_window=60,
            enabled=True,
        )
        manager.platform_configs[PlatformType.REDDIT] = config
        headers = manager._get_default_headers(PlatformType.REDDIT)
        assert "Authorization" in headers

    def test_build_hashtag_url_twitter(self):
        manager = SocialMediaAPIManager()
        url = manager._build_hashtag_url(PlatformType.TWITTER, "test", 24)
        assert "test" in url
        assert "twitter.com" in url

    def test_build_hashtag_url_reddit(self):
        manager = SocialMediaAPIManager()
        url = manager._build_hashtag_url(PlatformType.REDDIT, "test", 24)
        assert "test" in url

    def test_build_hashtag_url_facebook(self):
        manager = SocialMediaAPIManager()
        url = manager._build_hashtag_url(PlatformType.FACEBOOK, "test", 24)
        assert "test" in url

    def test_build_hashtag_url_youtube(self):
        manager = SocialMediaAPIManager()
        url = manager._build_hashtag_url(PlatformType.YOUTUBE, "test", 24)
        assert "test" in url

    def test_build_hashtag_url_tiktok(self):
        manager = SocialMediaAPIManager()
        url = manager._build_hashtag_url(PlatformType.TIKTOK, "test", 24)
        assert "test" in url

    def test_build_topic_url_twitter(self):
        manager = SocialMediaAPIManager()
        url = manager._build_topic_url(PlatformType.TWITTER, "topic", 48)
        assert "topic" in url

    def test_build_influencer_url_twitter(self):
        manager = SocialMediaAPIManager()
        url = manager._build_influencer_url(PlatformType.TWITTER, "handle")
        assert "handle" in url

    def test_build_influencer_url_reddit(self):
        manager = SocialMediaAPIManager()
        url = manager._build_influencer_url(PlatformType.REDDIT, "user")
        assert "/user/" in url

    def test_build_geotagged_url_twitter(self):
        manager = SocialMediaAPIManager()
        url = manager._build_geotagged_url(PlatformType.TWITTER, "topic")
        assert "topic" in url
        assert "geo" in url

    def test_parse_hashtag_response_twitter(self):
        manager = SocialMediaAPIManager()
        data = {
            "data": [
                {
                    "id": "1",
                    "text": "hello",
                    "author_id": "a1",
                    "created_at": "now",
                    "public_metrics": {},
                    "entities": {"hashtags": []},
                }
            ],
            "includes": {
                "users": [
                    {
                        "id": "a1",
                        "username": "u1",
                        "name": "n1",
                        "verified": False,
                        "public_metrics": {},
                    }
                ]
            },
        }
        result = manager._parse_hashtag_response(PlatformType.TWITTER, data, "test")
        assert "hashtag" in result
        assert "post_count" in result

    def test_parse_hashtag_response_reddit(self):
        manager = SocialMediaAPIManager()
        data = {
            "data": {
                "children": [{"data": {"id": "1", "author": "a1", "created_utc": 1, "score": 10}}]
            }
        }
        result = manager._parse_hashtag_response(PlatformType.REDDIT, data, "test")
        assert "hashtag" in result

    def test_parse_influencer_response_twitter(self):
        manager = SocialMediaAPIManager()
        data = {
            "data": {
                "id": "1",
                "name": "name",
                "username": "u",
                "verified": True,
                "public_metrics": {},
            }
        }
        result = manager._parse_influencer_response(PlatformType.TWITTER, data, "handle")
        assert "handle" in result
        assert "verified" in result

    def test_parse_influencer_response_reddit(self):
        manager = SocialMediaAPIManager()
        data = {"data": {"name": "name", "created_utc": 1, "comment_karma": 100, "link_karma": 50}}
        result = manager._parse_influencer_response(PlatformType.REDDIT, data, "handle")
        assert "handle" in result

    def test_parse_geotagged_response_twitter(self):
        manager = SocialMediaAPIManager()
        data = {"data": [{"id": "1", "text": "hello", "geo": {"coordinates": {}, "place": {}}}]}
        result = manager._parse_geotagged_response(PlatformType.TWITTER, data, "topic")
        assert len(result) == 1

    def test_parse_geotagged_response_no_geo(self):
        manager = SocialMediaAPIManager()
        data = {"data": [{"id": "1", "text": "hello"}]}
        result = manager._parse_geotagged_response(PlatformType.TWITTER, data, "topic")
        assert len(result) == 0

    def test_get_default_headers_no_config(self):
        manager = SocialMediaAPIManager()
        headers = manager._get_default_headers(PlatformType.TWITTER)
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Content-Type" in headers

    def test_get_default_headers_facebook_with_token(self):
        manager = SocialMediaAPIManager()
        config = APIConfig(
            platform=PlatformType.FACEBOOK,
            api_key=None,
            api_secret=None,
            access_token="fb_token",
            access_token_secret=None,
            client_id=None,
            client_secret=None,
            rate_limit=100,
            rate_window=60,
            enabled=True,
        )
        manager.platform_configs[PlatformType.FACEBOOK] = config
        headers = manager._get_default_headers(PlatformType.FACEBOOK)
        assert "Authorization" in headers

    def test_get_default_headers_youtube_with_api_key(self):
        manager = SocialMediaAPIManager()
        config = APIConfig(
            platform=PlatformType.YOUTUBE,
            api_key="youtube_key",
            api_secret=None,
            access_token=None,
            access_token_secret=None,
            client_id=None,
            client_secret=None,
            rate_limit=100,
            rate_window=60,
            enabled=True,
        )
        manager.platform_configs[PlatformType.YOUTUBE] = config
        headers = manager._get_default_headers(PlatformType.YOUTUBE)
        assert "X-API-Key" in headers

    def test_get_default_headers_tiktok_with_token(self):
        manager = SocialMediaAPIManager()
        config = APIConfig(
            platform=PlatformType.TIKTOK,
            api_key=None,
            api_secret=None,
            access_token="tiktok_token",
            access_token_secret=None,
            client_id=None,
            client_secret=None,
            rate_limit=100,
            rate_window=60,
            enabled=True,
        )
        manager.platform_configs[PlatformType.TIKTOK] = config
        headers = manager._get_default_headers(PlatformType.TIKTOK)
        assert "Authorization" in headers

    @pytest.mark.asyncio
    async def test_get_hashtag_data_not_initialized(self):
        manager = SocialMediaAPIManager()
        result = await manager.get_hashtag_data(PlatformType.TWITTER, "test")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_topic_content_not_initialized(self):
        manager = SocialMediaAPIManager()
        result = await manager.get_topic_content(PlatformType.TWITTER, "topic")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_keyword_data_not_initialized(self):
        manager = SocialMediaAPIManager()
        result = await manager.get_keyword_data(PlatformType.TWITTER, ["test"])
        assert "error" in result

    def test_build_hashtag_url_fallback(self):
        manager = SocialMediaAPIManager()
        url = manager._build_hashtag_url(PlatformType.FACEBOOK, "test", 24)
        assert "test" in url

    def test_build_topic_url_all_platforms(self):
        manager = SocialMediaAPIManager()
        for platform in [
            PlatformType.REDDIT,
            PlatformType.FACEBOOK,
            PlatformType.YOUTUBE,
            PlatformType.TIKTOK,
        ]:
            url = manager._build_topic_url(platform, "topic", 48)
            assert "topic" in url

    def test_build_keyword_url(self):
        manager = SocialMediaAPIManager()
        url = manager._build_keyword_url(PlatformType.TWITTER, ["test", "demo"], 24)
        assert "test" in url
        assert "demo" in url

    def test_build_influencer_url_all_platforms(self):
        manager = SocialMediaAPIManager()
        url = manager._build_influencer_url(PlatformType.FACEBOOK, "page")
        assert "page" in url

        url = manager._build_influencer_url(PlatformType.YOUTUBE, "channel")
        assert "channel" in url

        url = manager._build_influencer_url(PlatformType.TIKTOK, "creator")
        assert "creator" in url

    def test_build_geotagged_url_all_platforms(self):
        manager = SocialMediaAPIManager()
        for platform in [
            PlatformType.REDDIT,
            PlatformType.FACEBOOK,
            PlatformType.YOUTUBE,
            PlatformType.TIKTOK,
        ]:
            url = manager._build_geotagged_url(platform, "topic")
            assert "topic" in url

    def test_parse_hashtag_response_default_fallback(self):
        manager = SocialMediaAPIManager()
        data = {"raw": "data"}
        result = manager._parse_hashtag_response(PlatformType.FACEBOOK, data, "test")
        assert "hashtag" in result
        assert "raw_data" in result

    def test_parse_topic_response(self):
        manager = SocialMediaAPIManager()
        data = {"data": []}
        result = manager._parse_topic_response(PlatformType.TWITTER, data, "topic")
        assert "hashtag" in result

    def test_parse_keyword_response(self):
        manager = SocialMediaAPIManager()
        data = {"data": []}
        result = manager._parse_keyword_response(PlatformType.TWITTER, data, ["kw1", "kw2"])
        assert "hashtag" in result

    def test_parse_influencer_response_default_fallback(self):
        manager = SocialMediaAPIManager()
        data = {"raw": "data"}
        result = manager._parse_influencer_response(PlatformType.FACEBOOK, data, "handle")
        assert "handle" in result
        assert "raw_data" in result

    def test_parse_geotagged_response_default(self):
        manager = SocialMediaAPIManager()
        data = {"data": []}
        result = manager._parse_geotagged_response(PlatformType.REDDIT, data, "topic")
        assert result == []
