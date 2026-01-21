"""
NLP Pipeline - Advanced Linguistic Analysis

Provides comprehensive NLP analysis including POS tagging, chunking,
named entity recognition, lemmatization, and dependency parsing.

Integrates with DataManager and SemanticGraph for unified linguistic analysis.

Usage:
    from src.core.nlp_pipeline import NLPPipeline
    
    nlp = NLPPipeline()
    analysis = nlp.analyze(text)
    
    print(analysis.pos_tags)        # Part-of-speech tags
    print(analysis.entities)         # Named entities
    print(analysis.lemmas)          # Lemmatized forms
    print(analysis.chunks)          # Noun phrases
"""

import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

try:
    import nltk
    from nltk import pos_tag, ne_chunk, sent_tokenize, word_tokenize
    from nltk.stem import WordNetLemmatizer, PorterStemmer
    from nltk.chunk import RegexpParser
    from nltk.tag import PerceptronTagger
except ImportError:
    nltk = None

from src.core.data_manager import DataManager
from src.core.semantic_graph import SemanticGraph

logger = logging.getLogger(__name__)


class POS(Enum):
    """Part-of-speech tags."""
    NOUN = "NN"
    VERB = "VB"
    ADJ = "JJ"
    ADV = "RB"
    PREP = "IN"
    DET = "DT"
    OTHER = "XX"


@dataclass
class Token:
    """Analyzed token with linguistic features."""
    text: str
    pos: str                    # Part-of-speech tag
    lemma: str                  # Lemmatized form
    stem: str                   # Stemmed form
    is_stopword: bool          # Is common stopword
    entity_type: Optional[str]  # NER tag (PERSON, LOC, ORG, etc)
    semantic_type: Optional[str] # From semantic graph


@dataclass
class Phrase:
    """Identified phrase (noun phrase, verb phrase, etc)."""
    text: str
    phrase_type: str          # NP, VP, etc
    tokens: List[Token]
    head: str                 # Main word
    modifiers: List[str]      # Modifying words


@dataclass
class NamedEntity:
    """Identified named entity."""
    text: str
    entity_type: str          # PERSON, LOC, ORG, GPE, MONEY, DATE, etc
    tokens: List[str]
    position: Tuple[int, int] # Start, end positions


@dataclass
class NLPAnalysis:
    """Complete NLP analysis of text."""
    text: str
    sentences: List[str]
    tokens: List[Token]
    pos_tags: List[Tuple[str, str]]
    lemmas: Dict[str, str]
    stems: Dict[str, str]
    entities: List[NamedEntity]
    phrases: List[Phrase]
    stopwords: Set[str]
    vocabulary: Set[str]
    
    @property
    def key_terms(self) -> List[str]:
        """Get key terms (non-stopword nouns and verbs)."""
        return [token.text for token in self.tokens 
                if not token.is_stopword 
                and token.pos.startswith(('NN', 'VB'))]
    
    @property
    def entity_dict(self) -> Dict[str, List[str]]:
        """Get entities organized by type."""
        result = {}
        for entity in self.entities:
            if entity.entity_type not in result:
                result[entity.entity_type] = []
            result[entity.entity_type].append(entity.text)
        return result


