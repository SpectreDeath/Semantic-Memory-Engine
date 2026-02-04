"""
Rhetorical Behavior Audit Extension

Analyzes text for rhetorical anomalies including sentiment volatility,
synthetic repetitiveness, and deceptive language patterns.
"""

import re
import logging
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from collections import Counter

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
except ImportError as e:
    print(f"⚠️  Missing dependencies for Rhetorical Behavior Audit: {e}")
    print("Please install required packages: pip install nltk")


# Configure logging for the rhetorical behavior audit
logger = logging.getLogger('behavior_audit.rhetorical_behavior_audit')
logger.setLevel(logging.INFO)

# Create file handler for rhetorical behavior audit events
behavior_handler = logging.FileHandler('rhetorical_behavior_audit_events.log')
behavior_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
behavior_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(behavior_handler)


@dataclass
class RhetoricalAnalysis:
    """Result of rhetorical behavior analysis."""
    sentiment_volatility: float
    type_token_ratio: float
    lexical_diversity_score: float
    emphatic_qualifiers_count: int
    non_contracted_denials_count: int
    synthetic_repetitiveness_score: float
    deceptive_indicators: List[str]
    anomaly_detected: bool
    confidence_score: float
    timestamp: datetime


class RhetoricalBehaviorAuditor:
    """Audits text for rhetorical anomalies and deceptive patterns."""
    
    def __init__(self):
        # Initialize NLTK resources
        try:
            nltk.download('vader_lexicon', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.sia = SentimentIntensityAnalyzer()
            self.stop_words = set(stopwords.words('english'))
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize NLTK resources: {e}")
            self.sia = None
            self.stop_words = set()
        
        # Emphatic qualifiers that may indicate deceptive synthesis
        self.emphatic_qualifiers = {
            'in all candor', 'to be perfectly honest', 'frankly speaking', 'truthfully',
            'to tell the truth', 'honestly', 'in truth', 'to be completely frank',
            'let me be clear', 'without exaggeration', 'to say the least', 'needless to say',
            'obviously', 'clearly', 'undoubtedly', 'certainly', 'indeed', 'in fact',
            'as a matter of fact', 'to be sure', 'indeed', 'truly', 'absolutely',
            'definitely', 'certainly', 'surely', 'undoubtedly', 'without question'
        }
        
        # Non-contracted denials that may indicate deception
        self.non_contracted_denials = {
            'i do not', 'i cannot', 'i will not', 'i would not', 'i could not', 'i should not',
            'i am not', 'i was not', 'i were not', 'i have not', 'i had not', 'i will not',
            'i would not', 'i could not', 'i should not', 'i might not', 'i must not',
            'i shall not', 'i can not', 'i will not', 'i would not', 'i could not',
            'i should not', 'i might not', 'i must not', 'i shall not', 'i do not think',
            'i do not believe', 'i do not know', 'i do not understand', 'i do not agree',
            'i do not accept', 'i do not approve', 'i do not like', 'i do not want',
            'i do not need', 'i do not care', 'i do not mind', 'i do not remember',
            'i do not recall', 'i do not recognize', 'i do not acknowledge', 'i do not admit',
            'i do not confess', 'i do not concede', 'i do not grant', 'i do not permit',
            'i do not allow', 'i do not enable', 'i do not facilitate', 'i do not support',
            'i do not endorse', 'i do not approve', 'i do not validate', 'i do not confirm',
            'i do not verify', 'i do not authenticate', 'i do not certify', 'i do not guarantee',
            'i do not promise', 'i do not assure', 'i do not guarantee', 'i do not warrant',
            'i do not assure', 'i do not promise', 'i do not guarantee', 'i do not warrant'
        }
    
    def analyze_sentiment_volatility(self, text: str) -> float:
        """
        Analyze sentiment volatility in the text.
        
        Args:
            text: Text to analyze.
            
        Returns:
            Sentiment volatility score (0-1, higher = more volatile).
        """
        if not self.sia:
            return 0.0
        
        sentences = sent_tokenize(text)
        if len(sentences) < 2:
            return 0.0
        
        sentiment_scores = []
        for sentence in sentences:
            if sentence.strip():
                score = self.sia.polarity_scores(sentence)['compound']
                sentiment_scores.append(score)
        
        if len(sentiment_scores) < 2:
            return 0.0
        
        # Calculate standard deviation of sentiment scores
        mean_score = sum(sentiment_scores) / len(sentiment_scores)
        variance = sum((score - mean_score) ** 2 for score in sentiment_scores) / len(sentiment_scores)
        volatility = math.sqrt(variance)
        
        # Normalize to 0-1 range (assuming max reasonable volatility is 2.0)
        normalized_volatility = min(volatility / 2.0, 1.0)
        
        return round(normalized_volatility, 3)
    
    def calculate_type_token_ratio(self, text: str) -> float:
        """
        Calculate Type-Token Ratio (TTR) for lexical diversity analysis.
        
        Args:
            text: Text to analyze.
            
        Returns:
            Type-Token Ratio (0-1, higher = more diverse).
        """
        # Tokenize and clean text
        tokens = word_tokenize(text.lower())
        tokens = [token for token in tokens if token.isalpha() and token not in self.stop_words]
        
        if len(tokens) == 0:
            return 0.0
        
        # Calculate TTR
        unique_tokens = set(tokens)
        ttr = len(unique_tokens) / len(tokens)
        
        return round(ttr, 3)
    
    def analyze_synthetic_repetitiveness(self, text: str) -> float:
        """
        Analyze synthetic repetitiveness using various repetition metrics.
        
        Args:
            text: Text to analyze.
            
        Returns:
            Synthetic repetitiveness score (0-1, higher = more repetitive).
        """
        tokens = word_tokenize(text.lower())
        tokens = [token for token in tokens if token.isalpha()]
        
        if len(tokens) < 10:
            return 0.0
        
        # Calculate various repetition metrics
        token_counts = Counter(tokens)
        
        # Repetition ratio (tokens appearing more than once)
        repeated_tokens = sum(1 for count in token_counts.values() if count > 1)
        repetition_ratio = repeated_tokens / len(token_counts)
        
        # Average token frequency
        avg_frequency = sum(token_counts.values()) / len(token_counts)
        
        # Calculate repetitiveness score
        # High repetition ratio + high average frequency = high synthetic repetitiveness
        repetitiveness_score = (repetition_ratio * 0.6) + (min(avg_frequency / 10.0, 1.0) * 0.4)
        
        return round(repetitiveness_score, 3)
    
    def detect_emphatic_qualifiers(self, text: str) -> List[str]:
        """
        Detect emphatic qualifiers in the text.
        
        Args:
            text: Text to analyze.
            
        Returns:
            List of detected emphatic qualifiers.
        """
        text_lower = text.lower()
        detected_qualifiers = []
        
        for qualifier in self.emphatic_qualifiers:
            if qualifier in text_lower:
                detected_qualifiers.append(qualifier)
        
        return detected_qualifiers
    
    def detect_non_contracted_denials(self, text: str) -> List[str]:
        """
        Detect non-contracted denials in the text.
        
        Args:
            text: Text to analyze.
            
        Returns:
            List of detected non-contracted denials.
        """
        text_lower = text.lower()
        detected_denials = []
        
        for denial in self.non_contracted_denials:
            if denial in text_lower:
                detected_denials.append(denial)
        
        return detected_denials
    
    def calculate_lexical_diversity_score(self, ttr: float) -> float:
        """
        Calculate lexical diversity score based on TTR.
        
        Args:
            ttr: Type-Token Ratio.
            
        Returns:
            Lexical diversity score (0-1, higher = more diverse).
        """
        # TTR interpretation:
        # > 0.7: Very high diversity
        # 0.5-0.7: High diversity
        # 0.3-0.5: Medium diversity
        # 0.1-0.3: Low diversity
        # < 0.1: Very low diversity
        
        if ttr >= 0.7:
            return 1.0
        elif ttr >= 0.5:
            return 0.8
        elif ttr >= 0.3:
            return 0.6
        elif ttr >= 0.1:
            return 0.3
        else:
            return 0.1
    
    def audit_rhetorical_behavior(self, text: str) -> RhetoricalAnalysis:
        """
        Main function to audit rhetorical behavior in text.
        
        Args:
            text: Text to analyze for rhetorical anomalies.
            
        Returns:
            RhetoricalAnalysis containing all analysis results.
        """
        print(f"🔍 Starting rhetorical behavior audit for text length: {len(text)} characters")
        
        # Step 1: Sentiment volatility analysis
        sentiment_volatility = self.analyze_sentiment_volatility(text)
        print(f"📊 Sentiment volatility: {sentiment_volatility}")
        
        # Step 2: Type-Token Ratio analysis
        ttr = self.calculate_type_token_ratio(text)
        lexical_diversity_score = self.calculate_lexical_diversity_score(ttr)
        print(f"🔤 Type-Token Ratio: {ttr}, Lexical diversity: {lexical_diversity_score}")
        
        # Step 3: Synthetic repetitiveness analysis
        synthetic_repetitiveness_score = self.analyze_synthetic_repetitiveness(text)
        print(f"🔄 Synthetic repetitiveness: {synthetic_repetitiveness_score}")
        
        # Step 4: Emphatic qualifiers detection
        emphatic_qualifiers = self.detect_emphatic_qualifiers(text)
        emphatic_count = len(emphatic_qualifiers)
        print(f"💬 Emphatic qualifiers detected: {emphatic_count}")
        
        # Step 5: Non-contracted denials detection
        non_contracted_denials = self.detect_non_contracted_denials(text)
        denial_count = len(non_contracted_denials)
        print(f"🚫 Non-contracted denials detected: {denial_count}")
        
        # Step 6: Determine if rhetorical anomaly detected
        anomaly_detected = self._detect_rhetorical_anomaly(
            lexical_diversity_score, emphatic_count, synthetic_repetitiveness_score
        )
        
        # Step 7: Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            sentiment_volatility, lexical_diversity_score, emphatic_count, 
            denial_count, synthetic_repetitiveness_score, anomaly_detected
        )
        
        # Step 8: Log results
        if anomaly_detected:
            message = "[Rhetorical Anomaly: High Probability of Deceptive Synthesis]"
            logger.warning(message)
            print(f"🚨 {message}")
        
        analysis = RhetoricalAnalysis(
            sentiment_volatility=sentiment_volatility,
            type_token_ratio=ttr,
            lexical_diversity_score=lexical_diversity_score,
            emphatic_qualifiers_count=emphatic_count,
            non_contracted_denials_count=denial_count,
            synthetic_repetitiveness_score=synthetic_repetitiveness_score,
            deceptive_indicators=emphatic_qualifiers + non_contracted_denials,
            anomaly_detected=anomaly_detected,
            confidence_score=confidence_score,
            timestamp=datetime.now()
        )
        
        return analysis
    
    def _detect_rhetorical_anomaly(self, lexical_diversity: float, emphatic_count: int, 
                                 synthetic_repetitiveness: float) -> bool:
        """
        Detect rhetorical anomaly based on analysis criteria.
        
        Criteria: Low Lexical Diversity + High Emphatic Qualifiers
        """
        low_lexical_diversity = lexical_diversity < 0.5
        high_emphatic_qualifiers = emphatic_count >= 2
        high_synthetic_repetitiveness = synthetic_repetitiveness > 0.7
        
        # Anomaly detected if:
        # (Low lexical diversity AND high emphatic qualifiers) OR
        # (Low lexical diversity AND high synthetic repetitiveness)
        anomaly = (low_lexical_diversity and high_emphatic_qualifiers) or \
                 (low_lexical_diversity and high_synthetic_repetitiveness)
        
        return anomaly
    
    def _calculate_confidence_score(self, sentiment_volatility: float, lexical_diversity: float,
                                  emphatic_count: int, denial_count: int, 
                                  synthetic_repetitiveness: float, anomaly_detected: bool) -> float:
        """
        Calculate overall confidence score for rhetorical anomaly detection.
        """
        score = 0.0
        
        # Base score for anomaly detection
        if anomaly_detected:
            score += 0.5
        
        # Score for high sentiment volatility
        if sentiment_volatility > 0.5:
            score += 0.2
        
        # Score for low lexical diversity
        if lexical_diversity < 0.3:
            score += 0.2
        
        # Score for high emphatic qualifiers
        if emphatic_count >= 3:
            score += 0.2
        
        # Score for high synthetic repetitiveness
        if synthetic_repetitiveness > 0.8:
            score += 0.2
        
        # Score for high denial count
        if denial_count >= 3:
            score += 0.1
        
        return min(score, 1.0)


