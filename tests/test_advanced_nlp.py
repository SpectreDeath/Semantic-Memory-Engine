"""
Test suite for Advanced NLP Engine (Phase 4).

Comprehensive testing of:
- Dependency parsing
- Coreference resolution
- Semantic role labeling
- Event extraction
"""

import unittest

from src import ToolFactory
from src.core import advanced_nlp


class TestAdvancedNLPEngineBasics(unittest.TestCase):
    """Test basic Advanced NLP functionality."""
    
    def setUp(self):
        """Initialize engine."""
        self.engine = advanced_nlp.AdvancedNLPEngine()
    
    def test_engine_availability(self):
        """Test engine is available."""
        self.assertTrue(self.engine.is_available())
    
    def test_simple_analysis(self):
        """Test complete advanced analysis."""
        text = "John gave Mary a book yesterday."
        analysis = self.engine.analyze_advanced(text)
        
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.text, text)
        self.assertGreater(len(analysis.sentences), 0)
    
    def test_analysis_components(self):
        """Test analysis has all components."""
        text = "She read the book."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            # Check structure
            self.assertIsNotNone(analysis.dependencies)
            self.assertIsNotNone(analysis.coreference_chains)
            self.assertIsNotNone(analysis.semantic_roles)
            self.assertIsNotNone(analysis.events)


class TestDependencyParsing(unittest.TestCase):
    """Test dependency parsing functionality."""
    
    def setUp(self):
        """Initialize engine."""
        self.engine = advanced_nlp.AdvancedNLPEngine()
    
    def test_dependency_extraction(self):
        """Test dependency relation extraction."""
        text = "The dog chased the cat."
        deps = self.engine.extract_dependencies(text)
        
        self.assertIsInstance(deps, list)
    
    def test_dependency_relation_structure(self):
        """Test DependencyRelation structure."""
        text = "John sees Mary."
        deps = self.engine.extract_dependencies(text)
        
        for dep in deps:
            self.assertIsNotNone(dep.head)
            self.assertIsNotNone(dep.dependent)
            self.assertIsNotNone(dep.relation_type)
    
    def test_parse_tree_generation(self):
        """Test parse tree generation."""
        text = "Dogs eat bones."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            self.assertIsNotNone(analysis.parse_trees)


class TestCoreferenceResolution(unittest.TestCase):
    """Test coreference resolution."""
    
    def setUp(self):
        """Initialize engine."""
        self.engine = advanced_nlp.AdvancedNLPEngine()
    
    def test_coreference_resolution(self):
        """Test coreference chain detection."""
        text = "John went to the store. He bought milk."
        chains = self.engine.resolve_coreferences(text)
        
        self.assertIsInstance(chains, list)
    
    def test_coreference_chain_structure(self):
        """Test CoreferenceChain structure."""
        text = "Mary read a book. She enjoyed it."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            for chain in analysis.coreference_chains:
                self.assertIsNotNone(chain.representative)
                self.assertIsInstance(chain.mentions, list)
    
    def test_coreference_resolution_application(self):
        """Test coreference resolution to text."""
        text = "John likes Mary. He sees her."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            # Should have resolved text
            self.assertIsNotNone(analysis.resolved_text)
            self.assertIsInstance(analysis.resolved_text, str)


class TestSemanticRoleLabeling(unittest.TestCase):
    """Test semantic role labeling."""
    
    def setUp(self):
        """Initialize engine."""
        self.engine = advanced_nlp.AdvancedNLPEngine()
    
    def test_semantic_role_extraction(self):
        """Test semantic role extraction."""
        text = "John gave Mary a book."
        roles = self.engine.extract_semantic_roles(text)
        
        self.assertIsInstance(roles, list)
    
    def test_semantic_role_structure(self):
        """Test SemanticRoleLabel structure."""
        text = "The teacher gave the student homework."
        roles = self.engine.extract_semantic_roles(text)
        
        for role in roles:
            self.assertIsNotNone(role.predicate)
            self.assertIsNotNone(role.role)
            self.assertIsNotNone(role.argument)
    
    def test_predicate_identification(self):
        """Test predicate identification."""
        text = "She walks slowly."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            self.assertIsNotNone(analysis.predicates)