class NLPPipeline:
    """
    Advanced NLP analysis pipeline.
    
    Provides complete linguistic analysis including tokenization, POS tagging,
    NER, chunking, lemmatization, and semantic analysis.
    """
    
    # Chunking grammar for noun phrases
    CHUNK_GRAMMAR = r"""
        NP: {<DT>?<JJ>*<NN>+}           # Noun phrases
        VP: {<VB.?>+}                    # Verb phrases
        PP: {<IN><NP>}                   # Prepositional phrases
    """
    
    def __init__(self):
        """Initialize NLP pipeline."""
        if nltk is None:
            logger.error("NLTK not available")
            self._available = False
            return
        
        self._available = True
        
        # Initialize components
        self.data_manager = DataManager()
        self.semantic_graph = SemanticGraph()
        
        # Initialize tools
        self.lemmatizer = WordNetLemmatizer()
        self.stemmer = PorterStemmer()
        self.chunk_parser = RegexpParser(self.CHUNK_GRAMMAR)
        
        # Ensure required data
        if not self.data_manager.ensure_required_data(verbose=False):
            logger.warning("Some NLTK data not available")
        
        logger.info("NLPPipeline initialized")
    
    def is_available(self) -> bool:
        """Check if pipeline is available."""
        return self._available
    
    def analyze(self, text: str) -> Optional[NLPAnalysis]:
        """
        Perform complete NLP analysis on text.
        
        Args:
            text: Text to analyze
        
        Returns:
            NLPAnalysis with all linguistic features
        """
        if not self._available:
            logger.error("NLP pipeline not available")
            return None
        
        try:
            logger.debug(f"Analyzing text ({len(text)} chars)")
            
            # Sentence tokenization
            sentences = self.data_manager.sentence_tokenize(text)
            
            # Token-level analysis
            tokens_list = self.data_manager.tokenize(text)
            pos_tags = pos_tag(tokens_list)
            
            # Build token objects
            tokens = []
            stopwords = self.data_manager.get_stopwords()
            
            for text_token, pos in pos_tags:
                lemma = self._get_lemma(text_token, pos)
                stem = self.stemmer.stem(text_token)
                
                # Try semantic analysis
                semantic_type = None
                if self.semantic_graph:
                    meaning = self.semantic_graph.explore_meaning(text_token)
                    if meaning:
                        semantic_type = "known_concept"
                
                token = Token(
                    text=text_token,
                    pos=pos,
                    lemma=lemma,
                    stem=stem,
                    is_stopword=text_token.lower() in stopwords,
                    entity_type=None,  # Set by NER later
                    semantic_type=semantic_type
                )
                tokens.append(token)
            
            # Named entity recognition
            entities = self._extract_entities(sentences)
            
            # Chunking
            phrases = self._extract_phrases(pos_tags)
            
            # Build results
            lemmas = {token.text: token.lemma for token in tokens}
            stems = {token.text: token.stem for token in tokens}
            vocabulary = set(token.text for token in tokens)
            
            analysis = NLPAnalysis(
                text=text,
                sentences=sentences,
                tokens=tokens,
                pos_tags=pos_tags,
                lemmas=lemmas,
                stems=stems,
                entities=entities,
                phrases=phrases,
                stopwords=stopwords,
                vocabulary=vocabulary
            )
            
            logger.debug(f"Analysis complete: {len(tokens)} tokens, "
                        f"{len(entities)} entities, {len(phrases)} phrases")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None
    
    def extract_key_terms(self, text: str, min_freq: int = 1) -> List[Tuple[str, int]]:
        """
        Extract key terms from text by frequency.
        
        Args:
            text: Text to analyze
            min_freq: Minimum frequency to include
        
        Returns:
            List of (term, frequency) tuples, sorted by frequency
        """
        analysis = self.analyze(text)
        if not analysis:
            return []
        
        # Count key terms
        term_counts = {}
        for term in analysis.key_terms:
            normalized = term.lower()
            term_counts[normalized] = term_counts.get(normalized, 0) + 1
        
        # Filter and sort
        result = [(term, count) for term, count in term_counts.items() 
                  if count >= min_freq]
        result.sort(key=lambda x: x[1], reverse=True)
        
        return result
    
    def extract_entities_by_type(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities organized by type.
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary mapping entity types to entity lists
        """
        analysis = self.analyze(text)
        if not analysis:
            return {}
        
        return analysis.entity_dict
    
    def lemmatize_text(self, text: str) -> str:
        """
        Return lemmatized version of text.
        
        Args:
            text: Text to lemmatize
        
        Returns:
            Lemmatized text
        """
        analysis = self.analyze(text)
        if not analysis:
            return text
        
        return ' '.join(analysis.lemmas.get(token.text, token.text) 
                       for token in analysis.tokens)
    
    def get_linguistic_complexity(self, text: str) -> Dict[str, float]:
        """
        Calculate linguistic complexity metrics.
        
        Args:
            text: Text to analyze
        
        Returns:
            Dictionary with complexity metrics
        """
        analysis = self.analyze(text)
        if not analysis:
            return {}
        
        # Calculate metrics
        total_words = len(analysis.tokens)
        stopword_ratio = sum(1 for t in analysis.tokens if t.is_stopword) / max(1, total_words)
        unique_words = len(analysis.vocabulary) / max(1, total_words)
        avg_sentence_length = total_words / max(1, len(analysis.sentences))
        entity_density = len(analysis.entities) / max(1, len(analysis.sentences))
        
        return {
            'stopword_ratio': stopword_ratio,
            'vocabulary_richness': unique_words,
            'avg_sentence_length': avg_sentence_length,
            'entity_density': entity_density,
            'total_tokens': total_words,
            'unique_terms': len(analysis.vocabulary),
            'entity_count': len(analysis.entities),
            'phrase_count': len(analysis.phrases),
        }
    
    # Private helper methods
    
    def _get_lemma(self, word: str, pos: str) -> str:
        """Get lemma from word and POS tag."""
        try:
            # Map NLTK POS to WordNet POS
            from nltk.corpus import wordnet
            
            if pos.startswith('VB'):
                wordnet_pos = wordnet.VERB
            elif pos.startswith('NN'):
                wordnet_pos = wordnet.NOUN
            elif pos.startswith('JJ'):
                wordnet_pos = wordnet.ADJ
            elif pos.startswith('RB'):
                wordnet_pos = wordnet.ADV
            else:
                wordnet_pos = None
            
            if wordnet_pos:
                return self.lemmatizer.lemmatize(word, pos=wordnet_pos)
            else:
                return self.lemmatizer.lemmatize(word)
        except Exception:
            return word
    
    def _extract_entities(self, sentences: List[str]) -> List[NamedEntity]:
        """Extract named entities from sentences."""
        entities = []
        
        try:
            for sentence in sentences:
                tokens = self.data_manager.tokenize(sentence)
                pos_tags = pos_tag(tokens)
                
                # NER
                ner_tree = ne_chunk(pos_tags, binary=False)
                
                # Extract entities
                for subtree in ner_tree:
                    if hasattr(subtree, 'label'):  # It's a chunk
                        entity_type = subtree.label()
                        entity_text = ' '.join(token for token, _ in subtree.leaves())
                        entity_tokens = [token for token, _ in subtree.leaves()]
                        
                        entity = NamedEntity(
                            text=entity_text,
                            entity_type=entity_type,
                            tokens=entity_tokens,
                            position=(0, len(entity_text))  # Simplified
                        )
                        entities.append(entity)
        except Exception as e:
            logger.warning(f"Entity extraction failed: {e}")
        
        return entities
    
    def _extract_phrases(self, pos_tags: List[Tuple[str, str]]) -> List[Phrase]:
        """Extract noun phrases and other chunks."""
        phrases = []
        
        try:
            tree = self.chunk_parser.parse(pos_tags)
            
            for subtree in tree:
                if hasattr(subtree, 'label'):  # It's a chunk
                    phrase_type = subtree.label()
                    phrase_text = ' '.join(token for token, _ in subtree.leaves())
                    tokens_in_phrase = [token for token, _ in subtree.leaves()]
                    
                    # Head is usually the last noun/verb
                    head = tokens_in_phrase[-1] if tokens_in_phrase else ""
                    modifiers = tokens_in_phrase[:-1] if len(tokens_in_phrase) > 1 else []
                    
                    phrase = Phrase(
                        text=phrase_text,
                        phrase_type=phrase_type,
                        tokens=[],  # Would populate with Token objects
                        head=head,
                        modifiers=modifiers
                    )
                    phrases.append(phrase)
        except Exception as e:
            logger.warning(f"Phrase extraction failed: {e}")
        
        return phrases
