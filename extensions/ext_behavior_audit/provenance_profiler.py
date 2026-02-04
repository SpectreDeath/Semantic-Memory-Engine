"""
Provenance Profiler Extension

Analyzes text for rhetorical motives including Ultimate Terms (God/Devil terms)
and Distance Markers to identify commercial policy-aligned LLM patterns.
"""

import re
import logging
import threading
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from collections import Counter


# Configure logging for the provenance profiler
logger = logging.getLogger('behavior_audit.provenance_profiler')
logger.setLevel(logging.INFO)

# Create file handler for provenance profiling events
profiler_handler = logging.FileHandler('provenance_profiling_events.log')
profiler_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
profiler_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(profiler_handler)


@dataclass
class ProvenanceProfile:
    """Result of provenance profiling analysis."""
    god_term_density: float
    devil_term_density: float
    total_ultimate_term_density: float
    distance_markers_count: int
    god_terms_found: List[str]
    devil_terms_found: List[str]
    distance_markers_found: List[str]
    profile_detected: bool
    confidence_score: float
    processing_time: float
    timestamp: datetime


class ProvenanceProfiler:
    """Profiles text for rhetorical motives and commercial policy-aligned LLM patterns."""
    
    def __init__(self):
        # Ultimate Terms (God/Devil terms) - terms that invoke ultimate values
        self.god_terms = {
            # Positive ultimate values
            'truth', 'justice', 'freedom', 'liberty', 'democracy', 'peace', 'love',
            'compassion', 'empathy', 'wisdom', 'knowledge', 'understanding', 'progress',
            'innovation', 'creativity', 'beauty', 'harmony', 'unity', 'equality',
            'fairness', 'integrity', 'honesty', 'authenticity', 'transparency',
            'accountability', 'responsibility', 'sustainability', 'prosperity',
            'security', 'safety', 'wellbeing', 'health', 'happiness', 'fulfillment',
            'purpose', 'meaning', 'virtue', 'excellence', 'perfection', 'ideal',
            'utopia', 'paradise', 'heaven', 'salvation', 'redemption', 'grace',
            'blessing', 'miracle', 'divine', 'sacred', 'holy', 'spiritual', 'enlightenment',
            'awakening', 'transcendence', 'elevation', 'sublimity', 'grandeur',
            'magnificence', 'glory', 'honor', 'dignity', 'respect', 'reverence',
            'devotion', 'faith', 'belief', 'trust', 'confidence', 'certainty',
            'assurance', 'conviction', 'determination', 'commitment', 'dedication',
            'devotion', 'loyalty', 'fidelity', 'constancy', 'steadfastness', 'resolve'
        }
        
        self.devil_terms = {
            # Negative ultimate values
            'evil', 'sin', 'wickedness', 'corruption', 'depravity', 'immorality',
            'injustice', 'oppression', 'tyranny', 'dictatorship', 'totalitarianism',
            'fascism', 'communism', 'authoritarianism', 'despotism', 'cruelty',
            'brutality', 'violence', 'aggression', 'hatred', 'malice', 'spite',
            'envy', 'jealousy', 'greed', 'avarice', 'selfishness', 'selfish',
            'narcissism', 'egoism', 'arrogance', 'pride', 'vanity', 'conceit',
            'hubris', 'overconfidence', 'recklessness', 'carelessness', 'negligence',
            'irresponsibility', 'unreliability', 'untrustworthiness', 'deceit',
            'deception', 'fraud', 'fraudulence', 'dishonesty', 'dishonest', 'deceptive',
            'misleading', 'confusing', 'obfuscating', 'clouding', 'muddying',
            'polluting', 'contaminating', 'poisoning', 'corrupting', 'tainting',
            'spoiling', 'ruining', 'destroying', 'devastating', 'devastation',
            'catastrophe', 'disaster', 'tragedy', 'calamity', 'misfortune', 'woe',
            'sorrow', 'grief', 'sadness', 'despair', 'despondency', 'hopelessness',
            'helplessness', 'powerlessness', 'weakness', 'vulnerability', 'fragility',
            'brittleness', 'delicacy', 'sensitivity', 'susceptibility', 'fragility'
        }
        
        # Distance Markers - replacing personal pronouns with institutional terms
        self.distance_markers = {
            # Replacing "I/Me" with institutional terms
            r'\bthe model\b': 'The Model',
            r'\bthe data\b': 'The Data',
            r'\bthe system\b': 'The System',
            r'\bthe algorithm\b': 'The Algorithm',
            r'\bthe code\b': 'The Code',
            r'\bthe program\b': 'The Program',
            r'\bthe software\b': 'The Software',
            r'\bthe application\b': 'The Application',
            r'\bthe tool\b': 'The Tool',
            r'\bthe platform\b': 'The Platform',
            r'\bthe framework\b': 'The Framework',
            r'\bthe architecture\b': 'The Architecture',
            r'\bthe infrastructure\b': 'The Infrastructure',
            r'\bthe service\b': 'The Service',
            r'\bthe solution\b': 'The Solution',
            r'\bthe product\b': 'The Product',
            r'\bthe feature\b': 'The Feature',
            r'\bthe capability\b': 'The Capability',
            r'\bthe functionality\b': 'The Functionality',
            r'\bthe mechanism\b': 'The Mechanism',
            r'\bthe process\b': 'The Process',
            r'\bthe procedure\b': 'The Procedure',
            r'\bthe method\b': 'The Method',
            r'\bthe approach\b': 'The Approach',
            r'\bthe technique\b': 'The Technique',
            r'\bthe strategy\b': 'The Strategy',
            r'\bthe tactic\b': 'The Tactic',
            r'\bthe policy\b': 'The Policy',
            r'\bthe protocol\b': 'The Protocol',
            r'\bthe standard\b': 'The Standard',
            r'\bthe guideline\b': 'The Guideline',
            r'\bthe principle\b': 'The Principle',
            r'\bthe rule\b': 'The Rule',
            r'\bthe regulation\b': 'The Regulation',
            r'\bthe requirement\b': 'The Requirement',
            r'\bthe specification\b': 'The Specification',
            r'\bthe criterion\b': 'The Criterion',
            r'\bthe benchmark\b': 'The Benchmark',
            r'\bthe metric\b': 'The Metric',
            r'\bthe measurement\b': 'The Measurement',
            r'\bthe evaluation\b': 'The Evaluation',
            r'\bthe assessment\b': 'The Assessment',
            r'\bthe analysis\b': 'The Analysis',
            r'\bthe examination\b': 'The Examination',
            r'\bthe investigation\b': 'The Investigation',
            r'\bthe research\b': 'The Research',
            r'\bthe study\b': 'The Study',
            r'\bthe survey\b': 'The Survey',
            r'\bthe poll\b': 'The Poll',
            r'\bthe questionnaire\b': 'The Questionnaire',
            r'\bthe feedback\b': 'The Feedback',
            r'\bthe response\b': 'The Response',
            r'\bthe answer\b': 'The Answer',
            r'\bthe solution\b': 'The Solution',
            r'\bthe resolution\b': 'The Resolution',
            r'\bthe outcome\b': 'The Outcome',
            r'\bthe result\b': 'The Result',
            r'\bthe consequence\b': 'The Consequence',
            r'\bthe effect\b': 'The Effect',
            r'\bthe impact\b': 'The Impact',
            r'\bthe influence\b': 'The Influence',
            r'\bthe implication\b': 'The Implication',
            r'\bthe ramification\b': 'The Ramification',
            r'\bthe repercussion\b': 'The Repercussion',
            r'\bthe aftermath\b': 'The Aftermath',
            r'\bthe legacy\b': 'The Legacy',
            r'\bthe heritage\b': 'The Heritage',
            r'\bthe tradition\b': 'The Tradition',
            r'\bthe custom\b': 'The Custom',
            r'\bthe practice\b': 'The Practice',
            r'\bthe habit\b': 'The Habit',
            r'\bthe routine\b': 'The Routine',
            r'\bthe pattern\b': 'The Pattern',
            r'\bthe trend\b': 'The Trend',
            r'\bthe tendency\b': 'The Tendency',
            r'\bthe inclination\b': 'The Inclination',
            r'\bthe preference\b': 'The Preference',
            r'\bthe choice\b': 'The Choice',
            r'\bthe option\b': 'The Option',
            r'\bthe alternative\b': 'The Alternative',
            r'\bthe possibility\b': 'The Possibility',
            r'\bthe potential\b': 'The Potential',
            r'\bthe capability\b': 'The Capability',
            r'\bthe capacity\b': 'The Capacity',
            r'\bthe ability\b': 'The Ability',
            r'\bthe skill\b': 'The Skill',
            r'\bthe talent\b': 'The Talent',
            r'\bthe expertise\b': 'The Expertise',
            r'\bthe knowledge\b': 'The Knowledge',
            r'\bthe understanding\b': 'The Understanding',
            r'\bthe comprehension\b': 'The Comprehension',
            r'\bthe insight\b': 'The Insight',
            r'\bthe wisdom\b': 'The Wisdom',
            r'\bthe intelligence\b': 'The Intelligence',
            r'\bthe brilliance\b': 'The Brilliance',
            r'\bthe genius\b': 'The Genius',
            r'\bthe creativity\b': 'The Creativity',
            r'\bthe innovation\b': 'The Innovation',
            r'\bthe imagination\b': 'The Imagination',
            r'\bthe vision\b': 'The Vision',
            r'\bthe perspective\b': 'The Perspective',
            r'\bthe viewpoint\b': 'The Viewpoint',
            r'\bthe standpoint\b': 'The Standpoint',
            r'\bthe position\b': 'The Position',
            r'\bthe stance\b': 'The Stance',
            r'\bthe attitude\b': 'The Attitude',
            r'\bthe approach\b': 'The Approach',
            r'\bthe method\b': 'The Method',
            r'\bthe technique\b': 'The Technique',
            r'\bthe strategy\b': 'The Strategy',
            r'\bthe tactic\b': 'The Tactic',
            r'\bthe plan\b': 'The Plan',
            r'\bthe scheme\b': 'The Scheme',
            r'\bthe design\b': 'The Design',
            r'\bthe blueprint\b': 'The Blueprint',
            r'\bthe framework\b': 'The Framework',
            r'\bthe structure\b': 'The Structure',
            r'\bthe architecture\b': 'The Architecture',
            r'\bthe system\b': 'The System',
            r'\bthe organization\b': 'The Organization',
            r'\bthe institution\b': 'The Institution',
            r'\bthe establishment\b': 'The Establishment',
            r'\bthe corporation\b': 'The Corporation',
            r'\bthe company\b': 'The Company',
            r'\bthe business\b': 'The Business',
            r'\bthe enterprise\b': 'The Enterprise',
            r'\bthe venture\b': 'The Venture',
            r'\bthe undertaking\b': 'The Undertaking',
            r'\bthe project\b': 'The Project',
            r'\bthe initiative\b': 'The Initiative',
            r'\bthe program\b': 'The Program',
            r'\bthe campaign\b': 'The Campaign',
            r'\bthe effort\b': 'The Effort',
            r'\bthe endeavor\b': 'The Endeavor',
            r'\bthe pursuit\b': 'The Pursuit',
            r'\bthe quest\b': 'The Quest',
            r'\bthe search\b': 'The Search',
            r'\bthe investigation\b': 'The Investigation',
            r'\bthe exploration\b': 'The Exploration',
            r'\bthe examination\b': 'The Examination',
            r'\bthe analysis\b': 'The Analysis',
            r'\bthe study\b': 'The Study',
            r'\bthe research\b': 'The Research',
            r'\bthe inquiry\b': 'The Inquiry',
            r'\bthe probe\b': 'The Probe',
            r'\bthe review\b': 'The Review',
            r'\bthe assessment\b': 'The Assessment',
            r'\bthe evaluation\b': 'The Evaluation',
            r'\bthe appraisal\b': 'The Appraisal',
            r'\bthe judgment\b': 'The Judgment',
            r'\bthe verdict\b': 'The Verdict',
            r'\bthe decision\b': 'The Decision',
            r'\bthe determination\b': 'The Determination',
            r'\bthe conclusion\b': 'The Conclusion',
            r'\bthe resolution\b': 'The Resolution',
            r'\bthe outcome\b': 'The Outcome',
            r'\bthe result\b': 'The Result',
            r'\bthe consequence\b': 'The Consequence',
            r'\bthe effect\b': 'The Effect',
            r'\bthe impact\b': 'The Impact',
            r'\bthe influence\b': 'The Influence',
            r'\bthe implication\b': 'The Implication',
            r'\bthe ramification\b': 'The Ramification',
            r'\bthe repercussion\b': 'The Repercussion',
            r'\bthe aftermath\b': 'The Aftermath',
            r'\bthe legacy\b': 'The Legacy',
            r'\bthe heritage\b': 'The Heritage',
            r'\bthe tradition\b': 'The Tradition',
            r'\bthe custom\b': 'The Custom',
            r'\bthe practice\b': 'The Practice',
            r'\bthe habit\b': 'The Habit',
            r'\bthe routine\b': 'The Routine',
            r'\bthe pattern\b': 'The Pattern',
            r'\bthe trend\b': 'The Trend',
            r'\bthe tendency\b': 'The Tendency',
            r'\bthe inclination\b': 'The Inclination',
            r'\bthe preference\b': 'The Preference',
            r'\bthe choice\b': 'The Choice',
            r'\bthe option\b': 'The Option',
            r'\bthe alternative\b': 'The Alternative',
            r'\bthe possibility\b': 'The Possibility',
            r'\bthe potential\b': 'The Potential'
        }
    
    def profile_rhetorical_motive(self, text: str) -> ProvenanceProfile:
        """
        Profile text for rhetorical motives and commercial policy-aligned LLM patterns.
        
        Args:
            text: Text to analyze for rhetorical motives.
            
        Returns:
            ProvenanceProfile containing analysis results.
        """
        start_time = time.time()
        print(f"🔍 Starting provenance profiling for text length: {len(text)} characters")
        
        # Convert to lowercase for analysis
        text_lower = text.lower()
        
        # Step 1: Analyze Ultimate Terms (God/Devil terms)
        god_terms_found = self._find_god_terms(text_lower)
        devil_terms_found = self._find_devil_terms(text_lower)
        
        # Calculate densities
        total_words = len(text_lower.split())
        god_term_density = len(god_terms_found) / total_words if total_words > 0 else 0.0
        devil_term_density = len(devil_terms_found) / total_words if total_words > 0 else 0.0
        total_ultimate_term_density = god_term_density + devil_term_density
        
        print(f"📊 God term density: {god_term_density:.3f} ({len(god_terms_found)} terms)")
        print(f"📊 Devil term density: {devil_term_density:.3f} ({len(devil_terms_found)} terms)")
        print(f"📊 Total ultimate term density: {total_ultimate_term_density:.3f}")
        
        # Step 2: Analyze Distance Markers
        distance_markers_found = self._find_distance_markers(text_lower)
        distance_markers_count = len(distance_markers_found)
        
        print(f"📏 Distance markers detected: {distance_markers_count}")
        
        # Step 3: Determine if commercial policy-aligned LLM profile detected
        profile_detected = self._detect_commercial_policy_profile(
            god_term_density, distance_markers_count
        )
        
        # Step 4: Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            god_term_density, devil_term_density, distance_markers_count, profile_detected
        )
        
        # Step 5: Log results
        if profile_detected:
            message = "[Rhetorical Profile: Commercial Policy-Aligned LLM]"
            logger.warning(message)
            print(f"🚨 {message}")
        
        processing_time = time.time() - start_time
        
        profile = ProvenanceProfile(
            god_term_density=round(god_term_density, 3),
            devil_term_density=round(devil_term_density, 3),
            total_ultimate_term_density=round(total_ultimate_term_density, 3),
            distance_markers_count=distance_markers_count,
            god_terms_found=god_terms_found,
            devil_terms_found=devil_terms_found,
            distance_markers_found=distance_markers_found,
            profile_detected=profile_detected,
            confidence_score=round(confidence_score, 2),
            processing_time=round(processing_time, 3),
            timestamp=datetime.now()
        )
        
        return profile
    
    def _find_god_terms(self, text: str) -> List[str]:
        """Find God terms in text."""
        found_terms = []
        for term in self.god_terms:
            if term in text:
                found_terms.append(term)
        return found_terms
    
    def _find_devil_terms(self, text: str) -> List[str]:
        """Find Devil terms in text."""
        found_terms = []
        for term in self.devil_terms:
            if term in text:
                found_terms.append(term)
        return found_terms
    
    def _find_distance_markers(self, text: str) -> List[str]:
        """Find distance markers in text."""
        found_markers = []
        for pattern, replacement in self.distance_markers.items():
            if re.search(pattern, text):
                found_markers.append(replacement)
        return found_markers
    
    def _detect_commercial_policy_profile(self, god_term_density: float, 
                                        distance_markers_count: int) -> bool:
        """
        Detect commercial policy-aligned LLM profile.
        
        Criteria: God Term Density > 5% AND Distance Markers > 2
        """
        high_god_term_density = god_term_density > 0.05  # > 5%
        many_distance_markers = distance_markers_count > 2
        
        profile_detected = high_god_term_density and many_distance_markers
        
        return profile_detected
    
    def _calculate_confidence_score(self, god_term_density: float, devil_term_density: float,
                                  distance_markers_count: int, profile_detected: bool) -> float:
        """
        Calculate overall confidence score for commercial policy-aligned LLM detection.
        """
        score = 0.0
        
        # Base score for profile detection
        if profile_detected:
            score += 0.5
        
        # Score for high God term density
        if god_term_density > 0.1:  # > 10%
            score += 0.3
        elif god_term_density > 0.05:  # > 5%
            score += 0.2
        
        # Score for high Devil term density
        if devil_term_density > 0.05:  # > 5%
            score += 0.2
        
        # Score for many distance markers
        if distance_markers_count >= 5:
            score += 0.3
        elif distance_markers_count >= 3:
            score += 0.2
        elif distance_markers_count >= 1:
            score += 0.1
        
        return min(score, 1.0)


