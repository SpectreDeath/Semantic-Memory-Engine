"""
Sentiment & Emotion Analysis Module
====================================

Phase 5 component for detailed emotional analysis of text.
Provides sentiment scoring, emotion detection, and subjective language analysis.

Features:
- Multi-perspective sentiment analysis (TextBlob, VADER)
- Emotion detection (joy, anger, fear, sadness, surprise, trust)
- Subjectivity scoring
- Sentiment trend analysis for longer texts
- Confidence scoring
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import re

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    from nltk.sentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

logger = logging.getLogger(__name__)


class SentimentPolarity(Enum):
    """Sentiment classification categories."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class EmotionType(Enum):
    """Basic emotion categories (Ekman's 6 basic emotions)."""
    JOY = "joy"
    ANGER = "anger"
    FEAR = "fear"
    SADNESS = "sadness"
    SURPRISE = "surprise"
    TRUST = "trust"


@dataclass
class EmotionScore:
    """Score for a single emotion."""
    emotion: EmotionType
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    keywords: List[str]  # Words contributing to this emotion


@dataclass
class SentimentAnalysis:
    """Complete sentiment analysis result."""
    text: str
    polarity: SentimentPolarity
    polarity_score: float  # -1.0 to 1.0
    subjectivity: float  # 0.0 to 1.0 (objectivity)
    confidence: float  # 0.0 to 1.0
    emotions: Dict[EmotionType, EmotionScore]
    dominant_emotion: Optional[EmotionType]
    sentiment_keywords: List[str]
    intensity: float  # 0.0 to 1.0 (strength of sentiment)
    is_sarcastic: bool
    is_mixed: bool  # Multiple conflicting sentiments
    comparative: float  # Sentiment per word
    

@dataclass
class SentimentTrend:
    """Sentiment progression through text segments."""
    segments: List[str]
    sentiment_scores: List[float]
    polarity_progression: List[SentimentPolarity]
    trend_direction: str  # "increasing", "decreasing", "stable"
    volatility: float  # 0.0 to 1.0


