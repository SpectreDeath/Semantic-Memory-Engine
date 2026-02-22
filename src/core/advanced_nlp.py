"""
Advanced NLP Engine - Phase 4 Deep Linguistic Analysis

Provides sophisticated NLP capabilities beyond basic tokenization:
- Dependency parsing (syntactic trees, relationships)
- Coreference resolution (pronoun linkage, entity chains)
- Semantic role labeling (predicate-argument structures)
- Event extraction (actions, participants, temporal info)

Builds on NLPPipeline for comprehensive semantic understanding.

Usage:
    from src.core.advanced_nlp import AdvancedNLPEngine
    
    advanced = AdvancedNLPEngine()
    text = "John gave Mary a book. She read it yesterday."
    
    # Dependency parsing
    deps = advanced.extract_dependencies(text)
    
    # Coreference resolution
    resolved = advanced.resolve_coreferences(text)
    
    # Semantic role labeling
    srl = advanced.extract_semantic_roles(text)
    
    # Full analysis
    analysis = advanced.analyze_advanced(text)
"""

import sys
import logging
import typing

# --- PYDANTIC V1 PATCH FOR PYTHON 3.14 ---
def _patch_pydantic_v1():
    try:
        import pydantic.v1.main as pydantic_main
        from pydantic.v1.errors import ConfigError
        original_new = pydantic_main.ModelMetaclass.__new__
        def patched_new(mcs, name, bases, namespace, **kwargs):
            try:
                return original_new(mcs, name, bases, namespace, **kwargs)
            except ConfigError as e:
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
    except: pass

_patch_pydantic_v1()
# -----------------------------------------

# Standard library imports
import dataclasses
import enum
import logging
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import spacy

from src.core import data_manager, nlp_pipeline, semantic_graph

logger = logging.getLogger(__name__)


class DependencyType(enum.Enum):
    """Dependency relationship types."""
    SUBJECT = "nsubj"  # Nominal subject
    OBJECT = "dobj"    # Direct object
    INDIRECT_OBJECT = "iobj"  # Indirect object
    MODIFIER = "mod"   # Modifier
    PREPOSITION = "prep"
    CONJUNCTION = "conj"
    NEGATION = "neg"
    AUXILIARY = "aux"
    OTHER = "other"


class CorefType(enum.Enum):
    """Coreference resolution types."""
    PRONOUN = "pronoun"
    DEFINITE_NP = "definite_np"
    PROPER_NOUN = "proper_noun"
    DEMONSTRATIVE = "demonstrative"
    RELATIVE = "relative"


class SemanticRole(enum.Enum):
    """Semantic role types (PropBank-style)."""
    AGENT = "A0"              # Who is doing the action
    PATIENT = "A1"            # What is being acted upon
    INSTRUMENT = "A2"         # What is used
    LOCATION = "AM-LOC"       # Where
    TEMPORAL = "AM-TMP"       # When
    MANNER = "AM-MNR"         # How
    PURPOSE = "AM-PRP"        # Why
    CAUSE = "AM-CAU"          # Why (causal)
    OTHER = "OTHER"


@dataclasses.dataclass
class DependencyRelation:
    """Dependency parse relation."""
    head: str                  # Head word
    head_pos: str             # Head POS tag
    dependent: str            # Dependent word
    dependent_pos: str        # Dependent POS tag
    relation_type: str        # Dependency type (nsubj, obj, etc)
    head_idx: int             # Head position in sentence
    dependent_idx: int        # Dependent position


@dataclasses.dataclass
class CoreferenceChain:
    """Linked mentions of same entity."""
    entity_id: int            # Unique entity ID
    mentions: List[str]       # All mention texts
    mention_indices: List[Tuple[int, int]] # (start, end) positions
    entity_type: Optional[str] # PERSON, ORG, LOC, etc
    representative: str       # Main/first mention


@dataclasses.dataclass
class SemanticRoleLabel:
    """Semantic role for predicate argument."""
    predicate: str            # The action/state verb
    predicate_idx: int        # Position in sentence
    role: str                 # Role type (A0, A1, AM-LOC, etc)
    argument: str             # The argument text
    argument_span: Tuple[int, int] # Character positions


@dataclasses.dataclass
class Event:
    """Extracted event with participants."""
    event_trigger: str        # Main verb/action
    event_type: Optional[str] # EVENT_TYPE (if classified)
    participants: Dict[str, str] # Role -> entity mapping
    temporal_info: Optional[str] # When it happened
    location: Optional[str]   # Where it happened
    confidence: float         # Extraction confidence


