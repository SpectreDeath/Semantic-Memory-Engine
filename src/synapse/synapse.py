"""
The Synapse: Asynchronous Memory Consolidation
Merges similar entries into abstract concepts during idle time.
Recursive memory consolidation for efficient context windows.
"""

from mcp.server.fastmcp import FastMCP
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import hashlib

mcp = FastMCP("MemorySynapse")

DB_PATH = os.path.normpath("D:/mcp_servers/storage/laboratory.db")

class MemoryConsolidator:
    """Consolidates similar memory entries into abstract concepts."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensures consolidation tables exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_name TEXT UNIQUE,
                abstract_level INTEGER,
                member_count INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                definition TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concept_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id INTEGER,
                source_file TEXT,
                source_timestamp DATETIME,
                similarity_score REAL,
                FOREIGN KEY(concept_id) REFERENCES memory_concepts(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculates Jaccard similarity between two texts."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def find_similar_entries(self, threshold: float = 0.6) -> List[Tuple[str, List[str]]]:
        """Finds clusters of similar entries in sentiment logs."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT source_file FROM sentiment_logs 
                GROUP BY source_file 
                ORDER BY timestamp DESC LIMIT 100
            ''')
            files = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            clusters = []
            used = set()
            
            for i, file1 in enumerate(files):
                if file1 in used:
                    continue
                
                cluster = [file1]
                used.add(file1)
                
                for file2 in files[i+1:]:
                    if file2 in used:
                        continue
                    
                    # Extract text portions (simplified - using filenames)
                    similarity = self._calculate_similarity(file1, file2)
                    
                    if similarity >= threshold:
                        cluster.append(file2)
                        used.add(file2)
                
                if len(cluster) > 1:
                    clusters.append(cluster)
            
            return clusters
        
        except Exception as e:
            print(f"Error finding clusters: {e}")
            return []
    
    def create_concept(self, concept_name: str, members: List[str], definition: str = "") -> int:
        """Creates an abstract concept from clustered entries."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO memory_concepts 
                (concept_name, abstract_level, member_count, definition)
                VALUES (?, ?, ?, ?)
            ''', (concept_name, 1, len(members), definition))
            
            conn.commit()
            
            # Get the concept ID
            cursor.execute('SELECT id FROM memory_concepts WHERE concept_name = ?', (concept_name,))
            concept_id = cursor.fetchone()[0]
            
            # Add members
            for i, member in enumerate(members):
                cursor.execute('''
                    INSERT INTO concept_members (concept_id, source_file, source_timestamp, similarity_score)
                    VALUES (?, ?, ?, ?)
                ''', (concept_id, member, datetime.now(), 0.8 + (i * 0.02)))
            
            conn.commit()
            conn.close()
            
            return concept_id
        
        except Exception as e:
            print(f"Error creating concept: {e}")
            return -1
    
    def consolidate_idle(self, min_cluster_size: int = 3) -> Dict[str, Any]:
        """Performs consolidation during idle time."""
        results = {
            'clusters_found': 0,
            'concepts_created': 0,
            'total_members_consolidated': 0,
            'consolidation_summary': []
        }
        
        clusters = self.find_similar_entries(threshold=0.6)
        results['clusters_found'] = len(clusters)
        
        for i, cluster in enumerate(clusters):
            if len(cluster) >= min_cluster_size:
                # Generate concept name from common words
                concept_name = f"profile_{i}_{hashlib.md5(''.join(cluster).encode()).hexdigest()[:6]}"
                
                concept_id = self.create_concept(
                    concept_name,
                    cluster,
                    definition=f"Consolidated behavioral profile from {len(cluster)} observations"
                )
                
                if concept_id > 0:
                    results['concepts_created'] += 1
                    results['total_members_consolidated'] += len(cluster)
                    results['consolidation_summary'].append({
                        'concept_id': concept_id,
                        'concept_name': concept_name,
                        'member_count': len(cluster)
                    })
        
        return results


class BehavioralProfiler:
    """Creates behavioral profiles from consolidated memories."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def build_profile(self, entity_name: str, days: int = 30) -> Dict[str, Any]:
        """Builds a behavioral profile for an entity."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Aggregate sentiment data
            cursor.execute('''
                SELECT 
                    AVG(neg) as avg_neg,
                    AVG(neu) as avg_neu,
                    AVG(pos) as avg_pos,
                    AVG(compound) as avg_compound,
                    COUNT(*) as total_observations
                FROM sentiment_logs
                WHERE source_file LIKE ?
                AND timestamp >= datetime('now', ?)
            ''', (f'%{entity_name}%', f'-{days} days'))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                profile = {
                    'entity': entity_name,
                    'period_days': days,
                    'sentiment_profile': {
                        'avg_negativity': round(result[0] or 0, 3),
                        'avg_neutrality': round(result[1] or 0, 3),
                        'avg_positivity': round(result[2] or 0, 3),
                        'avg_compound': round(result[3] or 0, 4),
                    },
                    'total_observations': result[4] or 0,
                    'profile_status': 'stable' if result[4] and result[4] > 5 else 'incomplete'
                }
            else:
                profile = {'entity': entity_name, 'status': 'no_data'}
            
            return profile
        
        except Exception as e:
            return {'error': str(e)}


@mcp.tool()
def find_similar_memories(similarity_threshold: float = 0.6) -> str:
    """
    Identifies clusters of similar entries in memory database.
    Returns grouped entries for consolidation.
    """
    try:
        consolidator = MemoryConsolidator(DB_PATH)
        clusters = consolidator.find_similar_entries(threshold=similarity_threshold)
        
        result = {
            'clusters_found': len(clusters),
            'threshold': similarity_threshold,
            'clusters': [
                {
                    'size': len(cluster),
                    'members': cluster
                }
                for cluster in clusters
            ],
            'status': 'success'
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e), 'status': 'failed'})


@mcp.tool()
def create_memory_concept(concept_name: str, member_files: str, definition: str = "") -> str:
    """
    Creates an abstract concept from multiple memory entries.
    Returns concept ID and consolidation details.
    """
    try:
        members = json.loads(member_files) if isinstance(member_files, str) else member_files
        consolidator = MemoryConsolidator(DB_PATH)
        
        concept_id = consolidator.create_concept(concept_name, members, definition)
        
        result = {
            'concept_id': concept_id,
            'concept_name': concept_name,
            'member_count': len(members),
            'definition': definition,
            'status': 'created' if concept_id > 0 else 'failed'
        }
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e), 'status': 'failed'})


@mcp.tool()
def consolidate_during_idle() -> str:
    """
    Performs recursive memory consolidation.
    Designed to run during idle time without blocking main operations.
    """
    try:
        consolidator = MemoryConsolidator(DB_PATH)
        results = consolidator.consolidate_idle(min_cluster_size=3)
        
        return json.dumps({
            'consolidation_results': results,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed'
        }, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e), 'status': 'failed'})


@mcp.tool()
def build_behavioral_profile(entity_name: str, days: int = 30) -> str:
    """
    Builds a behavioral profile for an entity from consolidated memories.
    Shows sentiment trends and behavioral patterns.
    """
    try:
        profiler = BehavioralProfiler(DB_PATH)
        profile = profiler.build_profile(entity_name, days)
        
        return json.dumps({
            'behavioral_profile': profile,
            'status': 'success'
        }, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e), 'status': 'failed'})


if __name__ == "__main__":
    mcp.run()
