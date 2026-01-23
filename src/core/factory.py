"""
Tool Factory - Central location for instantiating all SimpleMem tools.

This factory pattern provides:
- Centralized dependency injection
- Consistent initialization across the toolkit
- Easy testing and mocking
- Clear dependency management

Usage:
    from src.core.factory import ToolFactory
    
    scribe = ToolFactory.create_scribe()
    scout = ToolFactory.create_scout()
    semantic_search = ToolFactory.create_search_engine()
"""

from typing import Optional, Dict, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class ToolFactory:
    """
    Factory for creating and managing SimpleMem tools.
    
    Provides lazy-loading and singleton-like caching for tools
    that are expensive to initialize.
    """
    
    _instances: Dict[str, Any] = {}
    
    @classmethod
    def reset(cls):
        """Clear all cached instances (useful for testing)."""
        cls._instances.clear()
    
    @classmethod
    def create_scribe(cls, reset: bool = False) -> 'ScribeEngine':
        """
        Create or retrieve the ScribeEngine instance.
        
        Args:
            reset: Force creation of new instance, ignoring cache
        
        Returns:
            ScribeEngine instance
        """
        if reset or 'scribe' not in cls._instances:
            try:
                from src.scribe.engine import ScribeEngine
                cls._instances['scribe'] = ScribeEngine()
                logger.info("Created ScribeEngine instance")
            except Exception as e:
                logger.error(f"Failed to create ScribeEngine: {e}")
                raise
        return cls._instances['scribe']
    
    @classmethod
    def create_lexicon_importer(cls, reset: bool = False) -> 'LexiconImporter':
        """
        Create or retrieve the LexiconImporter instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            LexiconImporter instance
        """
        if reset or 'lexicon_importer' not in cls._instances:
            try:
                from src.scribe.lexicon_importer import LexiconImporter
                cls._instances['lexicon_importer'] = LexiconImporter()
                logger.info("Created LexiconImporter instance")
            except Exception as e:
                logger.error(f"Failed to create LexiconImporter: {e}")
                raise
        return cls._instances['lexicon_importer']
    
    @classmethod
    def create_aifdb_connector(cls, reset: bool = False) -> 'AIFdbConnector':
        """
        Create or retrieve the AIFdbConnector instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            AIFdbConnector instance
        """
        if reset or 'aifdb' not in cls._instances:
            try:
                from src.query.aifdb_connector import AIFdbConnector
                cls._instances['aifdb'] = AIFdbConnector()
                logger.info("Created AIFdbConnector instance")
            except Exception as e:
                logger.error(f"Failed to create AIFdbConnector: {e}")
                raise
        return cls._instances['aifdb']
    
    @classmethod
    def create_concept_resolver(cls, reset: bool = False) -> 'ConceptResolver':
        """
        Create or retrieve the ConceptResolver instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            ConceptResolver instance
        """
        if reset or 'concept_resolver' not in cls._instances:
            try:
                from src.query.concept_resolver import ConceptResolver
                cls._instances['concept_resolver'] = ConceptResolver()
                logger.info("Created ConceptResolver instance")
            except Exception as e:
                logger.error(f"Failed to create ConceptResolver: {e}")
                raise
        return cls._instances['concept_resolver']
    
    @classmethod
    def create_stylo_wrapper(cls, reset: bool = False) -> 'StyloWrapper':
        """
        Create or retrieve the StyloWrapper instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            StyloWrapper instance
        """
        if reset or 'stylo_wrapper' not in cls._instances:
            try:
                from src.scribe.stylo_wrapper import StyloWrapper
                cls._instances['stylo_wrapper'] = StyloWrapper()
                logger.info("Created StyloWrapper instance")
            except Exception as e:
                logger.error(f"Failed to create StyloWrapper: {e}")
                raise
        return cls._instances['stylo_wrapper']
    
    @classmethod
    def create_pystyl_wrapper(cls, reset: bool = False) -> 'PyStylWrapper':
        """
        Create or retrieve the PyStylWrapper instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            PyStylWrapper instance
        """
        if reset or 'pystyl' not in cls._instances:
            try:
                from src.scribe.pystyl_wrapper import PyStylWrapper
                cls._instances['pystyl'] = PyStylWrapper()
                logger.info("Created PyStylWrapper instance")
            except Exception as e:
                logger.error(f"Failed to create PyStylWrapper: {e}")
                raise
        return cls._instances['pystyl']
    
    @classmethod
    def create_rolling_delta(cls, reset: bool = False) -> 'RollingDelta':
        """
        Create or retrieve the RollingDelta instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            RollingDelta instance
        """
        if reset or 'rolling_delta' not in cls._instances:
            try:
                from src.scribe.rolling_delta import RollingDelta
                cls._instances['rolling_delta'] = RollingDelta()
                logger.info("Created RollingDelta instance")
            except Exception as e:
                logger.error(f"Failed to create RollingDelta: {e}")
                raise
        return cls._instances['rolling_delta']
    
    @classmethod
    def create_adaptive_learner(cls, reset: bool = False) -> 'AdaptiveLearner':
        """
        Create or retrieve the AdaptiveLearner instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            AdaptiveLearner instance
        """
        if reset or 'adaptive_learner' not in cls._instances:
            try:
                from src.scribe.adaptive_learner import AdaptiveLearner
                cls._instances['adaptive_learner'] = AdaptiveLearner()
                logger.info("Created AdaptiveLearner instance")
            except Exception as e:
                logger.error(f"Failed to create AdaptiveLearner: {e}")
                raise
        return cls._instances['adaptive_learner']
    
    @classmethod
    def create_forensic_scout(cls, reset: bool = False) -> 'ForensicScout':
        """
        Create or retrieve the ForensicScout instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            ForensicScout instance
        """
        if reset or 'forensic_scout' not in cls._instances:
            try:
                from src.harvester.forensic_scout import ForensicScout
                cls._instances['forensic_scout'] = ForensicScout()
                logger.info("Created ForensicScout instance")
            except Exception as e:
                logger.error(f"Failed to create ForensicScout: {e}")
                raise
        return cls._instances['forensic_scout']
    
    @classmethod
    def create_contrastive_analyzer(cls, reset: bool = False) -> 'ContrastiveAnalyzer':
        """
        Create or retrieve the ContrastiveAnalyzer instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            ContrastiveAnalyzer instance
        """
        if reset or 'contrastive_analyzer' not in cls._instances:
            try:
                from src.scribe.contrastive_analyzer import ContrastiveAnalyzer
                cls._instances['contrastive_analyzer'] = ContrastiveAnalyzer()
                logger.info("Created ContrastiveAnalyzer instance")
            except Exception as e:
                logger.error(f"Failed to create ContrastiveAnalyzer: {e}")
                raise
        return cls._instances['contrastive_analyzer']
    
    @classmethod
    def create_impostors_checker(cls, reset: bool = False) -> 'ImpostorsChecker':
        """
        Create or retrieve the ImpostorsChecker instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            ImpostorsChecker instance
        """
        if reset or 'impostors_checker' not in cls._instances:
            try:
                from src.scribe.impostors_checker import ImpostorsChecker
                cls._instances['impostors_checker'] = ImpostorsChecker()
                logger.info("Created ImpostorsChecker instance")
            except Exception as e:
                logger.error(f"Failed to create ImpostorsChecker: {e}")
                raise
        return cls._instances['impostors_checker']
    
    @classmethod
    def create_network_generator(cls, reset: bool = False) -> 'NetworkGenerator':
        """
        Create or retrieve the NetworkGenerator instance.
        
        Args:
            reset: Force creation of new instance
            
        Returns:
            NetworkGenerator instance
        """
        if reset or 'network_generator' not in cls._instances:
            try:
                from src.visualization.network_generator import NetworkGenerator
                cls._instances['network_generator'] = NetworkGenerator()
                logger.info("Created NetworkGenerator instance")
            except Exception as e:
                logger.error(f"Failed to create NetworkGenerator: {e}")
                raise
        return cls._instances['network_generator']
    
    @classmethod
    def create_scout(cls, reset: bool = False) -> 'Scout':
        """
        Create or retrieve the Scout instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            Scout instance
        """
        if reset or 'scout' not in cls._instances:
            try:
                from src.query.scout_integration import Scout
                cls._instances['scout'] = Scout()
                logger.info("Created Scout instance")
            except Exception as e:
                logger.error(f"Failed to create Scout: {e}")
                raise
        return cls._instances['scout']
    
    @classmethod
    def create_search_engine(cls, reset: bool = False) -> 'SemanticSearchEngine':
        """
        Create or retrieve the SemanticSearchEngine instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            SemanticSearchEngine instance
        """
        if reset or 'search' not in cls._instances:
            try:
                from src.query.engine import SemanticSearchEngine
                cls._instances['search'] = SemanticSearchEngine()
                logger.info("Created SemanticSearchEngine instance")
            except Exception as e:
                logger.error(f"Failed to create SemanticSearchEngine: {e}")
                raise
        return cls._instances['search']
    
    @classmethod
    def create_synapse(cls, reset: bool = False) -> 'MemoryConsolidator':
        """
        Create or retrieve the MemoryConsolidator instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            MemoryConsolidator instance
        """
        if reset or 'synapse' not in cls._instances:
            try:
                from src.synapse.synapse import MemoryConsolidator
                cls._instances['synapse'] = MemoryConsolidator()
                logger.info("Created MemoryConsolidator instance")
            except Exception as e:
                logger.error(f"Failed to create MemoryConsolidator: {e}")
                raise
        return cls._instances['synapse']
    
    @classmethod
    def create_centrifuge(cls, reset: bool = False) -> 'Centrifuge':
        """
        Create or retrieve the Centrifuge database instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            Centrifuge instance
        """
        if reset or 'centrifuge' not in cls._instances:
            try:
                from src.core.centrifuge import Centrifuge
                cls._instances['centrifuge'] = Centrifuge()
                logger.info("Created Centrifuge instance")
            except Exception as e:
                logger.error(f"Failed to create Centrifuge: {e}")
                raise
        return cls._instances['centrifuge']
    
    @classmethod
    def create_event_bus(cls, reset: bool = False) -> 'EventBus':
        """
        Create or retrieve the EventBus instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            EventBus instance
        """
        if reset or 'event_bus' not in cls._instances:
            try:
                from src.core.events import EventBus
                cls._instances['event_bus'] = EventBus()
                logger.info("Created EventBus instance")
            except Exception as e:
                logger.error(f"Failed to create EventBus: {e}")
                raise
        return cls._instances['event_bus']
    
    @classmethod
    def create_log_manager(cls, reset: bool = False) -> 'LogManager':
        """
        Create or retrieve the LogManager instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            LogManager instance
        """
        if reset or 'log_manager' not in cls._instances:
            try:
                from src.core.logging_system import LogManager, setup_logging
                LogManager.setup()
                cls._instances['log_manager'] = LogManager()
                logger.info("Created LogManager instance")
            except Exception as e:
                logger.error(f"Failed to create LogManager: {e}")
                raise
        return cls._instances['log_manager']
    
    @classmethod
    def create_semantic_db(cls, reset: bool = False) -> 'SemanticMemory':
        """
        Create or retrieve the SemanticMemory (ChromaDB) instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            SemanticMemory instance
        """
        if reset or 'semantic_db' not in cls._instances:
            try:
                from src.core.semantic_db import SemanticMemory
                cls._instances['semantic_db'] = SemanticMemory()
                logger.info("Created SemanticMemory instance")
            except Exception as e:
                logger.error(f"Failed to create SemanticMemory: {e}")
                raise
        return cls._instances['semantic_db']
    
    @classmethod
    def create_semantic_graph(cls, reset: bool = False) -> 'SemanticGraph':
        """
        Create or retrieve the SemanticGraph (WordNet) instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            SemanticGraph instance
        """
        if reset or 'semantic_graph' not in cls._instances:
            try:
                from src.core.semantic_graph import SemanticGraph
                cls._instances['semantic_graph'] = SemanticGraph()
                logger.info("Created SemanticGraph instance")
            except Exception as e:
                logger.error(f"Failed to create SemanticGraph: {e}")
                raise
        return cls._instances['semantic_graph']
    
    @classmethod
    def create_data_manager(cls, reset: bool = False) -> 'DataManager':
        """
        Create or retrieve the DataManager instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            DataManager instance
        """
        if reset or 'data_manager' not in cls._instances:
            try:
                from src.core.data_manager import DataManager
                cls._instances['data_manager'] = DataManager()
                logger.info("Created DataManager instance")
            except Exception as e:
                logger.error(f"Failed to create DataManager: {e}")
                raise
        return cls._instances['data_manager']
    
    @classmethod
    def create_nlp_pipeline(cls, reset: bool = False) -> 'NLPPipeline':
        """
        Create or retrieve the NLPPipeline instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            NLPPipeline instance
        """
        if reset or 'nlp_pipeline' not in cls._instances:
            try:
                from src.core.nlp_pipeline import NLPPipeline
                cls._instances['nlp_pipeline'] = NLPPipeline()
                logger.info("Created NLPPipeline instance")
            except Exception as e:
                logger.error(f"Failed to create NLPPipeline: {e}")
                raise
        return cls._instances['nlp_pipeline']
    
    @classmethod
    def create_advanced_nlp(cls, reset: bool = False) -> 'AdvancedNLPEngine':
        """
        Create or retrieve the AdvancedNLPEngine instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            AdvancedNLPEngine instance
        """
        if reset or 'advanced_nlp' not in cls._instances:
            try:
                from src.core.advanced_nlp import AdvancedNLPEngine
                cls._instances['advanced_nlp'] = AdvancedNLPEngine()
                logger.info("Created AdvancedNLPEngine instance")
            except Exception as e:
                logger.error(f"Failed to create AdvancedNLPEngine: {e}")
                raise
        return cls._instances['advanced_nlp']
    
    @classmethod
    def create_monitor(cls, reset: bool = False) -> 'SystemMonitor':
        """
        Create or retrieve the SystemMonitor instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            SystemMonitor instance
        """
        if reset or 'monitor' not in cls._instances:
            try:
                from src.monitoring.diagnostics import SystemMonitor
                cls._instances['monitor'] = SystemMonitor()
                logger.info("Created SystemMonitor instance")
            except Exception as e:
                logger.error(f"Failed to create SystemMonitor: {e}")
                raise
        return cls._instances['monitor']
    
    @classmethod
    def create_orchestrator(cls, reset: bool = False) -> 'PipelineCoordinator':
        """
        Create or retrieve the PipelineCoordinator instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            PipelineCoordinator instance
        """
        if reset or 'orchestrator' not in cls._instances:
            try:
                from src.orchestration.orchestrator import PipelineCoordinator
                cls._instances['orchestrator'] = PipelineCoordinator()
                logger.info("Created PipelineCoordinator instance")
            except Exception as e:
                logger.error(f"Failed to create PipelineCoordinator: {e}")
                raise
        return cls._instances['orchestrator']
    
    @classmethod
    def create_sentiment_analyzer(cls, reset: bool = False) -> 'SentimentAnalyzer':
        """
        Create or retrieve the SentimentAnalyzer instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            SentimentAnalyzer instance
        """
        if reset or 'sentiment' not in cls._instances:
            try:
                from src.core.sentiment_analyzer import SentimentAnalyzer
                cls._instances['sentiment'] = SentimentAnalyzer()
                logger.info("Created SentimentAnalyzer instance")
            except Exception as e:
                logger.error(f"Failed to create SentimentAnalyzer: {e}")
                raise
        return cls._instances['sentiment']
    
    @classmethod
    def create_text_summarizer(cls, reset: bool = False) -> 'TextSummarizer':
        """
        Create or retrieve the TextSummarizer instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            TextSummarizer instance
        """
        if reset or 'summarizer' not in cls._instances:
            try:
                from src.core.text_summarizer import TextSummarizer
                cls._instances['summarizer'] = TextSummarizer()
                logger.info("Created TextSummarizer instance")
            except Exception as e:
                logger.error(f"Failed to create TextSummarizer: {e}")
                raise
        return cls._instances['summarizer']
    
    @classmethod
    def create_entity_linker(cls, reset: bool = False) -> 'EntityLinker':
        """
        Create or retrieve the EntityLinker instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            EntityLinker instance
        """
        if reset or 'entity_linker' not in cls._instances:
            try:
                from src.core.entity_linker import EntityLinker
                cls._instances['entity_linker'] = EntityLinker()
                logger.info("Created EntityLinker instance")
            except Exception as e:
                logger.error(f"Failed to create EntityLinker: {e}")
                raise
        return cls._instances['entity_linker']
    
    @classmethod
    def create_document_clusterer(cls, reset: bool = False) -> 'DocumentClusterer':
        """
        Create or retrieve the DocumentClusterer instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            DocumentClusterer instance
        """
        if reset or 'clusterer' not in cls._instances:
            try:
                from src.core.document_clusterer import DocumentClusterer
                cls._instances['clusterer'] = DocumentClusterer()
                logger.info("Created DocumentClusterer instance")
            except Exception as e:
                logger.error(f"Failed to create DocumentClusterer: {e}")
                raise
        return cls._instances['clusterer']
    
    @classmethod
    def create_knowledge_graph(cls, reset: bool = False) -> 'KnowledgeGraph':
        """
        Create or retrieve the KnowledgeGraph instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            KnowledgeGraph instance
        """
        if reset or 'knowledge_graph' not in cls._instances:
            try:
                from src.analysis.knowledge_graph import KnowledgeGraph
                cls._instances['knowledge_graph'] = KnowledgeGraph()
                logger.info("Created KnowledgeGraph instance")
            except Exception as e:
                logger.error(f"Failed to create KnowledgeGraph: {e}")
                raise
        return cls._instances['knowledge_graph']
    
    @classmethod
    def create_intelligence_reports(cls, reset: bool = False) -> 'IntelligenceReports':
        """
        Create or retrieve the IntelligenceReports instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            IntelligenceReports instance
        """
        if reset or 'intelligence_reports' not in cls._instances:
            try:
                from src.analysis.intelligence_reports import IntelligenceReports
                cls._instances['intelligence_reports'] = IntelligenceReports()
                logger.info("Created IntelligenceReports instance")
            except Exception as e:
                logger.error(f"Failed to create IntelligenceReports: {e}")
                raise
        return cls._instances['intelligence_reports']
    
    @classmethod
    def create_overlap_discovery(cls, reset: bool = False) -> 'OverlapDiscovery':
        """
        Create or retrieve the OverlapDiscovery instance.
        
        Args:
            reset: Force creation of new instance
        
        Returns:
            OverlapDiscovery instance
        """
        if reset or 'overlap_discovery' not in cls._instances:
            try:
                from src.analysis.overlap_discovery import OverlapDiscovery
                cls._instances['overlap_discovery'] = OverlapDiscovery()
                logger.info("Created OverlapDiscovery instance")
            except Exception as e:
                logger.error(f"Failed to create OverlapDiscovery: {e}")
                raise
        return cls._instances['overlap_discovery']
    
    @classmethod
    def get_instance(cls, tool_name: str) -> Optional[Any]:
        """
        Get a cached tool instance by name.
        
        Args:
            tool_name: Name of the tool (e.g., 'scribe', 'scout')
        
        Returns:
            Tool instance or None if not found
        """
        return cls._instances.get(tool_name)
    
    @classmethod
    def list_instances(cls) -> Dict[str, str]:
        """
        List all cached tool instances.
        
        Returns:
            Dictionary mapping tool names to their types
        """
        return {
            name: type(instance).__name__
            for name, instance in cls._instances.items()
        }
    
    @classmethod
    def health_check(cls) -> Dict[str, bool]:
        """
        Check health status of all cached instances.
        
        Returns:
            Dictionary mapping tool names to their health status
        """
        health = {}
        for name, instance in cls._instances.items():
            try:
                if hasattr(instance, 'health_check'):
                    health[name] = instance.health_check()
                else:
                    # Basic check - instance exists
                    health[name] = True
            except Exception as e:
                logger.warning(f"Health check failed for {name}: {e}")
                health[name] = False
        return health