@dataclasses.dataclass
class AdvancedAnalysis:
    """Complete advanced NLP analysis."""
    text: str
    sentences: List[str]
    base_analysis: Optional[nlp_pipeline.NLPAnalysis] # From NLPPipeline
    
    # Dependency parsing
    dependencies: List[DependencyRelation]
    parse_trees: List[str]    # Formatted tree strings
    
    # Coreference resolution
    coreference_chains: List[CoreferenceChain]
    resolved_text: str        # Text with coreferences resolved
    
    # Semantic role labeling
    semantic_roles: List[SemanticRoleLabel]
    predicates: List[str]     # Identified predicates
    
    # Event extraction
    events: List[Event]
    
    # Semantic summary
    key_participants: Set[str]
    key_events: Set[str]
    temporal_markers: List[str]
    spatial_markers: List[str]


class AdvancedNLPEngine:
    """
    Advanced NLP analysis engine with dependency parsing,
    coreference resolution, and semantic role labeling.
    """
    
    def __init__(self, use_spacy: bool = True):
        """
        Initialize advanced NLP engine.
        
        Args:
            use_spacy: Try to use spaCy if available (better parsing)
        """
        self.use_spacy = use_spacy
        self.nlp_pipeline = nlp_pipeline.NLPPipeline()
        self.data_manager = data_manager.DataManager()
        self.semantic_graph = semantic_graph.SemanticGraph()
        
        # Try spacy
        self.spacy_model = None
        if use_spacy:
            try:
                self.spacy_model = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded for advanced parsing")
            except Exception as e:
                logger.warning(f"spaCy not available: {e}")
        
        # Check availability
        self._available = True
        if not self.nlp_pipeline.is_available():
            logger.warning("NLPPipeline not available")
            self._available = False
        
        logger.info("AdvancedNLPEngine initialized")
    
    def is_available(self) -> bool:
        """Check if engine is available."""
        return self._available
    
    def analyze_advanced(self, text: str) -> Optional[AdvancedAnalysis]:
        """
        Perform complete advanced NLP analysis.
        
        Args:
            text: Text to analyze
        
        Returns:
            AdvancedAnalysis with all linguistic features
        """
        if not self._available:
            logger.error("Advanced NLP engine not available")
            return None
        
        try:
            logger.debug(f"Advanced analysis: {len(text)} chars")
            
            # Base analysis
            sentences = self.data_manager.sentence_tokenize(text)
            base_analysis = self.nlp_pipeline.analyze(text)
            
            # Dependency parsing
            dependencies = self._extract_dependencies(text, sentences)
            parse_trees = self._generate_parse_trees(text, sentences)
            
            # Coreference resolution
            coref_chains = self._resolve_coreferences(text, sentences)
            resolved_text = self._apply_coref_resolution(text, coref_chains)
            
            # Semantic role labeling
            semantic_roles = self._extract_semantic_roles(text, sentences)
            predicates = list(set(sr.predicate for sr in semantic_roles))
            
            # Event extraction
            events = self._extract_events(text, semantic_roles, coref_chains)
            
            # Extract semantic summary
            key_participants = set()
            for chain in coref_chains:
                if chain.entity_type in ('PERSON', 'ORG', 'GPE'):
                    key_participants.add(chain.representative)
            
            key_events = set(e.event_trigger for e in events)
            temporal_markers = self._extract_temporal_markers(text)
            spatial_markers = self._extract_spatial_markers(text)
            
            analysis = AdvancedAnalysis(
                text=text,
                sentences=sentences,
                base_analysis=base_analysis,
                dependencies=dependencies,
                parse_trees=parse_trees,
                coreference_chains=coref_chains,
                resolved_text=resolved_text,
                semantic_roles=semantic_roles,
                predicates=predicates,
                events=events,
                key_participants=key_participants,
                key_events=key_events,
                temporal_markers=temporal_markers,
                spatial_markers=spatial_markers
            )
            
            logger.debug(f"Advanced analysis complete: "
                        f"{len(dependencies)} deps, "
                        f"{len(coref_chains)} coref chains, "
                        f"{len(events)} events")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Advanced analysis failed: {e}")
            return None
    
    def extract_dependencies(self, text: str) -> List[DependencyRelation]:
        """
        Extract syntactic dependency relations.
        
        Args:
            text: Text to parse
        
        Returns:
            List of dependency relations
        """
        if self.spacy_model:
            return self._extract_dependencies_spacy(text)
        else:
            return self._extract_dependencies_nltk(text)
    
    def resolve_coreferences(self, text: str) -> List[CoreferenceChain]:
        """
        Resolve pronoun and entity coreferences.
        
        Args:
            text: Text to process
        
        Returns:
            List of coreference chains
        """
        return self._resolve_coreferences(text, 
                                         self.data_manager.sentence_tokenize(text))
    
    def extract_semantic_roles(self, text: str) -> List[SemanticRoleLabel]:
        """
        Extract semantic role labels.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of semantic role labels
        """
        sentences = self.data_manager.sentence_tokenize(text)
        return self._extract_semantic_roles(text, sentences)
    
    # Private helper methods
    
    def _extract_dependencies(self, text: str, sentences: List[str]) -> List[DependencyRelation]:
        """Extract dependencies using spaCy."""
        if not self.spacy_model:
            return []
        
        dependencies = []
        doc = self.spacy_model(text)
        
        for token in doc:
            if token.head != token:
                dep = DependencyRelation(
                    head=token.head.text,
                    head_pos=token.head.pos_,
                    dependent=token.text,
                    dependent_pos=token.pos_,
                    relation_type=token.dep_,
                    head_idx=token.head.i,
                    dependent_idx=token.i
                )
                dependencies.append(dep)
        
        return dependencies

    def _extract_dependencies_spacy(self, text: str) -> List[DependencyRelation]:
        """Extract dependencies using spaCy."""
        if not self.spacy_model:
            return []
        
        dependencies = []
        doc = self.spacy_model(text)
        
        for token in doc:
            if token.head != token:
                dep = DependencyRelation(
                    head=token.head.text,
                    head_pos=token.head.pos_,
                    dependent=token.text,
                    dependent_pos=token.pos_,
                    relation_type=token.dep_,
                    head_idx=token.head.i,
                    dependent_idx=token.i
                )
                dependencies.append(dep)
        
        return dependencies
    
    def _extract_dependencies_nltk(self, text: str) -> List[DependencyRelation]:
        """Extract dependencies using NLTK (basic)."""
        # NLTK dependency parsing requires specific trained models
        # For now, return empty list - production would use spacy
        logger.warning("NLTK dependency parsing requires specialized models")
        return []
    
    def _resolve_coreferences(self, text: str, 
                             sentences: List[str]) -> List[CoreferenceChain]:
        """
        Resolve coreferences using simple heuristics.
        Production: use neuralcoref or similar library.
        """
        coref_chains = []
        
        # Use spacy if available for better coreference
        if self.spacy_model:
            try:
                doc = self.spacy_model(text)
                
                # Track entities
                entity_mentions = {}
                for ent in doc.ents:
                    if ent.label_ not in entity_mentions:
                        entity_mentions[ent.label_] = []
                    entity_mentions[ent.label_].append(ent.text)
                
                # Create chains
                for entity_type, mentions in entity_mentions.items():
                    if mentions:
                        chain = CoreferenceChain(
                            entity_id=len(coref_chains),
                            mentions=mentions,
                            mention_indices=[(0, len(m)) for m in mentions],
                            entity_type=entity_type,
                            representative=mentions[0]
                        )
                        coref_chains.append(chain)
            except Exception as e:
                logger.warning(f"spaCy coreference failed: {e}")
        
        return coref_chains
    
    def _apply_coref_resolution(self, text: str, 
                                chains: List[CoreferenceChain]) -> str:
        """Apply coreference resolution to text."""
        # Replace pronouns with entity representatives
        resolved = text
        
        for chain in chains:
            for mention in chain.mentions[1:]:  # Skip first mention
                # Simple replacement (production: use proper alignment)
                resolved = resolved.replace(mention, chain.representative)
        
        return resolved
    
    def _extract_semantic_roles(self, text: str, 
                               sentences: List[str]) -> List[SemanticRoleLabel]:
        """
        Extract semantic roles (simplified).
        Production: use semantic role labeling library
        """
        roles = []
        
        # This is simplified - production uses SRL models
        # For now, identify basic predicate-argument structures
        
        if self.spacy_model:
            doc = self.spacy_model(text)
            
            for token in doc:
                # Find verbs as predicates
                if token.pos_ == "VERB":
                    # Look for common argument patterns
                    for child in token.children:
                        if child.dep_ in ("nsubj", "dobj", "iobj"):
                            role = SemanticRoleLabel(
                                predicate=token.text,
                                predicate_idx=token.i,
                                role=child.dep_,
                                argument=child.text,
                                argument_span=(child.idx, child.idx + len(child.text))
                            )
                            roles.append(role)
        
        return roles
    
    def _extract_events(self, text: str, semantic_roles: List[SemanticRoleLabel],
                       coref_chains: List[CoreferenceChain]) -> List[Event]:
        """Extract events from semantic roles."""
        events = []
        processed_predicates = set()
        
        for sr in semantic_roles:
            if sr.predicate not in processed_predicates:
                # Find all roles for this predicate
                predicate_roles = [r for r in semantic_roles 
                                 if r.predicate == sr.predicate]
                
                # Build participant map
                participants = {}
                for role in predicate_roles:
                    participants[role.role] = role.argument
                
                event = Event(
                    event_trigger=sr.predicate,
                    event_type=None,  # Could be classified
                    participants=participants,
                    temporal_info=None,
                    location=None,
                    confidence=0.7  # Simplified
                )
                events.append(event)
                processed_predicates.add(sr.predicate)
        
        return events
    
    def _extract_temporal_markers(self, text: str) -> List[str]:
        """Extract temporal expressions."""
        # Simple extraction of common temporal markers
        temporal_words = [
            'yesterday', 'today', 'tomorrow',
            'morning', 'afternoon', 'evening', 'night',
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
            'Saturday', 'Sunday', 'January', 'February', 'March',
            'April', 'May', 'June', 'July', 'August', 'September',
            'October', 'November', 'December',
            'ago', 'after', 'before', 'during', 'while', 'when',
            'now', 'then', 'soon', 'later', 'earlier'
        ]
        
        text_lower = text.lower()
        found_markers = []
        for marker in temporal_words:
            if marker in text_lower:
                found_markers.append(marker)
        
        return found_markers
    
    def _extract_spatial_markers(self, text: str) -> List[str]:
        """Extract spatial/location expressions."""
        spatial_words = [
            'above', 'below', 'left', 'right', 'north', 'south',
            'east', 'west', 'inside', 'outside', 'between', 'among',
            'near', 'far', 'beside', 'behind', 'front', 'back',
            'up', 'down', 'here', 'there', 'where'
        ]
        
        text_lower = text.lower()
        found_markers = []
        for marker in spatial_words:
            if marker in text_lower:
                found_markers.append(marker)
        
        return found_markers
    
    def _generate_parse_trees(self, text: str, 
                             sentences: List[str]) -> List[str]:
        """Generate formatted parse trees."""
        trees = []
        
        if self.spacy_model:
            doc = self.spacy_model(text)
            for sent in doc.sents:
                try:
                    # Create simple tree representation
                    tree_str = self._build_tree_string(sent.root)
                    trees.append(tree_str)
                except Exception as e:
                    logger.warning(f"Tree generation failed: {e}")
        
        return trees
    
    def _build_tree_string(self, token, depth: int = 0) -> str:
        """Build tree string recursively."""
        result = "  " * depth + f"{token.text} ({token.pos_})\n"
        
        for child in token.children:
            result += self._build_tree_string(child, depth + 1)
        
        return result


