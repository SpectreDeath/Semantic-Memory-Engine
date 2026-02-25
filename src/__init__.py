"""
SimpleMem Laboratory - Core Package
"""

import sys
import logging
import typing

# --- PYDANTIC V1 PATCH FOR PYTHON 3.14 ---
# Required for spacy and other Pydantic v1-dependent libraries on Python 3.14
def _patch_pydantic_v1():
    try:
        import pydantic.v1.main as pydantic_main
        from pydantic.v1.errors import ConfigError
        
        original_new = pydantic_main.ModelMetaclass.__new__
        
        def patched_new(mcs, name, bases, namespace, **kwargs):
            try:
                return original_new(mcs, name, bases, namespace, **kwargs)
            except (ConfigError, TypeError, Exception) as e:
                err_msg = str(e)
                if 'unable to infer type' in err_msg:
                    import re
                    match = re.search(r'attribute "([^"]+)"', err_msg)
                    if match:
                        attr_name = match.group(1)
                        if '__annotations__' not in namespace:
                            namespace['__annotations__'] = {}
                        namespace['__annotations__'][attr_name] = typing.Any
                        try:
                            return original_new(mcs, name, bases, namespace, **kwargs)
                        except: pass
                raise
        
        pydantic_main.ModelMetaclass.__new__ = patched_new
        
        # Also mock spacy.schemas if spacy is not yet imported
        # to prevent it from failing during later imports
        if 'spacy' not in sys.modules:
            class MockModel:
                def __init__(self, **kwargs): pass
                @classmethod
                def validate(cls, v): return v
            
            # Create a mock spacy.schemas module
            from types import ModuleType
            spacy_mock = ModuleType('spacy')
            schemas_mock = ModuleType('spacy.schemas')
            spacy_mock.schemas = schemas_mock
            
            # This is a bit risky but might help collection
            # sys.modules['spacy.schemas'] = schemas_mock
            
    except: pass

_patch_pydantic_v1()
# -----------------------------------------

# Configuration & Factory
from src.core.config import Config, get_config, ConfigError
from src.core.factory import ToolFactory

# Core Utilities
try:
    from src.core.centrifuge import Centrifuge
except Exception:
    Centrifuge = None

try:
    from src.core.semantic_db import SemanticMemory
except ImportError:
    SemanticMemory = None

from src.core.semantic_graph import SemanticGraph
from src.core.data_manager import DataManager
from src.core.nlp_pipeline import NLPPipeline

# Tier 2 - Event Bus Infrastructure
try:
    from src.core.events import EventBus, Event, EventType, get_event_bus, reset_event_bus
except ImportError:
    EventBus = None
    Event = None
    EventType = None
    get_event_bus = None
    reset_event_bus = None

# Tier 2 - Structured Logging Infrastructure
try:
    from src.core.logging_system import (
        StructuredLogger,
        LogLevel,
        LogManager,
        LogContext,
        get_logger,
        setup_logging,
        get_log_context,
        reset_logging,
    )
except ImportError:
    StructuredLogger = None
    LogLevel = None
    LogManager = None
    LogContext = None
    get_logger = None
    setup_logging = None
    get_log_context = None
    reset_logging = None

try:
    from src.core.advanced_nlp import AdvancedNLPEngine, AdvancedNLPAnalyzer
except Exception:
    AdvancedNLPEngine = None
    AdvancedNLPAnalyzer = None

# Phase 5 - Enhanced Analytics
try:
    from src.core.sentiment_analyzer import SentimentAnalyzer, SentimentAnalysis, EmotionType
except ImportError:
    SentimentAnalyzer = None
    SentimentAnalysis = None
    EmotionType = None

try:
    from src.core.text_summarizer import TextSummarizer, Summary, SummarizationType
except ImportError:
    TextSummarizer = None
    Summary = None
    SummarizationType = None

try:
    from src.core.entity_linker import EntityLinker, LinkedEntity, EntityType
except ImportError:
    EntityLinker = None
    LinkedEntity = None
    EntityType = None

try:
    from src.core.document_clusterer import DocumentClusterer, ClusteringResult
except ImportError:
    DocumentClusterer = None
    ClusteringResult = None

