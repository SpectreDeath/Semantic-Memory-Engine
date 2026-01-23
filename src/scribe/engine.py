"""
🖋️ SCRIBE - Layer 6 Forensic Analysis Engine
Linguistic fingerprinting and authorship attribution using 6,734 rhetoric signals.

The Scribe doesn't analyze MEANING (Loom does that). Instead, it identifies the
HABITUAL PATTERNS of the writer—elements that are extremely difficult to fake:
- Sentence structure preferences (complexity, length distribution)
- Punctuation "sparks" (Oxford commas, em-dashes, specific patterns)
- Signal consistency (which rhetorical dimensions they habitually favor)
- Lexical diversity (vocabulary richness, word repetition patterns)
- Syntactic DNA (active vs. passive voice ratios, clause construction)

This is your "forensic fingerprint" layer—useful for:
✓ Authorship attribution (matching unknown text to known profiles)
✓ Ghost-writing detection (sudden stylistic shift in a known author)
✓ AI text detection (AI patterns differ from human linguistic fingerprints)
✓ Authenticity verification (did this really come from who we think?)
"""

import asyncio
import json
import logging
import sqlite3
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from scipy.spatial.distance import cosine
from collections import Counter
import re
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk

# Download required NLTK data (newer versions use punkt_tab)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    try:
        nltk.download('punkt_tab', quiet=True)
    except:
        # Fallback for older NLTK versions
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)

# ============================================================================
# CONFIGURATION & SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

from src.core.config import Config
config = Config()
DB_PATH = str(config.get_path('storage.base_dir') / "storage" / "centrifuge_db.sqlite")
SCRIBE_DB_PATH = str(config.get_path('storage.base_dir') / "storage" / "scribe_profiles.sqlite")

# Linguistic thresholds for anomaly detection
ANOMALY_THRESHOLDS = {
    "sentence_length_shift": 0.25,  # 25% deviation = anomaly
    "signal_consistency_drop": 0.30,  # 30% drop = anomaly
    "vocabulary_shift": 0.20,  # 20% change = anomaly
    "punctuation_variation": 0.35,  # 35% change = anomaly
}

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class LinguisticFingerprint:
    """Complete linguistic profile of a writer."""
    author_id: Optional[str] = None
    avg_sentence_length: float = 0.0
    sentence_length_std: float = 0.0
    avg_word_length: float = 0.0
    lexical_diversity: float = 0.0  # Type-Token Ratio (0-1)
    type_token_ratio: float = 0.0
    passive_voice_ratio: float = 0.0
    active_voice_ratio: float = 0.0
    avg_clause_count: float = 0.0
    punctuation_profile: Dict = None  # {',': 0.5, ';': 0.1, ...}
    signal_weights: Dict = None  # {signal_id: weight, ...}
    signal_vector: List[float] = None  # Normalized vector for cosine similarity
    text_sample_count: int = 0
    created_at: str = ""

    def __post_init__(self):
        if self.punctuation_profile is None:
            self.punctuation_profile = {}
        if self.signal_weights is None:
            self.signal_weights = {}
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class AuthorshipMatch:
    """Result of comparing unknown text against known profiles."""
    author_id: str
    author_name: str
    confidence_score: float  # 0-100
    fingerprint_similarity: float  # Cosine similarity
    reasoning: str
    match_strength: str  # "High", "Medium", "Low", "Inconclusive"


@dataclass
class AnomalyReport:
    """Stylistic anomaly detection report."""
    author_id: str
    author_name: str
    anomalies_detected: List[str]
    severity: str  # "Critical", "High", "Medium", "Low"
    confidence: float  # 0-100
    baseline_profile: Dict
    current_profile: Dict
    analysis_timestamp: str


# ============================================================================
# SCRIBE ENGINE - CORE CLASS
# ============================================================================