class TestEventExtraction(unittest.TestCase):
    """Test event extraction."""
    
    def setUp(self):
        """Initialize engine."""
        self.engine = advanced_nlp.AdvancedNLPEngine()
    
    def test_event_extraction(self):
        """Test event extraction."""
        text = "John married Mary in Paris."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            self.assertIsInstance(analysis.events, list)
    
    def test_event_structure(self):
        """Test Event structure."""
        text = "She gave him a gift."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            for event in analysis.events:
                self.assertIsNotNone(event.event_trigger)
                self.assertIsInstance(event.participants, dict)
    
    def test_temporal_extraction(self):
        """Test temporal marker extraction."""
        text = "Yesterday, they went to the store. Today they are at home."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            self.assertIsNotNone(analysis.temporal_markers)
    
    def test_spatial_extraction(self):
        """Test spatial marker extraction."""
        text = "She went north to the mountain. He stayed behind."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            self.assertIsNotNone(analysis.spatial_markers)


class TestSemanticSummary(unittest.TestCase):
    """Test semantic summary extraction."""
    
    def setUp(self):
        """Initialize engine."""
        self.engine = advanced_nlp.AdvancedNLPEngine()
    
    def test_key_participants(self):
        """Test key participant extraction."""
        text = "John and Mary went to the party with Tom."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            self.assertIsInstance(analysis.key_participants, set)
    
    def test_key_events(self):
        """Test key event extraction."""
        text = "She ran quickly and jumped high."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            self.assertIsInstance(analysis.key_events, set)


class TestAdvancedNLPAnalyzer(unittest.TestCase):
    """Test high-level analyzer API."""
    
    def setUp(self):
        """Initialize analyzer."""
        self.analyzer = advanced_nlp.AdvancedNLPAnalyzer()
    
    def test_story_analysis(self):
        """Test story structure analysis."""
        text = "John and Mary lived in Boston. He worked as a doctor. She taught mathematics. They loved the city."
        result = self.analyzer.analyze_story(text)
        
        self.assertIsInstance(result, dict)
        if result:
            self.assertIn('characters', result)
            self.assertIn('events', result)
            self.assertIn('locations', result)
    
    def test_relationship_analysis(self):
        """Test relationship extraction."""
        text = "The president visited the capital yesterday."
        result = self.analyzer.analyze_relationships(text)
        
        self.assertIsInstance(result, dict)
        if result:
            self.assertIn('dependencies', result)
            self.assertIn('predicates', result)


class TestAdvancedNLPIntegration(unittest.TestCase):
    """Test integration with other components."""
    
    def setUp(self):
        """Initialize engine."""
        self.engine = advanced_nlp.AdvancedNLPEngine()
    
    def test_integration_with_nlp_pipeline(self):
        """Test integration with base NLPPipeline."""
        text = "John gave Mary a book."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            # Should have base analysis
            self.assertIsNotNone(analysis.base_analysis)
    
    def test_comprehensive_analysis(self):
        """Test comprehensive analysis."""
        text = "Yesterday, John went to New York. He met with Sarah and they discussed the project."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            # All components populated
            self.assertGreater(len(analysis.dependencies), 0)
            self.assertGreater(len(analysis.temporal_markers), 0)


class TestAdvancedNLPEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Initialize engine."""
        self.engine = advanced_nlp.AdvancedNLPEngine()
    
    def test_empty_text(self):
        """Test empty text handling."""
        result = self.engine.analyze_advanced("")
        # Should handle gracefully - returns analysis with empty or single empty sentence
        self.assertIsNotNone(result)
        # Either empty list or list with single empty string
        self.assertTrue(len(result.sentences) == 0 or (len(result.sentences) == 1 and result.sentences[0] == ""))
    
    def test_single_word(self):
        """Test single word analysis."""
        result = self.engine.analyze_advanced("Hello")
        if result:
            self.assertIsNotNone(result.text)
    
    def test_complex_sentence(self):
        """Test complex sentence analysis."""
        text = "Although John, who was a doctor, had warned Mary that the operation was dangerous, she decided to proceed anyway, knowing that without it, she would surely die."
        analysis = self.engine.analyze_advanced(text)
        
        if analysis:
            # Should handle complex structure
            self.assertIsNotNone(analysis)


class TestFactoryIntegration(unittest.TestCase):
    """Test factory integration."""
    
    def test_factory_creation(self):
        """Test factory creates advanced NLP engine."""
        
        engine = ToolFactory.create_advanced_nlp()
        self.assertIsNotNone(engine)
        self.assertTrue(engine.is_available())
    
    def test_factory_caching(self):
        """Test factory caching."""
        
        engine1 = ToolFactory.create_advanced_nlp()
        engine2 = ToolFactory.create_advanced_nlp()
        
        # Should return same instance
        self.assertIs(engine1, engine2)
    
    def test_factory_reset(self):
        """Test factory reset."""
        
        engine1 = ToolFactory.create_advanced_nlp()
        engine2 = ToolFactory.create_advanced_nlp(reset=True)
        
        # Should be different instances
        self.assertIsNot(engine1, engine2)


if __name__ == '__main__':
    unittest.main()
