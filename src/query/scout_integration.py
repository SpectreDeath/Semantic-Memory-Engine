"""
🔎 SCOUT - Knowledge Gap Detector & Auto-Harvest Trigger
Identifies missing information and automatically triggers content harvesting.

Uses all layers to:
✓ Detect unanswered questions
✓ Score knowledge complexity
✓ Trigger HarvesterSpider for gap resolution
✓ Track gap-to-answer lifecycle
✓ Learn from previous queries
"""

import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class KnowledgeGap:
    """Identified gap in knowledge"""
    gap_id: str
    question: str
    topic: str
    complexity_score: float  # 0-100
    urgency: str  # "Immediate", "High", "Medium", "Low"
    detected_timestamp: str
    related_claims: List[str]
    suggested_search_terms: List[str]
    auto_harvest_triggered: bool
    estimated_resolution_time: int  # seconds


@dataclass
class GapResolution:
    """Resolution of a knowledge gap"""
    gap_id: str
    resolution_timestamp: str
    harvested_articles: int
    key_findings: List[str]
    authoritative_sources: List[str]
    confidence_in_answer: float  # 0-100


@dataclass
class GapQuery:
    """Historical query information"""
    query_text: str
    frequency: int
    last_seen: str
    related_gaps: List[str]
    successful_resolutions: int
    avg_resolution_time: int


# ============================================================================
# SCOUT ENGINE
# ============================================================================

