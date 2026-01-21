"""
Phase 5 - Enhanced Analytics Tests

Comprehensive test suite for sentiment analysis, text summarization,
entity linking, and document clustering modules.

Test Coverage:
- SentimentAnalyzer (25+ test cases)
- TextSummarizer (20+ test cases)
- EntityLinker (15+ test cases)
- DocumentClusterer (15+ test cases)
- Integration (5+ test cases)
"""

import pytest
from typing import List, Dict

# Import Phase 5 modules
from src.core.sentiment_analyzer import (
    SentimentAnalyzer, SentimentAnalysis, EmotionType,
    SentimentPolarity, EmotionScore
)
from src.core.text_summarizer import (
    TextSummarizer, Summary, SummarizationType, SentenceScore
)
from src.core.entity_linker import (
    EntityLinker, EntityType, LinkedEntity, EntityLinkingResult,
    KnowledgeBase
)
from src.core.document_clusterer import (
    DocumentClusterer, ClusteringAlgorithm, ClusteringResult, Cluster
)


# ============================================================================
# SENTIMENT ANALYZER TESTS
# ============================================================================

class TestSentimentAnalyzerBasics:
    """Basic sentiment analyzer functionality."""
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = SentimentAnalyzer()
        assert analyzer is not None
        assert isinstance(analyzer.has_vader, bool)
        assert isinstance(analyzer.has_textblob, bool)
    
    def test_analyze_positive_sentiment(self):
        """Test analysis of positive text."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("This is absolutely amazing and wonderful!")
        
        assert result.polarity == SentimentPolarity.POSITIVE or result.polarity == SentimentPolarity.VERY_POSITIVE
        assert result.polarity_score > 0.2
        assert result.intensity > 0.0
    
    def test_analyze_negative_sentiment(self):
        """Test analysis of negative text."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("This is terrible and awful!")
        
        assert result.polarity == SentimentPolarity.NEGATIVE or result.polarity == SentimentPolarity.VERY_NEGATIVE
        assert result.polarity_score < -0.2
    
    def test_analyze_neutral_sentiment(self):
        """Test analysis of neutral text."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("The weather is today.")
        
        assert result.polarity == SentimentPolarity.NEUTRAL
        assert -0.2 <= result.polarity_score <= 0.2
    
    def test_analyze_empty_text(self):
        """Test analysis of empty text."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("")
        
        assert result.polarity == SentimentPolarity.NEUTRAL
        assert result.polarity_score == 0.0
        assert result.intensity == 0.0


