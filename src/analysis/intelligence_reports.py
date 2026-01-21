"""
Intelligence Reporting Module
=============================

Phase 6 component for generating narrative intelligence reports.
Synthesizes data from SentimentAnalyzer and TextSummarizer into structured briefings.

Features:
- Narrative synthesis of multi-document datasets
- Sentiment-aware executive summaries
- Topic-based deep dives
- Confidence-scored insight generation
- Markdown and JSON report formats
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from src.core.factory import ToolFactory
from src.core.sentiment_analyzer import SentimentAnalysis
from src.core.text_summarizer import Summary

logger = logging.getLogger(__name__)


@dataclass
class IntelligenceReport:
    """A synthesized intelligence briefing."""
    timestamp: str
    title: str
    summary: str
    key_points: List[str]
    sentiment_overview: Dict[str, Any]
    dominant_themes: List[str]
    confidence_score: float
    metadata: Dict[str, Any]


class IntelligenceReports:
    """
    Synthesizes multiple analysis perspectives into narrative reports.
    """
    
    def __init__(self):
        """Initialize with required analytical tools."""
        self.summarizer = ToolFactory.create_text_summarizer()
        self.sentiment_analyzer = ToolFactory.create_sentiment_analyzer()
        
        logger.info("IntelligenceReports engine initialized")

    def generate_briefing(self, text: str, title: str = "Intelligence Briefing") -> IntelligenceReport:
        """
        Generate a comprehensive intelligence report from a single text source.
        
        Args:
            text: Input text
            title: Title for the report
        """
        if not text or not text.strip():
            return self._create_empty_report(title)

        # 1. Summarization
        summary_obj: Summary = self.summarizer.summarize(text)
        
        # 2. Sentiment Analysis
        sentiment_obj: SentimentAnalysis = self.sentiment_analyzer.analyze(text)
        
        # 3. Emotion-aware points extraction
        key_points = self._extract_key_points(summary_obj, sentiment_obj)
        
        # 4. Synthesize narrative
        narrative = self._synthesize_narrative(summary_obj, sentiment_obj)
        
        return IntelligenceReport(
            timestamp=datetime.now().isoformat(),
            title=title,
            summary=narrative,
            key_points=key_points,
            sentiment_overview={
                "polarity": sentiment_obj.polarity.value,
                "score": sentiment_obj.polarity_score,
                "dominant_emotion": sentiment_obj.dominant_emotion.value if sentiment_obj.dominant_emotion else "neutral",
                "intensity": sentiment_obj.intensity
            },
            dominant_themes=summary_obj.keywords[:5],
            confidence_score=(summary_obj.score + sentiment_obj.confidence) / 2,
            metadata={
                "source_length": len(text),
                "is_sarcastic": sentiment_obj.is_sarcastic,
                "is_mixed": sentiment_obj.is_mixed
            }
        )

    def _extract_key_points(self, summary: Summary, sentiment: SentimentAnalysis) -> List[str]:
        """Combine summary sentences with emotional highlights."""
        # Fix: access sentence from SentenceScore objects in key_sentences
        points = [s.sentence for s in summary.key_sentences[:3]]
        
        # Add high-intensity emotion points if they exist
        if sentiment.intensity > 0.6 and sentiment.dominant_emotion:
            points.append(f"High emotional intensity detected: Strong expressions of {sentiment.dominant_emotion.value}.")
            
        if sentiment.is_sarcastic:
            points.append("Ambiguity Alert: Potential sarcasm or double-meaning detected in the source.")
            
        return points

    def _synthesize_narrative(self, summary: Summary, sentiment: SentimentAnalysis) -> str:
        """Create a human-readable narrative combining summary and tone."""
        tone = "neutral"
        if sentiment.polarity_score > 0.3:
            tone = "positive"
        elif sentiment.polarity_score < -0.3:
            tone = "negative"
            
        narrative = (
            f"The analyzed text presents a {tone} perspective focused on {', '.join(summary.keywords[:3])}. "
            f"The primary substance centers on: {summary.summary_text} "
            f"Linguistic markers indicate a confidence level of {sentiment.confidence:.1%} "
            f"with an overall emotional intensity of {sentiment.intensity:.1%}."
        )
        return narrative

    def _create_empty_report(self, title: str) -> IntelligenceReport:
        """Return a blank report for empty input."""
        return IntelligenceReport(
            timestamp=datetime.now().isoformat(),
            title=title,
            summary="No content provided for analysis.",
            key_points=[],
            sentiment_overview={},
            dominant_themes=[],
            confidence_score=0.0,
            metadata={}
        )

    def to_markdown(self, report: IntelligenceReport) -> str:
        """Convert a report to formatted Markdown."""
        md = [
            f"# {report.title}",
            f"**Generated:** {report.timestamp}",
            "",
            "## Executive Summary",
            report.summary,
            "",
            "## Key Findings",
        ]
        for point in report.key_points:
            md.append(f"- {point}")
            
        md.extend([
            "",
            "## Emotional & Semantic Metadata",
            f"- **Tone:** {report.sentiment_overview.get('polarity', 'Unknown')}",
            f"- **Dominant Emotion:** {report.sentiment_overview.get('dominant_emotion', 'None')}",
            f"- **Core Themes:** {', '.join(report.dominant_themes)}",
            f"- **Analytical Confidence:** {report.confidence_score:.1%}"
        ])
        
        return "\n".join(md)