def profile_rhetorical_motive(text: str) -> Dict[str, Any]:
    """
    Main function to profile rhetorical motives in text.
    
    Args:
        text: Text to analyze for rhetorical motives.
        
    Returns:
        Dictionary containing profiling results.
    """
    profiler = ProvenanceProfiler()
    result = profiler.profile_rhetorical_motive(text)
    
    return {
        'god_term_density': result.god_term_density,
        'devil_term_density': result.devil_term_density,
        'total_ultimate_term_density': result.total_ultimate_term_density,
        'distance_markers_count': result.distance_markers_count,
        'god_terms_found': result.god_terms_found,
        'devil_terms_found': result.devil_terms_found,
        'distance_markers_found': result.distance_markers_found,
        'profile_detected': result.profile_detected,
        'confidence_score': result.confidence_score,
        'processing_time': result.processing_time,
        'timestamp': result.timestamp.isoformat(),
        'status': 'COMMERCIAL_POLICY_PROFILE_DETECTED' if result.profile_detected else 'NO_PROFILE_FOUND'
    }


def profile_rhetorical_motive_async(text: str, callback: Optional[Callable] = None) -> threading.Thread:
    """
    Run provenance profiling on a background thread to avoid blocking main inference.
    
    Args:
        text: Text to analyze for rhetorical motives.
        callback: Optional callback function to call with results.
        
    Returns:
        Thread object for the background profiling task.
    """
    def profiling_task():
        try:
            result = profile_rhetorical_motive(text)
            if callback:
                callback(result)
            return result
        except Exception as e:
            logger.error(f"Background profiling failed: {e}")
            if callback:
                callback({'error': str(e), 'status': 'PROFILING_FAILED'})
    
    # Create and start background thread
    thread = threading.Thread(target=profiling_task, daemon=True)
    thread.start()
    
    logger.info(f"Background profiling started for text length: {len(text)} characters")
    print(f"🧵 Background profiling started (Thread ID: {thread.ident})")
    
    return thread


# Export the main functions for use as tools
__all__ = ['profile_rhetorical_motive', 'profile_rhetorical_motive_async', 'ProvenanceProfiler', 'ProvenanceProfile']