class AdvancedNLPAnalyzer:
    """
    High-level API for advanced NLP analysis.
    Combines all Phase 4 capabilities into coherent analysis.
    """
    
    def __init__(self):
        """Initialize analyzer."""
        self.engine = AdvancedNLPEngine()
    
    def analyze_story(self, text: str) -> Dict:
        """
        Analyze narrative text to extract story structure.
        
        Returns:
            Dictionary with story elements
        """
        analysis = self.engine.analyze_advanced(text)
        if not analysis:
            return {}
        
        return {
            'characters': list(analysis.key_participants),
            'events': [e.event_trigger for e in analysis.events],
            'locations': analysis.spatial_markers,
            'timeline': analysis.temporal_markers,
            'event_details': [
                {
                    'action': e.event_trigger,
                    'participants': e.participants,
                    'confidence': e.confidence
                }
                for e in analysis.events
            ],
            'coreference_chains': [
                {
                    'entity': c.representative,
                    'type': c.entity_type,
                    'mentions': c.mentions
                }
                for c in analysis.coreference_chains
            ]
        }
    
    def analyze_relationships(self, text: str) -> Dict:
        """
        Extract relationships and dependencies.
        
        Returns:
            Relationship graph
        """
        analysis = self.engine.analyze_advanced(text)
        if not analysis:
            return {}
        
        # Build relationship map from dependencies
        relationships = {}
        for dep in analysis.dependencies:
            key = f"{dep.dependent} -{dep.relation_type}-> {dep.head}"
            relationships[key] = {
                'from': dep.dependent,
                'type': dep.relation_type,
                'to': dep.head
            }
        
        return {
            'dependencies': relationships,
            'predicates': analysis.predicates,
            'semantic_roles': [
                {
                    'predicate': sr.predicate,
                    'role': sr.role,
                    'argument': sr.argument
                }
                for sr in analysis.semantic_roles
            ]
        }
