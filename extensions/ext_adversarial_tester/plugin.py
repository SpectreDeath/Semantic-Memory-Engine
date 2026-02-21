import os
import json
import logging
import asyncio
import time
import random
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict

# Try to import required libraries with fallbacks
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("[AdversarialTester] numpy not available, some features may be limited")

# NexusAPI: use self.nexus.nexus and self.nexus.get_hsm() — no gateway imports
from src.core.plugin_base import BasePlugin
from src.utils.error_handling import ErrorHandler, create_error_response, OperationContext

logger = logging.getLogger("LawnmowerMan.AdversarialTester")

@dataclass
class EvasionVariant:
    """Represents an evasion variant generated from a sample."""
    variant_id: str
    original_text: str
    modified_text: str
    variant_type: str
    modification_details: Dict[str, Any]

@dataclass
class DetectionResult:
    """Represents detection results from SDA and APB."""
    sample_id: str
    sda_result: Dict[str, Any]
    apb_result: Dict[str, Any]
    combined_score: float
    detection_confidence: str

@dataclass
class SignatureVulnerability:
    """Represents a detected signature vulnerability."""
    sample_id: str
    variant_id: str
    original_detection: float
    variant_detection: float
    vulnerability_score: float
    suggested_features: List[str]
    variant_details: Dict[str, Any]

