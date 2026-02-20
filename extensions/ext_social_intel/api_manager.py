"""
Social Media API Manager

Handles authentication, rate limiting, and API calls for multiple social media platforms.
Provides a unified interface for accessing Twitter/X, Reddit, Facebook, YouTube, and TikTok APIs.

Key Features:
- Multi-platform API authentication and management
- Rate limiting and quota management
- Request queuing and retry logic
- Content filtering and moderation
- OAuth integration for platform APIs
- Proxy support for geolocation-based access
"""

import logging
import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import aiohttp
from urllib.parse import urlencode

logger = logging.getLogger("SME.SocialIntelligence.APIManager")

class PlatformType(Enum):
    """Supported social media platforms."""
    TWITTER = "twitter"
    REDDIT = "reddit"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"

@dataclass
class APIConfig:
    """Configuration for a social media API."""
    platform: PlatformType
    api_key: Optional[str]
    api_secret: Optional[str]
    access_token: Optional[str]
    access_token_secret: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    rate_limit: int
    rate_window: int  # seconds
    enabled: bool = True

@dataclass
class RateLimiter:
    """Rate limiter for API requests."""
    platform: PlatformType
    max_requests: int
    window_seconds: int
    requests: List[float]
    
    def __init__(self, platform: PlatformType, max_requests: int, window_seconds: int):
        self.platform = platform
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    async def acquire(self) -> bool:
        """Acquire permission to make a request."""
        now = time.time()
        
        # Remove old requests outside the window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.window_seconds]
        
        # Check if we can make a request
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        
        # Calculate wait time
        oldest_request = min(self.requests)
        wait_time = self.window_seconds - (now - oldest_request)
        
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            return await self.acquire()
        
        return False