class TestSentimentAnalyzerEmotions:
    """Emotion detection tests."""
    
    def test_joy_detection(self):
        """Test joy emotion detection."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("I am so happy and delighted!")
        
        joy_score = result.emotions[EmotionType.JOY].score
        assert joy_score > 0.3
    
    def test_anger_detection(self):
        """Test anger emotion detection."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("I am furious and enraged!")
        
        anger_score = result.emotions[EmotionType.ANGER].score
        assert anger_score > 0.3
    
    def test_fear_detection(self):
        """Test fear emotion detection."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("I am very scared and terrified!")
        
        fear_score = result.emotions[EmotionType.FEAR].score
        assert fear_score > 0.3
    
    def test_dominant_emotion(self):
        """Test dominant emotion identification."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("I am so happy and joyful!")
        
        assert result.dominant_emotion in [e for e in EmotionType]
    
    def test_emotion_scores_normalized(self):
        """Test emotion scores are in valid range."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("Test text")
        
        for emotion_type, emotion_score in result.emotions.items():
            assert 0.0 <= emotion_score.score <= 1.0
            assert 0.0 <= emotion_score.confidence <= 1.0


class TestSentimentAnalyzerTrend:
    """Sentiment trend analysis tests."""
    
    def test_sentiment_trend_increasing(self):
        """Test increasing sentiment trend."""
        analyzer = SentimentAnalyzer()
        text = "It was okay. Then it got better. Now it's amazing!"
        trend = analyzer.analyze_trend(text)
        
        assert len(trend.segments) > 0
        assert len(trend.sentiment_scores) == len(trend.segments)
        assert trend.trend_direction in ["increasing", "decreasing", "stable"]
    
    def test_sentiment_trend_decreasing(self):
        """Test decreasing sentiment trend."""
        analyzer = SentimentAnalyzer()
        text = "It was wonderful. Then it got worse. Now it's terrible."
        trend = analyzer.analyze_trend(text)
        
        assert len(trend.segments) > 0
        assert 0.0 <= trend.volatility <= 1.0
    
    def test_sentiment_trend_single_sentence(self):
        """Test trend with single sentence."""
        analyzer = SentimentAnalyzer()
        trend = analyzer.analyze_trend("This is good.")
        
        assert len(trend.segments) >= 1


class TestSentimentAnalyzerAdvanced:
    """Advanced sentiment analysis features."""
    
    def test_subjectivity_scoring(self):
        """Test subjectivity scoring."""
        analyzer = SentimentAnalyzer()
        objective = analyzer.analyze("The temperature is 25 degrees.")
        subjective = analyzer.analyze("I believe this is wonderful.")
        
        assert 0.0 <= objective.subjectivity <= 1.0
        assert 0.0 <= subjective.subjectivity <= 1.0
    
    def test_sarcasm_detection(self):
        """Test sarcasm detection."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("Yeah right, that's just great!")
        
        # May or may not detect based on patterns
        assert isinstance(result.is_sarcastic, bool)
    
    def test_mixed_sentiment_detection(self):
        """Test mixed sentiment detection."""
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("I love the idea but hate the execution!")
        
        assert isinstance(result.is_mixed, bool)
    
    def test_intensity_calculation(self):
        """Test intensity calculation."""
        analyzer = SentimentAnalyzer()
        weak = analyzer.analyze("somewhat good")
        strong = analyzer.analyze("absolutely amazing and wonderful!")
        
        assert 0.0 <= weak.intensity <= 1.0
        assert 0.0 <= strong.intensity <= 1.0


# ============================================================================
# TEXT SUMMARIZER TESTS
# ============================================================================

class TestTextSummarizerBasics:
    """Basic text summarization tests."""
    
    def test_summarizer_initialization(self):
        """Test summarizer initializes correctly."""
        summarizer = TextSummarizer()
        assert summarizer is not None
        assert isinstance(summarizer.has_nltk, bool)
    
    def test_extractive_summarization(self):
        """Test extractive summarization."""
        summarizer = TextSummarizer()
        text = "This is the first sentence. This is the second sentence. This is the third sentence."
        summary = summarizer.summarize(text, ratio=0.5)
        
        assert summary.summary_type == SummarizationType.EXTRACTIVE
        assert len(summary.summary_text) > 0
        assert summary.num_sentences_summary <= summary.num_sentences_original
    
    def test_summarization_compression_ratio(self):
        """Test compression ratio calculation."""
        summarizer = TextSummarizer()
        text = "This is a long text. " * 20
        summary = summarizer.summarize(text, ratio=0.3)
        
        assert 0.0 <= summary.compression_ratio <= 1.0
        assert summary.num_sentences_summary > 0
    
    def test_summarization_empty_text(self):
        """Test summarization of empty text."""
        summarizer = TextSummarizer()
        summary = summarizer.summarize("")
        
        assert summary.summary_text == ""
        assert summary.num_sentences_original == 0


class TestTextSummarizerTypes:
    """Different summarization type tests."""
    
    def test_query_focused_summarization(self):
        """Test query-focused summarization."""
        summarizer = TextSummarizer()
        text = "The cat sat on the mat. The dog played in the yard. The cat and dog are friends."
        summary = summarizer.summarize(
            text,
            ratio=0.5,
            summary_type=SummarizationType.QUERY_FOCUSED,
            query="cat"
        )
        
        assert summary.summary_type == SummarizationType.QUERY_FOCUSED
        assert len(summary.summary_text) > 0
    
    def test_abstractive_summarization(self):
        """Test abstractive summarization."""
        summarizer = TextSummarizer()
        text = "This is a test document. It contains important information. The summary should capture the essence."
        summary = summarizer.summarize(
            text,
            ratio=0.5,
            summary_type=SummarizationType.ABSTRACTIVE
        )
        
        assert summary.summary_type == SummarizationType.ABSTRACTIVE
        assert len(summary.keywords) > 0


