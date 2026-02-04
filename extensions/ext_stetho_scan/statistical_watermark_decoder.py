"""
Statistical Watermark Decoder Extension

Detects invisible unicode markers and performs Z-Score analysis on token frequency
to identify statistical watermarks in text content.
"""

import re
import logging
import unicodedata
import statistics
from typing import Dict, List, Tuple, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
from collections import Counter


# Configure logging for the watermark decoder
logger = logging.getLogger('stetho_scan.statistical_watermark_decoder')
logger.setLevel(logging.INFO)

# Create file handler for watermark detection events
watermark_handler = logging.FileHandler('watermark_detection_events.log')
watermark_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
watermark_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(watermark_handler)


@dataclass
class WatermarkDetection:
    """Result of watermark detection analysis."""
    has_invisible_markers: bool
    z_score_analysis: Dict[str, float]
    provider_signature: Optional[str]
    confidence_score: float
    detected_markers: List[str]
    timestamp: datetime


class StatisticalWatermarkDecoder:
    """Detects statistical watermarks using invisible unicode markers and Z-Score analysis."""
    
    def __init__(self):
        # Invisible Unicode markers commonly used in watermarking
        self.invisible_markers = {
            # Zero-width characters
            '\u200B': 'ZERO WIDTH SPACE',
            '\u200C': 'ZERO WIDTH NON-JOINER', 
            '\u200D': 'ZERO WIDTH JOINER',
            '\u200E': 'LEFT-TO-RIGHT MARK',
            '\u200F': 'RIGHT-TO-LEFT MARK',
            '\u202A': 'LEFT-TO-RIGHT EMBEDDING',
            '\u202B': 'RIGHT-TO-LEFT EMBEDDING',
            '\u202C': 'POP DIRECTIONAL FORMATTING',
            '\u202D': 'LEFT-TO-RIGHT OVERRIDE',
            '\u202E': 'RIGHT-TO-LEFT OVERRIDE',
            '\u2060': 'WORD JOINER',
            '\u2061': 'FUNCTION APPLICATION',
            '\u2062': 'INVISIBLE TIMES',
            '\u2063': 'INVISIBLE SEPARATOR',
            '\uFEFF': 'ZERO WIDTH NO-BREAK SPACE (BOM)',
            
            # Other potentially invisible characters
            '\u034F': 'COMBINING GRAPHEME JOINER',
            '\u061C': 'ARABIC LETTER MARK',
            '\u180E': 'MONGOLIAN VOWEL SEPARATOR',
        }
        
        # Known provider signatures based on statistical patterns
        self.provider_signatures = {
            'OPENAI': {
                'common_tokens': ['the', 'of', 'and', 'to', 'a', 'in', 'is', 'it'],
                'expected_distribution': [0.05, 0.04, 0.035, 0.03, 0.025, 0.02, 0.015, 0.01],
                'z_score_threshold': 2.5
            },
            'GOOGLE': {
                'common_tokens': ['the', 'of', 'and', 'to', 'a', 'in', 'for', 'is'],
                'expected_distribution': [0.048, 0.042, 0.038, 0.032, 0.028, 0.022, 0.018, 0.014],
                'z_score_threshold': 2.2
            },
            'ANTHROPIC': {
                'common_tokens': ['the', 'of', 'and', 'to', 'a', 'in', 'that', 'is'],
                'expected_distribution': [0.052, 0.045, 0.032, 0.035, 0.026, 0.024, 0.016, 0.013],
                'z_score_threshold': 2.8
            },
            'META': {
                'common_tokens': ['the', 'of', 'and', 'to', 'a', 'in', 'is', 'for'],
                'expected_distribution': [0.046, 0.041, 0.036, 0.033, 0.027, 0.023, 0.017, 0.019],
                'z_score_threshold': 2.0
            }
        }
        
        # Character frequency analysis for additional watermark detection
        self.english_letter_freq = {
            'e': 12.70, 't': 9.06, 'a': 8.17, 'o': 7.51, 'i': 6.97, 'n': 6.75,
            's': 6.33, 'h': 6.09, 'r': 5.99, 'd': 4.25, 'l': 4.03, 'c': 2.78,
            'u': 2.76, 'm': 2.41, 'w': 2.36, 'f': 2.23, 'g': 2.02, 'y': 1.97,
            'p': 1.93, 'b': 1.29, 'v': 0.98, 'k': 0.77, 'j': 0.15, 'x': 0.15,
            'q': 0.10, 'z': 0.07
        }
    
    def detect_invisible_markers(self, text: str) -> List[str]:
        """
        Detect invisible unicode markers in text.
        
        Args:
            text: Text to analyze for invisible markers.
            
        Returns:
            List of detected invisible markers.
        """
        detected_markers = []
        
        for char in text:
            if char in self.invisible_markers:
                detected_markers.append(char)
                logger.info(f"Invisible marker detected: {repr(char)} - {self.invisible_markers[char]}")
        
        return detected_markers
    
    def tokenize_text(self, text: str) -> List[str]:
        """
        Tokenize text into words, filtering out punctuation and normalizing.
        
        Args:
            text: Text to tokenize.
            
        Returns:
            List of tokens.
        """
        # Remove punctuation and convert to lowercase
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Split into tokens and filter out empty strings
        tokens = [token.strip() for token in text.split() if token.strip()]
        
        return tokens
    
    def calculate_z_scores(self, tokens: List[str]) -> Dict[str, float]:
        """
        Calculate Z-Scores for token frequencies.
        
        Args:
            tokens: List of tokens from the text.
            
        Returns:
            Dictionary mapping tokens to their Z-Scores.
        """
        if not tokens:
            return {}
        
        # Calculate token frequencies
        token_counts = Counter(tokens)
        total_tokens = len(tokens)
        
        # Calculate frequency distribution
        token_frequencies = {token: count / total_tokens 
                           for token, count in token_counts.items()}
        
        # Calculate mean and standard deviation for common tokens
        common_tokens = ['the', 'of', 'and', 'to', 'a', 'in', 'is', 'it', 'for', 'that']
        observed_freqs = [token_frequencies.get(token, 0) for token in common_tokens]
        
        if len(observed_freqs) < 2:
            return {}
        
        mean_freq = statistics.mean(observed_freqs)
        std_dev = statistics.stdev(observed_freqs) if len(observed_freqs) > 1 else 0.01
        
        # Calculate Z-Scores
        z_scores = {}
        for token in token_frequencies:
            if token in common_tokens:
                freq = token_frequencies[token]
                z_score = (freq - mean_freq) / std_dev if std_dev > 0 else 0
                z_scores[token] = z_score
        
        return z_scores
    
    def analyze_provider_signature(self, z_scores: Dict[str, float]) -> Optional[str]:
        """
        Analyze Z-Scores to identify potential provider signatures.
        
        Args:
            z_scores: Dictionary of token Z-Scores.
            
        Returns:
            Provider name if signature detected, None otherwise.
        """
        best_match = None
        best_score = float('inf')
        
        for provider, signature in self.provider_signatures.items():
            # Calculate match score based on Z-Score patterns
            match_score = 0
            common_tokens = signature['common_tokens']
            
            for i, token in enumerate(common_tokens):
                if token in z_scores:
                    expected_z = signature['z_score_threshold']
                    actual_z = abs(z_scores[token])
                    
                    # Calculate difference from expected pattern
                    diff = abs(actual_z - expected_z)
                    match_score += diff
            
            if match_score < best_score:
                best_score = match_score
                best_match = provider
        
        # Only return match if it's significant enough
        if best_score < 5.0:  # Threshold for significant match
            return best_match
        
        return None
    
    def analyze_character_frequency(self, text: str) -> Dict[str, float]:
        """
        Analyze character frequency for additional watermark detection.
        
        Args:
            text: Text to analyze.
            
        Returns:
            Dictionary of character frequency deviations.
        """
        # Count letter frequencies
        letter_counts = Counter()
        total_letters = 0
        
        for char in text.lower():
            if char.isalpha():
                letter_counts[char] += 1
                total_letters += 1
        
        if total_letters == 0:
            return {}
        
        # Calculate frequencies and deviations
        freq_deviations = {}
        for char, count in letter_counts.items():
            observed_freq = (count / total_letters) * 100
            expected_freq = self.english_letter_freq.get(char, 0)
            deviation = observed_freq - expected_freq
            freq_deviations[char] = deviation
        
        return freq_deviations
    
    def detect_watermark_pulse(self, text: str) -> WatermarkDetection:
        """
        Main function to detect statistical watermarks in text.
        
        Args:
            text: Text to analyze for watermarks.
            
        Returns:
            WatermarkDetection result containing analysis results.
        """
        print(f"🔍 Starting watermark detection for text length: {len(text)} characters")
        
        # Step 1: Detect invisible markers
        detected_markers = self.detect_invisible_markers(text)
        has_invisible_markers = len(detected_markers) > 0
        
        if has_invisible_markers:
            print(f"⚠️  Found {len(detected_markers)} invisible markers")
        
        # Step 2: Tokenize and analyze
        tokens = self.tokenize_text(text)
        z_scores = self.calculate_z_scores(tokens)
        
        # Step 3: Analyze provider signature
        provider_signature = self.analyze_provider_signature(z_scores)
        
        # Step 4: Analyze character frequency
        char_deviations = self.analyze_character_frequency(text)
        
        # Step 5: Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            has_invisible_markers, 
            z_scores, 
            provider_signature,
            char_deviations
        )
        
        # Step 6: Log results
        if provider_signature:
            message = f"[PROVENANCE IDENTIFIED: {provider_signature} SIGNATURE FOUND]"
            logger.warning(message)
            print(f"🚨 {message}")
        
        detection = WatermarkDetection(
            has_invisible_markers=has_invisible_markers,
            z_score_analysis=z_scores,
            provider_signature=provider_signature,
            confidence_score=confidence_score,
            detected_markers=detected_markers,
            timestamp=datetime.now()
        )
        
        return detection
    
    def _calculate_confidence_score(self, has_markers: bool, z_scores: Dict[str, float], 
                                  provider: Optional[str], char_deviations: Dict[str, float]) -> float:
        """
        Calculate overall confidence score for watermark detection.
        
        Args:
            has_markers: Whether invisible markers were detected.
            z_scores: Z-Score analysis results.
            provider: Detected provider signature.
            char_deviations: Character frequency deviations.
            
        Returns:
            Confidence score between 0 and 1.
        """
        score = 0.0
        
        # Base score for invisible markers
        if has_markers:
            score += 0.4
        
        # Score for significant Z-Scores
        significant_z_scores = [z for z in z_scores.values() if abs(z) > 2.0]
        score += min(len(significant_z_scores) * 0.1, 0.3)
        
        # Score for provider signature
        if provider:
            score += 0.3
        
        # Score for character frequency deviations
        extreme_deviations = [dev for dev in char_deviations.values() if abs(dev) > 5.0]
        score += min(len(extreme_deviations) * 0.05, 0.2)
        
        return min(score, 1.0)


def detect_watermark_pulse(text: str) -> Dict[str, Any]:
    """
    Main function to detect watermarks in text.
    
    Args:
        text: Text to analyze for watermarks.
        
    Returns:
        Dictionary containing detection results.
    """
    decoder = StatisticalWatermarkDecoder()
    result = decoder.detect_watermark_pulse(text)
    
    return {
        'has_invisible_markers': result.has_invisible_markers,
        'z_score_analysis': result.z_score_analysis,
        'provider_signature': result.provider_signature,
        'confidence_score': round(result.confidence_score, 2),
        'detected_markers': [repr(marker) for marker in result.detected_markers],
        'timestamp': result.timestamp.isoformat(),
        'status': 'WATERMARK_DETECTED' if result.provider_signature else 'NO_WATERMARK_FOUND'
    }


# Export the main function for use as a tool
__all__ = ['detect_watermark_pulse', 'StatisticalWatermarkDecoder', 'WatermarkDetection']