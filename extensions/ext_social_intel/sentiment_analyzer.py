"""
Sentiment Analyzer

Advanced sentiment analysis component for social media content.
Provides multi-language sentiment detection, bias analysis, and
cross-platform sentiment correlation for disinformation detection.

Key Features:
- Multi-language sentiment analysis using transformer models
- Bias detection and analysis
- Cross-platform sentiment correlation
- Sentiment trend analysis over time
- Confidence scoring and uncertainty quantification
- Custom lexicon support for domain-specific analysis
"""

import logging
import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

logger = logging.getLogger("SME.SocialIntelligence.SentimentAnalyzer")

@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    text: str
    sentiment_score: float  # -1.0 to 1.0 (negative to positive)
    sentiment_label: str    # "negative", "neutral", "positive"
    confidence: float       # 0.0 to 1.0
    language: str
    bias_indicators: List[str]
    entities: List[str]
    keywords: List[str]

@dataclass
class SentimentTrend:
    """Sentiment trend over time."""
    platform: str
    topic: str
    time_points: List[datetime]
    sentiment_scores: List[float]
    volume: List[int]
    trend_direction: str  # "increasing", "decreasing", "stable"
    volatility: float

@dataclass
class SentimentCorrelation:
    """Cross-platform sentiment correlation."""
    platforms: List[str]
    correlation_matrix: Dict[str, Dict[str, float]]
    average_correlation: float
    outlier_platforms: List[str]
    correlation_strength: str  # "strong", "moderate", "weak"