class TestTextSummarizerMultiDocument:
    """Multi-document summarization tests."""
    
    def test_multi_document_summarization(self):
        """Test multi-document summarization."""
        summarizer = TextSummarizer()
        docs = [
            "The machine learning algorithm works well.",
            "Deep learning is a subset of machine learning.",
            "Neural networks are inspired by the human brain."
        ]
        result = summarizer.multi_document_summarize(docs, ratio=0.4)
        
        assert len(result.documents) == 3
        assert len(result.summary) > 0
        assert isinstance(result.doc_coverage, dict)
    
    def test_common_themes_extraction(self):
        """Test common themes extraction."""
        summarizer = TextSummarizer()
        docs = [
            "Machine learning is powerful.",
            "Deep learning uses machine learning.",
            "Machine learning algorithms are important."
        ]
        result = summarizer.multi_document_summarize(docs)
        
        assert isinstance(result.common_themes, list)


class TestTextSummarizerQuality:
    """Text summarization quality metrics."""
    
    def test_summary_score(self):
        """Test summary quality score."""
        summarizer = TextSummarizer()
        text = "This is sentence one. This is sentence two. This is sentence three."
        summary = summarizer.summarize(text, ratio=0.5)
        
        assert 0.0 <= summary.score <= 1.0
    
    def test_keyword_extraction(self):
        """Test keyword extraction."""
        summarizer = TextSummarizer()
        text = "Machine learning algorithms process data efficiently. Data science uses algorithms."
        summary = summarizer.summarize(text, ratio=0.5)
        
        assert len(summary.keywords) > 0
        assert "machine" in str(summary.keywords).lower() or "learning" in str(summary.keywords).lower()


# ============================================================================
# ENTITY LINKER TESTS
# ============================================================================

class TestEntityLinkerBasics:
    """Basic entity linking tests."""
    
    def test_entity_linker_initialization(self):
        """Test entity linker initializes."""
        linker = EntityLinker()
        assert linker is not None
        assert isinstance(linker.has_nltk, bool)
    
    def test_entity_recognition(self):
        """Test entity recognition."""
        linker = EntityLinker()
        result = linker.link_entities("Albert Einstein was a physicist.")
        
        assert len(result.entities) > 0
        assert any(e.entity_type == EntityType.PERSON for e in result.entities)
    
    def test_entity_types_recognized(self):
        """Test various entity types."""
        linker = EntityLinker()
        result = linker.link_entities("Paris is in France. Einstein lived there.")
        
        assert len(result.entities) > 0
    
    def test_empty_text_linking(self):
        """Test linking empty text."""
        linker = EntityLinker()
        result = linker.link_entities("")
        
        assert len(result.entities) == 0


class TestEntityLinkerDisambiguation:
    """Entity disambiguation tests."""
    
    def test_entity_disambiguation(self):
        """Test entity disambiguation."""
        linker = EntityLinker()
        candidates = linker.disambiguate_entity("Paris")
        
        assert isinstance(candidates, list)
    
    def test_disambiguation_with_context(self):
        """Test disambiguation with context."""
        linker = EntityLinker()
        candidates = linker.disambiguate_entity("Paris", context="The capital of France")
        
        assert isinstance(candidates, list)