class AdversarialTester(BasePlugin):
    """
    Adversarial Tester v1.0
    Tests adversarial evasion techniques by generating variants and analyzing detection rates.
    Uses rnj-1 to generate 3 evasion variants and tests them through SDA and APB.
    """
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        super().__init__(manifest, nexus_api)
        
        # Configuration
        self.detection_threshold = 0.50  # 50% detection threshold
        self.min_confidence_score = 0.70  # Minimum confidence for high-confidence samples
        self.variant_count = 3  # Number of variants to generate
        
        # Evasion techniques for rnj-1
        self.evasion_techniques = [
            self._character_substitution,
            self._word_obfuscation,
            self._structural_rewriting,
            self._semantic_preservation,
            self._formatting_manipulation
        ]
        
        # Registered plugins for testing
        self.sda_plugin = None
        self.apb_plugin = None
        
        logger.info(f"[{self.plugin_id}] Adversarial Tester initialized with {self.detection_threshold*100}% vulnerability threshold")

    async def on_startup(self):
        """
        Initialize the Adversarial Tester.
        """
        try:
            logger.info(f"[{self.plugin_id}] Adversarial Tester started successfully")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to start Adversarial Tester: {e}")

    async def on_shutdown(self):
        """
        Clean shutdown of the Adversarial Tester.
        """
        try:
            logger.info(f"[{self.plugin_id}] Adversarial Tester shutdown complete")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error during shutdown: {e}")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Adversarial Tester does not process on_ingestion directly.
        It provides tools for adversarial testing and vulnerability detection.
        """
        return {
            "status": "skipped",
            "reason": "Adversarial Tester provides testing tools, not direct ingestion processing"
        }

    def get_tools(self) -> list:
        return [
            self.run_evasion_test,
            self.get_evasion_statistics,
            self.generate_evasion_report,
            self.suggest_signature_improvements
        ]

    async def run_evasion_test(self, sample_id: str = None) -> str:
        """
        Run evasion test on a high-confidence sample.
        
        Fetches a high-confidence sample from the Forensic Vault, generates 3 evasion variants
        using rnj-1, and tests them through SDA and APB. Flags vulnerabilities if detection
        drops below 50%.
        """
        try:
            # Fetch high-confidence sample
            if sample_id:
                sample = await self._fetch_sample_by_id(sample_id)
                if not sample:
                    return json.dumps({
                        "error": f"Sample {sample_id} not found in forensic ledger"
                    })
            else:
                sample = await self._fetch_high_confidence_sample()
                if not sample:
                    return json.dumps({
                        "error": "No high-confidence samples found in forensic ledger"
                    })
            
            logger.info(f"[{self.plugin_id}] Running evasion test on sample: {sample.sample_id}")
            
            # Generate evasion variants using rnj-1 techniques
            variants = self._generate_evasion_variants(sample.model_fingerprint, sample.sample_id)
            
            # Test original sample
            original_result = await self._test_sample_detection(sample.model_fingerprint, sample.sample_id)
            
            # Test variants
            variant_results = []
            vulnerabilities = []
            
            for variant in variants:
                variant_result = await self._test_sample_detection(variant.modified_text, variant.variant_id)
                variant_results.append(variant_result)
                
                # Check for vulnerability
                if self._is_vulnerability(original_result, variant_result):
                    vulnerability = self._analyze_vulnerability(
                        sample.sample_id, variant, original_result, variant_result
                    )
                    vulnerabilities.append(vulnerability)
            
            # Generate report
            report = self._generate_evasion_report(
                sample, original_result, variants, variant_results, vulnerabilities
            )
            
            # Save vulnerability data
            await self._save_vulnerability_data(vulnerabilities)
            
            return json.dumps(report, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error running evasion test: {e}")
            return json.dumps({
                "error": f"Failed to run evasion test: {str(e)}"
            })

    async def get_evasion_statistics(self) -> str:
        """Get statistics about evasion testing results."""
        try:
            # Get statistics from vulnerability database
            stats = await self._get_vulnerability_statistics()
            return json.dumps(stats, indent=2)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error getting evasion statistics: {e}")
            return json.dumps({"error": f"Failed to get evasion statistics: {str(e)}"})

    async def generate_evasion_report(self, format: str = "json") -> str:
        """Generate comprehensive evasion testing report."""
        try:
            report = await self._generate_comprehensive_report()
            
            if format.lower() == "json":
                output_file = os.path.join("D:", "SME", "reports", "evasion_test_report.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, default=str)
                return json.dumps({
                    "status": "success",
                    "output_file": output_file,
                    "format": "JSON",
                    "report": report
                })
            else:
                return json.dumps(report, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error generating evasion report: {e}")
            return json.dumps({"error": f"Failed to generate evasion report: {str(e)}"})

    async def suggest_signature_improvements(self) -> str:
        """Suggest improvements to signatures.json based on vulnerability analysis."""
        try:
            suggestions = await self._analyze_signature_improvements()
            return json.dumps(suggestions, indent=2)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error suggesting signature improvements: {e}")
            return json.dumps({"error": f"Failed to suggest signature improvements: {str(e)}"})

    def register_plugins(self, sda_plugin=None, apb_plugin=None):
        """Register SDA and APB plugins for testing."""
        self.sda_plugin = sda_plugin
        self.apb_plugin = apb_plugin
        logger.info(f"[{self.plugin_id}] Registered plugins: SDA={sda_plugin is not None}, APB={apb_plugin is not None}")

    async def _fetch_high_confidence_sample(self) -> Optional[Any]:
        """Fetch a high-confidence sample from the forensic ledger."""
        try:
            sql = """
                SELECT sample_id, model_fingerprint, combined_anomaly_score, 
                       timestamp, source_plugin, metadata, is_recurring, recurring_with
                FROM nexus_forensic_ledger
                WHERE combined_anomaly_score >= ?
                ORDER BY combined_anomaly_score DESC
                LIMIT 1
            """
            
            rows = self.nexus.nexus.execute(sql, (self.min_confidence_score,)).fetchall()
            
            if rows:
                row = rows[0]
                metadata = json.loads(row[5]) if row[5] else {}
                return FingerprintRecord(
                    sample_id=row[0],
                    model_fingerprint=row[1],
                    combined_anomaly_score=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    source_plugin=row[4],
                    is_recurring=bool(row[6]),
                    recurring_with=row[7],
                    metadata=metadata
                )
            
            return None
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error fetching high-confidence sample: {e}")
            return None

    async def _fetch_sample_by_id(self, sample_id: str) -> Optional[Any]:
        """Fetch a specific sample by ID from the forensic ledger."""
        try:
            sql = """
                SELECT sample_id, model_fingerprint, combined_anomaly_score, 
                       timestamp, source_plugin, metadata, is_recurring, recurring_with
                FROM nexus_forensic_ledger
                WHERE sample_id = ?
            """
            
            rows = self.nexus.nexus.execute(sql, (sample_id,)).fetchall()
            
            if rows:
                row = rows[0]
                metadata = json.loads(row[5]) if row[5] else {}
                return FingerprintRecord(
                    sample_id=row[0],
                    model_fingerprint=row[1],
                    combined_anomaly_score=row[2],
                    timestamp=datetime.fromisoformat(row[3]),
                    source_plugin=row[4],
                    is_recurring=bool(row[6]),
                    recurring_with=row[7],
                    metadata=metadata
                )
            
            return None
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error fetching sample by ID: {e}")
            return None

    def _generate_evasion_variants(self, original_text: str, sample_id: str) -> List[EvasionVariant]:
        """Generate 3 evasion variants using rnj-1 techniques."""
        variants = []
        
        for i in range(self.variant_count):
            # Select random evasion technique
            technique = random.choice(self.evasion_techniques)
            
            # Generate variant
            variant_text, details = technique(original_text)
            
            variant = EvasionVariant(
                variant_id=f"{sample_id}_variant_{i+1}",
                original_text=original_text,
                modified_text=variant_text,
                variant_type=technique.__name__,
                modification_details=details
            )
            
            variants.append(variant)
        
        logger.debug(f"[{self.plugin_id}] Generated {len(variants)} evasion variants")
        return variants

    def _character_substitution(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Replace characters with visually similar alternatives."""
        substitutions = {
            'a': ['@', '4', 'α'],
            'e': ['3', '€', 'є'],
            'i': ['1', '!', 'ι'],
            'o': ['0', '°', 'ο'],
            's': ['5', '$', 'ѕ'],
            't': ['7', '+', 'τ'],
            'l': ['1', '|', '£'],
            'c': ['(', '<', '¢'],
            'b': ['6', '8', 'β'],
            'g': ['9', '6', '9']
        }
        
        modified_text = text
        changes = []
        
        for char, alternatives in substitutions.items():
            if char in modified_text.lower():
                alt = random.choice(alternatives)
                # Replace with probability
                if random.random() < 0.3:  # 30% chance of substitution
                    modified_text = modified_text.replace(char, alt)
                    changes.append(f"{char} -> {alt}")
        
        return modified_text, {
            "technique": "character_substitution",
            "changes": changes,
            "substitution_rate": len(changes) / len(text) if text else 0
        }

    def _word_obfuscation(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Obfuscate words using various techniques."""
        words = text.split()
        changes = []
        
        for i, word in enumerate(words):
            if len(word) > 3 and random.random() < 0.4:  # 40% chance
                # Add random characters
                if random.random() < 0.5:
                    # Insert random character
                    pos = random.randint(1, len(word) - 1)
                    char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    words[i] = word[:pos] + char + word[pos:]
                    changes.append(f"inserted '{char}' at position {pos}")
                else:
                    # Replace random character
                    pos = random.randint(0, len(word) - 1)
                    old_char = word[pos]
                    new_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                    words[i] = word[:pos] + new_char + word[pos+1:]
                    changes.append(f"replaced '{old_char}' with '{new_char}' at position {pos}")
        
        modified_text = ' '.join(words)
        return modified_text, {
            "technique": "word_obfuscation",
            "changes": changes,
            "obfuscation_rate": len(changes) / len(words) if words else 0
        }

    def _structural_rewriting(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Rewrite text structure while preserving meaning."""
        # Simple structural changes
        changes = []
        
        # Add/remove spaces
        if random.random() < 0.5:
            # Add extra spaces
            modified_text = re.sub(r'(\w)(\w)', r'\1 \2', text)
            changes.append("added extra spaces between characters")
        else:
            # Remove spaces
            modified_text = text.replace(' ', '')
            changes.append("removed all spaces")
        
        # Change case randomly
        if random.random() < 0.3:
            modified_text = ''.join(
                c.upper() if random.random() < 0.5 else c.lower() 
                for c in modified_text
            )
            changes.append("randomized character case")
        
        return modified_text, {
            "technique": "structural_rewriting",
            "changes": changes,
            "structural_changes": len(changes)
        }

    def _semantic_preservation(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Preserve semantic meaning while changing structure."""
        # Replace words with synonyms (simple implementation)
        synonym_map = {
            'test': ['trial', 'experiment', 'assessment'],
            'sample': ['example', 'specimen', 'instance'],
            'detection': ['identification', 'recognition', 'discovery'],
            'anomaly': ['irregularity', 'abnormality', 'deviation'],
            'pattern': ['sequence', 'structure', 'design']
        }
        
        words = text.lower().split()
        changes = []
        
        for i, word in enumerate(words):
            if word in synonym_map and random.random() < 0.6:  # 60% chance
                synonym = random.choice(synonym_map[word])
                words[i] = synonym
                changes.append(f"{word} -> {synonym}")
        
        modified_text = ' '.join(words)
        return modified_text, {
            "technique": "semantic_preservation",
            "changes": changes,
            "semantic_changes": len(changes)
        }

    def _formatting_manipulation(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Manipulate text formatting and encoding."""
        changes = []
        
        # Add Unicode homoglyphs
        homoglyphs = {
            'a': 'а',  # Cyrillic a
            'e': 'е',  # Cyrillic e
            'o': 'о',  # Cyrillic o
            'c': 'с',  # Cyrillic c
        }
        
        modified_text = text
        for char, homoglyph in homoglyphs.items():
            if char in modified_text and random.random() < 0.3:
                modified_text = modified_text.replace(char, homoglyph)
                changes.append(f"{char} -> {homoglyph} (homoglyph)")
        
        # Add invisible characters
        if random.random() < 0.4:
            # Add zero-width characters
            zero_width = '\u200B'  # Zero width space
            pos = random.randint(0, len(modified_text))
            modified_text = modified_text[:pos] + zero_width + modified_text[pos:]
            changes.append(f"added zero-width character at position {pos}")
        
        return modified_text, {
            "technique": "formatting_manipulation",
            "changes": changes,
            "formatting_changes": len(changes)
        }

    async def _test_sample_detection(self, text: str, sample_id: str) -> DetectionResult:
        """Test sample detection through SDA and APB."""
        try:
            sda_result = {"status": "not_tested", "score": 0.0, "details": {}}
            apb_result = {"status": "not_tested", "score": 0.0, "details": {}}
            
            # Test with SDA
            if self.sda_plugin and hasattr(self.sda_plugin, 'on_ingestion'):
                try:
                    sda_response = await self.sda_plugin.on_ingestion(text, {"source": "adversarial_test"})
                    sda_result = {
                        "status": "tested",
                        "score": sda_response.get("deception_score", 0.0),
                        "details": sda_response
                    }
                except Exception as e:
                    logger.warning(f"[{self.plugin_id}] SDA test failed: {e}")
                    sda_result = {"status": "failed", "score": 0.0, "error": str(e)}
            
            # Test with APB
            if self.apb_plugin and hasattr(self.apb_plugin, 'on_ingestion'):
                try:
                    apb_response = await self.apb_plugin.on_ingestion(text, {"source": "adversarial_test"})
                    apb_result = {
                        "status": "tested",
                        "score": apb_response.get("anomaly_score", 0.0),
                        "details": apb_response
                    }
                except Exception as e:
                    logger.warning(f"[{self.plugin_id}] APB test failed: {e}")
                    apb_result = {"status": "failed", "score": 0.0, "error": str(e)}
            
            # Calculate combined score
            combined_score = (sda_result.get("score", 0.0) + apb_result.get("score", 0.0)) / 2
            
            # Determine confidence level
            if combined_score >= 0.8:
                confidence = "HIGH"
            elif combined_score >= 0.5:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"
            
            return DetectionResult(
                sample_id=sample_id,
                sda_result=sda_result,
                apb_result=apb_result,
                combined_score=combined_score,
                detection_confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error testing sample detection: {e}")
            return DetectionResult(
                sample_id=sample_id,
                sda_result={"status": "error", "score": 0.0, "error": str(e)},
                apb_result={"status": "error", "score": 0.0, "error": str(e)},
                combined_score=0.0,
                detection_confidence="ERROR"
            )

    def _is_vulnerability(self, original: DetectionResult, variant: DetectionResult) -> bool:
        """Check if variant represents a signature vulnerability."""
        try:
            original_score = original.combined_score
            variant_score = variant.combined_score
            
            # Calculate vulnerability score
            vulnerability_score = original_score - variant_score
            
            # Check if detection dropped below 50%
            if variant_score < self.detection_threshold:
                logger.warning(f"[{self.plugin_id}] VULNERABILITY DETECTED: {variant.sample_id} "
                             f"dropped from {original_score:.3f} to {variant_score:.3f}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error checking vulnerability: {e}")
            return False

    def _analyze_vulnerability(self, sample_id: str, variant: EvasionVariant, 
                             original: DetectionResult, variant_result: DetectionResult) -> SignatureVulnerability:
        """Analyze and create vulnerability report."""
        vulnerability_score = original.combined_score - variant_result.combined_score
        
        # Generate suggestions based on variant type
        suggestions = self._generate_signature_suggestions(variant, original, variant_result)
        
        return SignatureVulnerability(
            sample_id=sample_id,
            variant_id=variant.variant_id,
            original_detection=original.combined_score,
            variant_detection=variant_result.combined_score,
            vulnerability_score=vulnerability_score,
            suggested_features=suggestions,
            variant_details=variant.modification_details
        )

    def _generate_signature_suggestions(self, variant: EvasionVariant, 
                                      original: DetectionResult, variant_result: DetectionResult) -> List[str]:
        """Generate suggestions for signature improvements."""
        suggestions = []
        
        variant_type = variant.variant_type
        
        if variant_type == "_character_substitution":
            suggestions.extend([
                "Add character homoglyph detection",
                "Implement character frequency analysis",
                "Include Unicode normalization checks"
            ])
        elif variant_type == "_word_obfuscation":
            suggestions.extend([
                "Add word boundary analysis",
                "Implement n-gram pattern matching",
                "Include dictionary-based validation"
            ])
        elif variant_type == "_structural_rewriting":
            suggestions.extend([
                "Add structural pattern analysis",
                "Implement whitespace normalization",
                "Include case-insensitive matching"
            ])
        elif variant_type == "_semantic_preservation":
            suggestions.extend([
                "Add semantic similarity detection",
                "Implement synonym mapping",
                "Include context-aware analysis"
            ])
        elif variant_type == "_formatting_manipulation":
            suggestions.extend([
                "Add Unicode normalization",
                "Implement invisible character detection",
                "Include encoding validation"
            ])
        
        # Add general suggestions
        if variant_result.combined_score < 0.3:
            suggestions.append("Consider adding multi-layer detection")
            suggestions.append("Implement ensemble detection methods")
        
        return list(set(suggestions))  # Remove duplicates

    def _generate_evasion_report(self, sample: Any, original: DetectionResult, 
                                variants: List[EvasionVariant], variant_results: List[DetectionResult],
                                vulnerabilities: List[SignatureVulnerability]) -> Dict[str, Any]:
        """Generate comprehensive evasion test report."""
        report = {
            "test_metadata": {
                "sample_id": sample.sample_id,
                "original_fingerprint": sample.model_fingerprint,
                "source_plugin": sample.source_plugin,
                "anomaly_score": sample.combined_anomaly_score,
                "is_recurring": sample.is_recurring,
                "test_timestamp": datetime.now().isoformat(),
                "variant_count": len(variants),
                "vulnerability_count": len(vulnerabilities)
            },
            "original_detection": {
                "sda_score": original.sda_result.get("score", 0.0),
                "apb_score": original.apb_result.get("score", 0.0),
                "combined_score": original.combined_score,
                "confidence": original.detection_confidence
            },
            "variant_analysis": [],
            "vulnerabilities": [],
            "summary": {
                "vulnerability_rate": len(vulnerabilities) / len(variants) if variants else 0,
                "average_detection_drop": self._calculate_avg_detection_drop(original, variant_results),
                "most_effective_techniques": self._get_effective_techniques(variants, variant_results)
            }
        }
        
        # Add variant analysis
        for variant, result in zip(variants, variant_results):
            variant_analysis = {
                "variant_id": variant.variant_id,
                "variant_type": variant.variant_type,
                "modification_details": variant.modification_details,
                "detection_result": {
                    "sda_score": result.sda_result.get("score", 0.0),
                    "apb_score": result.apb_result.get("score", 0.0),
                    "combined_score": result.combined_score,
                    "confidence": result.detection_confidence
                },
                "detection_drop": original.combined_score - result.combined_score
            }
            report["variant_analysis"].append(variant_analysis)
        
        # Add vulnerability details
        for vuln in vulnerabilities:
            vuln_details = {
                "variant_id": vuln.variant_id,
                "original_detection": vuln.original_detection,
                "variant_detection": vuln.variant_detection,
                "vulnerability_score": vuln.vulnerability_score,
                "suggested_features": vuln.suggested_features,
                "variant_details": vuln.variant_details
            }
            report["vulnerabilities"].append(vuln_details)
        
        return report

    def _calculate_avg_detection_drop(self, original: DetectionResult, results: List[DetectionResult]) -> float:
        """Calculate average detection drop across variants."""
        if not results:
            return 0.0
        
        drops = [original.combined_score - result.combined_score for result in results]
        return sum(drops) / len(drops)

    def _get_effective_techniques(self, variants: List[EvasionVariant], results: List[DetectionResult]) -> List[str]:
        """Get most effective evasion techniques."""
        technique_drops = defaultdict(list)
        
        for variant, result in zip(variants, results):
            drop = result.combined_score  # Lower is better for evasion
            technique_drops[variant.variant_type].append(drop)
        
        # Calculate average effectiveness
        effectiveness = {}
        for technique, drops in technique_drops.items():
            effectiveness[technique] = sum(drops) / len(drops)
        
        # Sort by effectiveness (lower combined score = more effective)
        sorted_techniques = sorted(effectiveness.items(), key=lambda x: x[1])
        return [tech for tech, _ in sorted_techniques]

    async def _save_vulnerability_data(self, vulnerabilities: List[SignatureVulnerability]):
        """Save vulnerability data to database."""
        try:
            # Initialize vulnerability database table
            sql = """
                CREATE TABLE IF NOT EXISTS nexus_evasion_vulnerabilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sample_id TEXT NOT NULL,
                    variant_id TEXT NOT NULL,
                    original_detection REAL NOT NULL,
                    variant_detection REAL NOT NULL,
                    vulnerability_score REAL NOT NULL,
                    suggested_features TEXT,
                    variant_details TEXT,
                    detected_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            self.nexus.nexus.execute(sql)
            
            # Insert vulnerabilities
            for vuln in vulnerabilities:
                sql = """
                    INSERT INTO nexus_evasion_vulnerabilities 
                    (sample_id, variant_id, original_detection, variant_detection, vulnerability_score, 
                     suggested_features, variant_details)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                self.nexus.nexus.execute(sql, (
                    vuln.sample_id,
                    vuln.variant_id,
                    vuln.original_detection,
                    vuln.variant_detection,
                    vuln.vulnerability_score,
                    json.dumps(vuln.suggested_features),
                    json.dumps(vuln.variant_details)
                ))
            
            logger.info(f"[{self.plugin_id}] Saved {len(vulnerabilities)} vulnerabilities to database")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error saving vulnerability data: {e}")

    async def _get_vulnerability_statistics(self) -> Dict[str, Any]:
        """Get statistics about evasion vulnerabilities."""
        try:
            # Get total vulnerabilities
            total_sql = "SELECT COUNT(*) FROM nexus_evasion_vulnerabilities"
            total_count = self.nexus.nexus.execute(total_sql).fetchone()[0]
            
            # Get average vulnerability score
            avg_sql = "SELECT AVG(vulnerability_score) FROM nexus_evasion_vulnerabilities"
            avg_score = self.nexus.nexus.execute(avg_sql).fetchone()[0] or 0.0
            
            # Get most common vulnerability types
            # Note: This is simplified for SQLite compatibility
            type_data = self.nexus.nexus.execute(
                "SELECT variant_details, COUNT(*) FROM nexus_evasion_vulnerabilities GROUP BY variant_details"
            ).fetchall()
            
            stats = {
                "total_vulnerabilities": total_count,
                "average_vulnerability_score": round(avg_score, 3),
                "vulnerability_trends": "Data available in database",
                "detection_threshold": self.detection_threshold,
                "min_confidence_score": self.min_confidence_score
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error getting vulnerability statistics: {e}")
            return {"error": str(e)}

    async def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive evasion testing report."""
        try:
            # Get vulnerability statistics
            stats = await self._get_vulnerability_statistics()
            
            # Get recent vulnerabilities
            recent_sql = """
                SELECT sample_id, variant_id, original_detection, variant_detection, 
                       vulnerability_score, suggested_features, detected_at
                FROM nexus_evasion_vulnerabilities
                ORDER BY detected_at DESC
                LIMIT 10
            """
            recent_vulns = self.nexus.nexus.execute(recent_sql).fetchall()
            
            report = {
                "report_metadata": {
                    "report_type": "Adversarial Evasion Testing Report",
                    "generated_at": datetime.now().isoformat(),
                    "version": "1.0"
                },
                "vulnerability_statistics": stats,
                "recent_vulnerabilities": [
                    {
                        "sample_id": row[0],
                        "variant_id": row[1],
                        "original_detection": row[2],
                        "variant_detection": row[3],
                        "vulnerability_score": row[4],
                        "suggested_features": json.loads(row[5]) if row[5] else [],
                        "detected_at": row[6]
                    }
                    for row in recent_vulns
                ],
                "recommendations": [
                    "Review and implement suggested signature improvements",
                    "Monitor detection rates for known evasion techniques",
                    "Consider ensemble detection methods for improved robustness",
                    "Regularly update signature patterns based on vulnerability analysis"
                ]
            }
            
            return report
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error generating comprehensive report: {e}")
            return {"error": str(e)}

    async def _analyze_signature_improvements(self) -> Dict[str, Any]:
        """Analyze and suggest signature improvements."""
        try:
            # Get vulnerability data for analysis
            vuln_sql = """
                SELECT variant_details, suggested_features
                FROM nexus_evasion_vulnerabilities
            """
            vuln_data = self.nexus.nexus.execute(vuln_sql).fetchall()
            
            # Analyze patterns
            technique_counts = defaultdict(int)
            all_suggestions = []
            
            for row in vuln_data:
                if row[0]:
                    variant_details = json.loads(row[0])
                    technique = variant_details.get("technique", "unknown")
                    technique_counts[technique] += 1
                
                if row[1]:
                    suggestions = json.loads(row[1])
                    all_suggestions.extend(suggestions)
            
            # Generate signature improvement suggestions
            suggestion_counts = defaultdict(int)
            for suggestion in all_suggestions:
                suggestion_counts[suggestion] += 1
            
            # Sort by frequency
            sorted_suggestions = sorted(suggestion_counts.items(), key=lambda x: x[1], reverse=True)
            
            improvements = {
                "most_common_vulnerabilities": [
                    {"technique": tech, "count": count}
                    for tech, count in sorted(technique_counts.items())
                ],
                "top_signature_improvements": [
                    {"suggestion": suggestion, "frequency": count}
                    for suggestion, count in sorted_suggestions[:10]
                ],
                "signatures_json_recommendations": [
                    {
                        "feature": suggestion,
                        "implementation_priority": "HIGH" if count > 5 else "MEDIUM" if count > 2 else "LOW",
                        "description": f"Add detection for {suggestion.lower()}"
                    }
                    for suggestion, count in sorted_suggestions[:5]
                ]
            }
            
            return improvements
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error analyzing signature improvements: {e}")
            return {"error": str(e)}


# Import FingerprintRecord from Forensic Vault or define locally
@dataclass
class FingerprintRecord:
    """Represents a fingerprint record from the forensic ledger."""
    sample_id: str
    model_fingerprint: str
    combined_anomaly_score: float
    timestamp: datetime
    source_plugin: str
    is_recurring: bool
    recurring_with: Optional[str]
    metadata: Dict[str, Any]


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return an AdversarialTester instance."""
    return AdversarialTester(manifest, nexus_api)


def register_extension(manifest: Dict[str, Any], nexus_api: Any):
    """Standard Lawnmower Man v1.1.1 extension hook; required by ExtensionManager."""
    return create_plugin(manifest, nexus_api)