try:
    from src.analysis.knowledge_graph import KnowledgeGraph
except ImportError:
    KnowledgeGraph = None

try:
    from src.analysis.intelligence_reports import IntelligenceReports, IntelligenceReport
except Exception:
    IntelligenceReports = None
    IntelligenceReport = None

try:
    from src.analysis.overlap_discovery import OverlapDiscovery
except ImportError:
    OverlapDiscovery = None

try:
    from src.core.loom import SemanticLoom
except ImportError:
    SemanticLoom = None

# Scribe - Authorship Analysis
try:
    from src.scribe.engine import ScribeEngine, LinguisticFingerprint
except ImportError:
    ScribeEngine = None
    LinguisticFingerprint = None

# Scout - Adaptive Query System
try:
    from src.query.scout_integration import Scout
    from src.query.scout import AdaptiveRetriever, QueryComplexityEstimator
    from src.query.engine import SemanticSearchEngine
except ImportError:
    Scout = None
    AdaptiveRetriever = None
    QueryComplexityEstimator = None
    SemanticSearchEngine = None

# Synapse - Memory Consolidation
try:
    from src.synapse.synapse import MemoryConsolidator, BehavioralProfiler
except ImportError:
    MemoryConsolidator = None
    BehavioralProfiler = None

# Visualization
try:
    from src.visualization.dashboard import RhetoricAnalyzer
except ImportError:
    RhetoricAnalyzer = None

# Monitoring
try:
    from src.monitoring.diagnostics import SystemMonitor
except ImportError:
    SystemMonitor = None

# Forensic Utilities
try:
    from src.utils import (
        detect_outliers,
        load_audit_data,
        get_persona,
        update_persona,
        stream_project_mode,
        stream_trust_mode,
    )
except ImportError:
    detect_outliers = None
    load_audit_data = None
    get_persona = None
    update_persona = None
    stream_project_mode = None
    stream_trust_mode = None

# Orchestration
try:
    from src.orchestration.orchestrator import PipelineCoordinator, PipelineJobQueue
except (ImportError, NameError):
    PipelineCoordinator = None
    PipelineJobQueue = None

__version__ = "3.0.0"
__author__ = "SimpleMem Laboratory"
__description__ = "Refactored SimpleMem Toolkit with Semantic Memory"

__all__ = [
    # Configuration & Factory
    "Config",
    "get_config",
    "ConfigError",
    "ToolFactory",
    
    # Core
    "Centrifuge",
    "SemanticMemory",
    "SemanticGraph",
    "DataManager",
    "NLPPipeline",
    "AdvancedNLPEngine",
    "AdvancedNLPAnalyzer",
    "SemanticLoom",
    
    # Tier 2 - Event Bus
    "EventBus",
    "Event",
    "EventType",
    "get_event_bus",
    "reset_event_bus",
    
    # Tier 2 - Structured Logging
    "StructuredLogger",
    "LogLevel",
    "LogManager",
    "LogContext",
    "get_logger",
    "setup_logging",
    "get_log_context",
    "reset_logging",
    
    # Phase 5 - Enhanced Analytics
    "SentimentAnalyzer",
    "SentimentAnalysis",
    "EmotionType",
    "TextSummarizer",
    "Summary",
    "SummarizationType",
    "EntityLinker",
    "LinkedEntity",
    "EntityType",
    "DocumentClusterer",
    "ClusteringResult",
    "KnowledgeGraph",
    "IntelligenceReports",
    "IntelligenceReport",
    "OverlapDiscovery",
    
    # Scribe
    "ScribeEngine",
    "LinguisticFingerprint",
    
    # Scout
    "Scout",
    "AdaptiveRetriever",
    "QueryComplexityEstimator",
    "SemanticSearchEngine",
    
    # Synapse
    "MemoryConsolidator",
    "BehavioralProfiler",
    
    # Visualization
    "RhetoricAnalyzer",
    
    # Monitoring
    "SystemMonitor",
    
    # Forensic Utilities
    "detect_outliers",
    "load_audit_data",
    "get_persona",
    "update_persona",
    "stream_project_mode",
    "stream_trust_mode",
    
    # Orchestration
    "PipelineCoordinator",
    "PipelineJobQueue",
]