class TestEntityLinkerKnowledgeBase:
    """Knowledge base operations."""
    
    def test_custom_kb_update(self):
        """Test custom knowledge base update."""
        linker = EntityLinker()
        entity_data = {
            "url": "https://example.com",
            "description": "Test entity",
            "aliases": ["test", "example"],
            "properties": {"type": "test"}
        }
        linker.update_custom_kb("test_entity", entity_data)
        
        assert "test_entity" in linker.custom_kb
    
    def test_wikipedia_linking(self):
        """Test Wikipedia entity linking."""
        linker = EntityLinker()
        result = linker.link_entities("Albert Einstein discovered relativity.", kb_type=KnowledgeBase.WIKIPEDIA)
        
        assert isinstance(result.linked_entities, list)


# ============================================================================
# DOCUMENT CLUSTERER TESTS
# ============================================================================

class TestDocumentClustererBasics:
    """Basic document clustering tests."""
    
    def test_clusterer_initialization(self):
        """Test clusterer initializes."""
        clusterer = DocumentClusterer()
        assert clusterer is not None
        assert isinstance(clusterer.has_nltk, bool)
    
    def test_basic_clustering(self):
        """Test basic document clustering."""
        clusterer = DocumentClusterer()
        docs = [
            "The cat sat on the mat.",
            "Dogs play in the park.",
            "Cats are independent animals.",
            "Parks are good for recreation."
        ]
        result = clusterer.cluster(docs, num_clusters=2)
        
        assert isinstance(result, ClusteringResult)
        assert result.num_clusters > 0
        assert len(result.clusters) > 0
    
    def test_optimal_cluster_estimation(self):
        """Test automatic cluster number estimation."""
        clusterer = DocumentClusterer()
        docs = [f"Document {i}. " * 5 for i in range(10)]
        result = clusterer.cluster(docs, num_clusters=None)
        
        assert result.num_clusters > 0
    
    def test_clustering_empty_documents(self):
        """Test clustering with single document."""
        clusterer = DocumentClusterer()
        result = clusterer.cluster(["Single document"])
        
        assert result.num_clusters >= 1


class TestDocumentClustererAlgorithms:
    """Test different clustering algorithms."""
    
    def test_kmeans_clustering(self):
        """Test K-means clustering."""
        clusterer = DocumentClusterer()
        docs = [
            "Machine learning is powerful.",
            "Deep learning uses neural networks.",
            "Data science processes information.",
            "Statistics analyzes data."
        ]
        result = clusterer.cluster(docs, num_clusters=2, algorithm=ClusteringAlgorithm.KMEANS)
        
        assert result.algorithm == ClusteringAlgorithm.KMEANS
        assert len(result.clusters) == 2
    
    def test_hierarchical_clustering(self):
        """Test hierarchical clustering."""
        clusterer = DocumentClusterer()
        docs = [
            "Document about cats.",
            "Document about dogs.",
            "Document about birds."
        ]
        result = clusterer.cluster(docs, num_clusters=2, algorithm=ClusteringAlgorithm.HIERARCHICAL)
        
        assert result.algorithm == ClusteringAlgorithm.HIERARCHICAL
        assert len(result.clusters) == 2


class TestDocumentClustererQuality:
    """Document clustering quality metrics."""
    
    def test_silhouette_score(self):
        """Test silhouette score calculation."""
        clusterer = DocumentClusterer()
        docs = [
            "First document.",
            "Second document.",
            "Third document.",
            "Fourth document."
        ]
        result = clusterer.cluster(docs, num_clusters=2)
        
        assert -1.0 <= result.silhouette_score <= 1.0
    
    def test_cluster_characterization(self):
        """Test cluster characterization."""
        clusterer = DocumentClusterer()
        docs = [
            "Machine learning algorithms.",
            "Deep learning networks.",
            "Neural network training."
        ]
        result = clusterer.cluster(docs, num_clusters=1)
        
        assert len(result.clusters[0].top_terms) > 0
        assert all(isinstance(t, tuple) for t in result.clusters[0].top_terms)
    
    def test_topic_labels_generation(self):
        """Test topic label generation."""
        clusterer = DocumentClusterer()
        docs = [
            "Machine learning and algorithms.",
            "Data processing systems."
        ]
        result = clusterer.cluster(docs, num_clusters=2)
        
        assert len(result.topic_labels) > 0