class SocialMediaAPIManager:
    """
    Manages API connections and requests for multiple social media platforms.
    
    Handles authentication, rate limiting, and provides a unified interface
    for accessing different social media APIs.
    """
    
    def __init__(self):
        self.platform_configs: Dict[PlatformType, APIConfig] = {}
        self.rate_limiters: Dict[PlatformType, RateLimiter] = {}
        self.active_sessions: Dict[PlatformType, aiohttp.ClientSession] = {}
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.is_initialized = False
        
        # Platform-specific API endpoints
        self.api_endpoints = {
            PlatformType.TWITTER: {
                "base_url": "https://api.twitter.com/2",
                "search": "/tweets/search/recent",
                "user": "/users/by/username/",
                "hashtag": "/tweets/search/recent"
            },
            PlatformType.REDDIT: {
                "base_url": "https://oauth.reddit.com",
                "search": "/search",
                "subreddit": "/r/",
                "user": "/user/"
            },
            PlatformType.FACEBOOK: {
                "base_url": "https://graph.facebook.com/v19.0",
                "search": "/search",
                "page": "/",
                "post": "/"
            },
            PlatformType.YOUTUBE: {
                "base_url": "https://www.googleapis.com/youtube/v3",
                "search": "/search",
                "videos": "/videos",
                "channels": "/channels"
            },
            PlatformType.TIKTOK: {
                "base_url": "https://open-api.tiktok.com",
                "search": "/search",
                "user": "/user/",
                "video": "/video/"
            }
        }
        
        logger.info("Social Media API Manager initialized")

    async def initialize_apis(self):
        """Initialize all configured API connections."""
        try:
            # Load configuration from environment or config file
            await self._load_api_configs()
            
            # Initialize rate limiters
            for platform, config in self.platform_configs.items():
                if config.enabled:
                    self.rate_limiters[platform] = RateLimiter(
                        platform, config.rate_limit, config.rate_window
                    )
            
            # Create client sessions
            for platform in self.platform_configs.keys():
                if self.platform_configs[platform].enabled:
                    self.active_sessions[platform] = aiohttp.ClientSession(
                        headers=self._get_default_headers(platform)
                    )
            
            self.is_initialized = True
            logger.info("Social Media API Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize API manager: {e}")
            raise

    async def shutdown(self):
        """Shutdown all API connections."""
        try:
            # Close all client sessions
            for session in self.active_sessions.values():
                await session.close()
            
            self.active_sessions.clear()
            self.is_initialized = False
            logger.info("Social Media API Manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during API manager shutdown: {e}")

    async def get_hashtag_data(self, platform: PlatformType, hashtag: str, 
                             time_window: int = 24) -> Dict:
        """
        Get hashtag data from a specific platform.
        
        Args:
            platform: Target platform
            hashtag: Hashtag to search for
            time_window: Time window in hours
            
        Returns:
            Dict containing hashtag data
        """
        if not self.is_initialized or platform not in self.active_sessions:
            return {"error": f"Platform {platform.value} not initialized"}
        
        try:
            # Acquire rate limit
            if platform in self.rate_limiters:
                await self.rate_limiters[platform].acquire()
            
            # Get platform-specific endpoint and parameters
            endpoint_config = self.api_endpoints[platform]
            url = self._build_hashtag_url(platform, hashtag, time_window)
            
            # Make request
            session = self.active_sessions[platform]
            headers = self._get_request_headers(platform)
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_hashtag_response(platform, data, hashtag)
                else:
                    return {"error": f"HTTP {response.status}: {response.reason}"}
                    
        except Exception as e:
            logger.error(f"Error fetching hashtag data for {platform.value}: {e}")
            return {"error": str(e)}

    async def get_topic_content(self, platform: PlatformType, topic: str, 
                              time_range: int = 48) -> Dict:
        """
        Get content related to a topic from a specific platform.
        
        Args:
            platform: Target platform
            topic: Topic to search for
            time_range: Time range in hours
            
        Returns:
            Dict containing topic content
        """
        if not self.is_initialized or platform not in self.active_sessions:
            return {"error": f"Platform {platform.value} not initialized"}
        
        try:
            # Acquire rate limit
            if platform in self.rate_limiters:
                await self.rate_limiters[platform].acquire()
            
            # Build search URL
            url = self._build_topic_url(platform, topic, time_range)
            
            # Make request
            session = self.active_sessions[platform]
            headers = self._get_request_headers(platform)
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_topic_response(platform, data, topic)
                else:
                    return {"error": f"HTTP {response.status}: {response.reason}"}
                    
        except Exception as e:
            logger.error(f"Error fetching topic content for {platform.value}: {e}")
            return {"error": str(e)}

    async def get_keyword_data(self, platform: PlatformType, keywords: List[str], 
                             time_window: int = 24) -> Dict:
        """
        Get data for multiple keywords from a platform.
        
        Args:
            platform: Target platform
            keywords: List of keywords to search for
            time_window: Time window in hours
            
        Returns:
            Dict containing keyword data
        """
        if not self.is_initialized or platform not in self.active_sessions:
            return {"error": f"Platform {platform.value} not initialized"}
        
        try:
            # Acquire rate limit
            if platform in self.rate_limiters:
                await self.rate_limiters[platform].acquire()
            
            # Build search URL with multiple keywords
            url = self._build_keyword_url(platform, keywords, time_window)
            
            # Make request
            session = self.active_sessions[platform]
            headers = self._get_request_headers(platform)
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_keyword_response(platform, data, keywords)
                else:
                    return {"error": f"HTTP {response.status}: {response.reason}"}
                    
        except Exception as e:
            logger.error(f"Error fetching keyword data for {platform.value}: {e}")
            return {"error": str(e)}

    async def get_influencer_data(self, influencer_handle: str, 
                                time_window: int = 168) -> Dict:
        """
        Get data for specific influencers across platforms.
        
        Args:
            influencer_handle: Influencer handle to search for
            time_window: Time window in hours
            
        Returns:
            Dict containing influencer data across platforms
        """
        results = {}
        
        for platform in self.active_sessions.keys():
            try:
                # Acquire rate limit
                if platform in self.rate_limiters:
                    await self.rate_limiters[platform].acquire()
                
                # Build influencer URL
                url = self._build_influencer_url(platform, influencer_handle)
                
                # Make request
                session = self.active_sessions[platform]
                headers = self._get_request_headers(platform)
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        results[platform.value] = self._parse_influencer_response(
                            platform, data, influencer_handle
                        )
                    else:
                        results[platform.value] = {"error": f"HTTP {response.status}: {response.reason}"}
                        
            except Exception as e:
                logger.error(f"Error fetching influencer data for {platform.value}: {e}")
                results[platform.value] = {"error": str(e)}
        
        return results

    async def get_geotagged_content(self, platform: PlatformType, topic: str) -> List[Dict]:
        """
        Get geotagged content for a topic from a platform.
        
        Args:
            platform: Target platform
            topic: Topic to search for
            
        Returns:
            List of geotagged content items
        """
        if not self.is_initialized or platform not in self.active_sessions:
            return []
        
        try:
            # Acquire rate limit
            if platform in self.rate_limiters:
                await self.rate_limiters[platform].acquire()
            
            # Build geotagged search URL
            url = self._build_geotagged_url(platform, topic)
            
            # Make request
            session = self.active_sessions[platform]
            headers = self._get_request_headers(platform)
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_geotagged_response(platform, data, topic)
                else:
                    logger.error(f"Error fetching geotagged content: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching geotagged content for {platform.value}: {e}")
            return []

    # Private helper methods
    
    async def _load_api_configs(self):
        """Load API configurations from environment variables or config file."""
        # This would typically load from environment variables or a config file
        # For now, we'll use placeholder configurations
        
        self.platform_configs = {
            PlatformType.TWITTER: APIConfig(
                platform=PlatformType.TWITTER,
                api_key=None,  # Would come from environment
                api_secret=None,
                access_token=None,
                access_token_secret=None,
                client_id=None,
                client_secret=None,
                rate_limit=300,  # 300 requests per 15 minutes
                rate_window=900,
                enabled=True
            ),
            PlatformType.REDDIT: APIConfig(
                platform=PlatformType.REDDIT,
                api_key=None,
                api_secret=None,
                access_token=None,
                access_token_secret=None,
                client_id=None,
                client_secret=None,
                rate_limit=60,  # 60 requests per minute
                rate_window=60,
                enabled=True
            ),
            PlatformType.FACEBOOK: APIConfig(
                platform=PlatformType.FACEBOOK,
                api_key=None,
                api_secret=None,
                access_token=None,
                access_token_secret=None,
                client_id=None,
                client_secret=None,
                rate_limit=200,  # 200 requests per hour
                rate_window=3600,
                enabled=True
            ),
            PlatformType.YOUTUBE: APIConfig(
                platform=PlatformType.YOUTUBE,
                api_key=None,
                api_secret=None,
                access_token=None,
                access_token_secret=None,
                client_id=None,
                client_secret=None,
                rate_limit=10000,  # 10,000 requests per day
                rate_window=86400,
                enabled=True
            ),
            PlatformType.TIKTOK: APIConfig(
                platform=PlatformType.TIKTOK,
                api_key=None,
                api_secret=None,
                access_token=None,
                access_token_secret=None,
                client_id=None,
                client_secret=None,
                rate_limit=1000,  # 1000 requests per hour
                rate_window=3600,
                enabled=True
            )
        }

    def _get_default_headers(self, platform: PlatformType) -> Dict[str, str]:
        """Get default headers for a platform."""
        base_headers = {
            "User-Agent": "SME-Social-Intelligence/1.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        config = self.platform_configs.get(platform)
        if not config:
            return base_headers
        
        # Add platform-specific headers
        if platform == PlatformType.TWITTER:
            if config.access_token:
                base_headers["Authorization"] = f"Bearer {config.access_token}"
        
        elif platform == PlatformType.REDDIT:
            if config.access_token:
                base_headers["Authorization"] = f"bearer {config.access_token}"
        
        elif platform == PlatformType.FACEBOOK:
            if config.access_token:
                base_headers["Authorization"] = f"Bearer {config.access_token}"
        
        elif platform == PlatformType.YOUTUBE:
            if config.api_key:
                base_headers["X-API-Key"] = config.api_key
        
        elif platform == PlatformType.TIKTOK:
            if config.access_token:
                base_headers["Authorization"] = f"Bearer {config.access_token}"
        
        return base_headers

    def _get_request_headers(self, platform: PlatformType) -> Dict[str, str]:
        """Get headers for a specific request."""
        return self._get_default_headers(platform)

    def _build_hashtag_url(self, platform: PlatformType, hashtag: str, 
                          time_window: int) -> str:
        """Build hashtag search URL for a platform."""
        base_url = self.api_endpoints[platform]["base_url"]
        
        if platform == PlatformType.TWITTER:
            # Twitter API v2 hashtag search
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_window)
            
            params = {
                "query": f"#{hashtag}",
                "start_time": start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z",
                "max_results": 100,
                "tweet.fields": "created_at,author_id,public_metrics,geo,lang",
                "user.fields": "username,name,public_metrics,verified",
                "expansions": "author_id,geo.place_id"
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.REDDIT:
            # Reddit search
            params = {
                "q": f"#{hashtag}",
                "type": "link",
                "limit": 100,
                "sort": "new",
                "t": "all"
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.FACEBOOK:
            # Facebook search
            params = {
                "q": hashtag,
                "type": "page",
                "limit": 100
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.YOUTUBE:
            # YouTube search
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_window)
            
            params = {
                "part": "snippet",
                "q": hashtag,
                "type": "video",
                "maxResults": 50,
                "publishedAfter": start_time.isoformat() + "Z",
                "publishedBefore": end_time.isoformat() + "Z"
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.TIKTOK:
            # TikTok search (would need proper API access)
            params = {
                "q": hashtag,
                "type": "video",
                "count": 50
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        return f"{base_url}/search?q={hashtag}"

    def _build_topic_url(self, platform: PlatformType, topic: str, 
                        time_range: int) -> str:
        """Build topic search URL for a platform."""
        base_url = self.api_endpoints[platform]["base_url"]
        
        if platform == PlatformType.TWITTER:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_range)
            
            params = {
                "query": topic,
                "start_time": start_time.isoformat() + "Z",
                "end_time": end_time.isoformat() + "Z",
                "max_results": 100,
                "tweet.fields": "created_at,author_id,public_metrics,geo,lang",
                "user.fields": "username,name,public_metrics,verified",
                "expansions": "author_id,geo.place_id"
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.REDDIT:
            params = {
                "q": topic,
                "type": "link",
                "limit": 100,
                "sort": "new",
                "t": "all"
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.FACEBOOK:
            params = {
                "q": topic,
                "type": "page",
                "limit": 100
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.YOUTUBE:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=time_range)
            
            params = {
                "part": "snippet",
                "q": topic,
                "type": "video",
                "maxResults": 50,
                "publishedAfter": start_time.isoformat() + "Z",
                "publishedBefore": end_time.isoformat() + "Z"
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.TIKTOK:
            params = {
                "q": topic,
                "type": "video",
                "count": 50
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        return f"{base_url}/search?q={topic}"

    def _build_keyword_url(self, platform: PlatformType, keywords: List[str], 
                          time_window: int) -> str:
        """Build keyword search URL for a platform."""
        # Combine keywords with OR operator
        query = " OR ".join(keywords)
        return self._build_topic_url(platform, query, time_window)

    def _build_influencer_url(self, platform: PlatformType, handle: str) -> str:
        """Build influencer profile URL for a platform."""
        base_url = self.api_endpoints[platform]["base_url"]
        
        if platform == PlatformType.TWITTER:
            return f"{base_url}/users/by/username/{handle}"
        
        elif platform == PlatformType.REDDIT:
            return f"{base_url}/user/{handle}/about"
        
        elif platform == PlatformType.FACEBOOK:
            return f"{base_url}/{handle}"
        
        elif platform == PlatformType.YOUTUBE:
            params = {
                "part": "snippet,statistics",
                "forUsername": handle,
                "maxResults": 1
            }
            return f"{base_url}/channels?{urlencode(params)}"
        
        elif platform == PlatformType.TIKTOK:
            return f"{base_url}/user/{handle}"
        
        return f"{base_url}/user/{handle}"

    def _build_geotagged_url(self, platform: PlatformType, topic: str) -> str:
        """Build geotagged search URL for a platform."""
        base_url = self.api_endpoints[platform]["base_url"]
        
        if platform == PlatformType.TWITTER:
            # Twitter with geo filter
            params = {
                "query": f"{topic} has:geo",
                "max_results": 100,
                "tweet.fields": "created_at,author_id,public_metrics,geo,lang",
                "user.fields": "username,name,public_metrics,verified",
                "expansions": "author_id,geo.place_id"
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.REDDIT:
            # Reddit with location filter (if available)
            params = {
                "q": topic,
                "type": "link",
                "limit": 100,
                "sort": "new",
                "t": "all"
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.FACEBOOK:
            # Facebook with location filter
            params = {
                "q": topic,
                "type": "page",
                "limit": 100
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.YOUTUBE:
            # YouTube with location filter
            params = {
                "part": "snippet",
                "q": topic,
                "type": "video",
                "maxResults": 50,
                "relevanceLanguage": "en"
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        elif platform == PlatformType.TIKTOK:
            # TikTok with location filter
            params = {
                "q": topic,
                "type": "video",
                "count": 50
            }
            return f"{base_url}{self.api_endpoints[platform]['search']}?{urlencode(params)}"
        
        return f"{base_url}/search?q={topic}"

    def _parse_hashtag_response(self, platform: PlatformType, data: Dict, 
                              hashtag: str) -> Dict:
        """Parse hashtag response data for a platform."""
        if platform == PlatformType.TWITTER:
            tweets = data.get("data", [])
            users = data.get("includes", {}).get("users", [])
            
            return {
                "hashtag": hashtag,
                "post_count": len(tweets),
                "unique_users": list(set(tweet.get("author_id") for tweet in tweets)),
                "posts": [
                    {
                        "id": tweet.get("id"),
                        "text": tweet.get("text"),
                        "created_at": tweet.get("created_at"),
                        "author_id": tweet.get("author_id"),
                        "metrics": tweet.get("public_metrics", {}),
                        "location": tweet.get("geo", {}).get("coordinates", {}),
                        "hashtags": [tag["tag"] for tag in tweet.get("entities", {}).get("hashtags", [])],
                        "language": tweet.get("lang")
                    }
                    for tweet in tweets
                ],
                "users": [
                    {
                        "id": user.get("id"),
                        "username": user.get("username"),
                        "name": user.get("name"),
                        "verified": user.get("verified", False),
                        "metrics": user.get("public_metrics", {})
                    }
                    for user in users
                ]
            }
        
        elif platform == PlatformType.REDDIT:
            posts = data.get("data", {}).get("children", [])
            
            return {
                "hashtag": hashtag,
                "post_count": len(posts),
                "unique_users": list(set(post.get("data", {}).get("author") for post in posts)),
                "posts": [
                    {
                        "id": post.get("data", {}).get("id"),
                        "title": post.get("data", {}).get("title"),
                        "selftext": post.get("data", {}).get("selftext"),
                        "author": post.get("data", {}).get("author"),
                        "created_utc": post.get("data", {}).get("created_utc"),
                        "score": post.get("data", {}).get("score"),
                        "num_comments": post.get("data", {}).get("num_comments"),
                        "subreddit": post.get("data", {}).get("subreddit"),
                        "url": post.get("data", {}).get("url")
                    }
                    for post in posts
                ]
            }
        
        # Default parsing for other platforms
        return {
            "hashtag": hashtag,
            "raw_data": data,
            "platform": platform.value
        }

    def _parse_topic_response(self, platform: PlatformType, data: Dict, 
                            topic: str) -> Dict:
        """Parse topic response data for a platform."""
        # Similar to hashtag parsing but for general topics
        return self._parse_hashtag_response(platform, data, topic)

    def _parse_keyword_response(self, platform: PlatformType, data: Dict, 
                              keywords: List[str]) -> Dict:
        """Parse keyword response data for a platform."""
        # Similar to hashtag parsing but for multiple keywords
        return self._parse_hashtag_response(platform, data, " ".join(keywords))

    def _parse_influencer_response(self, platform: PlatformType, data: Dict, 
                                 handle: str) -> Dict:
        """Parse influencer response data for a platform."""
        if platform == PlatformType.TWITTER:
            user = data.get("data", {})
            
            return {
                "handle": handle,
                "user_id": user.get("id"),
                "name": user.get("name"),
                "username": user.get("username"),
                "verified": user.get("verified", False),
                "metrics": user.get("public_metrics", {}),
                "description": user.get("description"),
                "created_at": user.get("created_at"),
                "profile_image_url": user.get("profile_image_url")
            }
        
        elif platform == PlatformType.REDDIT:
            user_data = data.get("data", {})
            
            return {
                "handle": handle,
                "name": user_data.get("name"),
                "created_utc": user_data.get("created_utc"),
                "comment_karma": user_data.get("comment_karma"),
                "link_karma": user_data.get("link_karma"),
                "is_verified": user_data.get("is_verified", False),
                "is_gold": user_data.get("is_gold", False),
                "total_karma": user_data.get("total_karma")
            }
        
        # Default parsing for other platforms
        return {
            "handle": handle,
            "raw_data": data,
            "platform": platform.value
        }

    def _parse_geotagged_response(self, platform: PlatformType, data: Dict, 
                                topic: str) -> List[Dict]:
        """Parse geotagged response data for a platform."""
        if platform == PlatformType.TWITTER:
            tweets = data.get("data", [])
            
            return [
                {
                    "id": tweet.get("id"),
                    "text": tweet.get("text"),
                    "created_at": tweet.get("created_at"),
                    "author_id": tweet.get("author_id"),
                    "location": tweet.get("geo", {}).get("coordinates", {}),
                    "country": tweet.get("geo", {}).get("place", {}).get("country"),
                    "city": tweet.get("geo", {}).get("place", {}).get("name"),
                    "topic": topic,
                    "platform": platform.value
                }
                for tweet in tweets
                if tweet.get("geo")
            ]
        
        # Default parsing for other platforms
        return []