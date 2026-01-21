"""
Test suite for NLPPipeline module.

Tests comprehensive NLP analysis capabilities including:
- Tokenization and POS tagging
- Named entity recognition
- Phrase extraction
- Key term analysis
- Linguistic complexity metrics
"""

import unittest
from src.core.nlp_pipeline import (
    NLPPipeline, Token, NamedEntity, Phrase, NLPAnalysis, POS
)


class TestNLPPipelineBasics(unittest.TestCase):
    """Test basic NLP pipeline functionality."""
    
    def setUp(self):
        """Initialize pipeline for tests."""
        self.nlp = NLPPipeline()
    
    def test_pipeline_availability(self):
        """Test that pipeline is available."""
        self.assertTrue(self.nlp.is_available())
    
    def test_simple_analysis(self):
        """Test analysis of simple sentence."""
        text = "The quick brown fox jumps."
        analysis = self.nlp.analyze(text)
        
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.text, text)
        self.assertGreater(len(analysis.tokens), 0)
        self.assertGreater(len(analysis.pos_tags), 0)
    
    def test_tokenization(self):
        """Test sentence and word tokenization."""
        text = "The dog runs. The cat sleeps."
        analysis = self.nlp.analyze(text)
        
        # Should have 2 sentences
        self.assertEqual(len(analysis.sentences), 2)
        
        # Should have multiple tokens
        self.assertGreater(len(analysis.tokens), 5)
    
    def test_pos_tagging(self):
        """Test POS tag assignment."""
        text = "I run quickly"
        analysis = self.nlp.analyze(text)
        
        # Extract POS tags
        pos_dict = {word: pos for word, pos in analysis.pos_tags}
        
        # Check for expected tags
        self.assertIn('I', pos_dict)
        self.assertIn('run', pos_dict)
        self.assertIn('quickly', pos_dict)
    
    def test_lemmatization(self):
        """Test lemmatization."""
        text = "The dogs are running quickly"
        analysis = self.nlp.analyze(text)
        
        # Lemmas dictionary should be populated
        self.assertGreater(len(analysis.lemmas), 0)
        
        # Should have lemmas for key words
        self.assertIn('dogs', analysis.lemmas)
        self.assertIn('running', analysis.lemmas)


class TestNLPTokenAnalysis(unittest.TestCase):
    """Test token-level analysis."""
    
    def setUp(self):
        """Initialize pipeline."""
        self.nlp = NLPPipeline()
    
    def test_token_structure(self):
        """Test Token dataclass structure."""
        text = "Machine learning"
        analysis = self.nlp.analyze(text)
        
        tokens = analysis.tokens
        self.assertGreater(len(tokens), 0)
        
        for token in tokens:
            self.assertIsNotNone(token.text)
            self.assertIsNotNone(token.pos)
            self.assertIsNotNone(token.lemma)
            self.assertIsNotNone(token.stem)
            self.assertIsNotNone(token.is_stopword)
    
    def test_stopword_detection(self):
        """Test stopword identification."""
        text = "the cat and dog"
        analysis = self.nlp.analyze(text)
        
        # Find stopwords
        stopword_tokens = [t for t in analysis.tokens if t.is_stopword]
        self.assertGreater(len(stopword_tokens), 0)
        
        # "the" and "and" should be stopwords
        stopword_texts = [t.text for t in stopword_tokens]
        self.assertIn('the', stopword_texts)
        self.assertIn('and', stopword_texts)


class TestNLPEntityExtraction(unittest.TestCase):
    """Test named entity recognition."""
    
    def setUp(self):
        """Initialize pipeline."""
        self.nlp = NLPPipeline()
    
    def test_entity_extraction(self):
        """Test basic entity extraction."""
        text = "John Smith works at Microsoft in Seattle"
        analysis = self.nlp.analyze(text)
        
        # Should have entities
        self.assertGreater(len(analysis.entities), 0)
    
    def test_extract_entities_by_type(self):
        """Test entity extraction by type."""
        text = "Apple Inc. is headquartered in Cupertino, California."
        result = self.nlp.extract_entities_by_type(text)
        
        # Should return dictionary
        self.assertIsInstance(result, dict)
    
    def test_entity_structure(self):
        """Test NamedEntity structure."""
        text = "Dr. John Smith is visiting Paris"
        analysis = self.nlp.analyze(text)
        
        for entity in analysis.entities:
            self.assertIsNotNone(entity.text)
            self.assertIsNotNone(entity.entity_type)
            self.assertIsInstance(entity.tokens, list)


class TestNLPKeyTermExtraction(unittest.TestCase):
    """Test key term extraction."""
    
    def setUp(self):
        """Initialize pipeline."""
        self.nlp = NLPPipeline()
    
    def test_key_terms_property(self):
        """Test key_terms property of analysis."""
        text = "Machine learning is powerful. Deep learning uses neural networks."
        analysis = self.nlp.analyze(text)
        
        key_terms = analysis.key_terms
        self.assertGreater(len(key_terms), 0)
        
        # Key terms should be non-stopwords
        stopwords = analysis.stopwords
        for term in key_terms:
            self.assertNotIn(term.lower(), stopwords)
    
    def test_extract_key_terms_method(self):
        """Test key term extraction method."""
        text = "Python is great. Python is powerful. Java is good."
        key_terms = self.nlp.extract_key_terms(text)
        
        # Should return list of (term, frequency) tuples
        self.assertIsInstance(key_terms, list)
        if key_terms:
            term, freq = key_terms[0]
            self.assertIsInstance(term, str)
            self.assertIsInstance(freq, int)
    
    def test_min_frequency_filter(self):
        """Test frequency filtering."""
        text = "cat cat dog dog dog bird"
        key_terms = self.nlp.extract_key_terms(text, min_freq=2)
        
        # All returned terms should have at least min_freq
        for term, freq in key_terms:
            self.assertGreaterEqual(freq, 2)


