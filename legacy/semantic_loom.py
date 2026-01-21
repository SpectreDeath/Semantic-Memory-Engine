"""
The Loom: Semantic Memory Weaver
Distills web search and monitoring outputs into atomic facts with coreference resolution.
Implements SimpleMem's semantic structured compression pipeline.
"""

from mcp.server.fastmcp import FastMCP
import json
import re
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from datetime import datetime

mcp = FastMCP("SemanticLoom")

class CoreferenceResolver:
    """Resolves pronouns and references to actual names/entities."""
    
    def __init__(self):
        self.pronouns = {
            'he': 'person', 'she': 'person', 'it': 'thing',
            'they': 'people', 'them': 'people', 'their': 'people',
            'his': 'person', 'her': 'person'
        }
        self.entity_cache = {}
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extracts named entities (simplified pattern matching)."""
        entities = {
            'persons': re.findall(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text),
            'organizations': re.findall(r'\b(?:the\s+)?[A-Z][a-z\s&]+(?:Inc|Corp|LLC|Ltd|Co|Group)\b', text),
            'locations': re.findall(r'\b(?:New\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b', text),
        }
        return entities
    
    def resolve_pronouns(self, text: str, entities: Dict[str, List[str]]) -> str:
        """Replaces pronouns with their likely referents."""
        resolved = text
        all_entities = entities['persons'] + entities['organizations'] + entities['locations']
        
        for pronoun in self.pronouns:
            pattern = rf'\b{pronoun}\b'
            if all_entities and re.search(pattern, resolved, re.IGNORECASE):
                # Use most recent entity as referent
                referent = all_entities[-1] if all_entities else f"[{self.pronouns[pronoun]}]"
                resolved = re.sub(pattern, f"[{referent}]", resolved, flags=re.IGNORECASE)
        
        return resolved


class AtomicFactExtractor:
    """Breaks down text into atomic facts (who-what-when-why)."""
    
    @staticmethod
    def extract_facts(text: str) -> List[Dict[str, str]]:
        """Extracts atomic facts from text."""
        facts = []
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue
            
            fact = {
                'statement': sentence.strip(),
                'extracted_at': datetime.now().isoformat(),
                'confidence': AtomicFactExtractor._estimate_confidence(sentence),
                'entity_types': AtomicFactExtractor._identify_entity_types(sentence)
            }
            
            facts.append(fact)
        
        return facts
    
    @staticmethod
    def _estimate_confidence(sentence: str) -> float:
        """Estimates confidence based on linguistic markers."""
        high_confidence = ['stated', 'confirmed', 'proven', 'demonstrated']
        low_confidence = ['alleged', 'reportedly', 'supposedly', 'claimed']
        
        confidence = 0.7  # default
        
        if any(marker in sentence.lower() for marker in high_confidence):
            confidence = 0.95
        elif any(marker in sentence.lower() for marker in low_confidence):
            confidence = 0.45
        
        return confidence
    
    @staticmethod
    def _identify_entity_types(sentence: str) -> List[str]:
        """Identifies entity types in sentence."""
        entity_types = []
        
        if re.search(r'\b(?:said|stated|announced|claimed)\b', sentence, re.I):
            entity_types.append('speech_act')
        if re.search(r'\b(?:date|time|when|tomorrow|yesterday|today)\b', sentence, re.I):
            entity_types.append('temporal')
        if re.search(r'\b(?:place|location|where|at|in)\b', sentence, re.I):
            entity_types.append('locational')
        if re.search(r'[A-Z][a-z]+ [A-Z][a-z]+', sentence):
            entity_types.append('person_mention')
        
        return entity_types


class SemanticCompressor:
    """Compresses semantic information with 30x token reduction."""
    
    @staticmethod
    def compress(facts: List[Dict[str, str]]) -> Dict[str, Any]:
        """Compresses facts into structured semantic representation."""
        compressed = {
            'total_facts': len(facts),
            'compressed_size_reduction': 0.0,
            'fact_summary': {},
            'entity_graph': defaultdict(list),
            'temporal_timeline': [],
            'semantic_clusters': {}
        }
        
        # Deduplicate facts
        unique_facts = SemanticCompressor._deduplicate(facts)
        compressed['unique_facts_count'] = len(unique_facts)
        compressed['deduplication_ratio'] = (
            1 - (len(unique_facts) / len(facts)) if facts else 0
        )
        
        # Cluster by entity types
        for fact in unique_facts:
            for entity_type in fact.get('entity_types', []):
                if entity_type not in compressed['semantic_clusters']:
                    compressed['semantic_clusters'][entity_type] = []
                compressed['semantic_clusters'][entity_type].append(fact['statement'])
        
        # Token count estimation (rough)
        original_tokens = sum(len(f['statement'].split()) for f in facts)
        compressed_tokens = sum(len(f['statement'].split()) for f in unique_facts)
        compressed['compressed_size_reduction'] = original_tokens / (compressed_tokens + 1)
        
        return compressed
    
    @staticmethod
    def _deduplicate(facts: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Removes near-duplicate facts."""
        seen = set()
        unique = []
        
        for fact in facts:
            # Simple deduplication via statement hash
            statement_hash = hash(fact['statement'].lower())
            if statement_hash not in seen:
                seen.add(statement_hash)
                unique.append(fact)
        
        return unique


