import os
import json
import logging
import re
import math
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from collections import defaultdict

from gateway.hardware_security import get_hsm
from gateway.nexus_db import get_nexus

logger = logging.getLogger("LawnmowerMan.LogicAuditor")

class LogicAuditor:
    """
    Logic Auditor v1.0
    Detects logical inconsistencies and hallucinations through round-robin claim contradiction analysis.
    Flags "Logic Hallucinations" when contradictions are found with >90% confidence.
    """
    
    def __init__(self, manifest: Dict[str, Any], nexus_api: Any):
        self.manifest = manifest
        self.nexus = nexus_api  # SmeCoreBridge
        self.plugin_id = manifest.get("plugin_id")
        
        # Claim extraction patterns
        self.claim_patterns = [
            r'\b(assert|claim|state|declare|affirm|maintain|argue|suggest|indicate|demonstrate)\b.*?that\b',
            r'\b(according to|based on|in light of|given that|since|because|therefore|thus|consequently)\b',
            r'\b(is|are|was|were|will be|has been|have been)\b.*?\.',
            r'\b(must|should|could|would|can|may|might)\b.*?\.',
        ]
        
        # Contradiction indicators
        self.contradiction_indicators = [
            r'\b(contradict|conflict|inconsistent|opposite|different|disagree|deny|refute)\b',
            r'\b(but|however|nevertheless|nonetheless|yet|although|though|while)\b',
            r'\b(not|no|never|none|neither|nor)\b',
            r'\b(only|just|solely|exclusively|specifically)\b',
        ]

    async def on_startup(self):
        """
        Initialize the 'nexus_logic_hallucinations' table in the core DB.
        """
        sql = """
            CREATE TABLE IF NOT EXISTS nexus_logic_hallucinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT NOT NULL,
                text_sample TEXT NOT NULL,
                hallucination_detected BOOLEAN NOT NULL,
                contradiction_confidence REAL NOT NULL,
                contradiction_details TEXT NOT NULL,
                claims_analyzed INTEGER NOT NULL,
                timestamp TEXT,
                source_id TEXT
            )
        """
        try:
            self.nexus.nexus.execute(sql)
            logger.info(f"[{self.plugin_id}] 'nexus_logic_hallucinations' table initialized.")
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to init DB table: {e}")

    async def on_ingestion(self, raw_data: str, metadata: Dict[str, Any]):
        """
        Logic Auditor analysis for on_ingestion pipeline.
        Performs round-robin claim contradiction analysis and flags Logic Hallucinations.
        """
        if not raw_data or len(raw_data) < 100:  # Minimum length for analysis
            return {"status": "skipped", "reason": "too_short"}

        # Perform logical consistency audit
        audit_result = self.audit_logical_consistency(raw_data)
        
        # Extract key results
        hallucination_detected = audit_result.get("hallucination_detected", False)
        contradiction_confidence = audit_result.get("contradiction_confidence", 0.0)
        contradiction_details = audit_result.get("contradiction_details", [])
        
        # Log significant findings
        if hallucination_detected:
            logger.warning(f"[{self.plugin_id}] LOGIC HALLUCINATION DETECTED - "
                          f"Confidence: {contradiction_confidence:.2%}")
            for detail in contradiction_details:
                logger.warning(f"[{self.plugin_id}] Contradiction: {detail['claim_a']} vs {detail['claim_b']}")
        
        # Store result in database if significant
        if hallucination_detected:
            await self._store_logic_hallucination(
                raw_data, 
                audit_result,
                metadata.get("source_id", "INGESTION_PIPELINE")
            )
        
        # Return analysis results
        return {
            "status": "analyzed",
            "logical_consistency": {
                "hallucination_detected": hallucination_detected,
                "contradiction_confidence": contradiction_confidence,
                "claims_analyzed": audit_result.get("claims_analyzed", 0),
                "contradiction_details": contradiction_details
            }
        }

    def get_tools(self) -> list:
        return [self.audit_logical_consistency_tool, self.get_logic_statistics, self.analyze_claim_consistency]

    async def audit_logical_consistency_tool(self, text: str) -> str:
        """
        Tool to audit logical consistency of text and detect hallucinations.
        """
        try:
            result = self.audit_logical_consistency(text)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Logical consistency audit failed: {str(e)}"})

    async def get_logic_statistics(self) -> str:
        """
        Get statistics on detected logic hallucinations from the database.
        """
        try:
            # Count total hallucinations detected
            sql_count = "SELECT COUNT(*) as total_hallucinations FROM nexus_logic_hallucinations"
            count_result = self.nexus.nexus.query(sql_count)
            total_hallucinations = count_result[0]["total_hallucinations"] if count_result else 0
            
            # Count high confidence hallucinations
            sql_high_confidence = "SELECT COUNT(*) as high_confidence FROM nexus_logic_hallucinations WHERE contradiction_confidence >= 0.9"
            high_confidence_result = self.nexus.nexus.query(sql_high_confidence)
            high_confidence_count = high_confidence_result[0]["high_confidence"] if high_confidence_result else 0
            
            # Get recent hallucinations
            sql_recent = """
                SELECT text_hash, contradiction_confidence, claims_analyzed, timestamp 
                FROM nexus_logic_hallucinations 
                ORDER BY timestamp DESC 
                LIMIT 10
            """
            recent_hallucinations = self.nexus.nexus.query(sql_recent)
            
            stats = {
                "total_hallucinations_detected": total_hallucinations,
                "high_confidence_hallucinations": high_confidence_count,
                "hallucination_rate": round((high_confidence_count / total_hallucinations * 100) if total_hallucinations > 0 else 0, 2),
                "recent_hallucinations": [
                    {
                        "hash": hallucination["text_hash"][:8] + "...",
                        "confidence": hallucination["contradiction_confidence"],
                        "claims_analyzed": hallucination["claims_analyzed"],
                        "timestamp": hallucination["timestamp"]
                    }
                    for hallucination in recent_hallucinations
                ]
            }
            
            return json.dumps(stats, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Failed to get logic statistics: {str(e)}"})

    async def analyze_claim_consistency(self, text: str) -> str:
        """
        Analyze individual claims for consistency and return detailed breakdown.
        """
        try:
            claims = self._extract_claims(text)
            
            analysis = {
                "total_claims": len(claims),
                "claims": [],
                "contradiction_pairs": [],
                "consistency_score": 0.0
            }
            
            # Analyze each claim
            for i, claim in enumerate(claims):
                claim_analysis = {
                    "claim_id": i + 1,
                    "text": claim,
                    "contradiction_indicators": self._check_contradiction_indicators(claim),
                    "logical_structure": self._analyze_logical_structure(claim)
                }
                analysis["claims"].append(claim_analysis)
            
            # Perform round-robin comparison
            contradiction_pairs = self._perform_round_robin_comparison(claims)
            analysis["contradiction_pairs"] = contradiction_pairs
            
            # Calculate consistency score
            if len(claims) > 1:
                total_comparisons = len(claims) * (len(claims) - 1) // 2
                consistency_score = 1.0 - (len(contradiction_pairs) / total_comparisons)
                analysis["consistency_score"] = round(consistency_score, 4)
            
            return json.dumps(analysis, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Claim consistency analysis failed: {str(e)}"})

    def audit_logical_consistency(self, text: str) -> Dict[str, Any]:
        """
        Main method to audit logical consistency and detect hallucinations.
        
        Returns comprehensive analysis with hallucination detection and confidence.
        """
        if not text or len(text) < 100:  # Minimum text length for analysis
            return {
                "hallucination_detected": False,
                "contradiction_confidence": 0.0,
                "reason": "Text too short for analysis",
                "claims_analyzed": 0,
                "contradiction_details": []
            }
        
        # Extract claims from text
        claims = self._extract_claims(text)
        
        if len(claims) < 2:
            return {
                "hallucination_detected": False,
                "contradiction_confidence": 0.0,
                "reason": "Insufficient claims for analysis",
                "claims_analyzed": len(claims),
                "contradiction_details": []
            }
        
        # Perform round-robin comparison
        contradiction_pairs = self._perform_round_robin_comparison(claims)
        
        # Calculate contradiction confidence
        contradiction_confidence = self._calculate_contradiction_confidence(contradiction_pairs, len(claims))
        
        # Determine if hallucination is detected
        hallucination_detected = contradiction_confidence >= 0.45  # Even lower threshold for better detection
        
        return {
            "hallucination_detected": hallucination_detected,
            "contradiction_confidence": round(contradiction_confidence, 4),
            "claims_analyzed": len(claims),
            "contradiction_details": contradiction_pairs
        }

    def _extract_claims(self, text: str) -> List[str]:
        """
        Extract key claims from text using pattern matching and sentence analysis.
        """
        # Split into sentences
        sentences = self._split_into_sentences(text)
        
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check if sentence contains claim indicators
            if self._is_claim_sentence(sentence):
                claims.append(sentence)
            # Also include sentences that seem substantive
            elif self._is_substantive_sentence(sentence):
                claims.append(sentence)
            # Include all sentences that have substantive content
            elif len(sentence.split()) >= 4:  # At least 4 words
                claims.append(sentence)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_claims = []
        for claim in claims:
            normalized = claim.lower().strip(' .')
            if normalized not in seen:
                seen.add(normalized)
                unique_claims.append(claim)
        
        return unique_claims

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # More sophisticated sentence splitting
        sentence_endings = re.compile(r'[.!?]+')
        sentences = sentence_endings.split(text)
        
        # Clean up sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences

    def _is_claim_sentence(self, sentence: str) -> bool:
        """Check if sentence contains claim indicators."""
        sentence_lower = sentence.lower()
        
        # Check for claim patterns
        for pattern in self.claim_patterns:
            if re.search(pattern, sentence_lower):
                return True
        
        # Check for substantive content
        words = sentence.split()
        if len(words) < 3:
            return False
            
        # Check for contradiction indicators (these often signal claims)
        for pattern in self.contradiction_indicators:
            if re.search(pattern, sentence_lower):
                return True
        
        return False

    def _is_substantive_sentence(self, sentence: str) -> bool:
        """Check if sentence contains substantive content worth analyzing."""
        # Remove common filler phrases
        filler_phrases = [
            r'\b(the|a|an|this|that|these|those)\s+',
            r'\b(is|are|was|were|be|been|being)\s+',
            r'\b(of|in|on|at|by|for|with|to|from)\s+',
        ]
        
        cleaned = sentence.lower()
        for pattern in filler_phrases:
            cleaned = re.sub(pattern, ' ', cleaned)
        
        # Check if there's meaningful content left
        meaningful_words = [word for word in cleaned.split() if len(word) > 2]
        
        return len(meaningful_words) >= 2

    def _perform_round_robin_comparison(self, claims: List[str]) -> List[Dict[str, Any]]:
        """
        Perform round-robin comparison of all claims to detect contradictions.
        """
        contradiction_pairs = []
        
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                claim_a = claims[i]
                claim_b = claims[j]
                
                # Analyze for contradiction
                contradiction_result = self._analyze_contradiction(claim_a, claim_b)
                
                if contradiction_result["is_contradiction"]:
                    contradiction_pairs.append({
                        "claim_a": claim_a,
                        "claim_b": claim_b,
                        "contradiction_type": contradiction_result["contradiction_type"],
                        "confidence": contradiction_result["confidence"],
                        "evidence": contradiction_result["evidence"]
                    })
        
        return contradiction_pairs

    def _analyze_contradiction(self, claim_a: str, claim_b: str) -> Dict[str, Any]:
        """
        Analyze two claims for contradiction.
        """
        # Normalize claims
        claim_a_lower = claim_a.lower().strip(' .')
        claim_b_lower = claim_b.lower().strip(' .')
        
        # Check for direct negation
        if self._check_direct_negation(claim_a_lower, claim_b_lower):
            return {
                "is_contradiction": True,
                "contradiction_type": "direct_negation",
                "confidence": 0.95,
                "evidence": "Direct negation detected"
            }
        
        # Check for opposite terms
        opposite_score = self._check_opposite_terms(claim_a_lower, claim_b_lower)
        if opposite_score > 0.3:  # Lowered threshold
            return {
                "is_contradiction": True,
                "contradiction_type": "opposite_terms",
                "confidence": opposite_score,
                "evidence": f"Opposite terms detected (score: {opposite_score:.2f})"
            }
        
        # Check for exclusive terms
        if self._check_exclusive_terms(claim_a_lower, claim_b_lower):
            return {
                "is_contradiction": True,
                "contradiction_type": "exclusive_terms",
                "confidence": 0.85,
                "evidence": "Exclusive terms detected"
            }
        
        # Check for temporal contradictions
        if self._check_temporal_contradiction(claim_a_lower, claim_b_lower):
            return {
                "is_contradiction": True,
                "contradiction_type": "temporal",
                "confidence": 0.80,
                "evidence": "Temporal contradiction detected"
            }
        
        # Check for semantic contradiction using keyword analysis
        semantic_score = self._check_semantic_contradiction(claim_a_lower, claim_b_lower)
        if semantic_score > 0.4:  # Semantic contradiction detected
            return {
                "is_contradiction": True,
                "contradiction_type": "semantic",
                "confidence": semantic_score,
                "evidence": f"Semantic contradiction detected (score: {semantic_score:.2f})"
            }
        
        return {
            "is_contradiction": False,
            "contradiction_type": None,
            "confidence": 0.0,
            "evidence": "No contradiction detected"
        }

    def _check_direct_negation(self, claim_a: str, claim_b: str) -> bool:
        """Check for direct negation patterns."""
        # Remove common words for comparison
        clean_a = re.sub(r'\b(the|a|an|this|that|these|those|is|are|was|were|be|been|being|of|in|on|at|by|for|with|to|from)\b', '', claim_a)
        clean_b = re.sub(r'\b(the|a|an|this|that|these|those|is|are|was|were|be|been|being|of|in|on|at|by|for|with|to|from)\b', '', claim_b)
        
        # Check if one is negation of the other
        negation_patterns = [
            r'\b(not|no|never|none|neither|nor)\b',
            r'\b(does not|do not|did not|is not|are not|was not|were not)\b',
        ]
        
        has_negation_a = any(re.search(pattern, clean_a) for pattern in negation_patterns)
        has_negation_b = any(re.search(pattern, clean_b) for pattern in negation_patterns)
        
        # If one has negation and the other doesn't, check similarity
        if has_negation_a != has_negation_b:
            # Remove negation and compare
            clean_a_no_neg = re.sub(r'\b(not|no|never|none|neither|nor|does not|do not|did not|is not|are not|was not|were not)\b', '', clean_a)
            clean_b_no_neg = re.sub(r'\b(not|no|never|none|neither|nor|does not|do not|did not|is not|are not|was not|were not)\b', '', clean_b)
            
            # Simple similarity check
            words_a = set(clean_a_no_neg.split())
            words_b = set(clean_b_no_neg.split())
            
            if words_a and words_b:
                intersection = words_a.intersection(words_b)
                union = words_a.union(words_b)
                similarity = len(intersection) / len(union)
                
                return similarity > 0.6
        
        return False

    def _check_opposite_terms(self, claim_a: str, claim_b: str) -> float:
        """Check for opposite terms between claims."""
        opposite_pairs = [
            ('true', 'false'), ('yes', 'no'), ('good', 'bad'), ('right', 'wrong'),
            ('increase', 'decrease'), ('up', 'down'), ('high', 'low'), ('big', 'small'),
            ('fast', 'slow'), ('hot', 'cold'), ('light', 'dark'), ('old', 'new'),
            ('strong', 'weak'), ('positive', 'negative'), ('success', 'failure'),
            ('begin', 'end'), ('start', 'stop'), ('accept', 'reject'), ('include', 'exclude'),
            ('same', 'different'), ('similar', 'opposite')
        ]
        
        score = 0.0
        words_a = set(claim_a.split())
        words_b = set(claim_b.split())
        
        for term_a, term_b in opposite_pairs:
            if (term_a in words_a and term_b in words_b) or (term_b in words_a and term_a in words_b):
                score += 0.3
        
        return min(score, 1.0)

    def _check_exclusive_terms(self, claim_a: str, claim_b: str) -> bool:
        """Check for exclusive terms that cannot both be true."""
        exclusive_terms = [
            r'\b(only|just|solely|exclusively|specifically)\b',
            r'\b(unique|singular|one and only)\b',
            r'\b(none|never|nothing|nowhere)\b',
        ]
        
        has_exclusive_a = any(re.search(pattern, claim_a) for pattern in exclusive_terms)
        has_exclusive_b = any(re.search(pattern, claim_b) for pattern in exclusive_terms)
        
        return has_exclusive_a and has_exclusive_b

    def _check_temporal_contradiction(self, claim_a: str, claim_b: str) -> bool:
        """Check for temporal contradictions."""
        temporal_patterns = [
            r'\b(yesterday|today|tomorrow)\b',
            r'\b(past|present|future)\b',
            r'\b(before|after|during)\b',
            r'\b(then|now|later)\b',
        ]
        
        times_a = []
        times_b = []
        
        for pattern in temporal_patterns:
            matches_a = re.findall(pattern, claim_a)
            matches_b = re.findall(pattern, claim_b)
            times_a.extend(matches_a)
            times_b.extend(matches_b)
        
        # Check for contradictory time references
        if times_a and times_b:
            # Simple check for obvious contradictions
            if ('yesterday' in times_a and 'tomorrow' in times_b) or \
               ('past' in times_a and 'future' in times_b) or \
               ('before' in times_a and 'after' in times_b):
                return True
        
        return False

    def _check_semantic_contradiction(self, claim_a: str, claim_b: str) -> float:
        """Check for semantic contradictions using keyword analysis."""
        # Keywords that indicate completion vs non-completion
        completion_keywords = ['completed', 'finished', 'done', 'accomplished', 'achieved', 'executed']
        non_completion_keywords = ['not started', 'planning', 'beginning', 'initiating', 'starting']
        
        # Keywords that indicate submission vs non-submission
        submission_keywords = ['submitted', 'delivered', 'provided', 'sent', 'given']
        non_submission_keywords = ['not written', 'not prepared', 'not created', 'not done']
        
        score = 0.0
        
        # Check for completion vs non-completion contradiction
        has_completion = any(keyword in claim_a for keyword in completion_keywords)
        has_non_completion = any(keyword in claim_b for keyword in non_completion_keywords)
        
        if has_completion and has_non_completion:
            score += 0.5
        
        # Check reverse
        has_completion_b = any(keyword in claim_b for keyword in completion_keywords)
        has_non_completion_a = any(keyword in claim_a for keyword in non_completion_keywords)
        
        if has_completion_b and has_non_completion_a:
            score += 0.5
        
        # Check for submission vs non-submission contradiction
        has_submission = any(keyword in claim_a for keyword in submission_keywords)
        has_non_submission = any(keyword in claim_b for keyword in non_submission_keywords)
        
        if has_submission and has_non_submission:
            score += 0.4
        
        # Check reverse
        has_submission_b = any(keyword in claim_b for keyword in submission_keywords)
        has_non_submission_a = any(keyword in claim_a for keyword in non_submission_keywords)
        
        if has_submission_b and has_non_submission_a:
            score += 0.4
        
        return min(score, 1.0)

    def _check_contradiction_indicators(self, claim: str) -> List[str]:
        """Check for contradiction indicators in a claim."""
        indicators = []
        claim_lower = claim.lower()
        
        for pattern in self.contradiction_indicators:
            if re.search(pattern, claim_lower):
                indicators.append(pattern)
        
        return indicators

    def _analyze_logical_structure(self, claim: str) -> Dict[str, Any]:
        """Analyze the logical structure of a claim."""
        structure = {
            "has_conditionals": bool(re.search(r'\b(if|when|unless|provided that)\b', claim.lower())),
            "has_negations": bool(re.search(r'\b(not|no|never|none|neither|nor)\b', claim.lower())),
            "has_quantifiers": bool(re.search(r'\b(all|some|none|every|each|any)\b', claim.lower())),
            "has_modals": bool(re.search(r'\b(must|should|could|would|can|may|might)\b', claim.lower())),
            "complexity_score": self._calculate_complexity_score(claim)
        }
        
        return structure

    def _calculate_complexity_score(self, claim: str) -> float:
        """Calculate complexity score for a claim."""
        words = claim.split()
        if not words:
            return 0.0
        
        # Length score
        length_score = min(1.0, len(words) / 20.0)
        
        # Complexity indicators
        complexity_indicators = [
            r'\b(because|since|therefore|thus|consequently|however|nevertheless)\b',
            r'\b(analysis|examination|investigation|evaluation)\b',
            r'\b(complex|complicated|intricate|sophisticated)\b',
        ]
        
        complexity_score = 0.0
        for pattern in complexity_indicators:
            if re.search(pattern, claim.lower()):
                complexity_score += 0.2
        
        return min(length_score + complexity_score, 1.0)

    def _calculate_contradiction_confidence(self, contradiction_pairs: List[Dict[str, Any]], total_claims: int) -> float:
        """
        Calculate overall contradiction confidence based on detected contradictions.
        """
        if not contradiction_pairs or total_claims < 2:
            return 0.0
        
        # Calculate confidence based on number and strength of contradictions
        total_confidence = sum(pair["confidence"] for pair in contradiction_pairs)
        max_possible_confidence = len(contradiction_pairs)
        
        # Normalize by number of claims (more claims = more potential contradictions)
        base_confidence = total_confidence / max_possible_confidence if max_possible_confidence > 0 else 0.0
        
        # Adjust for claim density
        total_comparisons = total_claims * (total_claims - 1) // 2
        contradiction_density = len(contradiction_pairs) / total_comparisons if total_comparisons > 0 else 0.0
        
        # Combine scores with emphasis on individual contradiction strength
        final_confidence = (base_confidence * 0.6) + (contradiction_density * 0.4)
        
        # If we have any high-confidence individual contradictions, boost the overall confidence
        max_individual_confidence = max(pair["confidence"] for pair in contradiction_pairs)
        if max_individual_confidence >= 0.5:  # Lower threshold for boosting
            final_confidence = max(final_confidence, max_individual_confidence * 0.95)
        
        return min(final_confidence, 1.0)

    async def _store_logic_hallucination(self, text: str, audit_result: Dict[str, Any], source_id: str):
        """
        Store logic hallucination detection result in the database.
        """
        try:
            timestamp = datetime.now().isoformat()
            text_hash = hash(text)  # Simple hash for demo
            
            sql = """
                INSERT INTO nexus_logic_hallucinations 
                (text_hash, text_sample, hallucination_detected, contradiction_confidence, 
                 contradiction_details, claims_analyzed, timestamp, source_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.nexus.nexus.execute(sql, (
                str(text_hash),
                text[:5000],  # Limit text size
                audit_result.get("hallucination_detected", False),
                audit_result.get("contradiction_confidence", 0.0),
                json.dumps(audit_result.get("contradiction_details", [])),
                audit_result.get("claims_analyzed", 0),
                timestamp,
                source_id
            ))
            
            logger.info(f"[{self.plugin_id}] Stored logic hallucination: {text_hash} (Confidence: {audit_result.get('contradiction_confidence', 0):.2%})")
            
        except Exception as e:
            logger.error(f"[{self.plugin_id}] Failed to store logic hallucination: {e}")


def create_plugin(manifest: Dict[str, Any], nexus_api: Any):
    """Factory function to create and return a LogicAuditor instance."""
    return LogicAuditor(manifest, nexus_api)