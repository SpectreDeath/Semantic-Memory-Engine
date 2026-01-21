"""
Text Summarization Module
=========================

Phase 5 component for automatic text summarization.
Provides both extractive and abstractive summarization with configurable length.

Features:
- Extractive summarization (importance-based sentence selection)
- Query-focused summarization
- Multi-document summarization
- Abstractive summarization (via NLTK)
- Configurable compression ratios
- Keyword-based extraction
"""

import logging
from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import heapq
from collections import Counter

try:
    from nltk.corpus import stopwords
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.probability import FreqDist
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)


class SummarizationType(Enum):
    """Types of summarization approaches."""
    EXTRACTIVE = "extractive"
    QUERY_FOCUSED = "query_focused"
    MULTI_DOCUMENT = "multi_document"
    ABSTRACTIVE = "abstractive"


@dataclass
class SentenceScore:
    """Score for a sentence in the document."""
    sentence: str
    score: float
    order: int  # Original order in document
    keywords: List[str]


@dataclass
class Summary:
    """Complete summarization result."""
    original_text: str
    summary_text: str
    summary_type: SummarizationType
    compression_ratio: float  # Summary length / original length
    num_sentences_original: int
    num_sentences_summary: int
    key_sentences: List[SentenceScore]
    keywords: List[str]
    score: float  # Overall summary quality 0-1
    

@dataclass
class MultiDocumentSummary:
    """Multi-document summarization result."""
    documents: List[str]
    summary: str
    common_themes: List[str]
    doc_coverage: Dict[int, float]  # Doc index -> coverage percentage
    