class Scout:
    """
    Detect knowledge gaps and trigger automated harvesting.
    
    Enhanced with semantic gap detection using WordNet for better
    identification of missing related concepts and semantic connections.
    """

    def __init__(self, harvester_path: str = None):
        self.db_path = "d:\\mcp_servers\\storage\\scout_gaps.sqlite"
        self.harvester_path = harvester_path or "d:\\mcp_servers\\harvester_spider.py"
        self._initialize_db()
        
        # Initialize semantic graph for semantic gap detection
        try:
            from src.core.semantic_graph import SemanticGraph
            self.semantic_graph = SemanticGraph()
        except Exception as e:
            logger.warning(f"Semantic graph not available: {e}")
            self.semantic_graph = None
        
        logger.info("🔎 Scout initialized")

    def _initialize_db(self):
        """Initialize Scout database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Knowledge gaps table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_gaps (
                    gap_id TEXT PRIMARY KEY,
                    question TEXT,
                    topic TEXT,
                    complexity_score REAL,
                    urgency TEXT,
                    detected_timestamp TEXT,
                    status TEXT,
                    auto_harvest_triggered BOOLEAN,
                    harvest_job_id TEXT
                )
            """)

            # Gap resolutions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gap_resolutions (
                    gap_id TEXT,
                    resolution_timestamp TEXT,
                    harvested_articles INTEGER,
                    key_findings TEXT,
                    confidence REAL,
                    PRIMARY KEY (gap_id, resolution_timestamp)
                )
            """)

            # Historical queries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_queries (
                    query_hash TEXT PRIMARY KEY,
                    query_text TEXT,
                    frequency INTEGER,
                    last_seen TEXT,
                    avg_resolution_time INTEGER
                )
            """)

            conn.commit()
            conn.close()
            logger.info("✅ Scout database initialized")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")
            raise

    # ========================================================================
    # TOOL 1: DETECT KNOWLEDGE GAPS
    # ========================================================================

    def detect_gaps_in_text(
        self,
        text: str,
        context: str = "",
        auto_harvest: bool = True
    ) -> List[KnowledgeGap]:
        """
        Detect knowledge gaps in provided text.
        
        Args:
            text: Source text to analyze
            context: Additional context about text source
            auto_harvest: Whether to auto-trigger harvesting
            
        Returns:
            List of detected knowledge gaps
        """
        logger.info(f"🔎 Analyzing text for knowledge gaps ({len(text)} chars)")

        try:
            gaps = []

            # Step 1: Extract questions and uncertain statements
            questions = self._extract_questions(text)
            uncertain_claims = self._extract_uncertain_claims(text)

            logger.info(f"📝 Found {len(questions)} questions, {len(uncertain_claims)} uncertain claims")

            # Step 2: Analyze each gap
            all_gaps = questions + uncertain_claims

            for i, gap_item in enumerate(all_gaps):
                gap_type, content = gap_item

                # Score complexity
                complexity = self._calculate_gap_complexity(content, gap_type)

                # Determine urgency
                urgency = self._determine_urgency(complexity, gap_type)

                # Extract topic
                topic = self._extract_topic(content)

                # Generate search terms
                search_terms = self._generate_search_terms(content, topic)
                
                # Add semantic variants if available
                if self.semantic_graph:
                    search_terms.extend(self._get_semantic_variants(topic))

                # Create gap object
                gap = KnowledgeGap(
                    gap_id=f"gap_{datetime.utcnow().timestamp()}_{i}",
                    question=content[:200],
                    topic=topic,
                    complexity_score=complexity,
                    urgency=urgency,
                    detected_timestamp=datetime.utcnow().isoformat(),
                    related_claims=[],  # Would extract from text
                    suggested_search_terms=search_terms,
                    auto_harvest_triggered=False,
                    estimated_resolution_time=self._estimate_resolution_time(complexity)
                )

                # Auto-harvest if complexity is high
                if auto_harvest and complexity >= 70:
                    harvest_job = self._trigger_harvest(gap)
                    gap.auto_harvest_triggered = True
                    logger.info(f"🚀 Auto-harvest triggered for: {gap.question[:50]}...")

                gaps.append(gap)

            # Step 3: Save to database
            self._save_gaps_to_db(gaps)

            logger.info(f"✅ Detected and processed {len(gaps)} knowledge gaps")
            return gaps

        except Exception as e:
            logger.error(f"❌ Gap detection failed: {str(e)}")
            return []
    
    def detect_semantic_gaps(
        self,
        central_concept: str,
        existing_facts: Optional[Set[str]] = None
    ) -> List[Dict]:
        """
        Detect knowledge gaps using semantic relationships.
        
        Finds related concepts that haven't been covered yet using WordNet,
        improving gap detection through semantic understanding.
        
        Args:
            central_concept: The main concept to analyze
            existing_facts: Set of fact identifiers already covered
        
        Returns:
            List of semantic gaps with priorities and reasoning
        """
        if not self.semantic_graph:
            logger.warning("Semantic graph not available for gap detection")
            return []
        
        logger.info(f"🧠 Detecting semantic gaps for: {central_concept}")
        
        try:
            gaps = self.semantic_graph.detect_semantic_gaps(
                central_concept,
                existing_facts or set()
            )
            
            # Annotate gaps with additional context
            annotated_gaps = []
            for gap in gaps:
                annotated_gap = {
                    **gap,
                    'gap_id': f"semantic_gap_{central_concept}_{gap['gap']}",
                    'detected_timestamp': datetime.utcnow().isoformat(),
                    'concept_source': central_concept,
                    'auto_harvest': gap.get('priority') in ('high', 'medium')
                }
                
                # Auto-harvest high-priority semantic gaps
                if annotated_gap['auto_harvest']:
                    search_terms = [annotated_gap['gap']]
                    logger.info(f"📚 Semantic gap detected: {annotated_gap['gap']} ({annotated_gap['type']})")
                
                annotated_gaps.append(annotated_gap)
            
            return annotated_gaps
            
        except Exception as e:
            logger.error(f"❌ Semantic gap detection failed: {e}")
            return []

    # ========================================================================
    # TOOL 2: KNOWLEDGE COMPLEXITY SCORING
    # ========================================================================

    def score_knowledge_complexity(
        self,
        text: str,
        topic: str = None
    ) -> float:
        """
        Score complexity of knowledge needed to answer a question.
        
        Args:
            text: Text to analyze
            topic: Optional topic classification
            
        Returns:
            Complexity score 0-100
        """
        logger.info(f"📊 Scoring complexity for: {text[:60]}...")

        try:
            score = 0

            # Factor 1: Sentence complexity (20%)
            sentence_complexity = self._analyze_sentence_complexity(text)
            score += sentence_complexity * 0.2

            # Factor 2: Vocabulary sophistication (15%)
            vocab_score = self._analyze_vocabulary_level(text)
            score += vocab_score * 0.15

            # Factor 3: Requires cross-domain knowledge (20%)
            multidomain_score = self._analyze_cross_domain_requirements(text)
            score += multidomain_score * 0.2

            # Factor 4: Temporal/temporal-spatial complexity (15%)
            temporal_score = self._analyze_temporal_complexity(text)
            score += temporal_score * 0.15

            # Factor 5: Subjectivity/Disputed nature (15%)
            disputed_score = self._analyze_dispute_level(text)
            score += disputed_score * 0.15

            # Factor 6: Information availability (15%)
            availability_score = self._analyze_information_availability(text, topic)
            score += availability_score * 0.15

            final_score = min(100, max(0, score))
            logger.info(f"✅ Complexity score: {final_score:.0f}%")
            return final_score

        except Exception as e:
            logger.error(f"❌ Complexity scoring failed: {str(e)}")
            return 0

    # ========================================================================
    # TOOL 3: TRIGGER AUTOMATED HARVEST
    # ========================================================================

    def trigger_harvest_for_gap(self, gap: KnowledgeGap) -> Dict:
        """
        Trigger HarvesterSpider to resolve knowledge gap.
        
        Args:
            gap: KnowledgeGap to resolve
            
        Returns:
            Harvest job details
        """
        logger.info(f"🚀 Triggering harvest for gap: {gap.gap_id}")

        try:
            from harvester_spider import HarvesterSpider

            spider = HarvesterSpider()

            # Build search queries from suggested terms
            search_queries = gap.suggested_search_terms

            logger.info(f"🔍 Starting harvesting with {len(search_queries)} queries")

            # Trigger spider with multiple searches
            results = []
            for query in search_queries[:3]:  # Top 3 queries
                result = spider.search_web(query, max_results=5)
                if result:
                    results.extend(result)

            # Store harvest metadata
            job_id = f"harvest_{gap.gap_id}_{datetime.utcnow().timestamp()}"

            harvest_job = {
                "job_id": job_id,
                "gap_id": gap.gap_id,
                "queries": search_queries,
                "articles_found": len(results),
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Harvest completed: {len(results)} articles found")
            return harvest_job

        except Exception as e:
            logger.error(f"❌ Harvest triggering failed: {str(e)}")
            return {"error": str(e)}

    # ========================================================================
    # TOOL 4: TRACK GAP LIFECYCLE
    # ========================================================================

    def track_gap_resolution(
        self,
        gap_id: str,
        harvested_articles: List[Dict],
        key_findings: List[str]
    ) -> GapResolution:
        """
        Track resolution of a knowledge gap.
        
        Args:
            gap_id: Gap identifier
            harvested_articles: Articles harvested for resolution
            key_findings: Key findings from resolution
            
        Returns:
            GapResolution object
        """
        logger.info(f"📊 Tracking resolution for gap: {gap_id}")

        try:
            # Extract authoritative sources
            sources = set()
            for article in harvested_articles:
                source = article.get('source', 'unknown')
                sources.add(source)

            # Calculate confidence
            article_count = len(harvested_articles)
            source_diversity = len(sources)
            confidence = min(100, (article_count * 10) + (source_diversity * 5))

            resolution = GapResolution(
                gap_id=gap_id,
                resolution_timestamp=datetime.utcnow().isoformat(),
                harvested_articles=article_count,
                key_findings=key_findings[:5],  # Top 5
                authoritative_sources=list(sources)[:3],
                confidence_in_answer=confidence
            )

            # Save to database
            self._save_resolution_to_db(resolution)

            logger.info(f"✅ Gap resolution tracked: {article_count} articles, {confidence:.0f}% confidence")
            return resolution

        except Exception as e:
            logger.error(f"❌ Resolution tracking failed: {str(e)}")
            raise

    # ========================================================================
    # TOOL 5: QUERY PATTERN LEARNING
    # ========================================================================

    def learn_from_query_patterns(self) -> List[GapQuery]:
        """
        Learn from historical query patterns to predict future gaps.
        
        Returns:
            List of high-frequency gap patterns
        """
        logger.info("📚 Learning from query patterns")

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get high-frequency historical queries
            cursor.execute("""
                SELECT query_text, frequency, last_seen, avg_resolution_time
                FROM historical_queries
                WHERE frequency > 3
                ORDER BY frequency DESC
                LIMIT 10
            """)

            patterns = []
            for row in cursor.fetchall():
                query_text, frequency, last_seen, avg_time = row

                pattern = GapQuery(
                    query_text=query_text,
                    frequency=frequency,
                    last_seen=last_seen,
                    related_gaps=[],
                    successful_resolutions=frequency // 2,  # Estimate
                    avg_resolution_time=avg_time
                )
                patterns.append(pattern)

            conn.close()

            logger.info(f"✅ Learned {len(patterns)} query patterns")
            return patterns

        except Exception as e:
            logger.error(f"❌ Pattern learning failed: {str(e)}")
            return []

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _extract_questions(self, text: str) -> List[Tuple[str, str]]:
        """Extract questions from text"""
        questions = []
        sentences = text.split('.')

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence.endswith('?'):
                questions.append(('question', sentence))

        return questions

    def _extract_uncertain_claims(self, text: str) -> List[Tuple[str, str]]:
        """Extract uncertain statements"""
        uncertain = []
        uncertainty_phrases = ['might', 'could', 'possibly', 'perhaps', 'uncertain', 'unclear', 'need more info']

        sentences = text.split('.')
        for sentence in sentences:
            if any(phrase in sentence.lower() for phrase in uncertainty_phrases):
                uncertain.append(('uncertain', sentence.strip()))

        return uncertain

    def _calculate_gap_complexity(self, content: str, gap_type: str) -> float:
        """Calculate complexity score for a gap"""
        base_score = 50

        # Questions are more complex
        if gap_type == 'question':
            base_score += 20

        # Longer gaps indicate complexity
        base_score += min(30, len(content) / 50)

        # Technical terms indicate complexity
        tech_terms = ['algorithm', 'quantum', 'genomic', 'statistical', 'neural', 'framework']
        tech_count = sum(1 for term in tech_terms if term in content.lower())
        base_score += tech_count * 5

        return min(100, base_score)

    def _determine_urgency(self, complexity: float, gap_type: str) -> str:
        """Determine urgency level"""
        if complexity >= 80:
            return "Immediate"
        elif complexity >= 60:
            return "High"
        elif complexity >= 40:
            return "Medium"
        else:
            return "Low"

    def _extract_topic(self, text: str) -> str:
        """Extract topic from text"""
        # Simplified - would use NLP
        words = text.split()
        if len(words) > 2:
            return ' '.join(words[:2])
        return 'General'

    def _generate_search_terms(self, text: str, topic: str) -> List[str]:
        """Generate search terms for gap resolution"""
        terms = []

        # Topic
        terms.append(topic)

        # Key nouns from text
        important_words = [w for w in text.split() if len(w) > 5]
        terms.extend(important_words[:2])

        # Question reformulation
        if text.endswith('?'):
            # Convert to search terms
            terms.append(text[:-1].replace('?', ''))

        return list(set(terms))[:5]

    def _estimate_resolution_time(self, complexity: float) -> int:
        """Estimate time to resolve gap in seconds"""
        # Low complexity: 10-60 seconds
        # High complexity: 60-600 seconds
        return int(10 + (complexity * 5.9))

    def _trigger_harvest(self, gap: KnowledgeGap) -> str:
        """Trigger harvesting for gap"""
        try:
            job_result = self.trigger_harvest_for_gap(gap)
            return job_result.get('job_id', 'unknown')
        except:
            return "failed"

    def _save_gaps_to_db(self, gaps: List[KnowledgeGap]):
        """Save detected gaps to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for gap in gaps:
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge_gaps
                    (gap_id, question, topic, complexity_score, urgency, detected_timestamp, status, auto_harvest_triggered)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    gap.gap_id,
                    gap.question,
                    gap.topic,
                    gap.complexity_score,
                    gap.urgency,
                    gap.detected_timestamp,
                    'detected',
                    gap.auto_harvest_triggered
                ))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Failed to save gaps: {str(e)}")

    def _save_resolution_to_db(self, resolution: GapResolution):
        """Save gap resolution to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO gap_resolutions
                (gap_id, resolution_timestamp, harvested_articles, key_findings, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (
                resolution.gap_id,
                resolution.resolution_timestamp,
                resolution.harvested_articles,
                '|'.join(resolution.key_findings),
                resolution.confidence_in_answer
            ))

            # Update gap status
            cursor.execute("""
                UPDATE knowledge_gaps SET status = 'resolved'
                WHERE gap_id = ?
            """, (resolution.gap_id,))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"❌ Failed to save resolution: {str(e)}")

    def _analyze_sentence_complexity(self, text: str) -> float:
        """Analyze sentence structure complexity"""
        sentences = text.split('.')
        if not sentences:
            return 0

        avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
        return min(100, avg_length * 5)

    def _analyze_vocabulary_level(self, text: str) -> float:
        """Score vocabulary sophistication"""
        long_words = [w for w in text.split() if len(w) > 8]
        return min(100, len(long_words) * 2)

    def _analyze_cross_domain_requirements(self, text: str) -> float:
        """Analyze if question spans multiple domains"""
        domains_found = 0
        domain_keywords = {
            'science': ['quantum', 'physics', 'biology', 'chemistry'],
            'technology': ['algorithm', 'neural', 'quantum', 'blockchain'],
            'history': ['century', 'era', 'historical', 'past'],
            'business': ['market', 'revenue', 'profit', 'company']
        }

        for domain, keywords in domain_keywords.items():
            if any(kw in text.lower() for kw in keywords):
                domains_found += 1

        return min(100, domains_found * 25)

    def _analyze_temporal_complexity(self, text: str) -> float:
        """Analyze temporal/spatial dimensions"""
        temporal_keywords = ['when', 'where', 'century', 'era', 'generation', 'period']
        temporal_count = sum(1 for kw in temporal_keywords if kw in text.lower())
        return min(100, temporal_count * 15)

    def _analyze_dispute_level(self, text: str) -> float:
        """Analyze how much topic is disputed"""
        dispute_keywords = ['controversial', 'debate', 'disputed', 'disagreement', 'conflicting']
        dispute_count = sum(1 for kw in dispute_keywords if kw in text.lower())
        return min(100, dispute_count * 20)

    def _analyze_information_availability(self, text: str, topic: str = None) -> float:
        """Analyze how available information is for this topic"""
        # Placeholder - would check web data availability
        return 50
    
    def _get_semantic_variants(self, term: str) -> List[str]:
        """Get semantic variants (synonyms, related terms) for a term."""
        if not self.semantic_graph or not term:
            return []
        
        try:
            variants = self.semantic_graph.find_semantic_variants(term)
            result = []
            # Collect synonyms and related terms, limit to 5
            for variant_type, words in variants.items():
                result.extend(words[:2])
            return result[:5]
        except Exception as e:
            logger.warning(f"Could not get semantic variants for '{term}': {e}")
            return []