class ScribeEngine:
    """
    Forensic authorship analysis engine.
    
    Uses 6,734 rhetoric signals + linguistic features to create unique
    "fingerprints" that are extremely difficult to fake.
    """

    def __init__(self, db_path: str = SCRIBE_DB_PATH, centrifuge_path: str = DB_PATH):
        self.db_path = db_path
        self.centrifuge_path = centrifuge_path
        self.browser_config = None  # Placeholder for potential expansion
        
        # Initialize databases
        self._ensure_scribe_tables()
        self._load_rhetoric_signals()
        
        logger.info("🖋️ ScribeEngine initialized")

    # ========================================================================
    # TOOL 1: EXTRACT LINGUISTIC FINGERPRINT
    # ========================================================================

    def extract_linguistic_fingerprint(self, text: str, author_id: Optional[str] = None) -> LinguisticFingerprint:
        """
        Transform raw text into a numerical fingerprint vector.
        
        This fingerprint captures:
        1. Syntactic patterns (sentence structure, clause complexity)
        2. Lexical patterns (vocabulary richness, repetition)
        3. Punctuation habits ("sparks" that identify the writer)
        4. Rhetorical signal distribution (which signals they favor)
        
        Args:
            text: The text sample to analyze
            author_id: Optional author identifier for profile tracking
            
        Returns:
            LinguisticFingerprint with all feature vectors normalized
        """
        logger.info(f"📊 Extracting linguistic fingerprint from {len(text)} characters...")

        try:
            # 1. SYNTACTIC FEATURES
            sentences = sent_tokenize(text)
            tokens = word_tokenize(text.lower())
            words = [w for w in tokens if w.isalpha()]  # Filter to alphabetic words

            if not sentences or not words:
                logger.warning("⚠️ Text too short for fingerprinting")
                return LinguisticFingerprint(author_id=author_id)

            # Sentence metrics
            sentence_lengths = [len(sent.split()) for sent in sentences]
            avg_sentence_length = np.mean(sentence_lengths)
            sentence_length_std = np.std(sentence_lengths)

            # Word metrics
            avg_word_length = np.mean([len(w) for w in words])

            # 2. LEXICAL DIVERSITY
            unique_words = set(words)
            type_token_ratio = len(unique_words) / len(words) if words else 0
            lexical_diversity = self._calculate_lexical_diversity(text)

            # 3. VOICE RATIOS (Active vs. Passive)
            passive_ratio = self._detect_passive_voice(text)
            active_ratio = 1.0 - passive_ratio

            # 4. CLAUSE COMPLEXITY
            avg_clause_count = self._count_clauses(sentences)

            # 5. PUNCTUATION PROFILE ("sparks")
            punctuation_profile = self._analyze_punctuation(text)

            # 6. RHETORICAL SIGNAL WEIGHTS
            signal_weights = self._map_to_rhetoric_signals(text)
            signal_vector = self._vectorize_signals(signal_weights)

            fingerprint = LinguisticFingerprint(
                author_id=author_id,
                avg_sentence_length=float(avg_sentence_length),
                sentence_length_std=float(sentence_length_std),
                avg_word_length=float(avg_word_length),
                lexical_diversity=float(lexical_diversity),
                type_token_ratio=float(type_token_ratio),
                passive_voice_ratio=float(passive_ratio),
                active_voice_ratio=float(active_ratio),
                avg_clause_count=float(avg_clause_count),
                punctuation_profile=punctuation_profile,
                signal_weights=signal_weights,
                signal_vector=signal_vector,
                text_sample_count=len(words),
                created_at=datetime.utcnow().isoformat()
            )

            logger.info(f"✅ Fingerprint extracted: {len(fingerprint.signal_vector)} signal dimensions")
            return fingerprint

        except Exception as e:
            logger.error(f"❌ Fingerprint extraction failed: {str(e)}")
            raise

    # ========================================================================
    # TOOL 2: COMPARE TO PROFILES
    # ========================================================================

    def compare_to_profiles(
        self,
        unknown_fingerprint: LinguisticFingerprint,
        min_confidence: float = 50.0
    ) -> List[AuthorshipMatch]:
        """
        Compare an unknown fingerprint against all known author profiles.
        
        Uses cosine similarity on vectorized signals + linguistic metrics
        to find the most likely author match.
        
        Args:
            unknown_fingerprint: The fingerprint to identify
            min_confidence: Minimum confidence threshold (0-100)
            
        Returns:
            List of AuthorshipMatch results, sorted by confidence descending
        """
        logger.info("🔍 Comparing unknown fingerprint against known profiles...")

        try:
            known_profiles = self._get_all_author_profiles()
            
            if not known_profiles:
                logger.warning("⚠️ No known profiles in database")
                return []

            matches = []

            for profile in known_profiles:
                # Calculate composite similarity score
                signal_similarity = self._calculate_signal_similarity(
                    unknown_fingerprint.signal_vector,
                    profile['signal_vector']
                )
                
                # Weighted metrics comparison
                metrics_similarity = self._compare_linguistic_metrics(
                    unknown_fingerprint,
                    LinguisticFingerprint(**profile)
                )
                
                # Composite score (70% signal + 30% metrics)
                composite_score = (signal_similarity * 0.7) + (metrics_similarity * 0.3)
                confidence = min(100.0, composite_score * 100)

                # Build reasoning
                reasoning = (
                    f"Signal alignment: {signal_similarity:.2%} | "
                    f"Metric similarity: {metrics_similarity:.2%} | "
                    f"Sentence length match: "
                    f"{abs(unknown_fingerprint.avg_sentence_length - profile['avg_sentence_length']):.1f} word diff"
                )

                if confidence >= min_confidence:
                    match = AuthorshipMatch(
                        author_id=profile['author_id'],
                        author_name=profile.get('author_name', 'Unknown'),
                        confidence_score=confidence,
                        fingerprint_similarity=signal_similarity,
                        reasoning=reasoning,
                        match_strength=self._classify_match_strength(confidence)
                    )
                    matches.append(match)

            # Sort by confidence descending
            matches = sorted(matches, key=lambda x: x.confidence_score, reverse=True)
            logger.info(f"✅ Found {len(matches)} potential matches")
            return matches

        except Exception as e:
            logger.error(f"❌ Profile comparison failed: {str(e)}")
            raise

    def get_stylo_attribution(self, text: str, corpus_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Performs secondary attribution using the R stylo package.
        
        Args:
            text: Text to analyze
            corpus_path: Path to directory of known author samples
            
        Returns:
            Stylo attribution results or error status
        """
        try:
            from src.core.factory import ToolFactory
            stylo = ToolFactory.create_stylo_wrapper()
            
            status = stylo.get_status()
            if not status["ready"]:
                return {
                    "status": "unavailable",
                    "reason": "R or stylo package not found",
                    "instructions": [
                        "1. Download R from cran.r-project.org",
                        "2. Run in R: install.packages('stylo')",
                        "3. Run in terminal: pip install rpy2"
                    ]
                }
            
            if not corpus_path:
                return {"status": "error", "reason": "No corpus path provided for Delta analysis"}
            
            results = stylo.analyze_distance(text, corpus_path)
            return {
                "status": "success",
                "results": results,
                "engine": "R-Stylo (Burrows Delta)"
            }
        except Exception as e:
            logger.error(f"Stylo attribution failed: {e}")
            return {"status": "error", "reason": str(e)}

    # ========================================================================
    # TOOL 3: CALCULATE ATTRIBUTION SCORE
    # ========================================================================

    def calculate_attribution_score(
        self,
        unknown_text: str,
        candidate_author_id: str
    ) -> Tuple[float, Dict]:
        """
        Calculate precise attribution probability for a specific author.
        
        Returns a 0-100 confidence score based on:
        - Signal vector cosine similarity
        - Linguistic metric alignment
        - Punctuation habit matching
        - Lexical diversity consistency
        
        Args:
            unknown_text: The text to attribute
            candidate_author_id: The candidate author to test
            
        Returns:
            (attribution_score: 0-100, detailed_breakdown: Dict)
        """
        logger.info(f"📈 Calculating attribution score for author: {candidate_author_id}")

        try:
            # Step 1: Extract fingerprint from unknown text
            unknown_fp = self.extract_linguistic_fingerprint(unknown_text)

            # Step 2: Get candidate author profile
            candidate_profile_dict = self._get_author_profile(candidate_author_id)
            if not candidate_profile_dict:
                logger.warning(f"⚠️ No profile found for author {candidate_author_id}")
                return 0.0, {"error": "Author profile not found"}

            candidate_profile = LinguisticFingerprint(**candidate_profile_dict)

            # Step 3: Calculate component scores
            signal_score = self._calculate_signal_similarity(
                unknown_fp.signal_vector,
                candidate_profile.signal_vector
            ) * 100

            metrics_score = self._compare_linguistic_metrics(
                unknown_fp,
                candidate_profile
            ) * 100

            punctuation_score = self._compare_punctuation_profiles(
                unknown_fp.punctuation_profile,
                candidate_profile.punctuation_profile
            ) * 100

            diversity_score = self._compare_lexical_diversity(
                unknown_fp.type_token_ratio,
                candidate_profile.type_token_ratio
            ) * 100

            voice_ratio_score = self._compare_voice_ratios(
                unknown_fp.passive_voice_ratio,
                candidate_profile.passive_voice_ratio
            ) * 100

            # Step 4: Weighted composite (signal is most important)
            breakdown = {
                "signal_alignment": signal_score,
                "linguistic_metrics": metrics_score,
                "punctuation_habits": punctuation_score,
                "lexical_diversity": diversity_score,
                "voice_ratio_match": voice_ratio_score,
                "component_weights": {
                    "signal": 0.40,
                    "metrics": 0.25,
                    "punctuation": 0.15,
                    "diversity": 0.15,
                    "voice": 0.05
                }
            }

            final_score = (
                signal_score * 0.40 +
                metrics_score * 0.25 +
                punctuation_score * 0.15 +
                diversity_score * 0.15 +
                voice_ratio_score * 0.05
            )

            breakdown["final_attribution_score"] = final_score
            breakdown["confidence_level"] = self._classify_confidence_level(final_score)

            logger.info(f"✅ Attribution score calculated: {final_score:.1f}%")
            return final_score, breakdown

        except Exception as e:
            logger.error(f"❌ Attribution score calculation failed: {str(e)}")
            return 0.0, {"error": str(e)}

    # ========================================================================
    # TOOL 4: IDENTIFY STYLISTIC ANOMALIES
    # ========================================================================

    def identify_stylistic_anomalies(
        self,
        author_id: str,
        new_text: str
    ) -> Optional[AnomalyReport]:
        """
        Detect when a "known" author's style suddenly changes.
        
        Used for detecting:
        - Ghost-writing (author's style becomes AI-like)
        - Account takeover (style drastically shifts)
        - Uncharacteristic behavior (sudden shift in preferred signals)
        
        Args:
            author_id: The known author to check
            new_text: New text allegedly from this author
            
        Returns:
            AnomalyReport if anomalies detected, None if style is consistent
        """
        logger.info(f"🔎 Scanning for stylistic anomalies: {author_id}")

        try:
            # Get baseline profile for this author
            baseline_dict = self._get_author_profile(author_id)
            if not baseline_dict:
                logger.warning(f"⚠️ No baseline profile for {author_id}")
                return None

            baseline_fp = LinguisticFingerprint(**baseline_dict)

            # Extract fingerprint from new text
            new_fp = self.extract_linguistic_fingerprint(new_text, author_id=author_id)

            anomalies = []
            severity_scores = []

            # Check 1: Sentence length shift
            sentence_shift = abs(
                (new_fp.avg_sentence_length - baseline_fp.avg_sentence_length) /
                max(baseline_fp.avg_sentence_length, 1.0)
            )
            if sentence_shift > ANOMALY_THRESHOLDS["sentence_length_shift"]:
                anomalies.append(
                    f"⚠️ SENTENCE LENGTH: Baseline {baseline_fp.avg_sentence_length:.1f} → "
                    f"New {new_fp.avg_sentence_length:.1f} words ({sentence_shift:.0%} shift)"
                )
                severity_scores.append(sentence_shift)

            # Check 2: Signal consistency
            signal_shift = self._calculate_signal_consistency_shift(
                baseline_fp.signal_weights,
                new_fp.signal_weights
            )
            if signal_shift > ANOMALY_THRESHOLDS["signal_consistency_drop"]:
                anomalies.append(
                    f"⚠️ SIGNAL SHIFT: Rhetorical patterns changed {signal_shift:.0%}"
                )
                severity_scores.append(signal_shift)

            # Check 3: Vocabulary shift
            vocab_shift = abs(new_fp.type_token_ratio - baseline_fp.type_token_ratio)
            if vocab_shift > ANOMALY_THRESHOLDS["vocabulary_shift"]:
                anomalies.append(
                    f"⚠️ VOCABULARY: Type-token ratio shifted from "
                    f"{baseline_fp.type_token_ratio:.2f} to {new_fp.type_token_ratio:.2f}"
                )
                severity_scores.append(vocab_shift)

            # Check 4: Punctuation changes
            punct_shift = self._calculate_punctuation_shift(
                baseline_fp.punctuation_profile,
                new_fp.punctuation_profile
            )
            if punct_shift > ANOMALY_THRESHOLDS["punctuation_variation"]:
                anomalies.append(
                    f"⚠️ PUNCTUATION: Usage patterns changed {punct_shift:.0%}"
                )
                severity_scores.append(punct_shift)

            # Check 5: Voice ratio (often signals AI-generated text)
            voice_shift = abs(new_fp.passive_voice_ratio - baseline_fp.passive_voice_ratio)
            if voice_shift > 0.15:  # 15% change is significant
                anomalies.append(
                    f"⚠️ VOICE SHIFT: Passive voice ratio {baseline_fp.passive_voice_ratio:.0%} → "
                    f"{new_fp.passive_voice_ratio:.0%} (might indicate AI generation)"
                )
                severity_scores.append(voice_shift)

            # Generate report only if anomalies detected
            if anomalies:
                avg_severity = np.mean(severity_scores) if severity_scores else 0
                confidence = min(100.0, avg_severity * 100)

                report = AnomalyReport(
                    author_id=author_id,
                    author_name=baseline_dict.get('author_name', 'Unknown'),
                    anomalies_detected=anomalies,
                    severity=self._classify_severity(avg_severity),
                    confidence=confidence,
                    baseline_profile={
                        "avg_sentence_length": baseline_fp.avg_sentence_length,
                        "type_token_ratio": baseline_fp.type_token_ratio,
                        "passive_voice_ratio": baseline_fp.passive_voice_ratio,
                        "signal_count": len(baseline_fp.signal_weights)
                    },
                    current_profile={
                        "avg_sentence_length": new_fp.avg_sentence_length,
                        "type_token_ratio": new_fp.type_token_ratio,
                        "passive_voice_ratio": new_fp.passive_voice_ratio,
                        "signal_count": len(new_fp.signal_weights)
                    },
                    analysis_timestamp=datetime.utcnow().isoformat()
                )

                logger.info(f"🚨 Anomalies detected ({len(anomalies)} issues, {report.severity} severity)")
                return report

            logger.info(f"✅ No anomalies detected - style is consistent")
            return None

        except Exception as e:
            logger.error(f"❌ Anomaly detection failed: {str(e)}")
            raise

    # ========================================================================
    # HELPER METHODS - LINGUISTIC ANALYSIS
    # ========================================================================

    def _calculate_lexical_diversity(self, text: str) -> float:
        """Calculates lexical diversity using Honoré's statistic."""
        words = word_tokenize(text.lower())
        words = [w for w in words if w.isalpha()]
        
        if not words:
            return 0.0
            
        N = len(words)
        V = len(set(words))
        
        if V == 0 or N == 0:
            return 0.0
        
        # Honoré's statistic: more accurate than simple TTR
        try:
            diversity = 100 * np.log(N) / (1 - (V / N))
            return min(diversity / 1000, 1.0)  # Normalize to 0-1
        except:
            return V / N  # Fallback to simple TTR

    def _detect_passive_voice(self, text: str) -> float:
        """Estimate passive voice ratio (simple heuristic)."""
        sentences = sent_tokenize(text)
        passive_count = 0
        
        for sent in sentences:
            # Simple detection: "was/were" + past participle
            if re.search(r'\b(was|were|is|are|be|been|being)\s+\w+ed\b', sent, re.IGNORECASE):
                passive_count += 1
        
        return passive_count / len(sentences) if sentences else 0.0

    def _count_clauses(self, sentences: List[str]) -> float:
        """Estimate average clause count per sentence."""
        clause_counts = []
        
        for sent in sentences:
            # Count conjunctions as rough proxy for clauses
            conj_count = len(re.findall(r'\b(and|but|or|because|since|although|if|when|where)\b', sent, re.IGNORECASE))
            clause_counts.append(conj_count + 1)  # At least 1 main clause
        
        return np.mean(clause_counts) if clause_counts else 1.0

    def _analyze_punctuation(self, text: str) -> Dict[str, float]:
        """Extract punctuation usage patterns ("sparks")."""
        total_chars = len(text)
        
        punct_chars = [',', '.', '!', '?', ';', ':', '"', "'", '-', '—', '…', '(', ')']
        profile = {}
        
        for p in punct_chars:
            count = text.count(p)
            profile[p] = count / max(total_chars, 1)  # Normalize by text length
        
        return profile

    def _map_to_rhetoric_signals(self, text: str) -> Dict[str, float]:
        """
        Map text to the 6,734 rhetoric signals from the lexicon.
        
        This is a lightweight approximation that scores signals based on
        keyword frequency and co-occurrence patterns.
        """
        signal_weights = {}
        words = word_tokenize(text.lower())
        words = [w for w in words if w.isalpha()]
        
        # Load signal keywords from rhetoric signals
        signal_keywords = self._load_signal_keywords()
        
        for signal_id, keywords in signal_keywords.items():
            # Count keyword hits
            hits = sum(1 for word in words if word in keywords)
            if hits > 0:
                # Weight by frequency (normalized)
                signal_weights[signal_id] = hits / len(words) if words else 0
        
        return signal_weights

    def _vectorize_signals(self, signal_weights: Dict[str, float]) -> List[float]:
        """Convert signal weights to normalized vector for cosine similarity."""
        if not signal_weights:
            return [0.0] * 100  # Default to 100-dim vector
        
        # Create sorted vector from weights
        values = list(signal_weights.values())
        vector = np.array(values[:100])  # Use first 100 signals as primary
        
        # Normalize to unit vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()

    def _calculate_signal_similarity(self, vector1: List[float], vector2: List[float]) -> float:
        """Calculate cosine similarity between two signal vectors."""
        if not vector1 or not vector2:
            return 0.0
        
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        
        # Pad to same length
        if len(v1) < len(v2):
            v1 = np.pad(v1, (0, len(v2) - len(v1)))
        elif len(v2) < len(v1):
            v2 = np.pad(v2, (0, len(v1) - len(v2)))
        
        # Cosine similarity (1 = identical, 0 = orthogonal)
        return 1 - cosine(v1, v2)

    def _compare_linguistic_metrics(self, fp1: LinguisticFingerprint, fp2: LinguisticFingerprint) -> float:
        """Compare overall linguistic metrics (sentence length, complexity, etc)."""
        metrics = [
            (fp1.avg_sentence_length, fp2.avg_sentence_length),
            (fp1.avg_word_length, fp2.avg_word_length),
            (fp1.type_token_ratio, fp2.type_token_ratio),
            (fp1.passive_voice_ratio, fp2.passive_voice_ratio),
        ]
        
        # Calculate normalized difference for each metric
        differences = []
        for m1, m2 in metrics:
            if m1 == 0 and m2 == 0:
                differences.append(1.0)  # Perfect match when both zero
            elif m1 == 0 or m2 == 0:
                differences.append(0.0)  # No match if one is zero
            else:
                # Relative difference (0-1, where 1 = identical)
                rel_diff = abs(m1 - m2) / max(abs(m1), abs(m2))
                differences.append(1.0 - min(rel_diff, 1.0))
        
        return np.mean(differences) if differences else 0.0

    def _compare_punctuation_profiles(self, p1: Dict, p2: Dict) -> float:
        """Compare punctuation usage patterns."""
        if not p1 or not p2:
            return 0.5  # No data = neutral
        
        all_punct = set(p1.keys()) | set(p2.keys())
        similarities = []
        
        for p in all_punct:
            v1 = p1.get(p, 0)
            v2 = p2.get(p, 0)
            
            if v1 == 0 and v2 == 0:
                similarities.append(1.0)
            elif v1 == 0 or v2 == 0:
                similarities.append(0.0)
            else:
                rel_diff = abs(v1 - v2) / max(v1, v2)
                similarities.append(1.0 - min(rel_diff, 1.0))
        
        return np.mean(similarities) if similarities else 0.5

    def _compare_lexical_diversity(self, ttr1: float, ttr2: float) -> float:
        """Compare lexical diversity (type-token ratio)."""
        if ttr1 == 0 or ttr2 == 0:
            return 0.5
        
        rel_diff = abs(ttr1 - ttr2) / max(ttr1, ttr2)
        return 1.0 - min(rel_diff, 1.0)

    def _compare_voice_ratios(self, ratio1: float, ratio2: float) -> float:
        """Compare active/passive voice ratios."""
        diff = abs(ratio1 - ratio2)
        return 1.0 - min(diff, 1.0)

    def _calculate_signal_consistency_shift(self, baseline_signals: Dict, new_signals: Dict) -> float:
        """Measure how much the signal distribution has changed."""
        if not baseline_signals or not new_signals:
            return 0.0
        
        # Get top signals in baseline
        top_baseline = set(sorted(baseline_signals.items(), key=lambda x: x[1], reverse=True)[:50])
        top_baseline_ids = {s[0] for s in top_baseline}
        
        # Check if top signals appear in new text
        overlap = sum(1 for sig_id in top_baseline_ids if sig_id in new_signals)
        shift = 1.0 - (overlap / len(top_baseline_ids)) if top_baseline_ids else 0.0
        
        return shift

    def _calculate_punctuation_shift(self, baseline_punct: Dict, new_punct: Dict) -> float:
        """Measure changes in punctuation usage patterns."""
        shifts = []
        
        for p in set(baseline_punct.keys()) | set(new_punct.keys()):
            b = baseline_punct.get(p, 0)
            n = new_punct.get(p, 0)
            
            if b == 0 and n == 0:
                continue
            elif b == 0 or n == 0:
                shifts.append(1.0)
            else:
                shift = abs(b - n) / max(b, n)
                shifts.append(shift)
        
        return np.mean(shifts) if shifts else 0.0

    def _classify_match_strength(self, confidence: float) -> str:
        """Classify match strength based on confidence score."""
        if confidence >= 85:
            return "High"
        elif confidence >= 70:
            return "Medium"
        elif confidence >= 50:
            return "Low"
        else:
            return "Inconclusive"

    def _classify_confidence_level(self, score: float) -> str:
        """Classify confidence level."""
        if score >= 90:
            return "Very High"
        elif score >= 75:
            return "High"
        elif score >= 60:
            return "Moderate"
        elif score >= 40:
            return "Low"
        else:
            return "Very Low"

    def _classify_severity(self, severity: float) -> str:
        """Classify anomaly severity."""
        if severity >= 0.6:
            return "Critical"
        elif severity >= 0.4:
            return "High"
        elif severity >= 0.25:
            return "Medium"
        else:
            return "Low"

    def _load_signal_keywords(self) -> Dict[str, set]:
        """Load signal-to-keyword mapping from Centrifuge DB."""
        # This would normally query the signals table
        # For now, return a basic mapping based on signal categories
        signal_keywords = {
            "sanctity_1": {"holy", "sacred", "divine", "blessed", "sacred"},
            "sanctity_2": {"pure", "clean", "unspoiled", "untainted"},
            "degradation_1": {"filthy", "dirty", "corrupt", "debased", "vile"},
            "care_1": {"compassion", "empathy", "kindness", "nurture", "support"},
            "harm_1": {"damage", "injure", "hurt", "wound", "pain"},
            "loyalty_1": {"faithful", "loyal", "devoted", "allegiance", "patriotic"},
            "betrayal_1": {"treachery", "treason", "disloyalty", "betrayal", "backstab"},
            "authority_1": {"leader", "command", "rank", "hierarchy", "superior"},
            "subversion_1": {"rebel", "resist", "challenge", "defy", "anarchist"},
            "freedom_1": {"liberty", "free", "independent", "autonomy", "unbound"},
            "oppression_1": {"enslaved", "imprisoned", "dominated", "controlled", "subjugated"},
            "fairness_1": {"equal", "just", "fair", "right", "deserve"},
            "cheating_1": {"unfair", "cheat", "deceive", "fraud", "dishonest"},
        }
        return signal_keywords

    # ========================================================================
    # DATABASE OPERATIONS
    # ========================================================================

    def _ensure_scribe_tables(self):
        """Create author profiles and analysis tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Author profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS author_profiles (
                    author_id TEXT PRIMARY KEY,
                    author_name TEXT,
                    avg_sentence_length REAL,
                    sentence_length_std REAL,
                    avg_word_length REAL,
                    lexical_diversity REAL,
                    type_token_ratio REAL,
                    passive_voice_ratio REAL,
                    active_voice_ratio REAL,
                    avg_clause_count REAL,
                    punctuation_profile TEXT,
                    signal_weights TEXT,
                    signal_vector TEXT,
                    text_sample_count INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    samples_count INTEGER DEFAULT 0,
                    avg_confidence REAL DEFAULT 0.0
                )
            """)

            # Attribution history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attribution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unknown_text_hash TEXT UNIQUE,
                    candidate_author_id TEXT,
                    attribution_score REAL,
                    confidence_level TEXT,
                    breakdown TEXT,
                    verified BOOLEAN DEFAULT 0,
                    created_at TEXT,
                    FOREIGN KEY (candidate_author_id) REFERENCES author_profiles(author_id)
                )
            """)

            # Anomaly reports table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anomaly_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_id TEXT,
                    anomalies_detected TEXT,
                    severity TEXT,
                    confidence REAL,
                    baseline_profile TEXT,
                    current_profile TEXT,
                    analysis_timestamp TEXT,
                    created_at TEXT,
                    FOREIGN KEY (author_id) REFERENCES author_profiles(author_id)
                )
            """)

            # Performance indices
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_author_id ON author_profiles(author_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attribution_author ON attribution_history(candidate_author_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_anomaly_author ON anomaly_reports(author_id)")

            conn.commit()
            logger.info("✅ Scribe database tables initialized")

        finally:
            conn.close()

    def _load_rhetoric_signals(self):
        """Load rhetoric signal definitions from Centrifuge DB."""
        # This would query the signals from centrifuge_db
        # For now, we cache basic signal info
        self.rhetoric_signals = {}
        logger.info("✅ Rhetoric signals loaded")

    def save_author_profile(self, fingerprint: LinguisticFingerprint, author_name: str):
        """Save a linguistic fingerprint as an author profile."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO author_profiles (
                    author_id, author_name, avg_sentence_length, sentence_length_std,
                    avg_word_length, lexical_diversity, type_token_ratio,
                    passive_voice_ratio, active_voice_ratio, avg_clause_count,
                    punctuation_profile, signal_weights, signal_vector,
                    text_sample_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fingerprint.author_id or f"author_{int(datetime.utcnow().timestamp())}",
                author_name,
                fingerprint.avg_sentence_length,
                fingerprint.sentence_length_std,
                fingerprint.avg_word_length,
                fingerprint.lexical_diversity,
                fingerprint.type_token_ratio,
                fingerprint.passive_voice_ratio,
                fingerprint.active_voice_ratio,
                fingerprint.avg_clause_count,
                json.dumps(fingerprint.punctuation_profile),
                json.dumps(fingerprint.signal_weights),
                json.dumps(fingerprint.signal_vector),
                fingerprint.text_sample_count,
                fingerprint.created_at,
                datetime.utcnow().isoformat()
            ))

            conn.commit()
            logger.info(f"✅ Profile saved for {author_name}")

        finally:
            conn.close()

    def _get_author_profile(self, author_id: str) -> Optional[Dict]:
        """Retrieve an author profile from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM author_profiles WHERE author_id = ?", (author_id,))
            row = cursor.fetchone()

            if not row:
                return None

            cols = [desc[0] for desc in cursor.description]
            profile = dict(zip(cols, row))

            # Deserialize JSON fields
            profile['punctuation_profile'] = json.loads(profile['punctuation_profile'] or '{}')
            profile['signal_weights'] = json.loads(profile['signal_weights'] or '{}')
            profile['signal_vector'] = json.loads(profile['signal_vector'] or '[]')

            # Remove non-dataclass fields before reconstruction
            profile.pop('author_name', None)
            profile.pop('samples_count', None)
            profile.pop('avg_confidence', None)
            profile.pop('updated_at', None)

            return profile

        finally:
            conn.close()

    def _get_all_author_profiles(self) -> List[Dict]:
        """Retrieve all author profiles."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM author_profiles")
            rows = cursor.fetchall()

            profiles = []
            for row in rows:
                cols = [desc[0] for desc in cursor.description]
                profile = dict(zip(cols, row))

                # Deserialize JSON fields
                profile['punctuation_profile'] = json.loads(profile['punctuation_profile'] or '{}')
                profile['signal_weights'] = json.loads(profile['signal_weights'] or '{}')
                profile['signal_vector'] = json.loads(profile['signal_vector'] or '[]')

                # Remove non-dataclass fields
                profile.pop('author_name', None)
                profile.pop('samples_count', None)
                profile.pop('avg_confidence', None)
                profile.pop('updated_at', None)

                profiles.append(profile)

            return profiles

        finally:
            conn.close()

    def save_attribution_result(self, unknown_text_hash: str, result: AuthorshipMatch, breakdown: Dict):
        """Save attribution result to history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO attribution_history (
                    unknown_text_hash, candidate_author_id, attribution_score,
                    confidence_level, breakdown, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                unknown_text_hash,
                result.author_id,
                result.confidence_score,
                result.match_strength,
                json.dumps(breakdown),
                datetime.utcnow().isoformat()
            ))

            conn.commit()

        finally:
            conn.close()

    def save_anomaly_report(self, report: AnomalyReport):
        """Save anomaly detection report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO anomaly_reports (
                    author_id, anomalies_detected, severity, confidence,
                    baseline_profile, current_profile, analysis_timestamp, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.author_id,
                json.dumps(report.anomalies_detected),
                report.severity,
                report.confidence,
                json.dumps(report.baseline_profile),
                json.dumps(report.current_profile),
                report.analysis_timestamp,
                datetime.utcnow().isoformat()
            ))

            conn.commit()
            logger.info(f"✅ Anomaly report saved for {report.author_id}")

        finally:
            conn.close()

    # ========================================================================
    # GET STATISTICS
    # ========================================================================

    def get_scribe_stats(self) -> Dict:
        """Return Scribe system statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM author_profiles")
            author_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM attribution_history")
            attribution_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM anomaly_reports")
            anomaly_count = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(avg_confidence) FROM author_profiles")
            avg_profile_confidence = cursor.fetchone()[0] or 0.0

            return {
                "total_author_profiles": author_count,
                "total_attributions": attribution_count,
                "total_anomaly_reports": anomaly_count,
                "avg_profile_confidence": avg_profile_confidence,
                "database_path": self.db_path,
                "status": "operational"
            }

        finally:
            conn.close()


# ============================================================================
# MCP TOOL FUNCTIONS (Exposed to SimpleMem)
# ============================================================================

def extract_linguistic_fingerprint_tool(text: str, author_id: Optional[str] = None) -> Dict:
    """
    MCP Tool: Extract linguistic fingerprint from text.
    
    Returns a unique "behavioral profile" based on style, not content.
    """
    scribe = ScribeEngine()
    fingerprint = scribe.extract_linguistic_fingerprint(text, author_id)
    
    return {
        "status": "success",
        "author_id": fingerprint.author_id,
        "fingerprint_features": {
            "avg_sentence_length": fingerprint.avg_sentence_length,
            "sentence_length_std": fingerprint.sentence_length_std,
            "avg_word_length": fingerprint.avg_word_length,
            "lexical_diversity": fingerprint.lexical_diversity,
            "type_token_ratio": fingerprint.type_token_ratio,
            "passive_voice_ratio": round(fingerprint.passive_voice_ratio, 3),
            "active_voice_ratio": round(fingerprint.active_voice_ratio, 3),
            "avg_clause_count": fingerprint.avg_clause_count,
        },
        "signal_dimensions": len(fingerprint.signal_vector),
        "text_analyzed": fingerprint.text_sample_count,
        "created_at": fingerprint.created_at
    }


def compare_to_profiles_tool(unknown_text: str, min_confidence: float = 50.0) -> Dict:
    """
    MCP Tool: Compare unknown text against all known author profiles.
    
    Returns ranked list of potential author matches.
    """
    scribe = ScribeEngine()
    fingerprint = scribe.extract_linguistic_fingerprint(unknown_text)
    matches = scribe.compare_to_profiles(fingerprint, min_confidence)
    
    return {
        "status": "success",
        "matches_found": len(matches),
        "matches": [
            {
                "author_id": m.author_id,
                "author_name": m.author_name,
                "confidence_score": round(m.confidence_score, 1),
                "match_strength": m.match_strength,
                "reasoning": m.reasoning
            }
            for m in matches[:10]  # Top 10 matches
        ]
    }


def calculate_attribution_score_tool(unknown_text: str, candidate_author_id: str) -> Dict:
    """
    MCP Tool: Calculate precise attribution probability for a specific author.
    
    Returns 0-100 confidence with detailed breakdown.
    """
    scribe = ScribeEngine()
    score, breakdown = scribe.calculate_attribution_score(unknown_text, candidate_author_id)
    
    return {
        "status": "success",
        "candidate_author_id": candidate_author_id,
        "attribution_score": round(score, 1),
        "confidence_level": breakdown.get("confidence_level", "Unknown"),
        "component_breakdown": {
            "signal_alignment": round(breakdown.get("signal_alignment", 0), 1),
            "linguistic_metrics": round(breakdown.get("linguistic_metrics", 0), 1),
            "punctuation_habits": round(breakdown.get("punctuation_habits", 0), 1),
            "lexical_diversity": round(breakdown.get("lexical_diversity", 0), 1),
            "voice_ratio_match": round(breakdown.get("voice_ratio_match", 0), 1),
        }
    }


def identify_stylistic_anomalies_tool(author_id: str, new_text: str) -> Dict:
    """
    MCP Tool: Detect stylistic anomalies (ghost-writing, account takeover, AI generation).
    
    Compares new text against author's baseline profile.
    """
    scribe = ScribeEngine()
    report = scribe.identify_stylistic_anomalies(author_id, new_text)
    
    if not report:
        return {
            "status": "success",
            "author_id": author_id,
            "anomalies_found": False,
            "message": "No stylistic anomalies detected - writing style is consistent"
        }
    
    return {
        "status": "success",
        "author_id": author_id,
        "anomalies_found": True,
        "severity": report.severity,
        "confidence": round(report.confidence, 1),
        "anomalies": report.anomalies_detected,
        "analysis_timestamp": report.analysis_timestamp
    }


def get_scribe_stats_tool() -> Dict:
    """MCP Tool: Get Scribe system statistics."""
    scribe = ScribeEngine()
    return scribe.get_scribe_stats()


# ============================================================================
# DEMO / TESTING
# ============================================================================

async def demo_scribe():
    """Demo showing all 4 Scribe tools in action."""
    print("\n" + "="*80)
    print("🖋️ SCRIBE ENGINE DEMO - Forensic Authorship Analysis")
    print("="*80)

    scribe = ScribeEngine()

    # Sample texts from different authors
    sample_texts = {
        "author_academic": """
        The examination of contemporary rhetorical patterns reveals a significant 
        divergence between formal and colloquial discourse structures. It is posited 
        that such variation stems from sociolinguistic factors inherent to academic 
        communities. Furthermore, the statistical analysis thereof demonstrates 
        considerable consistency across multiple dimensions.
        """,
        
        "author_casual": """
        So like, I was thinking about how people talk differently, you know? 
        And it's kinda wild how like, some folks are super formal and others are 
        just chill. I mean, it makes sense when you think about it, right?
        """,

        "author_technical": """
        The algorithm processes input vectors through a series of transformations.
        Each layer performs dimensionality reduction via PCA. Performance metrics
        indicate convergence within 1e-6 tolerance. See Table 3 for benchmark results.
        """,
    }

    # Step 1: Create author profiles
    print("\n📊 Step 1: Creating Author Profiles")
    print("-" * 80)
    for author_id, text in sample_texts.items():
        fp = scribe.extract_linguistic_fingerprint(text, author_id=author_id)
        scribe.save_author_profile(fp, author_name=author_id.replace("_", " ").title())
        print(f"✅ {author_id}")
        print(f"   • Avg sentence: {fp.avg_sentence_length:.1f} words")
        print(f"   • Lexical diversity: {fp.lexical_diversity:.2f}")
        print(f"   • Passive voice: {fp.passive_voice_ratio:.0%}")

    # Step 2: Test unknown text (matches academic style)
    unknown_academic = """
    The methodology employed in this investigation encompasses a comprehensive 
    examination of established paradigms within the discipline. The results obtained 
    thereby substantiate our initial hypothesis. These findings are moreover consistent 
    with previous scholarly works.
    """

    print("\n🔍 Step 2: Comparing Unknown Text to Profiles")
    print("-" * 80)
    matches = scribe.compare_to_profiles(
        scribe.extract_linguistic_fingerprint(unknown_academic)
    )
    for i, match in enumerate(matches, 1):
        print(f"{i}. {match.author_name} ({match.match_strength})")
        print(f"   Confidence: {match.confidence_score:.1f}%")
        print(f"   Signal match: {match.fingerprint_similarity:.0%}")

    # Step 3: Attribution score for specific author
    print("\n📈 Step 3: Attribution Score (Academic Author)")
    print("-" * 80)
    score, breakdown = scribe.calculate_attribution_score(
        unknown_academic,
        "author_academic"
    )
    print(f"Final Score: {score:.1f}%")
    print(f"Confidence: {breakdown.get('confidence_level')}")
    print("\nComponent Breakdown:")
    for component, value in breakdown.items():
        if component.endswith("_score") or component.endswith("alignment"):
            print(f"  • {component}: {value:.1f}%")

    # Step 4: Anomaly detection
    print("\n🔎 Step 4: Stylistic Anomaly Detection")
    print("-" * 80)
    # Create "anomalous" text (academic author writing casually)
    anomalous_text = """
    Yo, so like I was just chillin and thinking about this whole academic thing, 
    right? And I'm like, why do people talk so formal? It's kinda weird if you 
    ask me. I mean, just say what you mean, you know?
    """
    
    report = scribe.identify_stylistic_anomalies("author_academic", anomalous_text)
    if report:
        print(f"⚠️ ANOMALIES DETECTED ({report.severity} severity)")
        print(f"Confidence: {report.confidence:.1f}%")
        for anomaly in report.anomalies_detected:
            print(f"  {anomaly}")
    else:
        print("✅ No anomalies - style is consistent")

    # Step 5: Stats
    print("\n📊 Step 5: System Statistics")
    print("-" * 80)
    stats = scribe.get_scribe_stats()
    print(f"Author Profiles: {stats['total_author_profiles']}")
    print(f"Attributions Performed: {stats['total_attributions']}")
    print(f"Anomaly Reports: {stats['total_anomaly_reports']}")

    print("\n" + "="*80)
    print("✅ SCRIBE DEMO COMPLETE")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(demo_scribe())
