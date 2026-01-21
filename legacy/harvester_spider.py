"""
🕸️ Harvester Spider (Layer 0: Entry Point)

Streamlined web scraping module for SimpleMem pipeline.
- Async-first architecture
- Crawl4AI's fit_markdown + PruningContentFilter
- Direct Centrifuge DB integration
- Stage 1 Semantic Compression input

Purpose:
    Convert messy HTML into "LLM-ready" Markdown stripped of 80% web noise
    (ads, navbars, scripts, footers) before feeding to Loom semantic compression.

Memory Profile:
    • Headless browser overhead: <200MB (negligible on 32GB)
    • GPU usage: 0% (1660 Ti remains free for Loom/Synapse)
    • Typical crawl: 1-5 seconds per page
    • Output: Clean Markdown → Centrifuge DB → Loom compression

Integration:
    URL → HarvesterSpider.capture_site() → fit_markdown
    → Centrifuge.archive_source() → raw_content table
    → Loom.distill_web_content() → atomic facts
"""

import asyncio
import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    from crawl4ai.content_filter_strategy import PruningContentFilter
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    print("⚠️  Crawl4AI not installed. Install: pip install crawl4ai")

import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = "d:/mcp_servers/storage/laboratory.db"


class HarvesterSpider:
    """
    Streamlined web scraper optimized for LLM context windows.
    
    Workflow:
        1. Fetch HTML (headless browser)
        2. Apply PruningContentFilter (remove nav, footer, ads, scripts)
        3. Extract fit_markdown (optimized for LLM)
        4. Archive to Centrifuge DB (raw_content table)
        5. Mark ready for Loom semantic compression
    
    Example:
        spider = HarvesterSpider()
        capture_id, markdown = asyncio.run(
            spider.capture_site("https://arxiv.org/abs/2301.13688")
        )
        print(f"✅ Captured: {markdown[:200]}...")
    """
    
    def __init__(self, db_path: str = DB_PATH):
        """Initialize spider with database connection."""
        if not CRAWL4AI_AVAILABLE:
            raise ImportError("Crawl4AI required. Install: pip install crawl4ai")
        
        self.db_path = db_path
        self.browser_config = BrowserConfig(headless=True)
        
        # PruningContentFilter removes non-essential elements
        # threshold=0.45: Keep content with >45% semantic density
        # min_word_count=50: Discard sections with <50 words
        self.content_filter = PruningContentFilter(
            threshold=0.45, 
            min_word_count=50
        )
        
        # Crawler configuration for optimal compression
        self.run_config = CrawlerRunConfig(
            content_filter=self.content_filter,
            word_count_threshold=100,  # Skip pages with <100 words
            cache_mode="BYPASS"  # Always fresh (don't rely on browser cache)
        )
        
        logger.info("🕸️ HarvesterSpider initialized (Crawl4AI + PruningContentFilter)")
    
    async def capture_site(self, url: str) -> Tuple[Optional[int], Optional[str]]:
        """
        Fetch, clean, and archive web content.
        
        Args:
            url: Target URL to capture
        
        Returns:
            (capture_id, clean_markdown) or (None, None) on failure
        
        Example:
            capture_id, markdown = await spider.capture_site("https://example.com")
            if capture_id:
                print(f"✅ Archived as ID: {capture_id}")
        """
        try:
            # Async fetch with Crawl4AI
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(url=url, config=self.run_config)
            
            if not result.success:
                logger.error(f"❌ Crawl failed for {url}: {result.error_message}")
                return None, None
            
            # Extract LLM-ready markdown (fit_markdown removes semantic noise)
            clean_md = result.markdown_v2.fit_markdown
            
            if not clean_md or len(clean_md) < 100:
                logger.warning(f"⚠️ Insufficient content from {url} ({len(clean_md or '')} chars)")
                return None, None
            
            # Archive to Centrifuge DB
            capture_id = self._archive_to_db(
                url=url,
                clean_markdown=clean_md,
                metadata={
                    'title': result.metadata.get('title', url),
                    'description': result.metadata.get('description', ''),
                    'word_count': len(clean_md.split()),
                    'has_js': self._detect_js(result.html),
                    'capture_time_ms': result.response_time * 1000
                }
            )
            
            logger.info(f"✅ Captured: {url} | ID: {capture_id} | {len(clean_md.split())} words")
            return capture_id, clean_md
        
        except Exception as e:
            logger.error(f"❌ Error capturing {url}: {e}")
            return None, None
    
    async def batch_capture(self, urls: list) -> Dict[str, Any]:
        """
        Capture multiple URLs concurrently.
        
        Args:
            urls: List of URLs to capture
        
        Returns:
            {
                'captured': count,
                'failed': count,
                'captures': [(url, capture_id, markdown), ...],
                'total_words': int
            }
        
        Example:
            results = await spider.batch_capture([
                "https://arxiv.org/abs/2301.13688",
                "https://arxiv.org/abs/2302.12345"
            ])
            print(f"✅ Captured {results['captured']} pages")
        """
        results = {
            'captured': 0,
            'failed': 0,
            'captures': [],
            'total_words': 0
        }
        
        try:
            # Run captures concurrently (limited by system resources)
            tasks = [self.capture_site(url) for url in urls]
            responses = await asyncio.gather(*tasks)
            
            for url, (capture_id, markdown) in zip(urls, responses):
                if capture_id:
                    results['captured'] += 1
                    results['captures'].append((url, capture_id, markdown))
                    results['total_words'] += len(markdown.split()) if markdown else 0
                else:
                    results['failed'] += 1
            
            logger.info(f"✅ Batch complete: {results['captured']} captured, {results['failed']} failed")
            return results
        
        except Exception as e:
            logger.error(f"❌ Batch error: {e}")
            return results
    
    def _archive_to_db(self, url: str, clean_markdown: str, metadata: dict) -> Optional[int]:
        """
        Archive cleaned content to Centrifuge DB.
        
        Database workflow:
            raw_content table ← stores HTML + markdown
            ↓ (processed_by_loom = False initially)
            Loom.distill_web_content() → extracts atomic facts
            ↓
            raw_content table ← updates processed_by_loom = True
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Ensure table exists
            self._ensure_table(cursor)
            
            # Insert or update
            parsed = urlparse(url)
            domain = parsed.netloc
            
            cursor.execute("""
                INSERT OR REPLACE INTO raw_content 
                (url, domain, markdown_content, extracted_schema, 
                 content_type, js_required, timestamp, processed_by_loom, 
                 source_quality, fetch_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url,
                domain,
                clean_markdown,
                __import__('json').dumps(metadata),
                'article',  # Content type (can be refined)
                1 if metadata.get('has_js') else 0,
                datetime.now().isoformat(),
                0,  # Not processed by Loom yet
                self._score_quality(clean_markdown),
                'crawl4ai'
            ))
            
            conn.commit()
            capture_id = cursor.lastrowid
            conn.close()
            
            return capture_id
        
        except Exception as e:
            logger.error(f"❌ Archive error: {e}")
            return None
    
    def _ensure_table(self, cursor):
        """Create raw_content table if it doesn't exist."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                domain TEXT NOT NULL,
                raw_html TEXT,
                markdown_content TEXT,
                extracted_schema JSON,
                content_type TEXT DEFAULT 'article',
                js_required BOOLEAN DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                processed_by_loom BOOLEAN DEFAULT 0,
                source_quality INTEGER DEFAULT 0,
                fetch_method TEXT,
                error_log TEXT
            )
        """)
        
        # Create index for Loom pipeline (fast queries)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_raw_content_loom 
            ON raw_content(processed_by_loom)
        """)
    
    def _score_quality(self, markdown: str) -> int:
        """Score content quality 0-100."""
        score = 50  # Base score
        
        # More content = higher quality
        word_count = len(markdown.split())
        score += min(30, word_count // 100)
        
        # Structure indicates quality
        headers = markdown.count('#')
        score += min(20, headers)
        
        return max(0, min(100, score))
    
    def _detect_js(self, html: str) -> bool:
        """Detect if page has significant JavaScript."""
        import re
        return bool(re.search(r'<script|async|defer|fetch|XMLHttpRequest|React|Vue|Angular', html, re.I))
    
    def get_unprocessed_content(self, limit: int = 50) -> list:
        """
        Get content ready for Loom semantic compression.
        
        Typical workflow for Loom:
            urls = spider.get_unprocessed_content(limit=50)
            for url, markdown in urls:
                facts = loom.distill_web_content(markdown)
                # Store facts...
                spider.mark_processed(url)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT url, markdown_content, id 
                FROM raw_content 
                WHERE processed_by_loom = 0 
                AND source_quality >= 70
                ORDER BY source_quality DESC, timestamp DESC
                LIMIT ?
            """, (limit,))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return results
        
        except Exception as e:
            logger.error(f"❌ Query error: {e}")
            return []
    
    def mark_processed(self, url: str) -> bool:
        """Mark content as processed by Loom."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE raw_content 
                SET processed_by_loom = 1 
                WHERE url = ?
            """, (url,))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
        
        except Exception as e:
            logger.error(f"❌ Update error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get database statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM raw_content")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM raw_content WHERE processed_by_loom = 1")
            processed = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(source_quality) FROM raw_content")
            avg_quality = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(LENGTH(markdown_content)) FROM raw_content")
            total_bytes = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_captured': total,
                'processed_by_loom': processed,
                'pending': total - processed,
                'avg_quality': avg_quality,
                'storage_mb': total_bytes / (1024 * 1024)
            }
        
        except Exception as e:
            logger.error(f"❌ Stats error: {e}")
            return {}


# ============================================================================
# MCP Tool Interface
# ============================================================================

async def harvest_url(url: str) -> str:
    """MCP Tool: Capture single URL."""
    import json
    spider = HarvesterSpider()
    capture_id, markdown = await spider.capture_site(url)
    
    if capture_id:
        return json.dumps({
            'status': 'success',
            'capture_id': capture_id,
            'words': len(markdown.split()),
            'preview': markdown[:300]
        })
    else:
        return json.dumps({'status': 'error', 'message': 'Capture failed'})


async def harvest_batch(urls: list) -> str:
    """MCP Tool: Capture multiple URLs."""
    import json
    spider = HarvesterSpider()
    results = await spider.batch_capture(urls)
    
    return json.dumps({
        'status': 'success',
        'captured': results['captured'],
        'failed': results['failed'],
        'total_words': results['total_words']
    })


def harvest_stats() -> str:
    """MCP Tool: Get statistics."""
    import json
    spider = HarvesterSpider()
    stats = spider.get_stats()
    
    return json.dumps({
        'status': 'success',
        **stats
    })


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    async def demo():
        """Demonstrate HarvesterSpider workflow."""
        spider = HarvesterSpider()
        
        # Example 1: Single capture
        print("\n1️⃣ Single URL capture:")
        capture_id, markdown = await spider.capture_site(
            "https://en.wikipedia.org/wiki/Artificial_intelligence"
        )
        if capture_id:
            print(f"✅ Captured (ID: {capture_id})")
            print(f"   Words: {len(markdown.split())}")
            print(f"   Preview: {markdown[:200]}...")
        
        # Example 2: Get pending content for Loom
        print("\n2️⃣ Pending content for Loom:")
        pending = spider.get_unprocessed_content(limit=5)
        print(f"✅ Found {len(pending)} items ready for Loom")
        for item in pending[:2]:
            print(f"   • {item['url']}: {len(item['markdown_content'].split())} words")
        
        # Example 3: Statistics
        print("\n3️⃣ Database statistics:")
        stats = spider.get_stats()
        print(f"✅ Total captured: {stats['total_captured']}")
        print(f"   Processed: {stats['processed_by_loom']}")
        print(f"   Pending: {stats['pending']}")
        print(f"   Avg quality: {stats['avg_quality']:.0f}/100")
    
    asyncio.run(demo())
