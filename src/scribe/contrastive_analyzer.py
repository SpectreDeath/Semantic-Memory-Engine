import logging
import numpy as np
from typing import Dict, List, Tuple, Any
from collections import Counter
import sqlite3

from src.core.config import Config

logger = logging.getLogger(__name__)

class ContrastiveAnalyzer:
    """
    Contrastive lexical analysis for authorship discrimination.
    Based on Computational Stylistics Group's oppose() function.
    Uses Zeta-score to identify preferred/avoided words.
    """

    def __init__(self, db_path: str = None):
        config = Config()
        base_dir = config.get_path('storage.base_dir')
        self.db_path = db_path or str(base_dir / "storage" / "scribe_profiles.sqlite")

    def _get_author_texts(self, author_id: str) -> List[str]:
        """
        Retrieves all text samples for an author from profile snapshots.
        
        Args:
            author_id: The author identifier
            
        Returns:
            List of text samples (concatenated from signal weights or stored text)
        """
        # In a full implementation, this would retrieve actual text samples
        # For now, we'll return a placeholder that would be replaced with real data
        # Typically from attribution_history or a dedicated 'samples' table
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Placeholder query - in production would fetch actual text samples
        cursor.execute("SELECT COUNT(*) FROM profile_snapshots WHERE author_id = ?", (author_id,))
        count = cursor.fetchone()[0]
        conn.close()
        
        # For verification purposes, return dummy data
        # In production, this would fetch real text samples
        return [f"Sample text for {author_id} passage {i}" for i in range(max(1, count))]

    def _calculate_zeta_scores(
        self, 
        texts_a: List[str], 
        texts_b: List[str],
        min_freq: int = 2
    ) -> Dict[str, float]:
        """
        Calculates Zeta scores for word discrimination.
        
        Zeta = proportion of A texts containing word - proportion of B texts containing word
        
        Args:
            texts_a: Text samples from author A
            texts_b: Text samples from author B
            min_freq: Minimum frequency threshold
            
        Returns:
            Dict mapping words to Zeta scores (positive = preferred by A, negative = preferred by B)
        """
        # Build word presence matrices (not frequency, but binary presence per document)
        vocab_a = set()
        vocab_b = set()
        
        doc_word_presence_a = []
        doc_word_presence_b = []
        
        for text in texts_a:
            words = set(text.lower().split())
            vocab_a.update(words)
            doc_word_presence_a.append(words)
            
        for text in texts_b:
            words = set(text.lower().split())
            vocab_b.update(words)
            doc_word_presence_b.append(words)
        
        # Combined vocabulary
        vocab = vocab_a | vocab_b
        
        zeta_scores = {}
        
        for word in vocab:
            # Count how many documents in each corpus contain this word
            count_a = sum(1 for doc_words in doc_word_presence_a if word in doc_words)
            count_b = sum(1 for doc_words in doc_word_presence_b if word in doc_words)
            
            # Skip rare words
            if count_a + count_b < min_freq:
                continue
            
            # Calculate proportions
            prop_a = count_a / len(texts_a) if texts_a else 0
            prop_b = count_b / len(texts_b) if texts_b else 0
            
            # Zeta score
            zeta = prop_a - prop_b
            zeta_scores[word] = zeta
            
        return zeta_scores

    def get_contrastive_lexicon(
        self, 
        author_a_id: str, 
        author_b_id: str,
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Identifies distinctive lexical markers between two authors.
        
        Args:
            author_a_id: First author identifier
            author_b_id: Second author identifier
            top_n: Number of top markers to return for each side
            
        Returns:
            Dict formatted for bar chart visualization with 'preferred_a', 'preferred_b', 'labels', 'scores'
        """
        logger.info(f"⚔️ Contrastive analysis: {author_a_id} vs {author_b_id}")
        
        # Retrieve text samples
        texts_a = self._get_author_texts(author_a_id)
        texts_b = self._get_author_texts(author_b_id)
        
        if not texts_a or not texts_b:
            return {
                "error": "Insufficient data for contrastive analysis",
                "preferred_a": [],
                "preferred_b": [],
                "labels": [],
                "scores": []
            }
        
        # Calculate Zeta scores
        zeta_scores = self._calculate_zeta_scores(texts_a, texts_b)
        
        # Sort by absolute Zeta value
        sorted_words = sorted(zeta_scores.items(), key=lambda x: abs(x[1]), reverse=True)
        
        # Separate into A-preferred (positive) and B-preferred (negative)
        preferred_a = [(word, score) for word, score in sorted_words if score > 0][:top_n]
        preferred_b = [(word, abs(score)) for word, score in sorted_words if score < 0][:top_n]
        
        # Format for horizontal bar chart
        # Labels on Y-axis, scores on X-axis
        labels_a = [word for word, _ in preferred_a]
        scores_a = [score for _, score in preferred_a]
        
        labels_b = [word for word, _ in preferred_b]
        scores_b = [score for _, score in preferred_b]
        
        return {
            "author_a": author_a_id,
            "author_b": author_b_id,
            "preferred_a": {
                "words": labels_a,
                "scores": scores_a
            },
            "preferred_b": {
                "words": labels_b,
                "scores": scores_b
            },
            "total_markers_found": len(zeta_scores)
        }
