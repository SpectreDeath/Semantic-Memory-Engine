
import requests
import json
import logging
import sqlite3
import os
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ConceptNetTool")

# Constants
DB_PATH = Path("data/conceptnet_cache.db")
DB_LIMIT_MB = 500
MAX_DB_SIZE = DB_LIMIT_MB * 1024 * 1024  # 500MB in bytes

def init_db():
    """Initializes the SQLite database with WAL mode and schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Enable WAL mode for fast, non-blocking reads
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concepts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT UNIQUE,
            data TEXT,
            last_accessed TIMESTAMP,
            created_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def purge_old_records():
    """Purges the oldest records if the database exceeds DB_LIMIT_MB."""
    if not DB_PATH.exists():
        return
        
    current_size = os.path.getsize(DB_PATH)
    if current_size > MAX_DB_SIZE:
        logger.warning(f"Database size ({current_size} bytes) exceeds limit. Purging oldest records...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Delete 10% of the oldest records to create space
        cursor.execute("DELETE FROM concepts WHERE id IN (SELECT id FROM concepts ORDER BY last_accessed ASC LIMIT (SELECT COUNT(*) / 10 FROM concepts))")
        conn.commit()
        conn.close()
        # Run VACUUM to reclaim space
        conn = sqlite3.connect(DB_PATH)
        conn.execute("VACUUM")
        conn.close()

def get_concept_with_cache(term: str, limit: int = 5):
    """Checks cache first, then API, then updates cache."""
    term = term.lower().strip()
    
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Step 1: Check local cache
    cursor.execute("SELECT data FROM concepts WHERE term = ?", (term,))
    row = cursor.fetchone()
    
    if row:
        logger.info(f"Cache Hit: {term}")
        # Update last_accessed
        cursor.execute("UPDATE concepts SET last_accessed = ? WHERE term = ?", 
                       (datetime.datetime.now().isoformat(), term))
        conn.commit()
        conn.close()
        return json.loads(row[0])
    
    # Step 2: Cache Miss - Query API
    logger.info(f"Cache Miss: {term}. Querying Web API...")
    conn.close()
    
    results = lookup_concept_api(term, limit)
    
    if "error" not in results:
        # Step 3: Store in SQLite
        purge_old_records()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.datetime.now().isoformat()
        try:
            cursor.execute("INSERT OR REPLACE INTO concepts (term, data, last_accessed, created_at) VALUES (?, ?, ?, ?)",
                           (term, json.dumps(results), now, now))
            conn.commit()
        except Exception as e:
            logger.error(f"Failed to cache {term}: {e}")
        finally:
            conn.close()
            
    return results

def lookup_concept_api(term: str, limit: int = 5):
    """Core API lookup logic with weights and fallbacks."""
    base_url = "http://api.conceptnet.io/c/en/"
    formatted_term = term.lower().replace(" ", "_")
    url = f"{base_url}{formatted_term}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        edges = data.get("edges", [])
        results = {
            "RelatedTo": [],
            "UsedFor": [],
            "HasContext": [],
            "IsA": []
        }
        
        # Store high-weight relations
        for edge in edges:
            rel = edge.get("rel", {}).get("label")
            end_label = edge.get("end", {}).get("label")
            weight = edge.get("weight", 1.0)
            
            if rel in results and end_label.lower() != term.lower():
                # We store a dict with label and weight for forensic integrity
                if not any(item['label'] == end_label for item in results[rel]):
                    results[rel].append({"label": end_label, "weight": weight})
        
        # Sort and limit by weight
        for rel in results:
            results[rel] = sorted(results[rel], key=lambda x: x['weight'], reverse=True)[:limit]
            
        return results
        
    except Exception as e:
        logger.error(f"ConceptNet API lookup failed for {term}: {e}")
        # Fallback for stability (weights included)
        fallbacks = {
            "cbrn": {
                "RelatedTo": [{"label": "toxic", "weight": 5.0}, {"label": "chemical", "weight": 4.5}],
                "UsedFor": [{"label": "threat", "weight": 3.0}],
                "HasContext": [{"label": "security", "weight": 4.0}],
                "IsA": [{"label": "danger", "weight": 5.0}]
            },
            "sensor": {
                "RelatedTo": [{"label": "detection", "weight": 6.0}],
                "UsedFor": [{"label": "monitoring", "weight": 5.0}],
                "HasContext": [{"label": "security", "weight": 4.5}],
                "IsA": [{"label": "device", "weight": 5.0}]
            }
        }
        
        lower_term = term.lower()
        if lower_term in fallbacks:
            logger.info(f"Using simulated fallback for {term}")
            return fallbacks[lower_term]
            
        return {"error": str(e)}

def format_concept_summary(results: dict):
    """Formats results into a summary, highlighting high-weight links."""
    if "error" in results:
        return f"ConceptNet Error: {results['error']}"
    
    summary = []
    for rel, values in results.items():
        if values:
            labels = [f"{v['label']} (w:{v['weight']})" for v in values]
            summary.append(f"{rel}: {', '.join(labels)}")
            
    return " | ".join(summary) if summary else "No associations found."

if __name__ == "__main__":
    # Test cases
    test_terms = ["CBRN", "sensor", "toxic"]
    for t in test_terms:
        print(f"\n--- Look up: {t} ---")
        res = get_concept_with_cache(t)
        print(format_concept_summary(res))