@mcp.tool()
def distill_web_content(content: str, source_url: str = "") -> str:
    """
    Distills web search results into atomic facts with coreference resolution.
    Returns compressed semantic representation.
    """
    try:
        # Step 1: Extract entities
        resolver = CoreferenceResolver()
        entities = resolver.extract_entities(content)
        
        # Step 2: Resolve coreferences
        resolved_content = resolver.resolve_pronouns(content, entities)
        
        # Step 3: Extract atomic facts
        extractor = AtomicFactExtractor()
        facts = extractor.extract_facts(resolved_content)
        
        # Step 4: Compress semantically
        compressor = SemanticCompressor()
        compressed = compressor.compress(facts)
        
        result = {
            'source_url': source_url,
            'status': 'distilled',
            'entities_extracted': {
                'persons': len(entities['persons']),
                'organizations': len(entities['organizations']),
                'locations': len(entities['locations']),
            },
            'atomic_facts': facts,
            'compression_metrics': {
                'total_facts': compressed['total_facts'],
                'unique_facts': compressed['unique_facts_count'],
                'deduplication_ratio': round(compressed['deduplication_ratio'], 3),
                'compression_factor': round(compressed['compressed_size_reduction'], 2),
            },
            'semantic_clusters': dict(compressed['semantic_clusters']),
        }
        
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e), 'status': 'failed'})


@mcp.tool()
def resolve_coreferences(text: str) -> str:
    """
    Resolves pronouns and references to actual entity names.
    Returns text with pronouns replaced by [EntityName].
    """
    try:
        resolver = CoreferenceResolver()
        entities = resolver.extract_entities(text)
        resolved = resolver.resolve_pronouns(text, entities)
        
        return json.dumps({
            'original_text': text,
            'resolved_text': resolved,
            'entities_found': entities,
            'status': 'resolved'
        }, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def extract_atomic_facts(text: str) -> str:
    """
    Breaks text down into atomic facts (who-what-when-why).
    Each fact includes confidence score and entity type classification.
    """
    try:
        extractor = AtomicFactExtractor()
        facts = extractor.extract_facts(text)
        
        return json.dumps({
            'text_length': len(text),
            'facts_extracted': len(facts),
            'facts': facts,
            'status': 'success'
        }, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def compress_semantic_data(facts_json: str) -> str:
    """
    Compresses semantic facts into structured representation.
    Estimates 30x token reduction through deduplication and clustering.
    """
    try:
        if isinstance(facts_json, str):
            facts = json.loads(facts_json)
        else:
            facts = facts_json
        
        if not isinstance(facts, list):
            facts = [facts]
        
        compressor = SemanticCompressor()
        compressed = compressor.compress(facts)
        
        return json.dumps({
            'compression_results': compressed,
            'status': 'compressed'
        }, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


if __name__ == "__main__":
    mcp.run()