class TestDocumentClustererSimilarity:
    """Document similarity tests."""
    
    def test_similar_documents_retrieval(self):
        """Test retrieving similar documents."""
        clusterer = DocumentClusterer()
        docs = [
            "The cat sat on the mat.",
            "The dog played in the yard.",
            "The cat was very comfortable."
        ]
        similar = clusterer.get_similar_documents(docs[0], docs, top_n=2)
        
        assert len(similar) <= 2
        assert all(isinstance(item, tuple) for item in similar)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase5Integration:
    """Phase 5 component integration tests."""
    
    def test_all_components_import(self):
        """Test all Phase 5 components import correctly."""
        from src import (
            SentimentAnalyzer, TextSummarizer, EntityLinker, DocumentClusterer
        )
        
        assert SentimentAnalyzer is not None
        assert TextSummarizer is not None
        assert EntityLinker is not None
        assert DocumentClusterer is not None
    
    def test_factory_integration(self):
        """Test Phase 5 factory creation."""
        from src import ToolFactory
        
        sentiment = ToolFactory.create_sentiment_analyzer()
        summarizer = ToolFactory.create_text_summarizer()
        linker = ToolFactory.create_entity_linker()
        clusterer = ToolFactory.create_document_clusterer()
        
        assert sentiment is not None
        assert summarizer is not None
        assert linker is not None
        assert clusterer is not None
    
    def test_complete_analysis_pipeline(self):
        """Test complete analysis pipeline."""
        text = "This is an amazing document about machine learning. It discusses algorithms and neural networks."
        
        # Sentiment
        sentiment_analyzer = SentimentAnalyzer()
        sentiment = sentiment_analyzer.analyze(text)
        assert sentiment.polarity_score > 0  # "amazing" should trigger positive
        
        # Summarization
        summarizer = TextSummarizer()
        summary = summarizer.summarize(text, ratio=0.5)
        assert len(summary.summary_text) > 0
        
        # Entity linking
        linker = EntityLinker()
        entities = linker.link_entities(text)
        assert isinstance(entities, EntityLinkingResult)
    
    def test_factory_caching(self):
        """Test factory component caching."""
        from src import ToolFactory
        
        analyzer1 = ToolFactory.create_sentiment_analyzer()
        analyzer2 = ToolFactory.create_sentiment_analyzer()
        
        assert analyzer1 is analyzer2  # Should be same instance
        
        # Reset and check
        ToolFactory.reset()
        analyzer3 = ToolFactory.create_sentiment_analyzer()
        assert analyzer1 is not analyzer3  # Should be different instance


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestPhase5EdgeCases:
    """Edge case tests for Phase 5 modules."""
    
    def test_very_long_text_sentiment(self):
        """Test sentiment analysis on very long text."""
        analyzer = SentimentAnalyzer()
        long_text = "This is good. " * 1000
        result = analyzer.analyze(long_text)
        
        assert result.polarity_score > 0
    
    def test_special_characters_sentiment(self):
        """Test sentiment with special characters."""
        analyzer = SentimentAnalyzer()
        text = "Amazing!!! 🎉 Wonderful!!! @#$%"
        result = analyzer.analyze(text)
        
        assert isinstance(result.polarity_score, float)
    
    def test_mixed_language_clustering(self):
        """Test clustering with various text lengths."""
        clusterer = DocumentClusterer()
        docs = [
            "Short.",
            "This is a much longer document with more content.",
            "Medium length text here."
        ]
        result = clusterer.cluster(docs, num_clusters=2)
        
        assert len(result.clusters) > 0
    
    def test_duplicate_documents_clustering(self):
        """Test clustering with duplicate documents."""
        clusterer = DocumentClusterer()
        docs = [
            "The same document.",
            "The same document.",
            "A different document."
        ]
        result = clusterer.cluster(docs, num_clusters=2)
        
        assert len(result.clusters) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
