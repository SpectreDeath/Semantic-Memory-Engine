"""
Semantic Graph - WordNet Integration for SimpleMem

Provides semantic relationship analysis using WordNet, enhancing the toolkit's
ability to understand and connect concepts through meaning rather than just keywords.

This module bridges ChromaDB with WordNet to enable:
- Semantic similarity analysis
- Synonym/antonym discovery
- Concept hierarchy exploration (hypernyms/hyponyms)
- Better knowledge gap detection
- Richer memory consolidation

Usage:
    from src.core.semantic_graph import SemanticGraph
    
    sg = SemanticGraph()
    meaning = sg.explore_meaning("intelligence")
    related = sg.find_related_concepts("machine learning")
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import logging

try:
    from nltk.corpus import wordnet as wn
except ImportError:
    wn = None

logger = logging.getLogger(__name__)


@dataclass
class SemanticRelation:
    """Represents a semantic relationship between concepts."""
    word: str
    related_word: str
    relation_type: str  # synonym, antonym, hypernym, hyponym
    confidence: float  # 0-1
    definition: str = ""


@dataclass
class ConceptMeaning:
    """Comprehensive semantic analysis of a concept."""
    word: str
    definitions: List[str]
    synonyms: List[str]
    antonyms: List[str]
    hypernyms: List[str]  # Broader/more general concepts
    hyponyms: List[str]   # Narrower/more specific concepts
    related_words: List[SemanticRelation]
    total_meanings: int


class SemanticGraph:
    """
    Semantic relationship analyzer using WordNet.
    
    Provides methods to explore semantic connections between words,
    understand concept hierarchies, and find related terms for
    knowledge gap detection and memory consolidation.
    """
    
    def __init__(self):
        """Initialize SemanticGraph with WordNet."""
        if wn is None:
            logger.warning("WordNet not available. Install with: pip install nltk")
            self._available = False
        else:
            self._available = True
            self._cache: Dict[str, ConceptMeaning] = {}
    
    def is_available(self) -> bool:
        """Check if WordNet is available."""
        return self._available
    
    def explore_meaning(self, word: str, max_relations: int = 10) -> Optional[ConceptMeaning]:
        """
        Comprehensive semantic analysis of a word.
        
        Args:
            word: The word to analyze
            max_relations: Maximum number of relations to return
        
        Returns:
            ConceptMeaning with all semantic relationships or None if word not found
        """
        if not self._available:
            return None
        
        # Check cache
        if word in self._cache:
            return self._cache[word]
        
        try:
            synsets = wn.synsets(word)
            if not synsets:
                logger.debug(f"No synsets found for '{word}'")
                return None
            
            definitions = [s.definition() for s in synsets]
            synonyms = self._extract_lemmas(synsets)
            antonyms = self._extract_antonyms(synsets)
            hypernyms = self._extract_hypernyms(synsets, max_relations)
            hyponyms = self._extract_hyponyms(synsets, max_relations)
            
            related_words = self._build_semantic_relations(
                word, synonyms, antonyms, hypernyms, hyponyms
            )
            
            result = ConceptMeaning(
                word=word,
                definitions=definitions,
                synonyms=synonyms[:max_relations],
                antonyms=antonyms[:max_relations],
                hypernyms=hypernyms[:max_relations],
                hyponyms=hyponyms[:max_relations],
                related_words=related_words[:max_relations],
                total_meanings=len(synsets)
            )
            
            # Cache result
            self._cache[word] = result
            return result
            
        except Exception as e:
            logger.error(f"Error exploring meaning of '{word}': {e}")
            return None
    
    def find_semantic_variants(self, word: str) -> Dict[str, List[str]]:
        """
        Find all semantic variants (synonyms, related forms).
        
        Args:
            word: The word to find variants for
        
        Returns:
            Dictionary mapping relation types to lists of words
        """
        if not self._available:
            return {}
        
        meaning = self.explore_meaning(word)
        if not meaning:
            return {}
        
        return {
            'synonyms': meaning.synonyms,
            'antonyms': meaning.antonyms,
            'hypernyms': meaning.hypernyms,
            'hyponyms': meaning.hyponyms,
        }
    
    def calculate_semantic_similarity(self, word1: str, word2: str) -> float:
        """
        Calculate semantic similarity between two words (0-1).
        
        Uses WordNet path distance to estimate similarity.
        
        Args:
            word1: First word
            word2: Second word
        
        Returns:
            Similarity score (0=no relation, 1=identical meaning)
        """
        if not self._available:
            return 0.0
        
        try:
            synsets1 = wn.synsets(word1)
            synsets2 = wn.synsets(word2)
            
            if not synsets1 or not synsets2:
                return 0.0
            
            # Use best match similarity
            max_similarity = 0.0
            for s1 in synsets1:
                for s2 in synsets2:
                    similarity = s1.path_similarity(s2)
                    if similarity and similarity > max_similarity:
                        max_similarity = similarity
            
            return max(0.0, min(1.0, max_similarity))
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def find_related_concepts(self, word: str, depth: int = 2) -> Dict[str, Set[str]]:
        """
        Find all related concepts within specified depth.
        
        Args:
            word: Starting word
            depth: How many steps away to search (1-3 recommended)
        
        Returns:
            Dictionary mapping concept to related concepts at each depth
        """
        if not self._available:
            return {}
        
        result = defaultdict(set)
        visited = {word}
        current_level = {word}
        
        for level in range(1, depth + 1):
            next_level = set()
            
            for concept in current_level:
                meaning = self.explore_meaning(concept)
                if not meaning:
                    continue
                
                # Add all related concepts
                for related in (meaning.synonyms + meaning.hypernyms + meaning.hyponyms):
                    if related not in visited:
                        result[f"depth_{level}"].add(related)
                        next_level.add(related)
                        visited.add(related)
            
            current_level = next_level
            if not current_level:
                break
        
        return dict(result)
    
    def detect_semantic_gaps(self, concept: str, existing_concepts: Set[str]) -> List[Dict]:
        """
        Detect knowledge gaps by finding related concepts not yet covered.
        
        Args:
            concept: The main concept
            existing_concepts: Set of concepts already covered
        
        Returns:
            List of suggested gap fillers
        """
        if not self._available:
            return []
        
        meaning = self.explore_meaning(concept)
        if not meaning:
            return []
        
        gaps = []
        
        # Check synonyms
        for synonym in meaning.synonyms:
            if synonym not in existing_concepts:
                gaps.append({
                    'gap': synonym,
                    'type': 'synonym',
                    'reason': f'Synonym of {concept}',
                    'priority': 'high'
                })
        
        # Check hypernyms (broader concepts)
        for hypernym in meaning.hypernyms:
            if hypernym not in existing_concepts:
                gaps.append({
                    'gap': hypernym,
                    'type': 'hypernym',
                    'reason': f'Broader concept of {concept}',
                    'priority': 'medium'
                })
        
        # Check hyponyms (narrower concepts)
        for hyponym in meaning.hyponyms[:5]:  # Limit to top 5
            if hyponym not in existing_concepts:
                gaps.append({
                    'gap': hyponym,
                    'type': 'hyponym',
                    'reason': f'Specific instance of {concept}',
                    'priority': 'low'
                })
        
        return gaps
    
    def get_concept_hierarchy(self, word: str, direction: str = 'both') -> Dict:
        """
        Get the concept hierarchy (taxonomy) for a word.
        
        Args:
            word: The word to get hierarchy for
            direction: 'up' (hypernyms), 'down' (hyponyms), 'both'
        
        Returns:
            Hierarchical structure of concepts
        """
        if not self._available:
            return {}
        
        meaning = self.explore_meaning(word)
        if not meaning:
            return {}
        
        hierarchy = {
            'word': word,
            'definitions': meaning.definitions[:1] if meaning.definitions else []
        }
        
        if direction in ('up', 'both'):
            hierarchy['broader_concepts'] = meaning.hypernyms
        
        if direction in ('down', 'both'):
            hierarchy['specific_examples'] = meaning.hyponyms[:5]
        
        return hierarchy
    
    # Private helper methods
    
    @staticmethod
    def _extract_lemmas(synsets) -> List[str]:
        """Extract all lemma names from synsets."""
        lemmas = set()
        for synset in synsets:
            for lemma in synset.lemmas():
                lemmas.add(lemma.name().replace('_', ' '))
        return sorted(list(lemmas))
    
    @staticmethod
    def _extract_antonyms(synsets) -> List[str]:
        """Extract antonyms from synsets."""
        antonyms = set()
        for synset in synsets:
            for lemma in synset.lemmas():
                for antonym in lemma.antonyms():
                    antonyms.add(antonym.name().replace('_', ' '))
        return sorted(list(antonyms))
    
    @staticmethod
    def _extract_hypernyms(synsets, max_count: int = 10) -> List[str]:
        """Extract hypernyms (broader concepts)."""
        hypernyms = set()
        for synset in synsets:
            for hyp in synset.hypernyms()[:max_count]:
                for lemma in hyp.lemmas():
                    hypernyms.add(lemma.name().replace('_', ' '))
        return sorted(list(hypernyms))[:max_count]
    
    @staticmethod
    def _extract_hyponyms(synsets, max_count: int = 10) -> List[str]:
        """Extract hyponyms (narrower concepts)."""
        hyponyms = set()
        for synset in synsets:
            for hyp in synset.hyponyms()[:max_count]:
                for lemma in hyp.lemmas():
                    hyponyms.add(lemma.name().replace('_', ' '))
        return sorted(list(hyponyms))[:max_count]
    
    @staticmethod
    def _build_semantic_relations(
        word: str,
        synonyms: List[str],
        antonyms: List[str],
        hypernyms: List[str],
        hyponyms: List[str]
    ) -> List[SemanticRelation]:
        """Build semantic relation objects."""
        relations = []
        
        for syn in synonyms:
            relations.append(SemanticRelation(
                word=word,
                related_word=syn,
                relation_type='synonym',
                confidence=0.9
            ))
        
        for ant in antonyms:
            relations.append(SemanticRelation(
                word=word,
                related_word=ant,
                relation_type='antonym',
                confidence=0.85
            ))
        
        for hyp in hypernyms:
            relations.append(SemanticRelation(
                word=word,
                related_word=hyp,
                relation_type='hypernym',
                confidence=0.8
            ))
        
        for hyp in hyponyms:
            relations.append(SemanticRelation(
                word=word,
                related_word=hyp,
                relation_type='hyponym',
                confidence=0.75
            ))
        
        return relations
    
    def clear_cache(self):
        """Clear the exploration cache."""
        self._cache.clear()
        logger.info("Semantic graph cache cleared")
