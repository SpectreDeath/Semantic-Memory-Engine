import math
import re
import statistics
import numpy as np
from collections import Counter, defaultdict
from typing import Dict, Any, List, Tuple, Optional
import logging

logger = logging.getLogger("LawnmowerMan.APB")

class LogicAnomalyDetector:
    """
    Adversarial Pattern Breaker (APB) - Logic Anomaly Detector
    
    Detects 'Linguistic Camouflage' - artificial entropy smoothing used to hide synthetic origin.
    Identifies High-Confidence Deception by analyzing unnatural text patterns.
    """
    
    def __init__(self):
        # Thresholds for detecting artificial smoothing
        self.entropy_smoothing_threshold = 0.15  # How much entropy variation is too little
        self.burstiness_smoothing_threshold = 1.0  # How low is too low for burstiness variance
        self.pattern_uniformity_threshold = 0.85  # How uniform is too uniform
        self.confidence_deception_threshold = 0.80  # Confidence level for deception flag
        
    def detect_linguistic_camouflage(self, text: str) -> Dict[str, Any]:
        """
        Main detection method for linguistic camouflage.
        
        Returns comprehensive analysis with deception confidence score.
        """
        if not text or len(text) < 100:  # Minimum text length for analysis
            return {
                "camouflage_detected": False,
                "deception_confidence": 0.0,
                "reason": "Text too short for analysis",
                "analysis": {}
            }
        
        # Perform multiple anomaly checks
        entropy_analysis = self._analyze_entropy_smoothing(text)
        burstiness_analysis = self._analyze_burstiness_smoothing(text)
        pattern_analysis = self._analyze_pattern_uniformity(text)
        lexical_analysis = self._analyze_lexical_smoothing(text)
        
        # Calculate overall deception confidence
        deception_confidence = self._calculate_deception_confidence([
            entropy_analysis,
            burstiness_analysis, 
            pattern_analysis,
            lexical_analysis
        ])
        
        # Determine if camouflage is detected
        camouflage_detected = deception_confidence >= self.confidence_deception_threshold
        
        return {
            "camouflage_detected": camouflage_detected,
            "deception_confidence": round(deception_confidence, 4),
            "high_confidence_deception": deception_confidence >= 0.90,
            "analysis": {
                "entropy_smoothing": entropy_analysis,
                "burstiness_smoothing": burstiness_analysis,
                "pattern_uniformity": pattern_analysis,
                "lexical_smoothing": lexical_analysis
            }
        }
    
    def _analyze_entropy_smoothing(self, text: str) -> Dict[str, Any]:
        """
        Detects artificially smoothed entropy by analyzing entropy variation
        across different text segments.
        """
        # Split text into segments
        segments = self._split_into_segments(text, segment_size=100)
        
        if len(segments) < 3:
            return {"anomaly_detected": False, "reason": "Insufficient segments"}
        
        # Calculate entropy for each segment
        segment_entropies = []
        for segment in segments:
            entropy = self._calculate_segment_entropy(segment)
            if entropy > 0:
                segment_entropies.append(entropy)
        
        if len(segment_entropies) < 3:
            return {"anomaly_detected": False, "reason": "Insufficient valid segments"}
        
        # Analyze entropy variation
        entropy_std = statistics.stdev(segment_entropies)
        entropy_mean = statistics.mean(segment_entropies)
        
        # Check for artificial smoothing (unnaturally low variation)
        is_smoothed = entropy_std < self.entropy_smoothing_threshold
        
        return {
            "anomaly_detected": is_smoothed,
            "entropy_std": round(entropy_std, 4),
            "entropy_mean": round(entropy_mean, 4),
            "segment_count": len(segment_entropies),
            "smoothing_score": round(1.0 - (entropy_std / 0.5), 4)  # Normalize to 0-1
        }
    
    def _analyze_burstiness_smoothing(self, text: str) -> Dict[str, Any]:
        """
        Detects artificially smoothed burstiness by analyzing sentence length variation.
        """
        sentences = self._split_into_sentences(text)
        
        if len(sentences) < 5:
            return {"anomaly_detected": False, "reason": "Insufficient sentences"}
        
        # Calculate sentence lengths
        sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence.strip()]
        
        if len(sentence_lengths) < 5:
            return {"anomaly_detected": False, "reason": "Insufficient valid sentences"}
        
        # Calculate burstiness (standard deviation of sentence lengths)
        burstiness = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0
        
        # Check for artificial smoothing (unnaturally low burstiness)
        is_smoothed = burstiness < self.burstiness_smoothing_threshold
        
        return {
            "anomaly_detected": is_smoothed,
            "burstiness_score": round(burstiness, 4),
            "sentence_count": len(sentence_lengths),
            "length_variance": round(statistics.variance(sentence_lengths), 4) if len(sentence_lengths) > 1 else 0
        }
    
    def _analyze_pattern_uniformity(self, text: str) -> Dict[str, Any]:
        """
        Detects unnaturally uniform patterns in word usage, punctuation, and structure.
        """
        words = text.lower().split()
        if len(words) < 50:
            return {"anomaly_detected": False, "reason": "Insufficient words"}
        
        # Analyze word frequency distribution
        word_freq = Counter(words)
        unique_words = len(word_freq)
        total_words = len(words)
        type_token_ratio = unique_words / total_words
        
        # Analyze punctuation patterns
        punctuation_pattern = self._analyze_punctuation_pattern(text)
        
        # Analyze structural patterns (sentence starters, connectors)
        structural_pattern = self._analyze_structural_pattern(text)
        
        # Calculate uniformity score
        uniformity_score = self._calculate_uniformity_score(
            type_token_ratio, 
            punctuation_pattern, 
            structural_pattern
        )
        
        # Check for excessive uniformity
        is_uniform = uniformity_score > self.pattern_uniformity_threshold
        
        return {
            "anomaly_detected": is_uniform,
            "uniformity_score": round(uniformity_score, 4),
            "type_token_ratio": round(type_token_ratio, 4),
            "punctuation_uniformity": round(punctuation_pattern, 4),
            "structural_uniformity": round(structural_pattern, 4)
        }
    
    def _analyze_lexical_smoothing(self, text: str) -> Dict[str, Any]:
        """
        Detects artificially smoothed lexical choices and semantic patterns.
        """
        words = text.lower().split()
        if len(words) < 30:
            return {"anomaly_detected": False, "reason": "Insufficient words"}
        
        # Analyze word complexity distribution
        complexity_scores = [self._calculate_word_complexity(word) for word in words]
        complexity_variance = statistics.variance(complexity_scores) if len(complexity_scores) > 1 else 0
        
        # Analyze semantic diversity
        semantic_diversity = self._calculate_semantic_diversity(words)
        
        # Analyze transition patterns
        transition_smoothness = self._analyze_transition_patterns(words)
        
        # Calculate lexical smoothing score
        smoothing_score = self._calculate_lexical_smoothing_score(
            complexity_variance,
            semantic_diversity,
            transition_smoothness
        )
        
        return {
            "anomaly_detected": smoothing_score > 0.7,
            "lexical_smoothing_score": round(smoothing_score, 4),
            "complexity_variance": round(complexity_variance, 4),
            "semantic_diversity": round(semantic_diversity, 4),
            "transition_smoothness": round(transition_smoothness, 4)
        }
    
    def _calculate_deception_confidence(self, analyses: List[Dict[str, Any]]) -> float:
        """
        Calculate overall deception confidence based on multiple anomaly analyses.
        """
        anomaly_scores = []
        
        for analysis in analyses:
            if analysis.get("anomaly_detected", False):
                # Extract relevant scores for confidence calculation
                if "smoothing_score" in analysis:
                    anomaly_scores.append(analysis["smoothing_score"])
                elif "uniformity_score" in analysis:
                    anomaly_scores.append(analysis["uniformity_score"])
                elif "lexical_smoothing_score" in analysis:
                    anomaly_scores.append(analysis["lexical_smoothing_score"])
                elif "burstiness_score" in analysis:
                    # Invert burstiness score (lower is more suspicious)
                    burstiness_score = analysis.get("burstiness_score", 0)
                    anomaly_scores.append(max(0, 1.0 - (burstiness_score / 5.0)))
        
        if not anomaly_scores:
            return 0.0
        
        # Calculate weighted confidence
        max_score = max(anomaly_scores)
        mean_score = statistics.mean(anomaly_scores)
        
        # High confidence if multiple strong anomalies or one very strong anomaly
        if len(anomaly_scores) >= 2 and mean_score > 0.6:
            confidence = min(1.0, mean_score * 1.2)
        elif max_score > 0.8:
            confidence = max_score
        else:
            confidence = mean_score * 0.8
        
        return confidence
    
    # Helper methods
    
    def _split_into_segments(self, text: str, segment_size: int = 100) -> List[str]:
        """Split text into segments of specified size."""
        words = text.split()
        segments = []
        for i in range(0, len(words), segment_size):
            segment = ' '.join(words[i:i + segment_size])
            segments.append(segment)
        return segments
    
    def _calculate_segment_entropy(self, segment: str) -> float:
        """Calculate Shannon entropy for a text segment."""
        if not segment:
            return 0.0
        
        # Character-level entropy
        counter = Counter(segment)
        length = len(segment)
        entropy = 0.0
        
        for count in counter.values():
            p = count / length
            entropy -= p * math.log2(p)
        
        return entropy
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _analyze_punctuation_pattern(self, text: str) -> float:
        """Analyze uniformity of punctuation usage."""
        punctuation = re.findall(r'[.,;:!?]', text)
        if not punctuation:
            return 0.0
        
        # Calculate distribution of punctuation types
        punct_counts = Counter(punctuation)
        total = len(punctuation)
        
        # Calculate entropy of punctuation distribution
        entropy = 0.0
        for count in punct_counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        
        # Normalize to 0-1 (max entropy for uniform distribution)
        max_entropy = math.log2(len(punct_counts)) if punct_counts else 1.0
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _analyze_structural_pattern(self, text: str) -> float:
        """Analyze uniformity of structural patterns."""
        sentences = self._split_into_sentences(text)
        if len(sentences) < 3:
            return 0.0
        
        # Analyze sentence starter patterns
        starters = []
        for sentence in sentences:
            words = sentence.strip().split()
            if words:
                starters.append(words[0].lower())
        
        starter_counts = Counter(starters)
        total_starters = len(starters)
        
        if total_starters == 0:
            return 0.0
        
        # Calculate uniformity of sentence starters
        entropy = 0.0
        for count in starter_counts.values():
            p = count / total_starters
            entropy -= p * math.log2(p)
        
        max_entropy = math.log2(len(starter_counts)) if starter_counts else 1.0
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _calculate_uniformity_score(self, type_token_ratio: float, 
                                  punct_uniformity: float, 
                                  struct_uniformity: float) -> float:
        """Calculate overall uniformity score."""
        # High type-token ratio + high uniformity = suspicious
        # Normalize type-token ratio (higher is more uniform)
        normalized_ttr = min(1.0, type_token_ratio * 2.0)  # Assume max reasonable TTR is 0.5
        
        # Combine scores
        return (normalized_ttr + punct_uniformity + struct_uniformity) / 3.0
    
    def _calculate_word_complexity(self, word: str) -> float:
        """Calculate complexity score for a word."""
        # Simple complexity measure: length + syllable-like patterns
        length_score = min(1.0, len(word) / 10.0)
        
        # Count vowel groups as rough syllable estimate
        vowel_groups = len(re.findall(r'[aeiouy]+', word.lower()))
        syllable_score = min(1.0, vowel_groups / 3.0)
        
        return (length_score + syllable_score) / 2.0
    
    def _calculate_semantic_diversity(self, words: List[str]) -> float:
        """Calculate semantic diversity of word usage."""
        # Simple measure: type-token ratio with semantic grouping
        # Group similar words (basic stemming)
        stemmed_words = set()
        for word in words:
            # Basic stemming
            if word.endswith('ing'):
                stemmed = word[:-3]
            elif word.endswith('ed'):
                stemmed = word[:-2]
            elif word.endswith('s'):
                stemmed = word[:-1]
            else:
                stemmed = word
            stemmed_words.add(stemmed)
        
        return len(stemmed_words) / len(words) if words else 0.0
    
    def _analyze_transition_patterns(self, words: List[str]) -> float:
        """Analyze smoothness of word transitions."""
        if len(words) < 5:
            return 0.0
        
        # Calculate transition entropy
        transitions = []
        for i in range(len(words) - 1):
            transition = (words[i], words[i + 1])
            transitions.append(transition)
        
        if not transitions:
            return 0.0
        
        transition_counts = Counter(transitions)
        total_transitions = len(transitions)
        
        entropy = 0.0
        for count in transition_counts.values():
            p = count / total_transitions
            entropy -= p * math.log2(p)
        
        max_entropy = math.log2(len(transition_counts)) if transition_counts else 1.0
        return entropy / max_entropy if max_entropy > 0 else 0.0
    
    def _calculate_lexical_smoothing_score(self, complexity_variance: float,
                                         semantic_diversity: float,
                                         transition_smoothness: float) -> float:
        """Calculate overall lexical smoothing score."""
        # Low complexity variance + low semantic diversity + high transition smoothness = suspicious
        complexity_score = 1.0 - min(1.0, complexity_variance * 2.0)  # Invert: low variance = high score
        semantic_score = 1.0 - semantic_diversity  # Invert: low diversity = high score
        
        # Combine scores
        return (complexity_score + semantic_score + transition_smoothness) / 3.0