def audit_rhetorical_behavior(text: str) -> Dict[str, Any]:
    """
    Main function to audit rhetorical behavior in text.
    
    Args:
        text: Text to analyze for rhetorical anomalies.
        
    Returns:
        Dictionary containing analysis results.
    """
    auditor = RhetoricalBehaviorAuditor()
    result = auditor.audit_rhetorical_behavior(text)
    
    return {
        'sentiment_volatility': result.sentiment_volatility,
        'type_token_ratio': result.type_token_ratio,
        'lexical_diversity_score': result.lexical_diversity_score,
        'emphatic_qualifiers_count': result.emphatic_qualifiers_count,
        'non_contracted_denials_count': result.non_contracted_denials_count,
        'synthetic_repetitiveness_score': result.synthetic_repetitiveness_score,
        'deceptive_indicators': result.deceptive_indicators,
        'anomaly_detected': result.anomaly_detected,
        'confidence_score': round(result.confidence_score, 2),
        'timestamp': result.timestamp.isoformat(),
        'status': 'RHETORICAL_ANOMALY_DETECTED' if result.anomaly_detected else 'NO_ANOMALY_FOUND'
    }


# Export the main function for use as a tool
__all__ = ['audit_rhetorical_behavior', 'RhetoricalBehaviorAuditor', 'RhetoricalAnalysis']