import sqlite3
import csv
import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Callable, Generator, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LexiconImporter:
    """
    Production-ready Lexicon Importer for the Scribe Engine.
    Handles high-performance ingestion of forensic signals with low memory footprint.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path and ensure table schema."""
        if db_path is None:
            # Default to centrifuge_db.sqlite as per convention
            from src.core.config import Config
            config = Config()
            base_dir = config.get('storage.base_dir', './data')
            self.db_path = os.path.join(base_dir, "storage", "centrifuge_db.sqlite")
        else:
            self.db_path = db_path
            
        self._ensure_table()
        
    def _ensure_table(self):
        """Ensure the rhetorical_signals table exists with proper indices."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rhetorical_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    source_type TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index for fast lookup during forensic analysis
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_word ON rhetorical_signals(word)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signal_type ON rhetorical_signals(signal_type)")
            
            conn.commit()
            logger.info("✅ rhetorical_signals table initialized")
        finally:
            conn.close()

    def _stream_csv(self, file_path: str) -> Generator[Dict[str, str], None, None]:
        """Read CSV file line-by-line to keep memory usage low."""
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row

    def _stream_json(self, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """Read JSON file (assumes list of objects) iteratively."""
        # For very large JSONs, ijson would be better, but for now we use a generator 
        # around the loaded data if it's a standard list.
        with open(file_path, mode='r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    yield item
            else:
                yield data

    def import_lexicon(
        self, 
        file_path: str, 
        source_type: str, 
        mapping_func: Callable[[Dict[str, Any]], List[Tuple[str, str, float]]],
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Import signals from a file into CentrifugeDB using batch loading.
        
        Args:
            file_path: Path to CSV or JSON file.
            source_type: Label for the lexicon (e.g. 'emotion', 'sentiment').
            mapping_func: Function that takes a row dict and returns a list of 
                         (word, signal_type, weight) tuples.
            batch_size: Number of records to insert per transaction.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Lexicon file not found: {file_path}")
            
        ext = os.path.splitext(file_path)[1].lower()
        streamer = self._stream_csv if ext == '.csv' else self._stream_json
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_inserted = 0
        batch = []
        
        try:
            for row in streamer(file_path):
                signals = mapping_func(row)
                for word, signal_type, weight in signals:
                    batch.append((word, signal_type, weight, source_type))
                    
                    if len(batch) >= batch_size:
                        cursor.executemany("""
                            INSERT INTO rhetorical_signals (word, signal_type, weight, source_type)
                            VALUES (?, ?, ?, ?)
                        """, batch)
                        total_inserted += len(batch)
                        batch = []
            
            # Final remaining chunk
            if batch:
                cursor.executemany("""
                    INSERT INTO rhetorical_signals (word, signal_type, weight, source_type)
                    VALUES (?, ?, ?, ?)
                """, batch)
                total_inserted += len(batch)
                
            conn.commit()
            logger.info(f"✅ Imported {total_inserted} signals from {source_type}")
            
            return {
                "status": "success",
                "source_type": source_type,
                "records_processed": total_inserted
            }
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Failed to import lexicon: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            conn.close()

    def import_lexicon_internal_entry(self, word: str, signal_type: str, weight: float, source_type: str):
        """Helper for internal tools to insert single signals without a file."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO rhetorical_signals (word, signal_type, weight, source_type)
                VALUES (?, ?, ?, ?)
            """, (word, signal_type, weight, source_type))
            conn.commit()
        except Exception as e:
            logger.error(f"Error inserting internal lexicon entry: {e}")
        finally:
            conn.close()

    def get_category_summary(self) -> Dict[str, int]:
        """Returns counts of signals grouped by source type for Beacon integration."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT source_type, COUNT(*) 
                FROM rhetorical_signals 
                GROUP BY source_type
            """)
            return dict(cursor.fetchall())
        except Exception as e:
            logger.error(f"Error fetching summary: {e}")
            return {}
        finally:
            conn.close()

    def get_summary_by_author(self, author_id: str) -> pd.DataFrame:
        """
        Retrieves rhetorical signal distribution for a specific author.
        Queries the author profiles in scribe_profiles.sqlite.
        """
        # We need to find scribe_profiles.sqlite
        from src.core.config import Config
        config = Config()
        base_dir = config.get('storage.base_dir', './data')
        scribe_db = os.path.join(base_dir, "storage", "scribe_profiles.sqlite")
        
        if not os.path.exists(scribe_db):
            return pd.DataFrame()
            
        conn = sqlite3.connect(scribe_db)
        try:
            # ScribeEngine stores 'signal_weights' as a JSON string in author_profiles
            query = "SELECT signal_weights FROM author_profiles WHERE author_id = ?"
            cursor = conn.cursor()
            cursor.execute(query, (author_id,))
            row = cursor.fetchone()
            
            if not row or not row[0]:
                return pd.DataFrame()
            
            weights = json.loads(row[0])
            # Process weights into a format suitable for px.bar
            # weights is likely { "signal_anger": 0.4, "signal_trust": 0.2, ... }
            data = []
            for signal, weight in weights.items():
                category = signal.replace("signal_", "").replace("_", " ").title()
                data.append({"category": category, "count": weight})
            
            return pd.DataFrame(data).sort_values(by='count', ascending=False)
            
        except Exception as e:
            logger.error(f"Error fetching author summary: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
            
    def clear_lexicon(self, source_type: str):
        """Remove signals for a specific source type (useful for re-imports)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM rhetorical_signals WHERE source_type = ?", (source_type,))
            conn.commit()
            logger.info(f"🗑️ Cleared signals for: {source_type}")
        finally:
            conn.close()
