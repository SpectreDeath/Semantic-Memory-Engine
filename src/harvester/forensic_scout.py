import logging
import requests
import re
from datetime import datetime
from typing import Generator, Dict, Any, List, Optional
from bs4 import BeautifulSoup
import os

from src.core.config import Config

logger = logging.getLogger(__name__)

class ForensicScout:
    """
    High-fidelity harvester for forensic analysis.
    Preserves structural integrity for Rolling Delta and captures metadata for Adaptive Learning.
    Designed for memory efficiency using generators.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ScribeForensic/1.0 (Research; +http://github.com/SpectreDeath/Semantic-Memory-Engine)"
        })
        self._init_references()

    def _init_references(self):
        """Lazy load references to avoid circular imports."""
        # Typically imported when needed, but can cache types here if desired
        pass

    def clean_and_segment(self, raw_html: str) -> List[str]:
        """
        Cleans HTML but preserves paragraph structure and order.
        Critical for sequential analysis (Rolling Delta).
        
        Args:
            raw_html: The raw HTML content.
            
        Returns:
            List of text segments (paragraphs).
        """
        soup = BeautifulSoup(raw_html, 'html.parser')
        
        # Remove noise
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
            tag.decompose()
            
        segments = []
        
        # Prioritize P tags for narrative flow
        # Also capture headings for context boundaries
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote']):
            text = element.get_text(separator=' ', strip=True)
            # Filter logic: Allow headings even if short, but filter tiny paragraphs/list items
            is_heading = element.name.startswith('h')
            if len(text) > 30 or (is_heading and len(text) > 5):
                segments.append(text)
                
        return segments

    def harvest(self, url: str, author_id: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Streams harvested content in memory-efficient chunks.
        
        Args:
            url: Target URL.
            author_id: Known author ID (optional).
            
        Yields:
            Dictionary containing chunk text and metadata.
        """
        logger.info(f"🕵️‍♂️ Scouting target: {url}")
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Extract Metadata
            timestamp = datetime.utcnow().isoformat()
            
            # Basic metadata extraction (could be enhanced with extraction library)
            # For Adaptive Learner, we need a rough time anchor
            
            segments = self.clean_and_segment(response.text)
            
            # Streaming Logic: Yield chunks of ~10k words
            current_chunk = []
            current_word_count = 0
            chunk_limit = 10000
            
            for segment in segments:
                word_count = len(segment.split())
                current_chunk.append(segment)
                current_word_count += word_count
                
                if current_word_count >= chunk_limit:
                    yield {
                        "url": url,
                        "timestamp": timestamp,
                        "author_id": author_id,
                        "text": "\n\n".join(current_chunk),
                        "chunk_size": current_word_count
                    }
                    current_chunk = []
                    current_word_count = 0
            
            # Yield remaining
            if current_chunk:
                yield {
                    "url": url,
                    "timestamp": timestamp,
                    "author_id": author_id,
                    "text": "\n\n".join(current_chunk),
                    "chunk_size": current_word_count
                }
                
        except Exception as e:
            logger.error(f"❌ Scout failed on {url}: {e}")
            yield {"error": str(e), "url": url}

    def process_and_store(self, url: str, author_id: str):
        """
        Orchestrates harvesting, storage, and immediate forensic analysis.
        """
        from src.core.factory import ToolFactory
        
        scribe = ToolFactory.create_scribe()
        rolling = ToolFactory.create_rolling_delta()
        adaptive = ToolFactory.create_adaptive_learner()
        # db = ToolFactory.create_centrifuge() # Placeholder if DB interaction needed directly
        
        # Check Orchestrator for Gaps (Simulated for this implementation)
        # gap_check = ToolFactory.create_orchestrator().check_gaps(url) 
        # if gap_check.priority == 'low': return
        
        logger.info(f"🚀 Launching forensic pipeline for {author_id} @ {url}")
        
        for chunk_data in self.harvest(url, author_id):
            if "text" not in chunk_data:
                continue
                
            text = chunk_data["text"]
            
            # 1. Linguistic Fingerprint (Scribe)
            fingerprint = scribe.extract_linguistic_fingerprint(text, author_id)
            
            # 2. Adaptive Learning Update
            # Save snapshot before update if it's a new session
            # For simplicity, we assume every harvest might induce drift
            adaptive.save_profile_snapshot(author_id, fingerprint.signal_weights)
            
            # Check drift immediately
            is_drifting, score = adaptive.analyze_recent_drift(author_id)
            if is_drifting:
                logger.warning(f"⚠️ Live Drift Alert: {score:.2f}")
                
            # 3. Rolling Delta (Sequential)
            # Need candidates. For now, use the author's own weighted profile as 'Self'
            # and maybe a generic 'Average' profile.
            # This is complex to mock without a full candidate db, skipping detailed rolling call 
            # unless we have specific candidates.
            
            logger.info(f"✅ Processed chunk ({chunk_data['chunk_size']} words)")