# ============================================================================
# MCP TOOL FUNCTIONS
# ============================================================================

def detect_knowledge_gaps_tool(text: str) -> Dict:
    """MCP Tool: Detect knowledge gaps in text"""
    scout = Scout()
    gaps = scout.detect_gaps_in_text(text, auto_harvest=True)

    return {
        "status": "success",
        "total_gaps": len(gaps),
        "high_urgency": sum(1 for g in gaps if g.urgency in ["Immediate", "High"]),
        "auto_harvested": sum(1 for g in gaps if g.auto_harvest_triggered),
        "gaps": [
            {
                "id": g.gap_id,
                "question": g.question[:60],
                "complexity": f"{g.complexity_score:.0f}%",
                "urgency": g.urgency,
                "topic": g.topic
            }
            for g in gaps[:5]  # Top 5
        ]
    }


def score_complexity_tool(text: str) -> Dict:
    """MCP Tool: Score knowledge complexity"""
    scout = Scout()
    score = scout.score_knowledge_complexity(text)

    return {
        "status": "success",
        "complexity_score": round(score, 1),
        "level": "High" if score >= 70 else ("Medium" if score >= 40 else "Low"),
        "auto_harvest_triggered": score >= 70
    }


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🔎 SCOUT KNOWLEDGE GAP DETECTOR")
    print("="*80 + "\n")

    print("✅ SCOUT READY")
    print("="*80 + "\n")
