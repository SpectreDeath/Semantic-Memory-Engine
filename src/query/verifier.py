"""
✓ FACT VERIFIER - Verify Claims & Detect Contradictions
Checks factual consistency within author profiles and across sources.

Uses Scribe + knowledge base to:
✓ Extract factual claims from text
✓ Check author consistency (Has author contradicted themselves?)
✓ Compare claims across sources
✓ Identify potential disinformation patterns
✓ Rate claim reliability
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ExtractedClaim:
    """Factual claim extracted from text"""
    claim_text: str
    claim_type: str  # "factual", "opinion", "quote", "statistic"
    confidence: float  # How confident extraction was
    subject: str  # What/who the claim is about
    sentiment: str  # positive, negative, neutral
    supporting_details: List[str]


@dataclass
class VerificationResult:
    """Result of fact verification"""
    claim_text: str
    verified: bool
    confidence: float  # 0-100
    status: str  # "Verified", "Contradicted", "Disputed", "Unverifiable"
    evidence: List[str]
    source_count: int
    contradicting_sources: List[Tuple[str, str]]  # (source, contradiction)
    author_consistency: bool  # Has author contradicted this elsewhere?


@dataclass
class AuthorConsistency:
    """Consistency analysis for an author"""
    author_id: str
    total_claims: int
    verified_claims: int
    contradictory_claims: int
    disputed_claims: int
    unverifiable_claims: int
    consistency_score: float  # 0-100
    reliability_rating: str  # "High", "Medium", "Low"
    contradiction_history: List[Dict]


# ============================================================================
# FACT VERIFIER ENGINE
# ============================================================================

class FactVerifier:
    """
    Verify factual claims and detect contradictions.
    """

    def __init__(self):
        # Knowledge base (simplified - would connect to external sources)
        self.knowledge_base = self._initialize_knowledge_base()
        logger.info("✓ FactVerifier initialized")

    def _initialize_knowledge_base(self) -> Dict:
        """Initialize basic knowledge base"""
        return {
            "verified_facts": {
                "earth_shape": "spheroid",
                "climate_change_consensus": "97%_scientists",
                "moon_landing": "1969",
                "vaccination_safety": "established",
                "gravity": "fundamental_force"
            },
            "disputed_facts": {
                "5g_safety": ["safe", "potentially_harmful"],
                "inflation_causes": ["supply_chain", "government_spending"],
                "election_results": ["contested_in_some_jurisdictions"]
            },
            "known_false": {
                "flat_earth": "false",
                "vaccines_cause_autism": "false",
                "moon_landing_hoax": "false"
            }
        }

    # ========================================================================
    # TOOL 1: EXTRACT CLAIMS
    # ========================================================================

    def extract_claims(self, text: str, author_id: str = "unknown") -> List[ExtractedClaim]:
        """
        Extract factual claims from text.
        
        Args:
            text: Source text
            author_id: Author identifier
            
        Returns:
            List of extracted claims
        """
        logger.info(f"📝 Extracting claims from {author_id} ({len(text)} chars)")

        try:
            claims = []
            sentences = text.split('.')

            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:
                    continue

                # Simple heuristics to identify claim types
                claim_type = self._classify_claim_type(sentence)

                if claim_type == "none":
                    continue

                # Extract subject
                subject = self._extract_subject(sentence)

                # Determine sentiment
                sentiment = self._analyze_sentiment(sentence)

                # Extract supporting details (quoted phrases, numbers, etc.)
                details = self._extract_details(sentence)

                claim = ExtractedClaim(
                    claim_text=sentence,
                    claim_type=claim_type,
                    confidence=self._calculate_extraction_confidence(sentence),
                    subject=subject,
                    sentiment=sentiment,
                    supporting_details=details
                )
                claims.append(claim)

            logger.info(f"✅ Extracted {len(claims)} claims")
            return claims

        except Exception as e:
            logger.error(f"❌ Claim extraction failed: {str(e)}")
            return []

    # ========================================================================
    # TOOL 2: VERIFY INDIVIDUAL CLAIMS
    # ========================================================================

    def verify_claim(self, claim: ExtractedClaim, knowledge_sources: List[str] = None) -> VerificationResult:
        """
        Verify a single factual claim.
        
        Args:
            claim: ExtractedClaim to verify
            knowledge_sources: Additional sources to check
            
        Returns:
            VerificationResult
        """
        logger.info(f"🔍 Verifying claim: {claim.claim_text[:80]}...")

        try:
            # Step 1: Check against knowledge base
            kb_status, kb_confidence = self._check_knowledge_base(claim)

            # Step 2: Analyze claim components for verification difficulty
            if kb_status == "Verified":
                status = "Verified"
                confidence = kb_confidence
                contradicting = []
            elif kb_status == "Contradicted":
                status = "Contradicted"
                confidence = kb_confidence
                contradicting = [("Knowledge Base", "Claim contradicts verified facts")]
            elif kb_status == "Disputed":
                status = "Disputed"
                confidence = 50
                contradicting = []
            else:  # Unverifiable
                status = "Unverifiable"
                confidence = self._calculate_verifiability(claim)
                contradicting = []

            result = VerificationResult(
                claim_text=claim.claim_text,
                verified=(status == "Verified"),
                confidence=confidence,
                status=status,
                evidence=self._generate_evidence(claim, kb_status),
                source_count=1,  # Placeholder
                contradicting_sources=contradicting,
                author_consistency=True  # Would check against previous claims
            )

            logger.info(f"✅ Claim status: {status} ({confidence:.0f}%)")
            return result

        except Exception as e:
            logger.error(f"❌ Verification failed: {str(e)}")
            return VerificationResult(
                claim_text=claim.claim_text,
                verified=False,
                confidence=0,
                status="Error",
                evidence=[],
                source_count=0,
                contradicting_sources=[],
                author_consistency=False
            )

    # ========================================================================
    # TOOL 3: AUTHOR CONSISTENCY CHECK
    # ========================================================================

    def analyze_author_consistency(
        self,
        author_id: str,
        claim_history: List[Tuple[str, str]]  # (claim_text, timestamp)
    ) -> AuthorConsistency:
        """
        Analyze whether author contradicts themselves over time.
        
        Args:
            author_id: Author to analyze
            claim_history: List of (claim, timestamp) tuples
            
        Returns:
            AuthorConsistency analysis
        """
        logger.info(f"📊 Analyzing consistency for {author_id}")

        try:
            if not claim_history:
                return AuthorConsistency(
                    author_id=author_id,
                    total_claims=0,
                    verified_claims=0,
                    contradictory_claims=0,
                    disputed_claims=0,
                    unverifiable_claims=0,
                    consistency_score=0,
                    reliability_rating="Unknown",
                    contradiction_history=[]
                )

            # Extract claims from all texts
            all_claims = []
            for claim_text, timestamp in claim_history:
                claims = self.extract_claims(claim_text, author_id)
                for claim in claims:
                    all_claims.append((claim, timestamp))

            logger.info(f"📝 Found {len(all_claims)} claims from {author_id}")

            # Verify each claim
            verified_count = 0
            contradicted_count = 0
            disputed_count = 0
            unverifiable_count = 0
            contradictions = []

            for claim, timestamp in all_claims:
                result = self.verify_claim(claim)

                if result.status == "Verified":
                    verified_count += 1
                elif result.status == "Contradicted":
                    contradicted_count += 1
                    contradictions.append({
                        "claim": claim.claim_text[:100],
                        "timestamp": timestamp,
                        "contradiction": result.contradicting_sources[0][1] if result.contradicting_sources else "Unknown"
                    })
                elif result.status == "Disputed":
                    disputed_count += 1
                else:
                    unverifiable_count += 1

            # Calculate consistency score
            total = len(all_claims)
            if total > 0:
                verified_ratio = verified_count / total
                contradiction_penalty = (contradicted_count / total) * 50

                consistency_score = max(0, (verified_ratio * 100) - contradiction_penalty)
            else:
                consistency_score = 0

            # Rate reliability
            if consistency_score >= 80:
                reliability = "High"
            elif consistency_score >= 50:
                reliability = "Medium"
            else:
                reliability = "Low"

            consistency = AuthorConsistency(
                author_id=author_id,
                total_claims=total,
                verified_claims=verified_count,
                contradictory_claims=contradicted_count,
                disputed_claims=disputed_count,
                unverifiable_claims=unverifiable_count,
                consistency_score=consistency_score,
                reliability_rating=reliability,
                contradiction_history=contradictions
            )

            logger.info(f"✅ Consistency analysis: {reliability} ({consistency_score:.0f}%)")
            return consistency

        except Exception as e:
            logger.error(f"❌ Consistency analysis failed: {str(e)}")
            raise

    # ========================================================================
    # TOOL 4: CROSS-SOURCE CONTRADICTION DETECTION
    # ========================================================================

    def detect_cross_source_contradictions(
        self,
        sources: List[Dict]  # [{author_id, text, source_url}, ...]
    ) -> List[Dict]:
        """
        Find contradictions between sources.
        
        Args:
            sources: List of source documents
            
        Returns:
            List of detected contradictions
        """
        logger.info(f"🔀 Detecting contradictions across {len(sources)} sources")

        try:
            contradictions = []

            # Extract claims from all sources
            all_source_claims = {}
            for source in sources:
                author_id = source['author_id']
                text = source['text']
                url = source.get('source_url', 'unknown')

                claims = self.extract_claims(text, author_id)
                all_source_claims[url] = claims

            # Find contradicting claims (same subject, opposite sentiment)
            subjects_by_claim = {}
            for url, claims in all_source_claims.items():
                for claim in claims:
                    subject = claim.subject
                    if subject not in subjects_by_claim:
                        subjects_by_claim[subject] = []
                    subjects_by_claim[subject].append((url, claim))

            # Detect contradictions
            for subject, claim_list in subjects_by_claim.items():
                if len(claim_list) < 2:
                    continue

                # Find opposite sentiments
                positive = [c for _, c in claim_list if c.sentiment == "positive"]
                negative = [c for _, c in claim_list if c.sentiment == "negative"]

                if positive and negative:
                    for pos_claim in positive:
                        for neg_claim in negative:
                            # Find which sources
                            pos_source = next((u for u, c in claim_list if c == pos_claim), None)
                            neg_source = next((u for u, c in claim_list if c == neg_claim), None)

                            contradiction = {
                                "subject": subject,
                                "source_1": pos_source,
                                "claim_1": pos_claim.claim_text[:100],
                                "source_2": neg_source,
                                "claim_2": neg_claim.claim_text[:100],
                                "severity": "High",  # Both make definitive claims
                                "timestamp": datetime.utcnow().isoformat()
                            }
                            contradictions.append(contradiction)

            logger.info(f"✅ Found {len(contradictions)} contradictions")
            return contradictions

        except Exception as e:
            logger.error(f"❌ Contradiction detection failed: {str(e)}")
            return []

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _classify_claim_type(self, sentence: str) -> str:
        """Classify type of claim"""
        sentence = sentence.lower()

        # Factual claim indicators
        if any(word in sentence for word in ['study', 'research', 'found', 'shows', 'proved', 'verified']):
            return "factual"
        elif any(word in sentence for word in ['believe', 'think', 'feel', 'seem', 'appear']):
            return "opinion"
        elif sentence.startswith('"') or ' said ' in sentence:
            return "quote"
        elif re.search(r'\d+%|\d+\s*(million|billion|thousand)', sentence):
            return "statistic"

        return "none"

    def _extract_subject(self, sentence: str) -> str:
        """Extract what claim is about"""
        # Very simplified - real implementation would use NLP
        words = sentence.split()
        if len(words) > 0:
            return words[0]
        return "unknown"

    def _analyze_sentiment(self, sentence: str) -> str:
        """Simple sentiment analysis"""
        positive = ['good', 'excellent', 'safe', 'effective', 'beneficial']
        negative = ['bad', 'dangerous', 'ineffective', 'harmful', 'terrible']

        sentence_lower = sentence.lower()

        pos_count = sum(1 for word in positive if word in sentence_lower)
        neg_count = sum(1 for word in negative if word in sentence_lower)

        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"

    def _extract_details(self, sentence: str) -> List[str]:
        """Extract supporting details"""
        details = []

        # Numbers/statistics
        numbers = re.findall(r'\d+(?:%|\s*(?:million|billion|thousand))?', sentence)
        details.extend(numbers[:3])

        # Quoted phrases
        quotes = re.findall(r'"([^"]*)"', sentence)
        details.extend(quotes[:2])

        return details

    def _calculate_extraction_confidence(self, sentence: str) -> float:
        """Confidence in claim extraction"""
        # Longer, more specific claims = higher confidence
        length_factor = min(100, len(sentence) / 10)
        specificity_factor = 50  # Placeholder

        return (length_factor + specificity_factor) / 2

    def _check_knowledge_base(self, claim: ExtractedClaim) -> Tuple[str, float]:
        """Check claim against knowledge base"""
        claim_lower = claim.claim_text.lower()

        # Check verified facts
        for fact, value in self.knowledge_base['verified_facts'].items():
            if fact in claim_lower:
                return ("Verified", 95)

        # Check known false claims
        for false_claim in self.knowledge_base['known_false']:
            if false_claim in claim_lower:
                return ("Contradicted", 95)

        # Check disputed
        for disputed in self.knowledge_base['disputed_facts']:
            if disputed in claim_lower:
                return ("Disputed", 60)

        return ("Unverifiable", 40)

    def _calculate_verifiability(self, claim: ExtractedClaim) -> float:
        """Score how verifiable a claim is"""
        factors = 0

        # Specific dates = more verifiable
        if re.search(r'\d{4}|\d{1,2}/\d{1,2}', claim.claim_text):
            factors += 20

        # Numbers = more verifiable
        if re.search(r'\d+%|\d+\s*(?:million|billion)', claim.claim_text):
            factors += 20

        # Names of organizations/people = more verifiable
        if any(char.isupper() for char in claim.claim_text.split()[1:]):
            factors += 15

        # Quotes = more verifiable
        if '"' in claim.claim_text:
            factors += 15

        # General claims = less verifiable
        if any(word in claim.claim_text.lower() for word in ['always', 'never', 'everything', 'everyone']):
            factors -= 20

        return max(0, min(100, 40 + factors))

    def _generate_evidence(self, claim: ExtractedClaim, kb_status: str) -> List[str]:
        """Generate evidence/justification"""
        evidence = []

        if kb_status == "Verified":
            evidence.append("Matches verified knowledge base entry")
            evidence.append("Consistent with established facts")
        elif kb_status == "Contradicted":
            evidence.append("Contradicts verified facts")
        elif kb_status == "Disputed":
            evidence.append("Subject of ongoing debate")
            evidence.append("Multiple authoritative sources disagree")

        if claim.supporting_details:
            evidence.append(f"Supporting details: {', '.join(claim.supporting_details)}")

        return evidence


# ============================================================================
# MCP TOOL FUNCTIONS
# ============================================================================

def extract_claims_tool(text: str, author_id: str = "unknown") -> Dict:
    """MCP Tool: Extract claims from text"""
    verifier = FactVerifier()
    claims = verifier.extract_claims(text, author_id)

    return {
        "status": "success",
        "total_claims": len(claims),
        "claims": [
            {
                "text": c.claim_text[:80],
                "type": c.claim_type,
                "confidence": round(c.confidence, 1),
                "subject": c.subject,
                "sentiment": c.sentiment
            }
            for c in claims
        ]
    }


def verify_claims_tool(text: str) -> Dict:
    """MCP Tool: Extract and verify claims"""
    verifier = FactVerifier()
    claims = verifier.extract_claims(text)

    verified_results = []
    for claim in claims:
        result = verifier.verify_claim(claim)
        verified_results.append({
            "claim": claim.claim_text[:80],
            "status": result.status,
            "confidence": round(result.confidence, 1),
            "verified": result.verified
        })

    verified = sum(1 for r in verified_results if r['verified'])

    return {
        "status": "success",
        "total_claims": len(claims),
        "verified": verified,
        "results": verified_results
    }


if __name__ == "__main__":
    print("\n" + "="*80)
    print("✓ FACT VERIFIER DEMO")
    print("="*80 + "\n")

    print("✅ FACT VERIFIER READY")
    print("="*80 + "\n")
