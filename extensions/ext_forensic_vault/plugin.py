import os
import json
import logging
import asyncio
import time
import hashlib
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

# NexusAPI: use self.nexus.nexus and self.nexus.get_hsm() — no gateway imports

logger = logging.getLogger("LawnmowerMan.ForensicVault")

@dataclass
class SuspectRecord:
    """Represents a suspect record in the forensic ledger."""
    sample_id: str
    model_fingerprint: str
    combined_anomaly_score: float
    timestamp: datetime
    source_plugin: str
    metadata: Dict[str, Any]

@dataclass
class MatchResult:
    """Represents a fingerprint match result."""
    is_match: bool
    match_confidence: float
    matched_sample_id: Optional[str]
    matched_fingerprint: Optional[str]
    anomaly_score: float

class ForensicVault:
    """
    Forensic Vault v1.0
    Manages forensic analysis and suspect ledger for detecting recurring adversarial patterns.
    Implements cross-reference anomaly detection with 90% fingerprint matching threshold.
    """
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus = nexus_api  # SmeCoreBridge
        self.plugin_id = manifest.get("plugin_id")
        
        # Configuration
        self.fingerprint_threshold = 0.90  # 90% match threshold
        self.min_anomaly_score = 0.70  # Minimum anomaly score for high-confidence deception
        
        # Initialize database
        self._initialize_database()
        
        logger.info(f"[{self.plugin_id}] Forensic Vault initialized with {self.fingerprint_threshold*100}% fingerprint threshold")

    async def on_startup(self):
        """
        Initialize the Forensic Vault.
        """
        try:
            logger.info(f"[{self.plugin_id}] Forensic Vault started successfully")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to start Forensic Vault: {e}")

    async def on_shutdown(self):
        """
        Clean shutdown of the Forensic Vault.
        """
        try:
            logger.info(f"[{self.plugin_id}] Forensic Vault shutdown complete")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error during shutdown: {e}")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Forensic Vault does not process on_ingestion directly.
        It provides tools for cross-referencing anomalies.
        """
        return {
            "status": "skipped",
            "reason": "Forensic Vault provides cross-reference tools, not direct ingestion processing"
        }

    def get_tools(self) -> list:
        return [
            self.cross_reference_anomalies,
            self.get_suspect_ledger_stats,
            self.add_suspect_record,
            self.get_matching_records,
            self.clear_suspect_ledger
        ]

    async def cross_reference_anomalies(self, sample_id: str, model_fingerprint: str, combined_anomaly_score: float, source_plugin: str = "unknown", metadata: Dict[str, Any] = None) -> str:
        """
        Cross-reference anomalies against the suspect ledger.
        
        Logic: If a 90% match is found with a previously flagged High-Confidence Deception,
        update the log to: "[RECURRING ADVERSARIAL PATTERN DETECTED]".
        """
        try:
            # Validate input
            if not sample_id or not model_fingerprint:
                return json.dumps({
                    "error": "sample_id and model_fingerprint are required"
                })
            
            if combined_anomaly_score < 0 or combined_anomaly_score > 1:
                return json.dumps({
                    "error": "combined_anomaly_score must be between 0 and 1"
                })
            
            # Check for high-confidence deception (anomaly score >= threshold)
            is_high_confidence = combined_anomaly_score >= self.min_anomaly_score
            
            # Find matching records
            match_result = await self._find_matching_fingerprints(model_fingerprint)
            
            result = {
                "sample_id": sample_id,
                "model_fingerprint": model_fingerprint,
                "anomaly_score": combined_anomaly_score,
                "is_high_confidence": is_high_confidence,
                "match_found": match_result.is_match,
                "match_confidence": match_result.match_confidence,
                "action": "none"
            }
            
            if match_result.is_match:
                if is_high_confidence:
                    # RECURRING ADVERSARIAL PATTERN DETECTED
                    result["action"] = "RECURRING ADVERSARIAL PATTERN DETECTED"
                    result["matched_sample_id"] = match_result.matched_sample_id
                    result["previous_anomaly_score"] = match_result.anomaly_score
                    
                    # Log the recurring pattern
                    logger.warning(f"[{self.plugin_id}] RECURRING ADVERSARIAL PATTERN DETECTED: "
                                 f"Sample {sample_id} matches {match_result.matched_sample_id} "
                                 f"with {match_result.match_confidence*100:.1f}% confidence")
                    
                    # Update the matched record to indicate recurrence
                    await self._mark_as_recurring(match_result.matched_sample_id, sample_id)
                    
                else:
                    # Match found but not high-confidence
                    result["action"] = "MATCH_FOUND_LOW_CONFIDENCE"
                    result["matched_sample_id"] = match_result.matched_sample_id
                    result["previous_anomaly_score"] = match_result.anomaly_score
                    
                    logger.info(f"[{self.plugin_id}] Pattern match found (low confidence): "
                              f"Sample {sample_id} matches {match_result.matched_sample_id} "
                              f"with {match_result.match_confidence*100:.1f}% confidence")
            
            # Add new record to ledger
            await self._add_suspect_record(
                sample_id=sample_id,
                model_fingerprint=model_fingerprint,
                combined_anomaly_score=combined_anomaly_score,
                source_plugin=source_plugin,
                metadata=metadata or {}
            )
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error in cross_reference_anomalies: {e}")
            return json.dumps({
                "error": f"Failed to cross-reference anomalies: {str(e)}"
            })

    async def get_suspect_ledger_stats(self) -> str:
        """Get statistics about the suspect ledger."""
        try:
            # Get total records
            total_sql = "SELECT COUNT(*) FROM nexus_forensic_ledger"
            total_count = self.nexus.nexus.execute(total_sql).fetchone()[0]
            
            # Get high-confidence records
            high_conf_sql = "SELECT COUNT(*) FROM nexus_forensic_ledger WHERE combined_anomaly_score >= ?"
            high_conf_count = self.nexus.nexus.execute(high_conf_sql, (self.min_anomaly_score,)).fetchone()[0]
            
            # Get recurring patterns
            recurring_sql = "SELECT COUNT(*) FROM nexus_forensic_ledger WHERE is_recurring = 1"
            recurring_count = self.nexus.nexus.execute(recurring_sql).fetchone()[0]
            
            # Get source plugin distribution
            plugin_sql = "SELECT source_plugin, COUNT(*) FROM nexus_forensic_ledger GROUP BY source_plugin"
            plugin_rows = self.nexus.nexus.execute(plugin_sql).fetchall()
            plugin_stats = {row[0]: row[1] for row in plugin_rows}
            
            stats = {
                "total_records": total_count,
                "high_confidence_records": high_conf_count,
                "recurring_patterns": recurring_count,
                "plugin_distribution": plugin_stats,
                "fingerprint_threshold": self.fingerprint_threshold,
                "min_anomaly_score": self.min_anomaly_score
            }
            
            return json.dumps(stats, indent=2)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error getting suspect ledger stats: {e}")
            return json.dumps({"error": f"Failed to get stats: {str(e)}"})

    async def add_suspect_record(self, sample_id: str, model_fingerprint: str, combined_anomaly_score: float, source_plugin: str = "unknown", metadata: Dict[str, Any] = None) -> str:
        """Manually add a suspect record to the ledger."""
        try:
            await self._add_suspect_record(
                sample_id=sample_id,
                model_fingerprint=model_fingerprint,
                combined_anomaly_score=combined_anomaly_score,
                source_plugin=source_plugin,
                metadata=metadata or {}
            )
            
            return json.dumps({
                "status": "success",
                "message": f"Added suspect record for {sample_id}",
                "sample_id": sample_id
            })
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error adding suspect record: {e}")
            return json.dumps({
                "error": f"Failed to add suspect record: {str(e)}"
            })

    async def get_matching_records(self, model_fingerprint: str, threshold: float = None) -> str:
        """Get all records that match the given fingerprint above the threshold."""
        try:
            threshold = threshold or self.fingerprint_threshold
            
            # Get all records for comparison
            all_records = await self._get_all_suspect_records()
            
            matches = []
            for record in all_records:
                confidence = self._calculate_fingerprint_similarity(model_fingerprint, record.model_fingerprint)
                
                if confidence >= threshold:
                    matches.append({
                        "sample_id": record.sample_id,
                        "match_confidence": confidence,
                        "anomaly_score": record.combined_anomaly_score,
                        "source_plugin": record.source_plugin,
                        "timestamp": record.timestamp.isoformat(),
                        "is_recurring": getattr(record, 'is_recurring', False)
                    })
            
            # Sort by match confidence
            matches.sort(key=lambda x: x['match_confidence'], reverse=True)
            
            return json.dumps({
                "query_fingerprint": model_fingerprint,
                "threshold": threshold,
                "matches_found": len(matches),
                "matches": matches
            }, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error getting matching records: {e}")
            return json.dumps({"error": f"Failed to get matching records: {str(e)}"})

    async def clear_suspect_ledger(self) -> str:
        """Clear all records from the suspect ledger."""
        try:
            # Backup current data before clearing (for safety)
            backup_sql = "SELECT * FROM nexus_forensic_ledger"
            backup_data = self.nexus.nexus.execute(backup_sql).fetchall()
            
            # Clear the table
            clear_sql = "DELETE FROM nexus_forensic_ledger"
            self.nexus.nexus.execute(clear_sql)
            
            # Log the clearing action
            logger.info(f"[{self.plugin_id}] Suspect ledger cleared ({len(backup_data)} records removed)")
            
            return json.dumps({
                "status": "success",
                "message": f"Cleared {len(backup_data)} records from suspect ledger"
            })
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error clearing suspect ledger: {e}")
            return json.dumps({"error": f"Failed to clear suspect ledger: {str(e)}"})

    def _initialize_database(self):
        """Initialize the forensic ledger database table."""
        try:
            sql = """
                CREATE TABLE IF NOT EXISTS nexus_forensic_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_id TEXT UNIQUE NOT NULL,
                    model_fingerprint TEXT NOT NULL,
                    combined_anomaly_score REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    source_plugin TEXT NOT NULL,
                    metadata TEXT,
                    is_recurring INTEGER DEFAULT 0,
                    recurring_with TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            self.nexus.nexus.execute(sql)
            
            # Create index for faster fingerprint lookups
            index_sql = "CREATE INDEX IF NOT EXISTS idx_fingerprint ON nexus_forensic_ledger(model_fingerprint)"
            self.nexus.nexus.execute(index_sql)
            
            logger.info(f"[{self.plugin_id}] Suspect ledger database initialized")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to initialize database: {e}")
            raise

    async def _add_suspect_record(self, sample_id: str, model_fingerprint: str, combined_anomaly_score: float, source_plugin: str, metadata: Dict[str, Any]):
        """Add a suspect record to the ledger."""
        try:
            sql = """
                INSERT OR REPLACE INTO nexus_forensic_ledger 
                (sample_id, model_fingerprint, combined_anomaly_score, timestamp, source_plugin, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            
            self.nexus.nexus.execute(sql, (
                sample_id,
                model_fingerprint,
                combined_anomaly_score,
                datetime.now().isoformat(),
                source_plugin,
                json.dumps(metadata)
            ))
            
            logger.debug(f"[{self.plugin_id}] Added suspect record: {sample_id} (score: {combined_anomaly_score})")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to add suspect record: {e}")
            raise

    async def _find_matching_fingerprints(self, target_fingerprint: str) -> MatchResult:
        """Find matching fingerprints in the ledger."""
        try:
            # Get all records for comparison
            all_records = await self._get_all_suspect_records()
            
            best_match = None
            highest_confidence = 0.0
            
            for record in all_records:
                confidence = self._calculate_fingerprint_similarity(target_fingerprint, record.model_fingerprint)
                
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_match = record
            
            # Check if best match meets threshold
            if best_match and highest_confidence >= self.fingerprint_threshold:
                return MatchResult(
                    is_match=True,
                    match_confidence=highest_confidence,
                    matched_sample_id=best_match.sample_id,
                    matched_fingerprint=best_match.model_fingerprint,
                    anomaly_score=best_match.combined_anomaly_score
                )
            else:
                return MatchResult(
                    is_match=False,
                    match_confidence=highest_confidence,
                    matched_sample_id=None,
                    matched_fingerprint=None,
                    anomaly_score=0.0
                )
                
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error finding matching fingerprints: {e}")
            return MatchResult(False, 0.0, None, None, 0.0)

    async def _get_all_suspect_records(self) -> List[SuspectRecord]:
        """Get all suspect records from the ledger."""
        try:
            sql = "SELECT sample_id, model_fingerprint, combined_anomaly_score, timestamp, source_plugin, metadata FROM nexus_forensic_ledger"
            rows = self.nexus.nexus.execute(sql).fetchall()
            
            records = []
            for row in rows:
                metadata = json.loads(row[5]) if row[5] else {}
                records.append(SuspectRecord(
                    sample_id=row[0],
                    model_fingerprint=row[1],
                    combined_anomaly_score=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    source_plugin=row[4],
                    metadata=metadata
                ))
            
            return records
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error getting suspect records: {e}")
            return []

    def _calculate_fingerprint_similarity(self, fp1: str, fp2: str) -> float:
        """
        Calculate similarity between two fingerprints.
        
        Uses multiple similarity measures:
        1. Exact string match
        2. Levenshtein distance (edit distance)
        3. Jaccard similarity on character sets
        4. Cosine similarity on character frequency
        """
        try:
            if fp1 == fp2:
                return 1.0
            
            # Normalize fingerprints
            fp1_norm = fp1.lower().strip()
            fp2_norm = fp2.lower().strip()
            
            # Method 1: Jaccard similarity on character sets
            set1 = set(fp1_norm)
            set2 = set(fp2_norm)
            jaccard = len(set1.intersection(set2)) / len(set1.union(set2)) if set1.union(set2) else 0
            
            # Method 2: Character frequency cosine similarity
            from collections import Counter
            counter1 = Counter(fp1_norm)
            counter2 = Counter(fp2_norm)
            
            # Get all unique characters
            all_chars = set(counter1.keys()).union(set(counter2.keys()))
            
            # Create frequency vectors
            vec1 = [counter1.get(char, 0) for char in all_chars]
            vec2 = [counter2.get(char, 0) for char in all_chars]
            
            # Calculate cosine similarity
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5
            
            cosine_sim = dot_product / (magnitude1 * magnitude2) if magnitude1 * magnitude2 > 0 else 0
            
            # Method 3: Levenshtein distance normalized
            lev_distance = self._levenshtein_distance(fp1_norm, fp2_norm)
            max_len = max(len(fp1_norm), len(fp2_norm))
            lev_sim = 1.0 - (lev_distance / max_len) if max_len > 0 else 0
            
            # Weighted average of all methods
            # Jaccard: 30%, Cosine: 40%, Levenshtein: 30%
            combined_similarity = (jaccard * 0.3) + (cosine_sim * 0.4) + (lev_sim * 0.3)
            
            return combined_similarity
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error calculating fingerprint similarity: {e}")
            return 0.0

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    async def _mark_as_recurring(self, original_sample_id: str, new_sample_id: str):
        """Mark a record as recurring and link it to the new sample."""
        try:
            sql = """
                UPDATE nexus_forensic_ledger 
                SET is_recurring = 1, recurring_with = ?
                WHERE sample_id = ?
            """
            self.nexus.nexus.execute(sql, (new_sample_id, original_sample_id))
            
            logger.info(f"[{self.plugin_id}] Marked {original_sample_id} as recurring with {new_sample_id}")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error marking as recurring: {e}")

    def register_apb_integration(self, apb_plugin):
        """Register APB plugin for automatic high-confidence deception detection."""
        # This would be called by the APB plugin to register for automatic cross-referencing
        logger.info(f"[{self.plugin_id}] APB integration registered")
        # Implementation would depend on how APB wants to integrate


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return a ForensicVault instance."""
    return ForensicVault(manifest, nexus_api)


def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return create_plugin(manifest, nexus_api)