class SentimentAnalyzer:
    """Comprehensive sentiment and emotion analysis engine."""
    
    # Emotion keyword mappings
    EMOTION_KEYWORDS = {
        EmotionType.JOY: {
            'positive': ['happy', 'joy', 'love', 'amazing', 'wonderful', 'great', 
                        'excellent', 'fantastic', 'delightful', 'cheerful', 'blessed'],
            'negative': ['sad', 'miserable', 'heartbroken']
        },
        EmotionType.ANGER: {
            'positive': ['fury', 'enraged', 'furious', 'livid', 'angry', 'mad',
                        'infuriated', 'outraged', 'incensed'],
            'negative': ['calm', 'peaceful', 'serene']
        },
        EmotionType.FEAR: {
            'positive': ['scared', 'afraid', 'terrified', 'frightened', 'anxious',
                        'nervous', 'worried', 'fearful', 'dread'],
            'negative': ['brave', 'courageous', 'confident']
        },
        EmotionType.SADNESS: {
            'positive': ['sad', 'unhappy', 'miserable', 'depressed', 'sorrowful',
                        'gloomy', 'melancholy', 'grief', 'mourning'],
            'negative': ['happy', 'joyful', 'cheerful']
        },
        EmotionType.SURPRISE: {
            'positive': ['surprised', 'shocked', 'amazed', 'astounded', 'startled',
                        'astonished', 'stunned', 'bewildered'],
            'negative': []
        },
        EmotionType.TRUST: {
            'positive': ['trust', 'confident', 'believe', 'faith', 'reliable',
                        'sincere', 'honest', 'loyal', 'dedicated'],
            'negative': ['doubt', 'skeptical', 'suspicious']
        }
    }
    
    # Sarcasm indicators
    SARCASM_PATTERNS = [
        r'\b(yeah|right|sure|great|wonderful)\b.*\b(not|hate|terrible|awful)\b',
        r'\b(oh|wow)\b\s+\b(how|so|very)\b.*\b(great|amazing|wonderful)\b',
        r'(?:.*?)(good|great|best|perfect)(?:.*?)(way to|now|just)',
    ]
    
    def __init__(self):
        """Initialize sentiment analyzer with available backends."""
        self.has_textblob = TEXTBLOB_AVAILABLE
        self.has_vader = VADER_AVAILABLE
        
        if self.has_vader:
            self.vader = SentimentIntensityAnalyzer()
        
        if not (self.has_textblob or self.has_vader):
            logger.warning("No sentiment analysis backends available. Install textblob or nltk[vader]")
    
    def analyze(self, text: str) -> SentimentAnalysis:
        """Perform complete sentiment analysis on text."""
        if not text or not text.strip():
            return self._create_neutral_analysis(text)
        
        # Polarity scoring
        polarity_score = self._calculate_polarity(text)
        polarity = self._score_to_polarity(polarity_score)
        
        # Subjectivity
        subjectivity = self._calculate_subjectivity(text)
        
        # Emotion detection
        emotions = self._detect_emotions(text)
        dominant_emotion = max(emotions.items(), key=lambda x: x[1].score)[0]
        
        # Extract keywords
        sentiment_keywords = self._extract_sentiment_keywords(text)
        
        # Calculate metrics
        intensity = self._calculate_intensity(text, polarity_score, emotions)
        confidence = self._calculate_confidence(polarity_score, subjectivity)
        
        # Sarcasm detection
        is_sarcastic = self._detect_sarcasm(text)
        
        # Mixed sentiment detection
        is_mixed = self._detect_mixed_sentiment(emotions)
        
        # Comparative (sentiment per word)
        comparative = polarity_score / max(len(text.split()), 1)
        
        return SentimentAnalysis(
            text=text,
            polarity=polarity,
            polarity_score=polarity_score,
            subjectivity=subjectivity,
            confidence=confidence,
            emotions=emotions,
            dominant_emotion=dominant_emotion,
            sentiment_keywords=sentiment_keywords,
            intensity=intensity,
            is_sarcastic=is_sarcastic,
            is_mixed=is_mixed,
            comparative=comparative
        )
    
    def analyze_trend(self, text: str, segment_size: int = 50) -> SentimentTrend:
        """Analyze sentiment progression through text segments."""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        if not sentences:
            sentences = [text]
        
        sentiment_scores = []
        polarity_progression = []
        
        for sentence in sentences:
            score = self._calculate_polarity(sentence)
            sentiment_scores.append(score)
            polarity_progression.append(self._score_to_polarity(score))
        
        # Determine trend direction
        if len(sentiment_scores) >= 2:
            if sentiment_scores[-1] > sentiment_scores[0] + 0.1:
                trend_direction = "increasing"
            elif sentiment_scores[-1] < sentiment_scores[0] - 0.1:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"
        
        # Calculate volatility
        if len(sentiment_scores) > 1:
            diffs = [abs(sentiment_scores[i+1] - sentiment_scores[i]) 
                    for i in range(len(sentiment_scores)-1)]
            volatility = sum(diffs) / len(diffs) if diffs else 0.0
        else:
            volatility = 0.0
        
        return SentimentTrend(
            segments=sentences,
            sentiment_scores=sentiment_scores,
            polarity_progression=polarity_progression,
            trend_direction=trend_direction,
            volatility=volatility
        )
    
    def _calculate_polarity(self, text: str) -> float:
        """Calculate polarity score using available backends."""
        if not text.strip():
            return 0.0
        
        if self.has_vader:
            scores = self.vader.polarity_scores(text)
            return scores.get('compound', 0.0)
        
        if self.has_textblob:
            blob = TextBlob(text)
            return blob.sentiment.polarity
        
        return 0.0
    
    def _calculate_subjectivity(self, text: str) -> float:
        """Calculate subjectivity score."""
        if not self.has_textblob or not text.strip():
            # Simple heuristic: count subjective words
            subjective_words = ['think', 'feel', 'believe', 'opinion', 'my', 'i',
                              'seemed', 'appears', 'looks', 'sounds']
            count = sum(1 for word in text.lower().split() if word in subjective_words)
            return min(count / max(len(text.split()), 1), 1.0)
        
        blob = TextBlob(text)
        return blob.sentiment.subjectivity
    
    def _detect_emotions(self, text: str) -> Dict[EmotionType, EmotionScore]:
        """Detect emotions in text."""
        text_lower = text.lower()
        emotions = {}
        
        for emotion_type, keywords_dict in self.EMOTION_KEYWORDS.items():
            positive_matches = [w for w in keywords_dict['positive'] if w in text_lower]
            negative_matches = [w for w in keywords_dict['negative'] if w in text_lower]
            
            score = (len(positive_matches) - len(negative_matches)) / max(
                len(positive_matches) + len(negative_matches), 1
            )
            score = max(0.0, min(score, 1.0))
            
            # Confidence based on keyword presence
            total_keywords = len(positive_matches) + len(negative_matches)
            confidence = min(total_keywords * 0.1, 1.0)
            
            all_keywords = positive_matches + negative_matches
            
            emotions[emotion_type] = EmotionScore(
                emotion=emotion_type,
                score=score,
                confidence=confidence,
                keywords=all_keywords
            )
        
        return emotions
    
    def _extract_sentiment_keywords(self, text: str) -> List[str]:
        """Extract sentiment-bearing keywords."""
        all_keywords = []
        for emotion_keywords in self.EMOTION_KEYWORDS.values():
            all_keywords.extend(emotion_keywords['positive'])
            all_keywords.extend(emotion_keywords['negative'])
        
        text_lower = text.lower()
        found = [word for word in all_keywords if word in text_lower]
        return list(set(found))
    
    def _calculate_intensity(self, text: str, polarity: float, 
                            emotions: Dict[EmotionType, EmotionScore]) -> float:
        """Calculate overall sentiment intensity."""
        # Factor 1: Polarity magnitude
        polarity_intensity = abs(polarity)
        
        # Factor 2: Emotion confidence
        emotion_intensity = sum(e.confidence for e in emotions.values()) / len(emotions)
        
        # Factor 3: Keyword density
        keywords = self._extract_sentiment_keywords(text)
        keyword_density = len(keywords) / max(len(text.split()), 1)
        
        # Combined intensity
        intensity = (polarity_intensity * 0.5 + emotion_intensity * 0.3 + keyword_density * 0.2)
        return min(intensity, 1.0)
    
    def _calculate_confidence(self, polarity: float, subjectivity: float) -> float:
        """Calculate confidence in sentiment analysis."""
        # High confidence with clear polarity and subjectivity
        polarity_confidence = abs(polarity)
        subjectivity_confidence = subjectivity
        
        return (polarity_confidence * 0.7 + subjectivity_confidence * 0.3)
    
    def _detect_sarcasm(self, text: str) -> bool:
        """Detect potential sarcasm in text."""
        text_lower = text.lower()
        for pattern in self.SARCASM_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True
        return False
    
    def _detect_mixed_sentiment(self, emotions: Dict[EmotionType, EmotionScore]) -> bool:
        """Detect if text contains conflicting sentiments."""
        high_scores = [e.score for e in emotions.values() if e.score > 0.5]
        return len(high_scores) >= 2
    
    def _score_to_polarity(self, score: float) -> SentimentPolarity:
        """Convert numeric score to polarity category."""
        if score >= 0.6:
            return SentimentPolarity.VERY_POSITIVE
        elif score >= 0.2:
            return SentimentPolarity.POSITIVE
        elif score > -0.2:
            return SentimentPolarity.NEUTRAL
        elif score >= -0.6:
            return SentimentPolarity.NEGATIVE
        else:
            return SentimentPolarity.VERY_NEGATIVE
    
    def _create_neutral_analysis(self, text: str) -> SentimentAnalysis:
        """Create neutral sentiment analysis for empty text."""
        emotions = {e: EmotionScore(e, 0.0, 0.0, []) for e in EmotionType}
        return SentimentAnalysis(
            text=text,
            polarity=SentimentPolarity.NEUTRAL,
            polarity_score=0.0,
            subjectivity=0.0,
            confidence=0.0,
            emotions=emotions,
            dominant_emotion=None,
            sentiment_keywords=[],
            intensity=0.0,
            is_sarcastic=False,
            is_mixed=False,
            comparative=0.0
        )
