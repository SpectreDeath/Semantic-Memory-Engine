import logging
import numpy as np
import sqlite3
import random
from typing import List, Dict, Any, Tuple
from collections import Counter

from src.core.config import Config

logger = logging.getLogger(__name__)

class ImpostorsChecker:
    """
    Authorship verification using the Impostors Method.
    Compares a suspect author against a reference group of random profiles
    using iterative bootstrapping with Most Frequent Words (MFWs).
    """

    def __init__(self, db_path: str = None):
        config = Config()
        base_dir = config.get_path('storage.base_dir')
        self.db_path = db_path or str(base_dir / "storage" / "scribe_profiles.sqlite")

    def _get_author_vocabulary(self, author_id: str) -> Counter:
        """
        Retrieves word frequency distribution for an author.
        In production, this would aggregate from stored text samples.
        """
        # Placeholder - in production would fetch actual text samples
        # For now, return dummy vocab
        return Counter({
            f"word_{author_id}_{i}": random.randint(10, 100) 
            for i in range(100)
        })

    def _load_impostor_pool(self, exclude_author: str, pool_size: int = 20) -> List[str]:
        """
        Loads a lazy reference group from existing profiles.
        
        Args:
            exclude_author: Author ID to exclude from pool
            pool_size: Number of random impostors to load
            
        Returns:
            List of author IDs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT author_id FROM author_profiles 
            WHERE author_id != ? 
            LIMIT ?
        """, (exclude_author, pool_size))
        
        impostors = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # If no profiles in DB, create dummy impostors for testing
        if not impostors:
            impostors = [f"impostor_{i}" for i in range(min(pool_size, 10))]
            
        return impostors

    def _calculate_distance(self, vocab_a: Counter, vocab_b: Counter, mfws: List[str]) -> float:
        """
        Calculates distance between two vocabularies using selected MFWs.
        Uses simple Euclidean distance on normalized frequencies.
        """
        # Extract frequencies for selected MFWs
        vec_a = np.array([vocab_a.get(word, 0) for word in mfws], dtype=float)
        vec_b = np.array([vocab_b.get(word, 0) for word in mfws], dtype=float)
        
        # Normalize by total word count to get relative frequencies
        total_a = sum(vocab_a.values()) or 1
        total_b = sum(vocab_b.values()) or 1
        
        vec_a = vec_a / total_a
        vec_b = vec_b / total_b
        
        # Euclidean distance
        return float(np.linalg.norm(vec_a - vec_b))

    def verify_authorship(
        self,
        target_text: str,
        suspect_author_id: str,
        iterations: int = 100,
        mfw_size: int = 50,
        impostor_count: int = 10
    ) -> Dict[str, Any]:
        """
        Performs authorship verification using the Impostors Method.
        
        Args:
            target_text: The text to verify
            suspect_author_id: The claimed author
            iterations: Number of bootstrap iterations
            mfw_size: Number of Most Frequent Words to sample per iteration
            impostor_count: Number of random impostors to use
            
        Returns:
            Dict with verification results including confidence score
        """
        logger.info(f"🔍 Impostors verification: '{suspect_author_id}' suspect")
        
        # 1. Get vocabularies
        target_vocab = Counter(target_text.lower().split())
        suspect_vocab = self._get_author_vocabulary(suspect_author_id)
        
        # 2. Load impostor pool
        impostors = self._load_impostor_pool(suspect_author_id, impostor_count)
        
        if not impostors:
            return {
                "verified": False,
                "confidence": 0.0,
                "reason": "No impostor pool available"
            }
            
        impostor_vocabs = {
            imp_id: self._get_author_vocabulary(imp_id) 
            for imp_id in impostors
        }
        
        # 3. Build combined MFW vocabulary
        all_words = set(target_vocab.keys()) | set(suspect_vocab.keys())
        for vocab in impostor_vocabs.values():
            all_words |= set(vocab.keys())
        
        all_words = list(all_words)
        
        if len(all_words) < mfw_size:
            mfw_size = len(all_words)
        
        # 4. Iterative bootstrapping
        suspect_wins = 0
        
        for iteration in range(iterations):
            # Randomly sample MFWs
            selected_mfws = random.sample(all_words, mfw_size)
            
            # Calculate distance from target to suspect
            suspect_distance = self._calculate_distance(target_vocab, suspect_vocab, selected_mfws)
            
            # Calculate distances from target to each impostor
            impostor_distances = [
                self._calculate_distance(target_vocab, imp_vocab, selected_mfws)
                for imp_vocab in impostor_vocabs.values()
            ]
            
            # Check if suspect is the closest
            if suspect_distance < min(impostor_distances):
                suspect_wins += 1
        
        # 5. Calculate confidence
        confidence = suspect_wins / iterations
        
        # 6. Determine verdict
        verified = confidence >= 0.5
        
        result = {
            "verified": verified,
            "confidence": float(confidence),
            "suspect_author": suspect_author_id,
            "iterations": iterations,
            "suspect_wins": suspect_wins,
            "impostor_count": len(impostors),
            "verdict": "Verified" if verified else "External Author Likely"
        }
        
        if verified:
            logger.info(f"✅ Authorship VERIFIED: {confidence:.2%} confidence")
        else:
            logger.warning(f"⚠️ Authorship REJECTED: {confidence:.2%} confidence (threshold: 50%)")
        
        return result
