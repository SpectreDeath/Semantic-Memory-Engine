import logging
import sqlite3
import json
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import os

from src.core.config import Config

logger = logging.getLogger(__name__)

class AdaptiveLearner:
    """
    Manages evolving author fingerprints using temporal weighting and drift detection.
    Enables the Scribe Engine to adapt to an author's changing style over time.
    """

    def __init__(self, db_path: Optional[str] = None):
        config = Config()
        base_dir = config.get_path('storage.base_dir')
        self.db_path = db_path or str(base_dir / "storage" / "scribe_profiles.sqlite")
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensures the profile_snapshots table exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id TEXT NOT NULL,
                signal_weights TEXT NOT NULL, -- JSON
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Ensure index on author_id
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_author ON profile_snapshots(author_id)")
        conn.commit()
        conn.close()

    def save_profile_snapshot(self, author_id: str, current_weights: Dict[str, float]):
        """
        Stores the state of an author's profile before update.
        
        Args:
            author_id: The unique author identifier.
            current_weights: Dictionary of signal weights.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO profile_snapshots (author_id, signal_weights, timestamp)
                VALUES (?, ?, ?)
            """, (author_id, json.dumps(current_weights), datetime.utcnow().isoformat()))
            conn.commit()
            logger.info(f"📸 Saved profile snapshot for {author_id}")
        except Exception as e:
            logger.error(f"Failed to save snapshot for {author_id}: {e}")
        finally:
            conn.close()

    def calculate_weighted_profile(self, author_id: str, decay_factor: float = 0.9) -> Dict[str, float]:
        """
        Retrieves historical snapshots and applies exponential decay.
        
        Args:
            author_id: The author to calculate for.
            decay_factor: Rate of decay (0.0 < x < 1.0). Closer to 1 keeps history longer.
            
        Returns:
            Weighted average of signal weights.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get snapshots ordered by most recent first
        cursor.execute("""
            SELECT signal_weights FROM profile_snapshots 
            WHERE author_id = ? 
            ORDER BY timestamp DESC
        """, (author_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {}
            
        # Parse JSON and prepare for weighting
        snapshots = [json.loads(row[0]) for row in rows]
        
        # Identify all unique signals across all snapshots
        all_signals = set()
        for snap in snapshots:
            all_signals.update(snap.keys())
        
        # Accumulate weighted sums
        weighted_sums = {sig: 0.0 for sig in all_signals}
        total_weight = 0.0
        
        # Apply decay: Weight = decay_factor ^ index (0 is most recent)
        for i, snap in enumerate(snapshots):
            weight = decay_factor ** i
            total_weight += weight
            for sig, val in snap.items():
                weighted_sums[sig] += val * weight
                
        # Normalize
        if total_weight > 0:
            final_weights = {sig: val / total_weight for sig, val in weighted_sums.items()}
        else:
            final_weights = snapshots[0] # Fallback
            
        return final_weights

    def detect_style_drift(self, new_data: Dict[str, float], author_id: str, threshold: float = 0.15) -> Dict[str, Any]:
        """
        Flags if new content is a statistical outlier compared to weighted history.
        
        Args:
            new_data: Signal weights of the new text.
            author_id: Author to check against.
            threshold: Cosine distance threshold for alerting drift.
            
        Returns:
            Dict containing 'drift_detected' (bool), 'distance' (float), 'is_outlier' (bool).
        """
        historical_profile = self.calculate_weighted_profile(author_id)
        
        if not historical_profile:
            return {"drift_detected": False, "reason": "No history", "distance": 0.0}
            
        # Align vectors for cosine distance
        all_keys = set(historical_profile.keys()) | set(new_data.keys())
        sorted_keys = sorted(list(all_keys))
        
        vec_hist = np.array([historical_profile.get(k, 0.0) for k in sorted_keys], dtype=float)
        vec_new = np.array([new_data.get(k, 0.0) for k in sorted_keys], dtype=float)
        
        # Check for zero vectors to avoid NaN
        if np.all(vec_hist == 0) or np.all(vec_new == 0):
             return {"drift_detected": False, "reason": "Zero vector", "distance": 0.0}

        # Manual cosine distance to avoid scipy dependency
        dot_product = np.dot(vec_hist, vec_new)
        norm_hist = np.linalg.norm(vec_hist)
        norm_new = np.linalg.norm(vec_new)
        cosine_similarity = dot_product / (norm_hist * norm_new)
        dist = 1.0 - cosine_similarity
        
        result = {
            "drift_detected": dist > threshold,
            "distance": float(dist),
            "threshold": threshold,
            "is_outlier": dist > (threshold * 1.5) # Arbitrary outlier definition
        }
        
        if result["drift_detected"]:
            logger.warning(f"⚠️ Style Drift Detected for {author_id}: Distance {dist:.4f} > {threshold}")
            
        return result

    def get_evolution_history(self, author_id: str) -> pd.DataFrame:
        """
        Retrieves all historical snapshots for an author as a DataFrame.
        Useful for plotting style evolution over time.
        """
        conn = sqlite3.connect(self.db_path)
        try:
            # Get all snapshots sorted by time
            query = "SELECT timestamp, signal_weights FROM profile_snapshots WHERE author_id = ? ORDER BY timestamp ASC"
            df = pd.read_sql_query(query, conn, params=(author_id,))
            
            if df.empty:
                return pd.DataFrame()
            
            # Expand the JSON signal_weights into columns
            # 1. Parse JSON
            df['weights'] = df['signal_weights'].apply(json.loads)
            
            # 2. Normalize JSON into columns
            # This creates a new DF with signal columns
            signals_df = pd.json_normalize(df['weights'])
            
            # 3. Join back with timestamp
            result = pd.concat([df[['timestamp']], signals_df], axis=1)
            
            # Convert timestamp to datetime
            result['timestamp'] = pd.to_datetime(result['timestamp'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching history for {author_id}: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def analyze_recent_drift(self, author_id: str, threshold: float = 0.15) -> Tuple[bool, float]:
        """
        Checks if the *latest* snapshot deviates from the *historical weighted average* 
        of all prior snapshots.
        
        Returns:
            (is_drifting, drift_score)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get 2 most recent snapshots to ensure we have 'current' and 'history' candidates
            # Actually, to do this properly, we should take the LATEST snapshot as 'new_data'
            # and ALL PREVIOUS snapshots to build the 'weighted profile'.
            
            # 1. Get latest snapshot ID and data
            cursor.execute("""
                SELECT id, signal_weights FROM profile_snapshots 
                WHERE author_id = ? 
                ORDER BY timestamp DESC LIMIT 1
            """, (author_id,))
            row = cursor.fetchone()
            
            if not row:
                return False, 0.0
                
            latest_id = row[0]
            latest_data = json.loads(row[1])
            
            # 2. Calculate weighted profile of EVERYTHING ELSE (excluding latest)
            # We can reuse calculate_weighted_profile logic but we need to exclude the latest ID.
            # For simplicity in this 'lightweight' version, let's just use the standard weighted profile
            # which *includes* the latest. If the latest is an outlier, it will pull the average slightly,
            # but if it drifts enough, it should still show. 
            # STRICTER: If we want to detect if the *new* thing is weird, we should compare against *old* things.
            
            # Let's fetch all others.
            cursor.execute("""
                SELECT signal_weights FROM profile_snapshots 
                WHERE author_id = ? AND id != ?
                ORDER BY timestamp DESC
            """, (author_id, latest_id))
            
            history_rows = cursor.fetchall()
            
            if not history_rows:
                # No history to compare against
                return False, 0.0
                
            # Calculate manual weighted average of history
            snapshots = [json.loads(r[0]) for r in history_rows]
            
            all_signals = set()
            for snap in snapshots:
                all_signals.update(snap.keys())
            
            weighted_sums = {sig: 0.0 for sig in all_signals}
            total_weight = 0.0
            decay_factor = 0.9
            
            for i, snap in enumerate(snapshots):
                weight = decay_factor ** i
                total_weight += weight
                for sig, val in snap.items():
                    weighted_sums[sig] += val * weight
            
            history_profile = {sig: val / total_weight for sig, val in weighted_sums.items()} if total_weight > 0 else snapshots[0]
            
            # 3. Detect Drift
            # Use the internal manual cosine logic or call detect_style_drift helper if refactored
            # We'll just do the math here to be safe and dependency-free
            
            all_keys = set(history_profile.keys()) | set(latest_data.keys())
            sorted_keys = sorted(list(all_keys))
        
            vec_hist = np.array([history_profile.get(k, 0.0) for k in sorted_keys], dtype=float)
            vec_new = np.array([latest_data.get(k, 0.0) for k in sorted_keys], dtype=float)
            
            if np.all(vec_hist == 0) or np.all(vec_new == 0):
                 return False, 0.0

            dot_product = np.dot(vec_hist, vec_new)
            norm_hist = np.linalg.norm(vec_hist)
            norm_new = np.linalg.norm(vec_new)
            
            if norm_hist == 0 or norm_new == 0:
                return False, 0.0
                
            cosine_similarity = dot_product / (norm_hist * norm_new)
            dist = 1.0 - cosine_similarity
            
            return dist > threshold, float(dist)

        except Exception as e:
            logger.error(f"Error checking recent drift: {e}")
            return False, 0.0
        finally:
            conn.close()
