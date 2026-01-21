"""
Entity Linking Module
=====================

Phase 5 component for linking named entities to knowledge bases.
Provides entity disambiguation, knowledge base linking, and entity relationship extraction.

Features:
- Named entity recognition and classification
- Entity disambiguation (linking to knowledge bases)
- Wikipedia entity linking
- Entity relationship graphs
- Coreference entity linking
- Entity metadata enrichment
"""

import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum

try:
    import nltk
    from nltk import pos_tag, word_tokenize
    from nltk.ne_chunk import ne_chunk
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Named entity types."""
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    PRODUCT = "PRODUCT"
    EVENT = "EVENT"
    DATE = "DATE"
    MONEY = "MONEY"
    PERCENT = "PERCENT"
    TIME = "TIME"
    FACILITY = "FACILITY"
    LANGUAGE = "LANGUAGE"
    LAW = "LAW"
    WORK_OF_ART = "WORK_OF_ART"
    OTHER = "OTHER"


class KnowledgeBase(Enum):
    """Supported knowledge bases."""
    WIKIPEDIA = "wikipedia"
    WIKIDATA = "wikidata"
    DBpedia = "dbpedia"
    FREEBASE = "freebase"
    CUSTOM = "custom"


@dataclass
class Entity:
    """Recognized and linked entity."""
    text: str
    entity_type: EntityType
    start_char: int
    end_char: int
    mention_count: int = 1
    confidence: float = 0.8


@dataclass
class LinkedEntity:
    """Entity linked to knowledge base."""
    entity: Entity
    kb_id: str  # Knowledge base identifier
    kb_type: KnowledgeBase
    url: Optional[str]
    description: Optional[str]
    aliases: List[str]
    properties: Dict[str, str]
    confidence: float
    

@dataclass
class EntityLink:
    """Relationship between two entities."""
    source: LinkedEntity
    target: LinkedEntity
    relation_type: str
    confidence: float


@dataclass
class EntityLinkingResult:
    """Complete entity linking result."""
    text: str
    entities: List[Entity]
    linked_entities: List[LinkedEntity]
    entity_links: List[EntityLink]
    entity_graph: Dict[str, List[str]]  # Entity -> related entities
    summary: Dict[str, int]  # Entity type counts
    

class EntityLinker:
    """Entity linking and disambiguation engine."""
    
    # Common Wikipedia disambiguation patterns
    WIKI_URLS = {
        "Albert Einstein": "https://en.wikipedia.org/wiki/Albert_Einstein",
        "Paris": "https://en.wikipedia.org/wiki/Paris",
        "United Nations": "https://en.wikipedia.org/wiki/United_Nations",
        # This would be populated with extensive mappings
    }
    
    # Entity type mappings
    ENTITY_PROPERTIES = {
        EntityType.PERSON: {
            'fields': ['birth_date', 'death_date', 'nationality', 'occupation', 'notable_for'],
            'aliases': ['firstname', 'surname', 'fullname']
        },
        EntityType.ORGANIZATION: {
            'fields': ['founded', 'headquarters', 'industry', 'revenue', 'employees'],
            'aliases': ['company', 'corp', 'org', 'institution']
        },
        EntityType.LOCATION: {
            'fields': ['coordinates', 'country', 'population', 'area', 'capital_of'],
            'aliases': ['place', 'city', 'country', 'region']
        },
        EntityType.EVENT: {
            'fields': ['date', 'location', 'participants', 'significance'],
            'aliases': ['happening', 'occurrence']
        }
    }
    
    def __init__(self):
        """Initialize entity linker."""
        self.has_nltk = NLTK_AVAILABLE
        self.custom_kb = {}  # For custom knowledge base
    
    def link_entities(self, text: str, kb_type: KnowledgeBase = KnowledgeBase.WIKIPEDIA) -> EntityLinkingResult:
        """
        Recognize and link entities in text.
        
        Args:
            text: Input text
            kb_type: Target knowledge base
        """
        if not text or not text.strip():
            return self._create_empty_result(text)
        
        # Recognize entities
        entities = self._recognize_entities(text)
        
        # Link entities to knowledge base
        linked_entities = []
        for entity in entities:
            linked = self._link_entity(entity, kb_type)
            if linked:
                linked_entities.append(linked)
        
        # Extract entity relationships
        entity_links = self._extract_entity_relationships(linked_entities, text)
        
        # Build entity graph
        entity_graph = self._build_entity_graph(linked_entities, entity_links)
        
        # Generate summary
        summary = self._generate_summary(entities)
        
        return EntityLinkingResult(
            text=text,
            entities=entities,
            linked_entities=linked_entities,
            entity_links=entity_links,
            entity_graph=entity_graph,
            summary=summary
        )
    
    def disambiguate_entity(self, entity_text: str, context: str = "") -> List[LinkedEntity]:
        """
        Disambiguate entity by resolving to multiple possible candidates.
        
        Args:
            entity_text: Entity to disambiguate
            context: Context for disambiguation
        """
        candidates = []
        
        # Generate candidates from knowledge base
        base_candidates = self._generate_candidates(entity_text)
        
        # Score candidates based on context
        for candidate in base_candidates:
            if context:
                score = self._calculate_context_similarity(candidate, context)
            else:
                score = candidate.confidence
            
            candidate.confidence = score
            if score > 0.3:  # Only keep reasonable candidates
                candidates.append(candidate)
        
        # Sort by confidence
        candidates.sort(key=lambda x: x.confidence, reverse=True)
        return candidates[:5]  # Return top 5
    
    def update_custom_kb(self, entity_id: str, entity_data: Dict[str, Any]):
        """Add or update entity in custom knowledge base."""
        self.custom_kb[entity_id] = entity_data
        logger.info(f"Updated custom KB with entity: {entity_id}")
    
    def add_entity_links(self, source_entity: LinkedEntity, target_entity: LinkedEntity,
                        relation_type: str, confidence: float = 0.8) -> EntityLink:
        """Create explicit link between entities."""
        return EntityLink(
            source=source_entity,
            target=target_entity,
            relation_type=relation_type,
            confidence=confidence
        )
    
    def _recognize_entities(self, text: str) -> List[Entity]:
        """Recognize named entities in text."""
        if not self.has_nltk:
            return self._simple_entity_recognition(text)
        
        try:
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            chunks = ne_chunk(pos_tags)
            
            entities = []
            char_pos = 0
            
            for chunk in chunks:
                if hasattr(chunk, 'label'):
                    # Named entity
                    entity_text = " ".join([token for token, _ in chunk.leaves()])
                    entity_type = self._map_nltk_entity_type(chunk.label())
                    
                    char_pos = text.find(entity_text, char_pos)
                    if char_pos >= 0:
                        entities.append(Entity(
                            text=entity_text,
                            entity_type=entity_type,
                            start_char=char_pos,
                            end_char=char_pos + len(entity_text),
                            confidence=0.9
                        ))
                        char_pos += len(entity_text)
            
            # Merge duplicate entities
            return self._merge_duplicate_entities(entities)
        
        except Exception as e:
            logger.warning(f"NLTK entity recognition failed: {e}")
            return self._simple_entity_recognition(text)
    
    def _link_entity(self, entity: Entity, kb_type: KnowledgeBase) -> Optional[LinkedEntity]:
        """Link entity to knowledge base."""
        if kb_type == KnowledgeBase.WIKIPEDIA:
            return self._link_wikipedia(entity)
        elif kb_type == KnowledgeBase.CUSTOM:
            return self._link_custom_kb(entity)
        else:
            # Placeholder for other knowledge bases
            return self._create_generic_link(entity)
    
    def _link_wikipedia(self, entity: Entity) -> Optional[LinkedEntity]:
        """Link to Wikipedia (simulated)."""
        # In production, would use Wikipedia API
        entity_text = entity.text
        
        # Check direct mappings
        if entity_text in self.WIKI_URLS:
            url = self.WIKI_URLS[entity_text]
            description = self._get_description(entity_text)
            
            return LinkedEntity(
                entity=entity,
                kb_id=entity_text.replace(" ", "_"),
                kb_type=KnowledgeBase.WIKIPEDIA,
                url=url,
                description=description,
                aliases=[entity_text.lower(), entity_text.upper()],
                properties=self._get_entity_properties(entity),
                confidence=0.95
            )
        
        # Fuzzy matching for common entities
        similarity, match = self._find_similar_entity(entity_text)
        if similarity > 0.7 and match:
            return LinkedEntity(
                entity=entity,
                kb_id=match.replace(" ", "_"),
                kb_type=KnowledgeBase.WIKIPEDIA,
                url=self.WIKI_URLS.get(match, ""),
                description=self._get_description(match),
                aliases=[entity_text.lower(), match.lower()],
                properties=self._get_entity_properties(entity),
                confidence=similarity
            )
        
        return None
    
    def _link_custom_kb(self, entity: Entity) -> Optional[LinkedEntity]:
        """Link to custom knowledge base."""
        entity_text = entity.text
        
        if entity_text in self.custom_kb:
            data = self.custom_kb[entity_text]
            return LinkedEntity(
                entity=entity,
                kb_id=entity_text,
                kb_type=KnowledgeBase.CUSTOM,
                url=data.get('url'),
                description=data.get('description'),
                aliases=data.get('aliases', []),
                properties=data.get('properties', {}),
                confidence=0.9
            )
        
        return None
    
    def _generate_candidates(self, entity_text: str) -> List[LinkedEntity]:
        """Generate disambiguation candidates."""
        candidates = []
        
        # Check custom KB
        if entity_text in self.custom_kb:
            data = self.custom_kb[entity_text]
            candidates.append(LinkedEntity(
                entity=Entity(entity_text, EntityType.OTHER, 0, len(entity_text)),
                kb_id=entity_text,
                kb_type=KnowledgeBase.CUSTOM,
                url=data.get('url'),
                description=data.get('description'),
                aliases=data.get('aliases', []),
                properties=data.get('properties', {}),
                confidence=0.9
            ))
        
        # Check Wikipedia mappings (would be much larger)
        for wiki_entity, url in self.WIKI_URLS.items():
            if entity_text.lower() in wiki_entity.lower() or wiki_entity.lower() in entity_text.lower():
                candidates.append(LinkedEntity(
                    entity=Entity(entity_text, EntityType.OTHER, 0, len(entity_text)),
                    kb_id=wiki_entity.replace(" ", "_"),
                    kb_type=KnowledgeBase.WIKIPEDIA,
                    url=url,
                    description=self._get_description(wiki_entity),
                    aliases=[wiki_entity.lower(), entity_text.lower()],
                    properties={},
                    confidence=0.8
                ))
        
        return candidates
    
    def _extract_entity_relationships(self, linked_entities: List[LinkedEntity], 
                                     text: str) -> List[EntityLink]:
        """Extract relationships between entities."""
        links = []
        
        # Simple co-occurrence based linking
        for i, entity1 in enumerate(linked_entities):
            for entity2 in linked_entities[i+1:]:
                # Check if entities co-occur in sentences
                if self._entities_cooccur(entity1.entity, entity2.entity, text):
                    # Infer relationship type
                    rel_type = self._infer_relationship(entity1, entity2)
                    
                    links.append(EntityLink(
                        source=entity1,
                        target=entity2,
                        relation_type=rel_type,
                        confidence=0.7
                    ))
        
        return links
    
    def _build_entity_graph(self, linked_entities: List[LinkedEntity],
                           entity_links: List[EntityLink]) -> Dict[str, List[str]]:
        """Build entity relationship graph."""
        graph = {}
        
        for entity in linked_entities:
            graph[entity.kb_id] = []
        
        for link in entity_links:
            graph[link.source.kb_id].append(link.target.kb_id)
            if link.target.kb_id not in graph:
                graph[link.target.kb_id] = []
            graph[link.target.kb_id].append(link.source.kb_id)
        
        return graph
    
    def _generate_summary(self, entities: List[Entity]) -> Dict[str, int]:
        """Generate entity type summary."""
        summary = {}
        for entity_type in EntityType:
            count = sum(1 for e in entities if e.entity_type == entity_type)
            if count > 0:
                summary[entity_type.value] = count
        return summary
    
    def _simple_entity_recognition(self, text: str) -> List[Entity]:
        """Simple entity recognition (fallback)."""
        entities = []
        
        # Very basic pattern matching
        import re
        
        # Capitalized sequences (potential proper nouns)
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        for match in re.finditer(pattern, text):
            entities.append(Entity(
                text=match.group(),
                entity_type=EntityType.OTHER,
                start_char=match.start(),
                end_char=match.end(),
                confidence=0.5
            ))
        
        return entities
    
    def _merge_duplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Merge duplicate entity mentions."""
        merged = {}
        
        for entity in entities:
            key = entity.text.lower()
            if key in merged:
                merged[key].mention_count += 1
            else:
                merged[key] = entity
        
        return list(merged.values())
    
    def _map_nltk_entity_type(self, nltk_type: str) -> EntityType:
        """Map NLTK entity types to our enum."""
        mapping = {
            'PERSON': EntityType.PERSON,
            'ORGANIZATION': EntityType.ORGANIZATION,
            'GPE': EntityType.LOCATION,
            'LOCATION': EntityType.LOCATION,
            'FACILITY': EntityType.FACILITY,
            'PRODUCT': EntityType.PRODUCT,
            'EVENT': EntityType.EVENT,
            'DATE': EntityType.DATE,
            'TIME': EntityType.TIME,
            'MONEY': EntityType.MONEY,
            'PERCENT': EntityType.PERCENT,
            'LAW': EntityType.LAW,
            'LANGUAGE': EntityType.LANGUAGE,
        }
        return mapping.get(nltk_type, EntityType.OTHER)
    
    def _calculate_context_similarity(self, candidate: LinkedEntity, context: str) -> float:
        """Calculate similarity between candidate and context."""
        context_words = set(context.lower().split())
        desc_words = set((candidate.description or "").lower().split()) if candidate.description else set()
        
        if not context_words or not desc_words:
            return candidate.confidence
        
        overlap = len(context_words & desc_words)
        similarity = overlap / max(len(context_words), len(desc_words))
        
        return min(candidate.confidence + similarity * 0.2, 1.0)
    
    def _entities_cooccur(self, entity1: Entity, entity2: Entity, text: str) -> bool:
        """Check if entities occur in same sentence."""
        sentences = text.split('.')
        
        for sentence in sentences:
            if entity1.text in sentence and entity2.text in sentence:
                return True
        
        return False
    
    def _infer_relationship(self, entity1: LinkedEntity, entity2: LinkedEntity) -> str:
        """Infer relationship type between entities."""
        # Simple heuristics
        if entity1.entity.entity_type == EntityType.PERSON and entity2.entity.entity_type == EntityType.ORGANIZATION:
            return "works_for"
        elif entity1.entity.entity_type == EntityType.PERSON and entity2.entity.entity_type == EntityType.LOCATION:
            return "located_in"
        elif entity1.entity.entity_type == EntityType.ORGANIZATION and entity2.entity.entity_type == EntityType.LOCATION:
            return "headquartered_in"
        else:
            return "related_to"
    
    def _find_similar_entity(self, entity_text: str) -> Tuple[float, Optional[str]]:
        """Find similar entity in knowledge base."""
        best_match = None
        best_score = 0.0
        
        for known_entity in self.WIKI_URLS.keys():
            score = self._string_similarity(entity_text.lower(), known_entity.lower())
            if score > best_score:
                best_score = score
                best_match = known_entity
        
        return best_score, best_match
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity (Jaccard)."""
        set1 = set(str1.split())
        set2 = set(str2.split())
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _get_description(self, entity: str) -> Optional[str]:
        """Get description for entity."""
        descriptions = {
            "Albert Einstein": "German-born theoretical physicist",
            "Paris": "Capital and largest city of France",
            "United Nations": "International organization founded in 1945",
        }
        return descriptions.get(entity)
    
    def _get_entity_properties(self, entity: Entity) -> Dict[str, str]:
        """Get properties for entity type."""
        type_props = self.ENTITY_PROPERTIES.get(entity.entity_type, {})
        return {field: "" for field in type_props.get('fields', [])}
    
    def _create_generic_link(self, entity: Entity) -> LinkedEntity:
        """Create generic link for entity."""
        return LinkedEntity(
            entity=entity,
            kb_id=entity.text.replace(" ", "_"),
            kb_type=KnowledgeBase.CUSTOM,
            url=None,
            description=None,
            aliases=[entity.text.lower()],
            properties=self._get_entity_properties(entity),
            confidence=0.5
        )
    
    def _create_empty_result(self, text: str) -> EntityLinkingResult:
        """Create empty result for empty text."""
        return EntityLinkingResult(
            text=text,
            entities=[],
            linked_entities=[],
            entity_links=[],
            entity_graph={},
            summary={}
        )
