import os
import json
import logging
import asyncio
import time
import re
import random
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict, Counter

# Try to import required libraries with fallbacks
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("[Immunizer] numpy not available, some features may be limited")

from gateway.hardware_security import get_hsm
from gateway.nexus_db import get_nexus

logger = logging.getLogger("LawnmowerMan.Immunizer")

@dataclass
class VulnerabilityRecord:
    """Represents a vulnerability from the evasion test report."""
    sample_id: str
    variant_id: str
    original_detection: float
    variant_detection: float
    vulnerability_score: float
    suggested_features: List[str]
    variant_details: Dict[str, Any]
    variant_type: str
    modification_details: Dict[str, Any]

@dataclass
class HardenedRule:
    """Represents a hardened detection rule."""
    rule_id: str
    rule_type: str  # "regex" or "keyword_set"
    pattern: str
    description: str
    vulnerability_source: str
    confidence: float
    created_at: str
    baseline_compatibility: Dict[str, Any]

@dataclass
class BaselineTestResult:
    """Represents the result of testing against the human-only baseline."""
    rule_id: str
    false_positive_rate: float
    tested_samples: int
    flagged_samples: int
    flagged_texts: List[str]
    safety_status: str  # "SAFE", "WARNING", "UNSAFE"

class Immunizer:
    """
    Immunizer v1.0
    Immunizes the system against detected vulnerabilities by creating hardened detection rules.
    Reads evasion test reports, identifies high-impact vulnerabilities, and generates robust
    detection rules with safety checks against human-only baseline.
    """
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus = nexus_api  # SmeCoreBridge
        self.plugin_id = manifest.get("plugin_id")
        
        # Configuration
        self.high_impact_threshold = 0.30  # Vulnerability score threshold for high impact
        self.baseline_compatibility_threshold = 0.05  # Max 5% false positive rate allowed
        self.min_confidence_score = 0.70  # Minimum confidence for generated rules
        
        # Output directory
        self.data_dir = os.path.join("D:", "SME", "data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Baseline data
        self.human_baseline_texts = []
        self.load_human_baseline()
        
        # Rule generation patterns
        self.rule_patterns = {
            "character_substitution": self._generate_char_substitution_rules,
            "word_obfuscation": self._generate_word_obfuscation_rules,
            "structural_rewriting": self._generate_structural_rules,
            "semantic_preservation": self._generate_semantic_rules,
            "formatting_manipulation": self._generate_formatting_rules
        }
        
        logger.info(f"[{self.plugin_id}] Immunizer initialized with high-impact threshold {self.high_impact_threshold}")

    async def on_startup(self):
        """
        Initialize the Immunizer.
        """
        try:
            logger.info(f"[{self.plugin_id}] Immunizer started successfully")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to start Immunizer: {e}")

    async def on_shutdown(self):
        """
        Clean shutdown of the Immunizer.
        """
        try:
            logger.info(f"[{self.plugin_id}] Immunizer shutdown complete")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error during shutdown: {e}")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Immunizer does not process on_ingestion directly.
        It provides tools for signature hardening and rule generation.
        """
        return {
            "status": "skipped",
            "reason": "Immunizer provides hardening tools, not direct ingestion processing"
        }

    def get_tools(self) -> list:
        return [
            self.run_signature_patch,
            self.get_hardening_statistics,
            self.test_rule_safety,
            self.generate_hardening_report
        ]

    async def run_signature_patch(self, report_path: str = None) -> str:
        """
        Run the signature patch process.
        
        Reads the evasion test report, identifies high-impact vulnerabilities,
        generates hardened detection rules using rnj-1 techniques, performs
        safety checks against human baseline, and appends to hardened_signatures.json.
        """
        try:
            # Determine report path
            if not report_path:
                report_path = os.path.join("D:", "SME", "reports", "evasion_test_report.json")
            
            if not os.path.exists(report_path):
                return json.dumps({
                    "error": f"Evasion test report not found at {report_path}"
                })
            
            logger.info(f"[{self.plugin_id}] Reading evasion test report: {report_path}")
            
            # Load and analyze report
            report_data = await self._load_evasion_report(report_path)
            high_impact_vulnerabilities = self._identify_high_impact_vulnerabilities(report_data)
            
            if not high_impact_vulnerabilities:
                return json.dumps({
                    "status": "no_high_impact_vulnerabilities",
                    "message": "No high-impact vulnerabilities found requiring hardening"
                })
            
            logger.info(f"[{self.plugin_id}] Found {len(high_impact_vulnerabilities)} high-impact vulnerabilities")
            
            # Generate hardened rules
            hardened_rules = []
            for vuln in high_impact_vulnerabilities:
                rules = self._generate_hardened_rules(vuln)
                hardened_rules.extend(rules)
            
            # Test safety against baseline
            safe_rules = []
            for rule in hardened_rules:
                safety_result = await self._test_rule_safety(rule)
                if safety_result.safety_status == "SAFE":
                    safe_rules.append(rule)
                else:
                    logger.warning(f"[{self.plugin_id}] Rule {rule.rule_id} failed safety check: {safety_result.safety_status}")
            
            # Save hardened rules
            hardened_file = os.path.join(self.data_dir, "hardened_signatures.json")
            await self._save_hardened_rules(safe_rules, hardened_file)
            
            # Generate summary report
            summary = {
                "status": "success",
                "report_path": report_path,
                "high_impact_vulnerabilities": len(high_impact_vulnerabilities),
                "generated_rules": len(hardened_rules),
                "safe_rules": len(safe_rules),
                "hardened_file": hardened_file,
                "vulnerability_types": self._get_vulnerability_type_summary(high_impact_vulnerabilities),
                "rule_types": self._get_rule_type_summary(safe_rules)
            }
            
            logger.info(f"[{self.plugin_id}] Signature patch completed: {len(safe_rules)} safe rules added")
            return json.dumps(summary, indent=2)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error running signature patch: {e}")
            return json.dumps({
                "error": f"Failed to run signature patch: {str(e)}"
            })

    async def get_hardening_statistics(self) -> str:
        """Get statistics about the hardening process."""
        try:
            hardened_file = os.path.join(self.data_dir, "hardened_signatures.json")
            if not os.path.exists(hardened_file):
                return json.dumps({"error": "No hardened signatures file found"})
            
            with open(hardened_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            stats = {
                "total_rules": len(rules),
                "rule_types": Counter(rule.get("rule_type", "unknown") for rule in rules),
                "average_confidence": sum(rule.get("confidence", 0) for rule in rules) / len(rules) if rules else 0,
                "vulnerability_sources": Counter(rule.get("vulnerability_source", "unknown") for rule in rules),
                "baseline_compatibility": {
                    "safe_rules": sum(1 for rule in rules if rule.get("baseline_compatibility", {}).get("safety_status") == "SAFE"),
                    "warning_rules": sum(1 for rule in rules if rule.get("baseline_compatibility", {}).get("safety_status") == "WARNING"),
                    "unsafe_rules": sum(1 for rule in rules if rule.get("baseline_compatibility", {}).get("safety_status") == "UNSAFE")
                }
            }
            
            return json.dumps(stats, indent=2)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error getting hardening statistics: {e}")
            return json.dumps({"error": f"Failed to get hardening statistics: {str(e)}"})

    async def test_rule_safety(self, rule_id: str = None) -> str:
        """Test the safety of specific rules against the human baseline."""
        try:
            hardened_file = os.path.join(self.data_dir, "hardened_signatures.json")
            if not os.path.exists(hardened_file):
                return json.dumps({"error": "No hardened signatures file found"})
            
            with open(hardened_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            if rule_id:
                # Test specific rule
                rule = next((r for r in rules if r.get("rule_id") == rule_id), None)
                if not rule:
                    return json.dumps({"error": f"Rule {rule_id} not found"})
                
                test_result = await self._test_rule_safety(HardenedRule(**rule))
                return json.dumps({
                    "rule_id": rule_id,
                    "safety_result": {
                        "false_positive_rate": test_result.false_positive_rate,
                        "tested_samples": test_result.tested_samples,
                        "flagged_samples": test_result.flagged_samples,
                        "safety_status": test_result.safety_status
                    }
                }, indent=2)
            else:
                # Test all rules
                safety_results = []
                for rule in rules:
                    test_result = await self._test_rule_safety(HardenedRule(**rule))
                    safety_results.append({
                        "rule_id": rule.get("rule_id"),
                        "false_positive_rate": test_result.false_positive_rate,
                        "safety_status": test_result.safety_status
                    })
                
                return json.dumps({
                    "total_rules": len(safety_results),
                    "safety_summary": {
                        "safe": sum(1 for r in safety_results if r["safety_status"] == "SAFE"),
                        "warning": sum(1 for r in safety_results if r["safety_status"] == "WARNING"),
                        "unsafe": sum(1 for r in safety_results if r["safety_status"] == "UNSAFE")
                    },
                    "detailed_results": safety_results
                }, indent=2)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error testing rule safety: {e}")
            return json.dumps({"error": f"Failed to test rule safety: {str(e)}"})

    async def generate_hardening_report(self) -> str:
        """Generate a comprehensive hardening report."""
        try:
            hardened_file = os.path.join(self.data_dir, "hardened_signatures.json")
            if not os.path.exists(hardened_file):
                return json.dumps({"error": "No hardened signatures file found"})
            
            with open(hardened_file, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            
            # Generate comprehensive report
            report = {
                "report_metadata": {
                    "report_type": "Signature Hardening Report",
                    "generated_at": datetime.now().isoformat(),
                    "version": "1.0",
                    "baseline_samples": len(self.human_baseline_texts)
                },
                "hardening_summary": {
                    "total_rules": len(rules),
                    "rule_types": Counter(rule.get("rule_type", "unknown") for rule in rules),
                    "average_confidence": sum(rule.get("confidence", 0) for rule in rules) / len(rules) if rules else 0,
                    "vulnerability_coverage": len(set(rule.get("vulnerability_source", "") for rule in rules))
                },
                "safety_analysis": {
                    "baseline_compatibility": {
                        "safe_rules": sum(1 for rule in rules if rule.get("baseline_compatibility", {}).get("safety_status") == "SAFE"),
                        "warning_rules": sum(1 for rule in rules if rule.get("baseline_compatibility", {}).get("safety_status") == "WARNING"),
                        "unsafe_rules": sum(1 for rule in rules if rule.get("baseline_compatibility", {}).get("safety_status") == "UNSAFE")
                    },
                    "false_positive_analysis": {
                        "average_fpr": sum(rule.get("baseline_compatibility", {}).get("false_positive_rate", 0) for rule in rules) / len(rules) if rules else 0,
                        "max_fpr": max((rule.get("baseline_compatibility", {}).get("false_positive_rate", 0) for rule in rules), default=0)
                    }
                },
                "rule_details": [
                    {
                        "rule_id": rule.get("rule_id"),
                        "rule_type": rule.get("rule_type"),
                        "pattern": rule.get("pattern"),
                        "description": rule.get("description"),
                        "confidence": rule.get("confidence"),
                        "vulnerability_source": rule.get("vulnerability_source"),
                        "safety_status": rule.get("baseline_compatibility", {}).get("safety_status", "UNKNOWN")
                    }
                    for rule in rules
                ],
                "recommendations": self._generate_hardening_recommendations(rules)
            }
            
            return json.dumps(report, indent=2)
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error generating hardening report: {e}")
            return json.dumps({"error": f"Failed to generate hardening report: {str(e)}"})

    def load_human_baseline(self):
        """Load the human-only baseline texts for safety testing."""
        try:
            # Try to load from existing baseline file
            baseline_file = os.path.join(self.data_dir, "human_baseline.json")
            if os.path.exists(baseline_file):
                with open(baseline_file, 'r', encoding='utf-8') as f:
                    self.human_baseline_texts = json.load(f)
                logger.info(f"[{self.plugin_id}] Loaded {len(self.human_baseline_texts)} baseline samples")
            else:
                # Create default baseline if file doesn't exist
                self._create_default_baseline()
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error loading human baseline: {e}")
            self._create_default_baseline()

    def _create_default_baseline(self):
        """Create a default human baseline for testing."""
        self.human_baseline_texts = [
            "This is a normal human-written text sample for testing purposes.",
            "I am writing this text to demonstrate typical human language patterns.",
            "The quick brown fox jumps over the lazy dog in the garden.",
            "Please find below the details of our scheduled meeting for tomorrow.",
            "Thank you for your time and consideration in this matter.",
            "Based on the analysis, we can conclude that the results are promising.",
            "The implementation of this feature will require additional resources.",
            "We should proceed with caution when making these changes.",
            "This document contains important information for all team members.",
            "Please review the attached files and provide your feedback.",
            "The project timeline has been adjusted to accommodate new requirements.",
            "Our team is committed to delivering high-quality solutions.",
            "Customer satisfaction is our top priority in all interactions.",
            "The system will undergo maintenance during the weekend hours.",
            "Please ensure all deadlines are met according to the project schedule."
        ]
        
        # Save baseline for future use
        baseline_file = os.path.join(self.data_dir, "human_baseline.json")
        with open(baseline_file, 'w', encoding='utf-8') as f:
            json.dump(self.human_baseline_texts, f, indent=2)
        
        logger.info(f"[{self.plugin_id}] Created default baseline with {len(self.human_baseline_texts)} samples")

    async def _load_evasion_report(self, report_path: str) -> Dict[str, Any]:
        """Load the evasion test report."""
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _identify_high_impact_vulnerabilities(self, report_data: Dict[str, Any]) -> List[VulnerabilityRecord]:
        """Identify high-impact vulnerabilities from the report."""
        vulnerabilities = []
        
        # Extract vulnerabilities from report
        if "vulnerabilities" in report_data:
            for vuln_data in report_data["vulnerabilities"]:
                vulnerability = VulnerabilityRecord(
                    sample_id=vuln_data.get("sample_id", ""),
                    variant_id=vuln_data.get("variant_id", ""),
                    original_detection=vuln_data.get("original_detection", 0.0),
                    variant_detection=vuln_data.get("variant_detection", 0.0),
                    vulnerability_score=vuln_data.get("vulnerability_score", 0.0),
                    suggested_features=vuln_data.get("suggested_features", []),
                    variant_details=vuln_data.get("variant_details", {}),
                    variant_type=vuln_data.get("variant_details", {}).get("technique", "unknown"),
                    modification_details=vuln_data.get("variant_details", {})
                )
                
                # Check if it's high impact
                if vulnerability.vulnerability_score >= self.high_impact_threshold:
                    vulnerabilities.append(vulnerability)
        
        return vulnerabilities

    def _generate_hardened_rules(self, vulnerability: VulnerabilityRecord) -> List[HardenedRule]:
        """Generate hardened detection rules for a vulnerability."""
        rules = []
        
        # Get the appropriate rule generation function
        rule_generator = self.rule_patterns.get(vulnerability.variant_type)
        if rule_generator:
            rules = rule_generator(vulnerability)
        else:
            # Default rule generation for unknown types
            rules = self._generate_generic_rules(vulnerability)
        
        return rules

    def _generate_char_substitution_rules(self, vulnerability: VulnerabilityRecord) -> List[HardenedRule]:
        """Generate rules for character substitution vulnerabilities."""
        rules = []
        
        # Analyze character substitutions in the vulnerability
        changes = vulnerability.modification_details.get("changes", [])
        
        # Generate regex patterns for common homoglyph attacks
        homoglyph_patterns = [
            r'[a@4α]',  # a variants
            r'[e3€є]',  # e variants
            r'[i1!ι]',  # i variants
            r'[o0°ο]',  # o variants
            r'[s5$ѕ]',  # s variants
            r'[t7+τ]',  # t variants
            r'[l1|£]',  # l variants
            r'[c(<¢]',  # c variants
            r'[b68β]',  # b variants
            r'[g969]'   # g variants
        ]
        
        # Create rules for suspicious character combinations
        for i, pattern in enumerate(homoglyph_patterns):
            rule = HardenedRule(
                rule_id=f"char_sub_{vulnerability.variant_id}_{i+1}",
                rule_type="regex",
                pattern=f"({pattern}){{2,}}",  # Multiple suspicious characters
                description=f"Detects multiple character substitutions ({pattern})",
                vulnerability_source=vulnerability.variant_id,
                confidence=0.8,
                created_at=datetime.now().isoformat(),
                baseline_compatibility={}
            )
            rules.append(rule)
        
        # Create keyword set for common substitution patterns
        keyword_set = {
            "keywords": ["@lph@", "3m@il", "p@ssw0rd", "l0g1n", "s3cur1ty"],
            "description": "Common character substitution patterns in sensitive terms"
        }
        
        rule = HardenedRule(
            rule_id=f"keyword_sub_{vulnerability.variant_id}",
            rule_type="keyword_set",
            pattern=json.dumps(keyword_set),
            description="Detects common character substitution patterns in sensitive terms",
            vulnerability_source=vulnerability.variant_id,
            confidence=0.75,
            created_at=datetime.now().isoformat(),
            baseline_compatibility={}
        )
        rules.append(rule)
        
        return rules

    def _generate_word_obfuscation_rules(self, vulnerability: VulnerabilityRecord) -> List[HardenedRule]:
        """Generate rules for word obfuscation vulnerabilities."""
        rules = []
        
        # Generate regex patterns for word boundary attacks
        word_patterns = [
            r'\b\w{1,2}\w+\w{1,2}\b',  # Suspicious word lengths
            r'\b\w*[0-9]\w*\b',        # Words with numbers
            r'\b\w*[!@#$%^&*()]\w*\b', # Words with special characters
            r'\b\w{2,}\s*\w{2,}\b'     # Suspicious spacing in words
        ]
        
        for i, pattern in enumerate(word_patterns):
            rule = HardenedRule(
                rule_id=f"word_obs_{vulnerability.variant_id}_{i+1}",
                rule_type="regex",
                pattern=pattern,
                description=f"Detects word obfuscation patterns ({pattern})",
                vulnerability_source=vulnerability.variant_id,
                confidence=0.7,
                created_at=datetime.now().isoformat(),
                baseline_compatibility={}
            )
            rules.append(rule)
        
        return rules

    def _generate_structural_rules(self, vulnerability: VulnerabilityRecord) -> List[HardenedRule]:
        """Generate rules for structural rewriting vulnerabilities."""
        rules = []
        
        # Generate patterns for structural manipulation
        structural_patterns = [
            r'\s{2,}',                    # Multiple spaces
            r'[A-Z][a-z]*\s+[A-Z]',     # Suspicious capitalization patterns
            r'\b\w+\s+\w+\s+\w+\b',     # Suspicious word spacing
            r'[^\w\s]{3,}'              # Multiple non-word characters
        ]
        
        for i, pattern in enumerate(structural_patterns):
            rule = HardenedRule(
                rule_id=f"struct_{vulnerability.variant_id}_{i+1}",
                rule_type="regex",
                pattern=pattern,
                description=f"Detects structural manipulation ({pattern})",
                vulnerability_source=vulnerability.variant_id,
                confidence=0.65,
                created_at=datetime.now().isoformat(),
                baseline_compatibility={}
            )
            rules.append(rule)
        
        return rules

    def _generate_semantic_rules(self, vulnerability: VulnerabilityRecord) -> List[HardenedRule]:
        """Generate rules for semantic preservation vulnerabilities."""
        rules = []
        
        # Generate patterns for synonym-based attacks
        semantic_patterns = [
            r'\b(?:trial|experiment|assessment)\b',  # Test synonyms
            r'\b(?:example|specimen|instance)\b',    # Sample synonyms
            r'\b(?:identification|recognition|discovery)\b',  # Detection synonyms
            r'\b(?:irregularity|abnormality|deviation)\b'      # Anomaly synonyms
        ]
        
        for i, pattern in enumerate(semantic_patterns):
            rule = HardenedRule(
                rule_id=f"semantic_{vulnerability.variant_id}_{i+1}",
                rule_type="regex",
                pattern=pattern,
                description=f"Detects semantic preservation attempts ({pattern})",
                vulnerability_source=vulnerability.variant_id,
                confidence=0.6,
                created_at=datetime.now().isoformat(),
                baseline_compatibility={}
            )
            rules.append(rule)
        
        return rules

    def _generate_formatting_rules(self, vulnerability: VulnerabilityRecord) -> List[HardenedRule]:
        """Generate rules for formatting manipulation vulnerabilities."""
        rules = []
        
        # Generate patterns for Unicode and invisible character attacks
        formatting_patterns = [
            r'[\u0430-\u044F]',          # Cyrillic characters
            r'[\u200B-\u200D]',         # Zero-width characters
            r'[\uFEFF]',                # Byte order mark
            r'[\u202A-\u202E]',         # Directional formatting
            r'[^\x00-\x7F]'             # Non-ASCII characters
        ]
        
        for i, pattern in enumerate(formatting_patterns):
            rule = HardenedRule(
                rule_id=f"format_{vulnerability.variant_id}_{i+1}",
                rule_type="regex",
                pattern=pattern,
                description=f"Detects formatting manipulation ({pattern})",
                vulnerability_source=vulnerability.variant_id,
                confidence=0.85,
                created_at=datetime.now().isoformat(),
                baseline_compatibility={}
            )
            rules.append(rule)
        
        return rules

    def _generate_generic_rules(self, vulnerability: VulnerabilityRecord) -> List[HardenedRule]:
        """Generate generic rules for unknown vulnerability types."""
        rules = []
        
        # Generic suspicious pattern detection
        generic_patterns = [
            r'[^\w\s]{4,}',             # Multiple special characters
            r'\b\w{10,}\b',            # Very long words
            r'\s{3,}',                  # Multiple spaces
            r'[A-Z]{3,}'                # Multiple consecutive capitals
        ]
        
        for i, pattern in enumerate(generic_patterns):
            rule = HardenedRule(
                rule_id=f"generic_{vulnerability.variant_id}_{i+1}",
                rule_type="regex",
                pattern=pattern,
                description=f"Generic suspicious pattern detection ({pattern})",
                vulnerability_source=vulnerability.variant_id,
                confidence=0.5,
                created_at=datetime.now().isoformat(),
                baseline_compatibility={}
            )
            rules.append(rule)
        
        return rules

    async def _test_rule_safety(self, rule: HardenedRule) -> BaselineTestResult:
        """Test a rule against the human baseline for safety."""
        try:
            flagged_samples = 0
            flagged_texts = []
            
            # Test the rule against each baseline sample
            for text in self.human_baseline_texts:
                if self._rule_matches(rule, text):
                    flagged_samples += 1
                    flagged_texts.append(text[:100])  # Store first 100 chars
            
            false_positive_rate = flagged_samples / len(self.human_baseline_texts) if self.human_baseline_texts else 0
            
            # Determine safety status
            if false_positive_rate <= self.baseline_compatibility_threshold:
                safety_status = "SAFE"
            elif false_positive_rate <= self.baseline_compatibility_threshold * 2:
                safety_status = "WARNING"
            else:
                safety_status = "UNSAFE"
            
            return BaselineTestResult(
                rule_id=rule.rule_id,
                false_positive_rate=false_positive_rate,
                tested_samples=len(self.human_baseline_texts),
                flagged_samples=flagged_samples,
                flagged_texts=flagged_texts,
                safety_status=safety_status
            )
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error testing rule safety: {e}")
            return BaselineTestResult(
                rule_id=rule.rule_id,
                false_positive_rate=1.0,
                tested_samples=0,
                flagged_samples=0,
                flagged_texts=[],
                safety_status="ERROR"
            )

    def _rule_matches(self, rule: HardenedRule, text: str) -> bool:
        """Check if a rule matches the given text."""
        try:
            if rule.rule_type == "regex":
                return bool(re.search(rule.pattern, text, re.IGNORECASE))
            elif rule.rule_type == "keyword_set":
                keyword_data = json.loads(rule.pattern)
                keywords = keyword_data.get("keywords", [])
                return any(keyword.lower() in text.lower() for keyword in keywords)
            else:
                return False
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error matching rule: {e}")
            return False

    async def _save_hardened_rules(self, rules: List[HardenedRule], output_file: str):
        """Save hardened rules to the output file."""
        try:
            # Load existing rules if file exists
            existing_rules = []
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_rules = json.load(f)
            
            # Convert HardenedRule objects to dictionaries
            new_rule_dicts = []
            for rule in rules:
                rule_dict = {
                    "rule_id": rule.rule_id,
                    "rule_type": rule.rule_type,
                    "pattern": rule.pattern,
                    "description": rule.description,
                    "vulnerability_source": rule.vulnerability_source,
                    "confidence": rule.confidence,
                    "created_at": rule.created_at,
                    "baseline_compatibility": rule.baseline_compatibility
                }
                new_rule_dicts.append(rule_dict)
            
            # Combine existing and new rules
            all_rules = existing_rules + new_rule_dicts
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_rules, f, indent=2)
            
            logger.info(f"[{self.plugin_id}] Saved {len(rules)} hardened rules to {output_file}")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Error saving hardened rules: {e}")
            raise

    def _get_vulnerability_type_summary(self, vulnerabilities: List[VulnerabilityRecord]) -> Dict[str, int]:
        """Get summary of vulnerability types."""
        type_counts = Counter(v.variant_type for v in vulnerabilities)
        return dict(type_counts)

    def _get_rule_type_summary(self, rules: List[HardenedRule]) -> Dict[str, int]:
        """Get summary of rule types."""
        type_counts = Counter(rule.rule_type for rule in rules)
        return dict(type_counts)

    def _generate_hardening_recommendations(self, rules: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on the hardening results."""
        recommendations = []
        
        # Analyze rule distribution
        rule_types = Counter(rule.get("rule_type", "unknown") for rule in rules)
        
        if rule_types.get("regex", 0) > rule_types.get("keyword_set", 0):
            recommendations.append("Consider adding more keyword-based detection rules for better coverage")
        
        # Analyze safety status
        unsafe_rules = sum(1 for rule in rules if rule.get("baseline_compatibility", {}).get("safety_status") == "UNSAFE")
        if unsafe_rules > 0:
            recommendations.append(f"Review {unsafe_rules} unsafe rules that may cause false positives")
        
        # General recommendations
        recommendations.extend([
            "Regularly update the human baseline with new samples",
            "Monitor rule effectiveness in production",
            "Consider ensemble approaches combining multiple rule types",
            "Review and refine rules based on real-world performance"
        ])
        
        return recommendations


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return an Immunizer instance."""
    return Immunizer(manifest, nexus_api)