class TestNLPComplexityMetrics(unittest.TestCase):
    """Test linguistic complexity analysis."""
    
    def setUp(self):
        """Initialize pipeline."""
        self.nlp = NLPPipeline()
    
    def test_get_complexity_metrics(self):
        """Test complexity metric calculation."""
        text = "The quick brown fox jumps over the lazy dog. " * 2
        metrics = self.nlp.get_linguistic_complexity(text)
        
        # Should return dictionary with expected keys
        expected_keys = [
            'stopword_ratio',
            'vocabulary_richness',
            'avg_sentence_length',
            'entity_density',
            'total_tokens',
            'unique_terms',
            'entity_count',
            'phrase_count'
        ]
        
        for key in expected_keys:
            self.assertIn(key, metrics)
    
    def test_complexity_values(self):
        """Test that complexity values are reasonable."""
        text = "The dog runs. The cat sleeps. The bird flies."
        metrics = self.nlp.get_linguistic_complexity(text)
        
        # All ratios should be between 0 and 1
        self.assertGreaterEqual(metrics['stopword_ratio'], 0)
        self.assertLessEqual(metrics['stopword_ratio'], 1)
        
        self.assertGreaterEqual(metrics['vocabulary_richness'], 0)
        self.assertLessEqual(metrics['vocabulary_richness'], 1)
    
    def test_complexity_comparison(self):
        """Test that complexity metrics differentiate texts."""
        simple = "Dog run. Cat sleep."
        complex = "The sophisticated canine rapidly traverses the verdant meadow."
        
        simple_metrics = self.nlp.get_linguistic_complexity(simple)
        complex_metrics = self.nlp.get_linguistic_complexity(complex)
        
        # Complex text should have different metrics
        self.assertNotEqual(
            simple_metrics['stopword_ratio'],
            complex_metrics['stopword_ratio']
        )


class TestNLPPhraseExtraction(unittest.TestCase):
    """Test phrase extraction."""
    
    def setUp(self):
        """Initialize pipeline."""
        self.nlp = NLPPipeline()
    
    def test_phrase_extraction(self):
        """Test phrase identification."""
        text = "The quick brown fox jumps over the fence"
        analysis = self.nlp.analyze(text)
        
        # Should have phrases
        self.assertGreater(len(analysis.phrases), 0)
    
    def test_phrase_structure(self):
        """Test Phrase dataclass structure."""
        text = "The big dog barked loudly"
        analysis = self.nlp.analyze(text)
        
        for phrase in analysis.phrases:
            self.assertIsNotNone(phrase.text)
            self.assertIsNotNone(phrase.phrase_type)
            self.assertIsNotNone(phrase.head)


class TestNLPIntegration(unittest.TestCase):
    """Test integration with other components."""
    
    def setUp(self):
        """Initialize pipeline."""
        self.nlp = NLPPipeline()
    
    def test_lemmatize_text_method(self):
        """Test text lemmatization."""
        text = "The companies are running faster"
        lemmatized = self.nlp.lemmatize_text(text)
        
        # Should return string
        self.assertIsInstance(lemmatized, str)
        self.assertGreater(len(lemmatized), 0)
    
    def test_full_analysis_consistency(self):
        """Test consistency across analysis components."""
        text = "Python developers love programming in Python"
        analysis = self.nlp.analyze(text)
        
        # Token count should match POS tags
        self.assertEqual(len(analysis.tokens), len(analysis.pos_tags))
        
        # Vocabulary should be subset of all tokens
        unique_tokens = set(t.text for t in analysis.tokens)
        self.assertEqual(len(analysis.vocabulary), len(unique_tokens))
    
    def test_analysis_reproducibility(self):
        """Test that analysis is reproducible."""
        text = "The quick brown fox"
        analysis1 = self.nlp.analyze(text)
        analysis2 = self.nlp.analyze(text)
        
        # Should produce identical results
        self.assertEqual(len(analysis1.tokens), len(analysis2.tokens))
        self.assertEqual(analysis1.pos_tags, analysis2.pos_tags)


class TestNLPEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Initialize pipeline."""
        self.nlp = NLPPipeline()
    
    def test_empty_text(self):
        """Test handling of empty text."""
        result = self.nlp.analyze("")
        # Should handle gracefully
        self.assertTrue(result is None or len(result.tokens) == 0)
    
    def test_single_word(self):
        """Test single word analysis."""
        result = self.nlp.analyze("Hello")
        self.assertIsNotNone(result)
        self.assertGreater(len(result.tokens), 0)
    
    def test_special_characters(self):
        """Test text with special characters."""
        text = "Email me@example.com or call 555-1234"
        result = self.nlp.analyze(text)
        self.assertIsNotNone(result)
    
    def test_unicode_text(self):
        """Test Unicode text handling."""
        text = "Café, naïve, résumé"
        result = self.nlp.analyze(text)
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
