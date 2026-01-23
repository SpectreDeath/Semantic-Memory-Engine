import requests
import sqlite3
import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.config import Config
from src.core.centrifuge import get_current_db_path

logger = logging.getLogger(__name__)

class ConceptResolver:
    """
    Common Sense Reasoning layer using ConceptNet.
    Provides semantic expansion, validation, and local caching.
    """

    def __init__(self, cache_path: Optional[str] = None):
        config = Config()
        base_dir = config.get_path('storage.base_dir')
        self.cache_path = cache_path or str(base_dir / "storage" / "concept_cache.sqlite")
        self.api_base_url = "http://api.conceptnet.io/c/en"
        self._init_cache()

    def _init_cache(self):
        """Initializes the local SQLite cache."""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concept_cache (
                term TEXT PRIMARY KEY,
                data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def _get_from_cache(self, term: str) -> Optional[List[Dict[str, Any]]]:
        """Retrieves relations from cache if available."""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM concept_cache WHERE term = ?", (term.lower(),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
        return None

    def _save_to_cache(self, term: str, data: List[Dict[str, Any]]):
        """Saves relations to cache."""
        conn = sqlite3.connect(self.cache_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO concept_cache (term, data, timestamp)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (term.lower(), json.dumps(data)))
        conn.commit()
        conn.close()

    def get_common_sense(self, term: str) -> List[Dict[str, Any]]:
        """
        Queries ConceptNet for core relations: IsA, UsedFor, PartOf.
        Uses local cache to minimize API calls.
        """
        term = term.lower().strip().replace(" ", "_")
        cached_data = self._get_from_cache(term)
        if cached_data is not None:
            return cached_data

        url = f"{self.api_base_url}/{term}"
        logger.info(f"🌐 Querying ConceptNet for: {term}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            raw_data = response.json()
            
            # Filter for core relations
            core_relations = []
            interesting_rels = ['/r/IsA', '/r/UsedFor', '/r/PartOf', '/r/HasProperty', '/r/CapableOf']
            
            for edge in raw_data.get('edges', []):
                rel = edge.get('rel', {}).get('@id')
                if rel in interesting_rels:
                    core_relations.append({
                        'start': edge.get('start', {}).get('label'),
                        'rel': rel.split('/')[-1],
                        'end': edge.get('end', {}).get('label'),
                        'weight': edge.get('weight', 1.0)
                    })
            
            self._save_to_cache(term, core_relations)
            return core_relations
            
        except Exception as e:
            logger.error(f"❌ ConceptNet query failed for {term}: {e}")
            return []

    def expand_concept(self, term: str) -> List[str]:
        """
        Finds related concepts for search expansion.
        Calls ConceptNet/Cache and returns unique labels of related nodes.
        """
        relations = self.get_common_sense(term)
        expanded = {term.lower()}
        
        for rel in relations:
            expanded.add(rel['start'].lower())
            expanded.add(rel['end'].lower())
            
        return list(expanded)

    def verify_fact(self, subject: str, relation: str, obj: str) -> Dict[str, Any]:
        """
        Verifies a fact against ConceptNet core relations.
        Returns a veracity score and details.
        """
        subject = subject.lower()
        obj = obj.lower()
        relations = self.get_common_sense(subject)
        
        # Look for the specific relation in the fetched data
        # Mapping common English relation terms to ConceptNet IDs
        rel_map = {
            'is a': 'IsA',
            'used for': 'UsedFor',
            'part of': 'PartOf',
            'has': 'HasProperty',
            'can': 'CapableOf'
        }
        
        target_rel = rel_map.get(relation.lower(), relation)
        
        match = None
        for r in relations:
            if r['rel'].lower() == target_rel.lower() and r['end'].lower() == obj:
                match = r
                break
        
        if match:
            return {
                "veracity": "verified",
                "score": 1.0,
                "confidence": match['weight'],
                "evidence": f"ConceptNet confirms: {subject} {relation} {obj}"
            }
        else:
            # If no direct match, could be "unknown" or "contradiction" 
            # (Contradiction requires checking negative relations or incompatible types)
            return {
                "veracity": "unverified",
                "score": 0.0,
                "confidence": 0.5,
                "evidence": f"No direct evidence found in ConceptNet for: {subject} {relation} {obj}"
            }
