"""
Cloud Storage Fetcher - Access Shared Cloud Storage Links

Supports fetching content from various cloud storage providers:
- Google Drive (shared links)
- Dropbox (shared links)
- OneDrive (shared links)
- S3 (presigned URLs)
- Generic HTTP/HTTPS URLs
"""

import os
import re
import logging
import hashlib
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs
from pathlib import Path

import httpx

logger = logging.getLogger("lawnmower.cloud_fetcher")

# Cache directory for downloaded files
CACHE_DIR = os.environ.get("SME_CLOUD_CACHE_DIR", "data/cloud_cache")


class CloudFetcher:
    """
    Fetches content from cloud storage shared links.
    
    Supports:
    - Google Drive (drive.google.com/file/... or drive.google.com/open?id=...)
    - Dropbox (dropbox.com/s/... or dropbox.com/home/...)
    - OneDrive (1drv.ms/... or onedrive.live.com/...)
    - S3 (aws.amazon.com/s3/... or any presigned URL)
    - Generic URLs (any HTTP-accessible file)
    """
    
    # Known patterns for cloud providers
    PROVIDER_PATTERNS = {
        "google_drive": [
            r"drive\.google\.com/file/d/([^/]+)",
            r"drive\.google\.com/open\?id=([^&]+)",
            r"drive\.google\.com/uc\?id=([^&]+)",
        ],
        "dropbox": [
            r"dropbox\.com/s/([^/]+)",
            r"dropbox\.com/home/.*\?preview=([^&]+)",
            r"www\.dropbox\.com/s/([^/]+)",
        ],
        "onedrive": [
            r"1drv\.ms/([^/]+)",
            r"onedrive\.live\.com/share/([^/\?]+)",
            r"onedrive\.live\.com/edit\.jspa\?([^&]+)",
        ],
        "s3": [
            r"\.s3\.amazonaws\.com/([^/]+)",
            r"aws\.amazon\.com/s3/.*\?([^&]+)",
            r"s3\.([^/]+)\.amazonaws\.com/([^/]+)",
        ],
    }
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # HTTP client with reasonable timeout
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "SME-CloudFetcher/1.0"
            }
        )
        
    def _detect_provider(self, url: str) -> str:
        """Detect which cloud provider the URL belongs to."""
        for provider, patterns in self.PROVIDER_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return provider
        return "generic"
    
    def _get_cache_path(self, url: str) -> Path:
        """Generate a cache file path for a URL."""
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return Path(self.cache_dir) / f"{url_hash}.cache"
    
    async def fetch(
        self,
        url: str,
        use_cache: bool = True,
        force_download: bool = False
    ) -> Dict[str, Any]:
        """
        Fetch content from a cloud storage URL.
        
        Args:
            url: The shared link URL
            use_cache: Whether to use cached content if available
            force_download: Force re-download even if cached
        
        Returns:
            Dict with keys: content, filename, mime_type, provider, cached
        """
        # Check cache first
        if use_cache and not force_download:
            cache_path = self._get_cache_path(url)
            if cache_path.exists():
                content = cache_path.read_bytes()
                logger.info(f"CloudFetcher: Cache hit for {url[:50]}...")
                return {
                    "content": content,
                    "filename": cache_path.stem,
                    "mime_type": self._guess_mime_type(cache_path.name),
                    "provider": self._detect_provider(url),
                    "cached": True
                }
        
        # Detect provider and fetch
        provider = self._detect_provider(url)
        logger.info(f"CloudFetcher: Fetching from {provider}: {url[:50]}...")
        
        try:
            if provider == "google_drive":
                result = await self._fetch_google_drive(url)
            elif provider == "dropbox":
                result = await self._fetch_dropbox(url)
            elif provider == "onedrive":
                result = await self._fetch_onedrive(url)
            elif provider == "s3":
                result = await self._fetch_s3(url)
            else:
                result = await self._fetch_generic(url)
            
            # Cache the result
            if use_cache and result.get("content"):
                cache_path = self._get_cache_path(url)
                cache_path.write_bytes(result["content"])
                logger.info(f"CloudFetcher: Cached to {cache_path}")
            
            result["provider"] = provider
            result["cached"] = False
            return result
            
        except Exception as e:
            logger.error(f"CloudFetcher: Failed to fetch {url}: {e}")
            return {
                "error": str(e),
                "provider": provider,
                "cached": False
            }
    
    async def _fetch_google_drive(self, url: str) -> Dict[str, Any]:
        """Fetch from Google Drive shared link."""
        # Extract file ID
        match = re.search(r"/d/([^/]+)", url)
        if not match:
            match = re.search(r"id=([^&]+)", url)
        
        if match:
            file_id = match.group(1)
            # Use the export URL for known formats
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
        else:
            download_url = url
        
        response = await self.client.get(download_url)
        response.raise_for_status()
        
        return {
            "content": response.content,
            "filename": self._extract_filename(response, url),
            "mime_type": response.headers.get("content-type", "application/octet-stream")
        }
    
    async def _fetch_dropbox(self, url: str) -> Dict[str, Any]:
        """Fetch from Dropbox shared link."""
        # Dropbox shared links need dl=1 for direct download
        if "dl=0" in url:
            url = url.replace("dl=0", "dl=1")
        elif "dl?" not in url and "?" in url:
            url = url + "&dl=1"
        elif "dl?" not in url:
            url = url + "?dl=1"
        
        response = await self.client.get(url)
        response.raise_for_status()
        
        return {
            "content": response.content,
            "filename": self._extract_filename(response, url),
            "mime_type": response.headers.get("content-type", "application/octet-stream")
        }
    
    async def _fetch_onedrive(self, url: str) -> Dict[str, Any]:
        """Fetch from OneDrive shared link."""
        # OneDrive uses embed URLs for direct access
        # Try to get the embed URL
        response = await self.client.get(url, follow_redirects=True)
        response.raise_for_status()
        
        return {
            "content": response.content,
            "filename": self._extract_filename(response, url),
            "mime_type": response.headers.get("content-type", "application/octet-stream")
        }
    
    async def _fetch_s3(self, url: str) -> Dict[str, Any]:
        """Fetch from S3 presigned URL."""
        response = await self.client.get(url)
        response.raise_for_status()
        
        return {
            "content": response.content,
            "filename": self._extract_filename(response, url),
            "mime_type": response.headers.get("content-type", "application/octet-stream")
        }
    
    async def _fetch_generic(self, url: str) -> Dict[str, Any]:
        """Fetch from generic HTTP/HTTPS URL."""
        response = await self.client.get(url)
        response.raise_for_status()
        
        return {
            "content": response.content,
            "filename": self._extract_filename(response, url),
            "mime_type": response.headers.get("content-type", "application/octet-stream")
        }
    
    def _extract_filename(self, response: httpx.Response, url: str) -> str:
        """Extract filename from response headers or URL."""
        # Try Content-Disposition header
        content_disposition = response.headers.get("content-disposition", "")
        if "filename=" in content_disposition:
            match = re.search(r'filename="?([^";\n]+)"?', content_disposition)
            if match:
                return match.group(1)
        
        # Try URL path
        parsed = urlparse(url)
        path = Path(parsed.path)
        if path.name and "." in path.name:
            return path.name
        
        return "download"
    
    def _guess_mime_type(self, filename: str) -> str:
        """Guess MIME type from filename extension."""
        ext = Path(filename).suffix.lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".csv": "text/csv",
            ".xml": "application/xml",
            ".zip": "application/zip",
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
        }
        return mime_types.get(ext, "application/octet-stream")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# ---------------------------------------------------------------------------
# Synchronous wrapper for easier usage
# ---------------------------------------------------------------------------
import asyncio

def fetch_sync(url: str, **kwargs) -> Dict[str, Any]:
    """Synchronous wrapper for CloudFetcher.fetch()"""
    async def _fetch():
        fetcher = CloudFetcher()
        try:
            return await fetcher.fetch(url, **kwargs)
        finally:
            await fetcher.close()
    
    return asyncio.run(_fetch())