class TextSummarizer:
    """Automatic text summarization engine."""
    
    def __init__(self):
        """Initialize summarizer."""
        self.has_nltk = NLTK_AVAILABLE
        if self.has_nltk:
            try:
                self.stop_words = set(stopwords.words('english'))
            except:
                logger.warning("NLTK stopwords not available, using basic set")
                self.stop_words = self._get_basic_stopwords()
        else:
            self.stop_words = self._get_basic_stopwords()
    
    def summarize(self, text: str, ratio: float = 0.3, 
                 summary_type: SummarizationType = SummarizationType.EXTRACTIVE,
                 query: Optional[str] = None) -> Summary:
        """
        Summarize text with specified approach.
        
        Args:
            text: Text to summarize
            ratio: Compression ratio (0-1, e.g., 0.3 = 30% of original)
            summary_type: Type of summarization
            query: Optional query for query-focused summarization
        """
        if not text or not text.strip():
            return self._create_empty_summary(text)
        
        # Validate ratio
        ratio = max(0.1, min(ratio, 1.0))
        
        if summary_type == SummarizationType.QUERY_FOCUSED and query:
            return self._summarize_query_focused(text, query, ratio)
        elif summary_type == SummarizationType.ABSTRACTIVE:
            return self._summarize_abstractive(text, ratio)
        else:
            return self._summarize_extractive(text, ratio)
    
    def multi_document_summarize(self, documents: List[str], 
                                ratio: float = 0.3) -> MultiDocumentSummary:
        """Summarize multiple documents together."""
        if not documents:
            return MultiDocumentSummary([], "", [], {})
        
        # Combine documents with markers
        combined = " ".join(documents)
        
        # Extract common themes
        common_themes = self._extract_common_themes(documents)
        
        # Summarize combined
        summary_result = self._summarize_extractive(combined, ratio)
        
        # Calculate per-document coverage
        doc_coverage = {}
        for idx, doc in enumerate(documents):
            coverage = self._calculate_coverage(doc, summary_result.summary_text)
            doc_coverage[idx] = coverage
        
        return MultiDocumentSummary(
            documents=documents,
            summary=summary_result.summary_text,
            common_themes=common_themes,
            doc_coverage=doc_coverage
        )
    
    def _summarize_extractive(self, text: str, ratio: float) -> Summary:
        """Extractive summarization - select important sentences."""
        sentences = self._split_sentences(text)
        if len(sentences) < 2:
            return self._create_summary_from_sentences(text, sentences, sentences, ratio, SummarizationType.EXTRACTIVE)
        
        # Score sentences
        scored_sentences = self._score_sentences(sentences)
        
        # Select top sentences
        num_summary_sentences = max(1, int(len(sentences) * ratio))
        selected = sorted(scored_sentences[:num_summary_sentences], key=lambda x: x.order)
        
        # Build summary preserving original order
        summary_text = " ".join(s.sentence for s in selected)
        
        # Extract keywords
        keywords = self._extract_keywords(text, top_n=10)
        
        # Calculate compression ratio
        actual_ratio = len(summary_text.split()) / max(len(text.split()), 1)
        
        return Summary(
            original_text=text,
            summary_text=summary_text,
            summary_type=SummarizationType.EXTRACTIVE,
            compression_ratio=actual_ratio,
            num_sentences_original=len(sentences),
            num_sentences_summary=len(selected),
            key_sentences=selected[:5],
            keywords=keywords,
            score=self._calculate_summary_score(sentences, selected)
        )
    
    def _summarize_query_focused(self, text: str, query: str, ratio: float) -> Summary:
        """Query-focused summarization."""
        sentences = self._split_sentences(text)
        if len(sentences) < 2:
            return self._create_summary_from_sentences(text, sentences, sentences, ratio, 
                                                      SummarizationType.QUERY_FOCUSED)
        
        # Score sentences based on query relevance
        query_terms = set(self._tokenize(query.lower()))
        scored_sentences = []
        
        for idx, sentence in enumerate(sentences):
            # TF-IDF-like scoring
            term_freq = self._calculate_term_frequency(sentence, query_terms)
            sentence_score = self._calculate_sentence_score(sentence) * (1 + term_freq * 2)
            
            keywords = [w for w in self._tokenize(sentence.lower()) 
                       if w in query_terms and w not in self.stop_words]
            
            scored_sentences.append(SentenceScore(
                sentence=sentence,
                score=sentence_score,
                order=idx,
                keywords=keywords
            ))
        
        # Select top by score
        scored_sentences.sort(key=lambda x: x.score, reverse=True)
        num_summary_sentences = max(1, int(len(sentences) * ratio))
        selected = sorted(scored_sentences[:num_summary_sentences], key=lambda x: x.order)
        
        summary_text = " ".join(s.sentence for s in selected)
        keywords = self._extract_keywords(text, top_n=10)
        
        return Summary(
            original_text=text,
            summary_text=summary_text,
            summary_type=SummarizationType.QUERY_FOCUSED,
            compression_ratio=len(summary_text.split()) / max(len(text.split()), 1),
            num_sentences_original=len(sentences),
            num_sentences_summary=len(selected),
            key_sentences=selected[:5],
            keywords=keywords,
            score=self._calculate_summary_score(sentences, selected)
        )
    
    def _summarize_abstractive(self, text: str, ratio: float) -> Summary:
        """Abstractive summarization (simplified - generates related summary)."""
        sentences = self._split_sentences(text)
        
        # Extract key concepts
        keywords = self._extract_keywords(text, top_n=15)
        
        # Build abstractive summary from keywords (simplified approach)
        # In production, would use seq2seq or transformer models
        abstract_summary = self._generate_from_keywords(keywords, sentences, ratio)
        
        scored_sentences = self._score_sentences(sentences)
        
        return Summary(
            original_text=text,
            summary_text=abstract_summary,
            summary_type=SummarizationType.ABSTRACTIVE,
            compression_ratio=len(abstract_summary.split()) / max(len(text.split()), 1),
            num_sentences_original=len(sentences),
            num_sentences_summary=len(self._split_sentences(abstract_summary)),
            key_sentences=scored_sentences[:5],
            keywords=keywords,
            score=0.7  # Abstractive summaries are harder to score
        )
    
    def _score_sentences(self, sentences: List[str]) -> List[SentenceScore]:
        """Score sentences by importance."""
        # Build frequency distribution
        words = []
        for sentence in sentences:
            words.extend(self._tokenize(sentence.lower()))
        
        freq_dist = FreqDist(words) if self.has_nltk else Counter(words)
        
        # Score sentences
        scored = []
        for idx, sentence in enumerate(sentences):
            score = 0
            keywords = []
            for word in self._tokenize(sentence.lower()):
                if word not in self.stop_words:
                    word_score = freq_dist.get(word, 0)
                    score += word_score
                    if word_score > freq_dist.get(max(freq_dist, key=freq_dist.get), 0) * 0.5:
                        keywords.append(word)
            
            scored.append(SentenceScore(
                sentence=sentence,
                score=score / max(len(sentence.split()), 1),  # Normalize by length
                order=idx,
                keywords=keywords
            ))
        
        # Sort by score
        scored.sort(key=lambda x: x.score, reverse=True)
        return scored
    
    def _calculate_sentence_score(self, sentence: str) -> float:
        """Calculate base sentence score."""
        words = self._tokenize(sentence.lower())
        keywords = [w for w in words if w not in self.stop_words]
        return len(keywords) / max(len(words), 1)
    
    def _calculate_term_frequency(self, sentence: str, query_terms: set) -> float:
        """Calculate term frequency for query terms in sentence."""
        words = self._tokenize(sentence.lower())
        matches = sum(1 for w in words if w in query_terms)
        return matches / max(len(words), 1)
    
    def _extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract top keywords using frequency."""
        words = self._tokenize(text.lower())
        keywords = [w for w in words if w not in self.stop_words and len(w) > 3]
        
        freq_dist = FreqDist(keywords) if self.has_nltk else Counter(keywords)
        return [word for word, _ in freq_dist.most_common(top_n)]
    
    def _extract_common_themes(self, documents: List[str]) -> List[str]:
        """Extract themes common across documents."""
        all_keywords = []
        for doc in documents:
            keywords = self._extract_keywords(doc, top_n=5)
            all_keywords.extend(keywords)
        
        freq = Counter(all_keywords)
        # Common themes appear in multiple documents
        return [word for word, count in freq.most_common(5) if count > 1]
    
    def _generate_from_keywords(self, keywords: List[str], sentences: List[str], 
                               ratio: float) -> str:
        """Generate abstractive summary from keywords."""
        # Select sentences containing most keywords
        keyword_set = set(keywords)
        scored = []
        
        for idx, sentence in enumerate(sentences):
            sentence_words = set(self._tokenize(sentence.lower()))
            overlap = len(keyword_set & sentence_words)
            if overlap > 0:
                scored.append((idx, sentence, overlap))
        
        if not scored:
            return sentences[0] if sentences else ""
        
        # Sort by keyword overlap
        scored.sort(key=lambda x: x[2], reverse=True)
        
        # Select sentences
        num_sentences = max(1, int(len(sentences) * ratio))
        selected = sorted(scored[:num_sentences], key=lambda x: x[0])
        
        return " ".join(s[1] for s in selected)
    
    def _calculate_summary_score(self, original: List[str], 
                                selected: List[SentenceScore]) -> float:
        """Calculate quality score of summary."""
        if not original:
            return 0.0
        
        # Coverage score
        coverage = len(selected) / len(original)
        
        # Diversity score (selected from different parts)
        if len(selected) > 1:
            positions = [s.order / len(original) for s in selected]
            diversity = 1 - (max(positions) - min(positions)) if positions else 1
        else:
            diversity = 0.5
        
        # Average sentence score
        avg_score = sum(s.score for s in selected) / len(selected) if selected else 0
        
        # Balanced score
        return coverage * 0.4 + diversity * 0.3 + min(avg_score, 1.0) * 0.3
    
    def _calculate_coverage(self, document: str, summary: str) -> float:
        """Calculate coverage of document in summary."""
        doc_words = set(self._tokenize(document.lower()))
        summary_words = set(self._tokenize(summary.lower()))
        
        if not doc_words:
            return 0.0
        
        overlap = len(doc_words & summary_words)
        return overlap / len(doc_words)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        if self.has_nltk:
            try:
                return sent_tokenize(text)
            except:
                pass
        
        # Fallback: simple split on periods
        sentences = text.split('.')
        return [s.strip() for s in sentences if s.strip()]
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        if self.has_nltk:
            try:
                return word_tokenize(text)
            except:
                pass
        
        # Fallback: simple split
        import re
        return re.findall(r'\b\w+\b', text.lower())
    
    def _get_basic_stopwords(self) -> set:
        """Get basic set of stopwords if NLTK not available."""
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
            'when', 'where', 'why', 'how'
        }
    
    def _create_summary_from_sentences(self, text: str, original: List[str],
                                       summary_sentences: List[str],
                                       ratio: float, summary_type: SummarizationType) -> Summary:
        """Helper to create Summary object."""
        summary_text = " ".join(summary_sentences)
        keywords = self._extract_keywords(text, top_n=10)
        
        return Summary(
            original_text=text,
            summary_text=summary_text,
            summary_type=summary_type,
            compression_ratio=len(summary_text.split()) / max(len(text.split()), 1),
            num_sentences_original=len(original),
            num_sentences_summary=len(summary_sentences),
            key_sentences=[],
            keywords=keywords,
            score=0.6
        )
    
    def _create_empty_summary(self, text: str) -> Summary:
        """Create empty summary."""
        return Summary(
            original_text=text,
            summary_text="",
            summary_type=SummarizationType.EXTRACTIVE,
            compression_ratio=0.0,
            num_sentences_original=0,
            num_sentences_summary=0,
            key_sentences=[],
            keywords=[],
            score=0.0
        )
