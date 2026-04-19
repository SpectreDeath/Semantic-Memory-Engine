"""
Triplet Harvester v2 - Extracts (Entity, Relation, Target) triples from text.

This transforms the SME from RAG (storing facts in vector DB) to "Physical" facts
that map to weight-space triples - enabling the V-index paradigm.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

import spacy
from spacy.tokens import Doc, Span

logger = logging.getLogger("lawnmower.triplet_harvester")

RELATION_PATTERNS = {
    "is_a": ["is a", "is an", "was a", "were", "acts as", "serves as", "functions as"],
    "has_property": ["has", "possesses", "owns", "contains", "includes", "features"],
    "related_to": ["relates to", "connected to", "linked to", "associated with", "tied to"],
    "occurs_in": ["occurs in", "happens in", "takes place in", "located in", "found in"],
    "created_by": [
        "created by",
        "made by",
        "authored by",
        "written by",
        "built by",
        "developed by",
    ],
    "authored": ["wrote", "authored", "created", "composed", "drafted"],
    "influenced": ["influenced", "inspired", "affected", "impacted", "shaped"],
    "contains": ["contains", "includes", "covers", "encompasses", "comprises"],
    "demonstrates": ["demonstrates", "shows", "illustrates", "exhibits", "displays"],
    "requires": ["requires", "needs", "demands", "necessitates"],
    "depends_on": ["depends on", "relies on", "rests on", " hinges on"],
    "compares_to": ["compares to", "similar to", "like", "unlike", "contrasts with"],
    "precedes": ["precedes", "comes before", "follows", "leads to", "results in"],
    "defined_as": ["defined as", "referred to as", "known as", "termed", "called"],
}


@dataclass
class EntityTriple:
    """Represents a (Entity, Relation, Target) triple."""

    subject: str
    relation: str
    target: str
    source_sentence: str
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "relation": self.relation,
            "target": self.target,
            "source_sentence": self.source_sentence,
            "confidence": self.confidence,
        }

    def __str__(self) -> str:
        return f"({self.subject}, {self.relation}, {self.target})"


class TripletHarvester:
    """
    Extracts (Entity, Relation, Target) triples from text for V-index.

    Uses spacy for NER and pattern matching for relation extraction.
    """

    def __init__(self, model: str = "en_core_web_sm"):
        self._load_spacy_model(model)
        self.entity_patterns = self._compile_entity_patterns()

    def _load_spacy_model(self, model: str):
        """Load spacy model with fallback."""
        try:
            self.nlp = spacy.load(model)
            logger.info(f"Loaded spacy model: {model}")
        except OSError:
            logger.warning(f"Model {model} not found, downloading...")
            from spacy.cli import download

            download(model)
            self.nlp = spacy.load(model)
            logger.info(f"Downloaded and loaded spacy model: {model}")

    def _compile_entity_patterns(self) -> dict[str, re.Pattern]:
        """Compile regex patterns for additional entity types."""
        return {
            "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            "url": re.compile(r"https?://\S+|www\.\S+"),
            "date": re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b"),
            "quote": re.compile(r'"([^"]+)"|"([^"]+)"'),
        }

    def extract_triplets(self, text: str) -> list[EntityTriple]:
        """
        Extract all (Entity, Relation, Target) triples from text.

        Args:
            text: Input text to extract from

        Returns:
            List of EntityTriple objects
        """
        doc = self.nlp(text)
        triplets = []

        for sent in doc.sents:
            sent_triplets = self._extract_from_sentence(sent)
            triplets.extend(sent_triplets)

        return triplets

    def _extract_from_sentence(self, sent: Span) -> list[EntityTriple]:
        """Extract triples from a single sentence."""
        triplets = []
        sent_text = sent.text

        entities = list(sent.ents)

        if not entities:
            return []

        subj_entity = entities[0]
        other_entities = entities[1:]

        relation = self._infer_relation(sent, subj_entity, other_entities)

        for obj_entity in other_entities:
            triple = EntityTriple(
                subject=self._clean_entity(subj_entity.text, sent_text),
                relation=relation,
                target=self._clean_entity(obj_entity.text, sent_text),
                source_sentence=sent_text.strip(),
                confidence=self._calculate_confidence(subj_entity.label_, obj_entity.label_),
            )
            triplets.append(triple)

        if len(entities) == 1:
            extracted = self._extract_pattern_based_triplets(sent)
            triplets.extend(extracted)

        return triplets

    def _infer_relation(self, sent: Span, subj: Span, others: list[Span]) -> str:
        """Infer the relation between entities based on sentence context."""
        sent_text = sent.text.lower()

        for rel_type, patterns in RELATION_PATTERNS.items():
            for pattern in patterns:
                if pattern in sent_text:
                    return rel_type

        if subj.label_ == "ORG" and others and others[0].label_ == "PERSON":
            return "founded_by"
        if subj.label_ == "WORK_OF_ART":
            return "authored"
        if "influenced" in sent.text.lower():
            return "influenced"

        return "related_to"

    def _extract_pattern_based_triplets(self, sent: Span) -> list[EntityTriple]:
        """Extract additional triples using pattern matching when no NER entities found."""
        triplets = []
        sent_text = sent.text

        for rel_type, patterns in RELATION_PATTERNS.items():
            for pattern in patterns:
                pattern_regex = re.compile(
                    rf"(.*?)\b{re.escape(pattern)}\b(.*?)(?:[.?!]|$)",
                    re.IGNORECASE,
                )
                match = pattern_regex.search(sent_text)
                if match:
                    subj = match.group(1).strip()
                    obj = match.group(2).strip() if match.group(2) else ""

                    if subj and obj and len(subj) > 2 and len(obj) > 2:
                        triple = EntityTriple(
                            subject=subj,
                            relation=rel_type,
                            target=obj,
                            source_sentence=sent_text.strip(),
                            confidence=0.7,
                        )
                        triplets.append(triple)
                        break

        return triplets

    def _clean_entity(self, text: str, source: str) -> str:
        """Clean entity text."""
        cleaned = text.strip()
        cleaned = re.sub(r"\s+", " ", cleaned)

        for pattern in self.entity_patterns.values():
            cleaned = pattern.sub("[REDACTED]", cleaned)

        return cleaned[:200] if len(cleaned) > 200 else cleaned

    def _calculate_confidence(self, subj_label: str, obj_label: str) -> float:
        """Calculate confidence based on entity type combinations."""
        high_conf = {"PERSON", "ORG", "GPE", "DATE", "MONEY"}
        medium_conf = {"FAC", "PRODUCT", "EVENT", "WORK_OF_ART", "LAW"}

        if subj_label in high_conf and obj_label in high_conf:
            return 0.9
        if subj_label in high_conf and obj_label in medium_conf:
            return 0.75
        if subj_label in medium_conf and obj_label in medium_conf:
            return 0.6
        return 0.5

    def extract_to_format(self, text: str, format: str = "triples") -> str | list[dict]:
        """
        Extract triplets in various output formats.

        Args:
            text: Input text
            format: "triples", "json", or "markdown"
        """
        triplets = self.extract_triplets(text)

        if format == "json":
            return [t.to_dict() for t in triplets]

        if format == "markdown":
            lines = ["## Extracted Triplets\n"]
            for t in triplets:
                lines.append(f"- **{t.subject}** --{t.relation}--> **{t.target}**")
            return "\n".join(lines)

        lines = []
        for t in triplets:
            lines.append(f"({t.subject}, {t.relation}, {t.target})")
        return "\n".join(lines)

    def get_stats(self, text: str) -> dict[str, Any]:
        """Get extraction statistics."""
        triplets = self.extract_triplets(text)

        relation_counts: dict[str, int] = {}
        for t in triplets:
            relation_counts[t.relation] = relation_counts.get(t.relation, 0) + 1

        return {
            "total_triplets": len(triplets),
            "relation_distribution": relation_counts,
            "avg_confidence": sum(t.confidence for t in triplets) / len(triplets)
            if triplets
            else 0,
        }


def extract_triplets_tool(text: str, format: str = "triples") -> dict[str, Any]:
    """MCP Tool: Extract (Entity, Relation, Target) triples from text."""
    harvester = TripletHarvester()

    try:
        if format == "triples":
            result = harvester.extract_to_format(text, "triples")
            return {"status": "success", "triplets": result}

        return {"status": "success", "data": harvester.extract_to_format(text, format)}

    except Exception as e:
        logger.exception(f"Triplet extraction failed: {e}")
        return {"status": "error", "error": str(e)}


def triplet_stats_tool(text: str) -> dict[str, Any]:
    """MCP Tool: Get triplet extraction statistics."""
    harvester = TripletHarvester()

    try:
        return {"status": "success", "stats": harvester.get_stats(text)}

    except Exception as e:
        logger.exception(f"Stats calculation failed: {e}")
        return {"status": "error", "error": str(e)}