class SentimentAnalyzer:
    """
    Advanced sentiment analysis component for social media content.
    
    Provides multi-language sentiment detection, bias analysis, and
    cross-platform sentiment correlation for disinformation detection.
    """
    
    def __init__(self):
        self.language_models = {}
        self.bias_lexicon = self._load_bias_lexicon()
        self.sentiment_lexicon = self._load_sentiment_lexicon()
        self.entity_extractor = self._initialize_entity_extractor()
        self.bias_patterns = self._compile_bias_patterns()
        
        logger.info("Sentiment Analyzer initialized")

    def _load_bias_lexicon(self) -> Dict[str, List[str]]:
        """Load bias detection lexicon."""
        return {
            "political_bias": [
                "left-wing", "right-wing", "conservative", "liberal", "progressive",
                "reactionary", "establishment", "mainstream", "alternative"
            ],
            "emotional_manipulation": [
                "fear", "anger", "hate", "panic", "outrage", "indignation",
                "disgust", "contempt", "loathing", "terror", "anxiety"
            ],
            "conspiracy_indicators": [
                "they", "them", "the elite", "the establishment", "mainstream media",
                "big pharma", "deep state", "globalists", "illuminati"
            ],
            "absolutist_language": [
                "always", "never", "everyone", "nobody", "completely", "totally",
                "absolutely", "definitely", "certainly", "undoubtedly"
            ]
        }

    def _load_sentiment_lexicon(self) -> Dict[str, float]:
        """Load sentiment lexicon with scores."""
        # This would typically load from a comprehensive sentiment lexicon
        # For now, we'll use a basic implementation
        return {
            # Positive words
            "good": 0.5, "great": 0.8, "excellent": 0.9, "amazing": 0.8,
            "wonderful": 0.7, "fantastic": 0.8, "love": 0.6, "like": 0.4,
            "happy": 0.6, "joy": 0.7, "pleased": 0.5, "satisfied": 0.6,
            "success": 0.7, "win": 0.6, "victory": 0.7, "triumph": 0.8,
            
            # Negative words
            "bad": -0.5, "terrible": -0.8, "awful": -0.9, "horrible": -0.8,
            "hate": -0.6, "dislike": -0.4, "angry": -0.6, "mad": -0.5,
            "sad": -0.6, "depressed": -0.7, "unhappy": -0.5, "disappointed": -0.6,
            "failure": -0.7, "lose": -0.6, "defeat": -0.7, "tragedy": -0.8,
            
            # Neutral words (would be filtered out)
            "the": 0.0, "and": 0.0, "or": 0.0, "but": 0.0, "is": 0.0,
            "are": 0.0, "was": 0.0, "were": 0.0, "be": 0.0, "been": 0.0
        }

    def _initialize_entity_extractor(self):
        """Initialize entity extraction patterns."""
        # This would typically use a more sophisticated NER model
        # For now, we'll use regex patterns
        return {
            "person": re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'),
            "organization": re.compile(r'\b(?:[A-Z][a-z]*\s*)+(?:Inc|Corp|Ltd|LLC|Co)\b'),
            "location": re.compile(r'\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]*)*)\b'),
            "hashtag": re.compile(r'#\w+'),
            "mention": re.compile(r'@\w+')
        }

    def _compile_bias_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for bias detection."""
        return {
            "emotional_manipulation": re.compile(
                r'\b(' + '|'.join(self.bias_lexicon["emotional_manipulation"]) + r')\b',
                re.IGNORECASE
            ),
            "conspiracy_indicators": re.compile(
                r'\b(' + '|'.join(self.bias_lexicon["conspiracy_indicators"]) + r')\b',
                re.IGNORECASE
            ),
            "absolutist_language": re.compile(
                r'\b(' + '|'.join(self.bias_lexicon["absolutist_language"]) + r')\b',
                re.IGNORECASE
            )
        }

    async def analyze_platform_sentiment(self, platform: str, content_data: Dict, 
                                       topic: str) -> Dict:
        """
        Analyze sentiment for content from a specific platform.
        
        Args:
            platform: Platform name
            content_data: Content data from the platform
            topic: Topic being analyzed
            
        Returns:
            Dict containing sentiment analysis results
        """
        try:
            # Extract text content
            posts = content_data.get("posts", [])
            texts = [post.get("text", "") for post in posts]
            
            if not texts:
                return {
                    "platform": platform,
                    "topic": topic,
                    "error": "No content to analyze"
                }
            
            # Analyze each post
            sentiment_results = []
            for text in texts:
                if text.strip():
                    result = await self._analyze_single_text(text)
                    sentiment_results.append(result)
            
            # Aggregate results
            aggregated = self._aggregate_sentiment_results(sentiment_results, platform, topic)
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error analyzing platform sentiment for {platform}: {e}")
            return {
                "platform": platform,
                "topic": topic,
                "error": str(e)
            }

    async def analyze_content_sentiment(self, content: List[Dict]) -> Dict:
        """
        Analyze sentiment for a list of content items.
        
        Args:
            content: List of content items with text
            
        Returns:
            Dict containing aggregated sentiment analysis
        """
        try:
            sentiment_results = []
            
            for item in content:
                text = item.get("text", "")
                if text.strip():
                    result = await self._analyze_single_text(text)
                    sentiment_results.append(result)
            
            if not sentiment_results:
                return {
                    "average_sentiment": 0.0,
                    "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                    "confidence": 0.0,
                    "total_analyzed": 0
                }
            
            # Calculate statistics
            scores = [result.sentiment_score for result in sentiment_results]
            average_sentiment = np.mean(scores)
            
            # Count sentiment distribution
            positive_count = sum(1 for s in scores if s > 0.1)
            negative_count = sum(1 for s in scores if s < -0.1)
            neutral_count = len(scores) - positive_count - negative_count
            
            # Calculate average confidence
            confidences = [result.confidence for result in sentiment_results]
            average_confidence = np.mean(confidences) if confidences else 0.0
            
            return {
                "average_sentiment": average_sentiment,
                "sentiment_distribution": {
                    "positive": positive_count,
                    "neutral": neutral_count,
                    "negative": negative_count
                },
                "confidence": average_confidence,
                "total_analyzed": len(sentiment_results),
                "details": [
                    {
                        "text": result.text[:100] + "..." if len(result.text) > 100 else result.text,
                        "sentiment_score": result.sentiment_score,
                        "sentiment_label": result.sentiment_label,
                        "confidence": result.confidence,
                        "bias_indicators": result.bias_indicators
                    }
                    for result in sentiment_results[:10]  # Limit to first 10 for summary
                ]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing content sentiment: {e}")
            return {
                "error": str(e),
                "average_sentiment": 0.0,
                "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "confidence": 0.0,
                "total_analyzed": 0
            }

    async def calculate_sentiment_correlation(self, platform1_data: Dict, 
                                            platform2_data: Dict) -> float:
        """
        Calculate sentiment correlation between two platforms.
        
        Args:
            platform1_data: Sentiment data for platform 1
            platform2_data: Sentiment data for platform 2
            
        Returns:
            Correlation coefficient (-1 to 1)
        """
        try:
            # Extract sentiment scores from both platforms
            scores1 = self._extract_sentiment_scores(platform1_data)
            scores2 = self._extract_sentiment_scores(platform2_data)
            
            if not scores1 or not scores2:
                return 0.0
            
            # Ensure same length by truncating to minimum length
            min_length = min(len(scores1), len(scores2))
            scores1 = scores1[:min_length]
            scores2 = scores2[:min_length]
            
            if len(scores1) < 2:
                return 0.0
            
            # Calculate correlation
            correlation = np.corrcoef(scores1, scores2)[0, 1]
            
            # Handle NaN (when all values are the same)
            if np.isnan(correlation):
                return 0.0
            
            return float(correlation)
            
        except Exception as e:
            logger.error(f"Error calculating sentiment correlation: {e}")
            return 0.0

    async def analyze_sentiment_trend(self, sentiment_data: Dict) -> Dict:
        """
        Analyze sentiment trends over time.
        
        Args:
            sentiment_data: Sentiment data with timestamps
            
        Returns:
            Dict containing trend analysis
        """
        try:
            # Extract time-series data
            time_points = []
            sentiment_scores = []
            volumes = []
            
            # This would typically be implemented based on the actual data structure
            # For now, we'll create a mock implementation
            posts = sentiment_data.get("posts", [])
            
            # Group by time periods (e.g., hourly)
            time_groups = {}
            for post in posts:
                # Extract timestamp (would need actual timestamp from data)
                timestamp = post.get("created_at", datetime.now())
                if isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except:
                        timestamp = datetime.now()
                
                # Group by hour
                hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                
                if hour_key not in time_groups:
                    time_groups[hour_key] = []
                
                time_groups[hour_key].append(post)
            
            # Calculate sentiment for each time period
            for hour in sorted(time_groups.keys()):
                posts_in_hour = time_groups[hour]
                texts = [post.get("text", "") for post in posts_in_hour if post.get("text")]
                
                if texts:
                    sentiment_result = await self.analyze_content_sentiment(
                        [{"text": text} for text in texts]
                    )
                    
                    time_points.append(hour)
                    sentiment_scores.append(sentiment_result.get("average_sentiment", 0.0))
                    volumes.append(len(texts))
            
            if not sentiment_scores:
                return {
                    "trend_direction": "stable",
                    "volatility": 0.0,
                    "correlation_with_volume": 0.0,
                    "significant_changes": []
                }
            
            # Calculate trend direction
            trend_direction = self._calculate_trend_direction(sentiment_scores)
            
            # Calculate volatility (standard deviation)
            volatility = float(np.std(sentiment_scores))
            
            # Calculate correlation with volume (if available)
            volume_correlation = 0.0
            if volumes and len(volumes) == len(sentiment_scores):
                volume_correlation = float(np.corrcoef(sentiment_scores, volumes)[0, 1])
                if np.isnan(volume_correlation):
                    volume_correlation = 0.0
            
            # Identify significant changes
            significant_changes = self._identify_significant_changes(sentiment_scores, time_points)
            
            return {
                "time_points": time_points,
                "sentiment_scores": sentiment_scores,
                "volumes": volumes,
                "trend_direction": trend_direction,
                "volatility": volatility,
                "correlation_with_volume": volume_correlation,
                "significant_changes": significant_changes
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment trend: {e}")
            return {
                "error": str(e),
                "trend_direction": "stable",
                "volatility": 0.0,
                "correlation_with_volume": 0.0,
                "significant_changes": []
            }

    # Private helper methods
    
    async def _analyze_single_text(self, text: str) -> SentimentResult:
        """Analyze sentiment of a single text."""
        try:
            # Basic text preprocessing
            clean_text = self._clean_text(text)
            
            # Language detection (simplified)
            language = self._detect_language(clean_text)
            
            # Sentiment analysis using lexicon-based approach
            sentiment_score = self._calculate_sentiment_score(clean_text)
            
            # Determine sentiment label
            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            # Calculate confidence (simplified)
            confidence = self._calculate_confidence(clean_text, sentiment_score)
            
            # Detect bias indicators
            bias_indicators = self._detect_bias_indicators(clean_text)
            
            # Extract entities
            entities = self._extract_entities(clean_text)
            
            # Extract keywords
            keywords = self._extract_keywords(clean_text)
            
            return SentimentResult(
                text=text,
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=confidence,
                language=language,
                bias_indicators=bias_indicators,
                entities=entities,
                keywords=keywords
            )
            
        except Exception as e:
            logger.error(f"Error analyzing single text: {e}")
            return SentimentResult(
                text=text,
                sentiment_score=0.0,
                sentiment_label="neutral",
                confidence=0.0,
                language="unknown",
                bias_indicators=[],
                entities=[],
                keywords=[]
            )

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis."""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove mentions and hashtags (keep the text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#\w+', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.lower()

    def _detect_language(self, text: str) -> str:
        """Detect language of text (simplified)."""
        # This would typically use a language detection library
        # For now, return 'en' as default
        return 'en'

    def _calculate_sentiment_score(self, text: str) -> float:
        """Calculate sentiment score using lexicon."""
        words = text.split()
        total_score = 0.0
        word_count = 0
        
        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in self.sentiment_lexicon:
                total_score += self.sentiment_lexicon[clean_word]
                word_count += 1
        
        if word_count == 0:
            return 0.0
        
        # Normalize score to -1 to 1 range
        average_score = total_score / word_count
        normalized_score = max(-1.0, min(1.0, average_score))
        
        return normalized_score

    def _calculate_confidence(self, text: str, sentiment_score: float) -> float:
        """Calculate confidence in sentiment analysis."""
        words = text.split()
        lexicon_matches = sum(1 for word in words if re.sub(r'[^\w]', '', word) in self.sentiment_lexicon)
        
        if len(words) == 0:
            return 0.0
        
        # Base confidence on lexicon coverage
        confidence = min(1.0, lexicon_matches / len(words))
        
        # Adjust based on sentiment score magnitude
        confidence *= (0.5 + abs(sentiment_score) * 0.5)
        
        return confidence

    def _detect_bias_indicators(self, text: str) -> List[str]:
        """Detect bias indicators in text."""
        bias_indicators = []
        
        for bias_type, pattern in self.bias_patterns.items():
            if pattern.search(text):
                bias_indicators.append(bias_type)
        
        return bias_indicators

    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities from text."""
        entities = []
        
        for entity_type, pattern in self.entity_extractor.items():
            matches = pattern.findall(text)
            entities.extend(matches)
        
        return list(set(entities))  # Remove duplicates

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction based on frequency and sentiment
        words = text.split()
        
        # Filter out common words
        stop_words = {'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'to', 'of', 'in', 'for', 'on', 'with', 'by'}
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Get unique keywords
        unique_keywords = list(set(keywords))
        
        # Sort by frequency (simplified)
        keyword_freq = [(word, keywords.count(word)) for word in unique_keywords]
        keyword_freq.sort(key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in keyword_freq[:10]]  # Return top 10

    def _aggregate_sentiment_results(self, results: List[SentimentResult], 
                                   platform: str, topic: str) -> Dict:
        """Aggregate sentiment analysis results."""
        if not results:
            return {
                "platform": platform,
                "topic": topic,
                "error": "No results to aggregate"
            }
        
        scores = [result.sentiment_score for result in results]
        confidences = [result.confidence for result in results]
        
        return {
            "platform": platform,
            "topic": topic,
            "total_posts": len(results),
            "average_sentiment": float(np.mean(scores)),
            "sentiment_std": float(np.std(scores)),
            "positive_posts": sum(1 for s in scores if s > 0.1),
            "negative_posts": sum(1 for s in scores if s < -0.1),
            "neutral_posts": sum(1 for s in scores if -0.1 <= s <= 0.1),
            "average_confidence": float(np.mean(confidences)),
            "bias_indicators": self._aggregate_bias_indicators(results),
            "top_entities": self._aggregate_entities(results),
            "top_keywords": self._aggregate_keywords(results)
        }

    def _aggregate_bias_indicators(self, results: List[SentimentResult]) -> Dict[str, int]:
        """Aggregate bias indicators across results."""
        bias_counts = {}
        
        for result in results:
            for bias in result.bias_indicators:
                bias_counts[bias] = bias_counts.get(bias, 0) + 1
        
        return bias_counts

    def _aggregate_entities(self, results: List[SentimentResult]) -> List[str]:
        """Aggregate entities across results."""
        all_entities = []
        for result in results:
            all_entities.extend(result.entities)
        
        # Count and sort by frequency
        entity_counts = {}
        for entity in all_entities:
            entity_counts[entity] = entity_counts.get(entity, 0) + 1
        
        sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
        return [entity for entity, count in sorted_entities[:20]]  # Top 20 entities

    def _aggregate_keywords(self, results: List[SentimentResult]) -> List[str]:
        """Aggregate keywords across results."""
        all_keywords = []
        for result in results:
            all_keywords.extend(result.keywords)
        
        # Count and sort by frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, count in sorted_keywords[:20]]  # Top 20 keywords

    def _extract_sentiment_scores(self, platform_data: Dict) -> List[float]:
        """Extract sentiment scores from platform data."""
        scores = []
        
        # This would depend on the actual structure of platform_data
        # For now, we'll look for common patterns
        if "sentiment_scores" in platform_data:
            scores = platform_data["sentiment_scores"]
        elif "posts" in platform_data:
            for post in platform_data["posts"]:
                if "sentiment_score" in post:
                    scores.append(post["sentiment_score"])
        
        return scores

    def _calculate_trend_direction(self, scores: List[float]) -> str:
        """Calculate trend direction from sentiment scores."""
        if len(scores) < 2:
            return "stable"
        
        # Calculate linear trend
        x = list(range(len(scores)))
        slope = np.polyfit(x, scores, 1)[0]
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"

    def _identify_significant_changes(self, scores: List[float], 
                                    time_points: List[datetime]) -> List[Dict]:
        """Identify significant changes in sentiment."""
        significant_changes = []
        
        if len(scores) < 3:
            return significant_changes
        
        # Look for significant changes (threshold-based)
        threshold = 0.3  # 30% change threshold
        
        for i in range(1, len(scores)):
            change = scores[i] - scores[i-1]
            if abs(change) > threshold:
                significant_changes.append({
                    "time": time_points[i],
                    "change": change,
                    "from": scores[i-1],
                    "to": scores[i],
                    "direction": "increase" if change > 0 else "decrease"
                })
        
        return significant_changes