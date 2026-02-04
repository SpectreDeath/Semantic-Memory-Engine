import os
import json
import logging
import math
import hashlib
import statistics
import re
from collections import Counter
from datetime import datetime
from typing import Dict, Any, List

from gateway.hardware_security import get_hsm
from gateway.nexus_db import get_nexus
from .logic_anomaly_detector import LogicAnomalyDetector

logger = logging.getLogger("LawnmowerMan.APB")

class AdversarialPatternBreaker:
    """
    Adversarial Pattern Breaker (APB) v1.0
    Detects 'Linguistic Camouflage' - artificial entropy smoothing used to hide synthetic origin.
    Flags 'High-Confidence Deception' in the on_ingestion pipeline.
    """
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus = nexus_api  # SmeCoreBridge
        self.plugin_id = manifest.get("plugin_id")
        # Initialize Logic Anomaly Detector
        self.anomaly_detector = LogicAnomalyDetector()

    async def on_startup(self):
        """
        Initialize the 'nexus_adversarial_patterns' table in the core DB.
        """
        sql = """
            CREATE TABLE IF NOT EXISTS nexus_adversarial_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT NOT NULL,
                text_sample TEXT NOT NULL,
                camouflage_detected BOOLEAN NOT NULL,
                deception_confidence REAL NOT NULL,
                high_confidence_deception BOOLEAN NOT NULL,
                analysis_data TEXT NOT NULL,
                timestamp TEXT,
                source_id TEXT
            )
        """
        try:
            # We access the underlying sqlite connection via nexus_api.nexus.conn 
            # or execute directly if exposed. SmeCoreBridge exposes .nexus (NexusDB).
            # NexusDB has execute(sql, params).
            self.nexus.nexus.execute(sql)
            logger.info(f"[{self.plugin_id}] 'nexus_adversarial_patterns' table initialized.")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to init DB table: {e}")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Adversarial Pattern Breaker analysis for on_ingestion pipeline.
        Detects linguistic camouflage and flags High-Confidence Deception.
        """
        if not raw_data or len(raw_data) < 100:  # Minimum length for analysis
            return {"status": "skipped", "reason": "too_short"}

        # Perform linguistic camouflage detection
        camouflage_result = self.anomaly_detector.detect_linguistic_camouflage(raw_data)
        
        # Extract key results
        camouflage_detected = camouflage_result.get("camouflage_detected", False)
        deception_confidence = camouflage_result.get("deception_confidence", 0.0)
        high_confidence_deception = camouflage_result.get("high_confidence_deception", False)
        
        # Log significant findings
        if camouflage_detected:
            confidence_level = "HIGH" if high_confidence_deception else "MODERATE"
            logger.warning(f"[{self.plugin_id}] LINGUISTIC CAMOUFLAGE DETECTED - "
                          f"Confidence: {deception_confidence:.2%} ({confidence_level})")
        
        if high_confidence_deception:
            logger.critical(f"[{self.plugin_id}] *** HIGH-CONFIDENCE DECEPTION DETECTED *** "
                           f"Deception Confidence: {deception_confidence:.2%}")
        
        # Store result in database if significant
        if camouflage_detected:
            await self._store_adversarial_pattern(
                raw_data, 
                camouflage_result,
                metadata.get("source_id", "INGESTION_PIPELINE")
            )
        
        # Return analysis results
        return {
            "status": "analyzed",
            "linguistic_camouflage": {
                "detected": camouflage_detected,
                "deception_confidence": deception_confidence,
                "high_confidence_deception": high_confidence_deception,
                "analysis": camouflage_result.get("analysis", {})
            }
        }

    def get_tools(self) -> list:
        return [self.analyze_linguistic_camouflage, self.get_adversarial_statistics, self.compare_text_patterns]

    async def analyze_linguistic_camouflage(self, text: str) -> str:
        """
        Analyze text for linguistic camouflage and artificial entropy smoothing.
        """
        try:
            result = self.anomaly_detector.detect_linguistic_camouflage(text)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Linguistic camouflage analysis failed: {str(e)}"})

    async def get_adversarial_statistics(self) -> str:
        """
        Get statistics on detected adversarial patterns from the database.
        """
        try:
            # Count total patterns detected
            sql_count = "SELECT COUNT(*) as total_patterns FROM nexus_adversarial_patterns"
            count_result = self.nexus.nexus.query(sql_count)
            total_patterns = count_result[0]["total_patterns"] if count_result else 0
            
            # Count high confidence deceptions
            sql_high_confidence = "SELECT COUNT(*) as high_confidence FROM nexus_adversarial_patterns WHERE high_confidence_deception = 1"
            high_confidence_result = self.nexus.nexus.query(sql_high_confidence)
            high_confidence_count = high_confidence_result[0]["high_confidence"] if high_confidence_result else 0
            
            # Get recent patterns
            sql_recent = """
                SELECT text_hash, deception_confidence, high_confidence_deception, timestamp 
                FROM nexus_adversarial_patterns 
                ORDER BY timestamp DESC 
                LIMIT 10
            """
            recent_patterns = self.nexus.nexus.query(sql_recent)
            
            stats = {
                "total_patterns_detected": total_patterns,
                "high_confidence_deceptions": high_confidence_count,
                "deception_rate": round((high_confidence_count / total_patterns * 100) if total_patterns > 0 else 0, 2),
                "recent_patterns": [
                    {
                        "hash": pattern["text_hash"][:8] + "...",
                        "confidence": pattern["deception_confidence"],
                        "high_confidence": bool(pattern["high_confidence_deception"]),
                        "timestamp": pattern["timestamp"]
                    }
                    for pattern in recent_patterns
                ]
            }
            
            return json.dumps(stats, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Failed to get adversarial statistics: {str(e)}"})

    async def compare_text_patterns(self, text_a: str, text_b: str) -> str:
        """
        Compare two texts for adversarial pattern similarities.
        """
        try:
            result_a = self.anomaly_detector.detect_linguistic_camouflage(text_a)
            result_b = self.anomaly_detector.detect_linguistic_camouflage(text_b)
            
            # Compare deception confidences
            confidence_a = result_a.get("deception_confidence", 0.0)
            confidence_b = result_b.get("deception_confidence", 0.0)
            
            # Compare analysis patterns
            analysis_a = result_a.get("analysis", {})
            analysis_b = result_b.get("analysis", {})
            
            comparison = {
                "text_a": {
                    "camouflage_detected": result_a.get("camouflage_detected", False),
                    "deception_confidence": confidence_a,
                    "high_confidence_deception": result_a.get("high_confidence_deception", False)
                },
                "text_b": {
                    "camouflage_detected": result_b.get("camouflage_detected", False),
                    "deception_confidence": confidence_b,
                    "high_confidence_deception": result_b.get("high_confidence_deception", False)
                },
                "comparison": {
                    "confidence_difference": round(abs(confidence_a - confidence_b), 4),
                    "both_camouflaged": result_a.get("camouflage_detected", False) and result_b.get("camouflage_detected", False),
                    "both_high_confidence": result_a.get("high_confidence_deception", False) and result_b.get("high_confidence_deception", False),
                    "similarity_score": self._calculate_pattern_similarity(analysis_a, analysis_b)
                }
            }
            
            return json.dumps(comparison, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Text pattern comparison failed: {str(e)}"})

    async def _store_adversarial_pattern(self, text: str, analysis_result: Dict[str, Any], source_id: str):
        """
        Store adversarial pattern detection result in the database.
        """
        try:
            timestamp = datetime.now().isoformat()
            text_hash = hashlib.sha256(text.encode()).hexdigest()
            
            sql = """
                INSERT INTO nexus_adversarial_patterns 
                (text_hash, text_sample, camouflage_detected, deception_confidence, 
                 high_confidence_deception, analysis_data, timestamp, source_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.nexus.nexus.execute(sql, (
                text_hash,
                text[:5000],  # Limit text size
                analysis_result.get("camouflage_detected", False),
                analysis_result.get("deception_confidence", 0.0),
                analysis_result.get("high_confidence_deception", False),
                json.dumps(analysis_result.get("analysis", {})),
                timestamp,
                source_id
            ))
            
            logger.info(f"[{self.plugin_id}] Stored adversarial pattern: {text_hash[:8]}... (Confidence: {analysis_result.get('deception_confidence', 0):.2%})")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to store adversarial pattern: {e}")

    def _calculate_pattern_similarity(self, analysis_a: Dict[str, Any], analysis_b: Dict[str, Any]) -> float:
        """
        Calculate similarity score between two pattern analyses.
        """
        try:
            # Compare key metrics
            scores = []
            
            # Compare entropy smoothing scores
            if "entropy_smoothing" in analysis_a and "entropy_smoothing" in analysis_b:
                score_a = analysis_a["entropy_smoothing"].get("smoothing_score", 0.0)
                score_b = analysis_b["entropy_smoothing"].get("smoothing_score", 0.0)
                scores.append(1.0 - abs(score_a - score_b))
            
            # Compare uniformity scores
            if "pattern_uniformity" in analysis_a and "pattern_uniformity" in analysis_b:
                score_a = analysis_a["pattern_uniformity"].get("uniformity_score", 0.0)
                score_b = analysis_b["pattern_uniformity"].get("uniformity_score", 0.0)
                scores.append(1.0 - abs(score_a - score_b))
            
            # Compare lexical smoothing scores
            if "lexical_smoothing" in analysis_a and "lexical_smoothing" in analysis_b:
                score_a = analysis_a["lexical_smoothing"].get("lexical_smoothing_score", 0.0)
                score_b = analysis_b["lexical_smoothing"].get("lexical_smoothing_score", 0.0)
                scores.append(1.0 - abs(score_a - score_b))
            
            # Return average similarity
            return round(sum(scores) / len(scores), 4) if scores else 0.0
            
        except Exception:
            return 0.0


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return an AdversarialPatternBreaker instance."""
    return AdversarialPatternBreaker(manifest, nexus_api)