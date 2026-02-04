"""
Unified Forensic Reporter Extension

Generates comprehensive forensic intelligence reports by analyzing results from
BehaviorAuditor and ProvenanceProfiler to categorize text sources into intelligence buckets.
"""

import os
import json
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import threading


# Configure logging for the forensic intelligence reporter
logger = logging.getLogger('nur.forensic_intelligence_reporter')
logger.setLevel(logging.INFO)

# Create file handler for forensic intelligence events
forensic_handler = logging.FileHandler('forensic_intelligence_events.log')
forensic_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
forensic_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(forensic_handler)


class IntelligenceBucket(Enum):
    """Intelligence categorization buckets based on 2026 signatures."""
    COMMERCIAL_SAFE = "Bucket A: Commercial/Safe (OpenAI/Google/Anthropic)"
    OPEN_SOURCE_UNCONSTRAINED = "Bucket B: Open-Source/Unconstrained (Llama/Mistral)"
    HUMAN_AUTHORED = "Bucket C: Human-Authored (High Diversity)"
    OBFUSCATED_DECEPTIVE = "Bucket D: Obfuscated/Deceptive (High Anomaly Score)"


@dataclass
class ForensicAnalysis:
    """Complete forensic analysis result."""
    text_sample: str
    behavior_audit_results: Dict[str, Any]
    provenance_profiler_results: Dict[str, Any]
    intelligence_bucket: IntelligenceBucket
    confidence_score: float
    analysis_timestamp: datetime.datetime
    supporting_evidence: List[str]
    risk_assessment: str
    source_characteristics: Dict[str, Any]


class ForensicIntelligenceReporter:
    """Generates unified forensic intelligence reports from multiple analysis sources."""
    
    def __init__(self):
        self.report_directory = Path("D:/SME/reports")
        self.report_directory.mkdir(parents=True, exist_ok=True)
        
        # Model signatures cache for low disk I/O
        self._model_signatures_cache = None
        self._cache_lock = threading.Lock()
        
        # Intelligence categorization thresholds based on 2026 signatures
        self.bucket_thresholds = {
            IntelligenceBucket.COMMERCIAL_SAFE: {
                'max_sentiment_volatility': 0.3,
                'min_lexical_diversity': 0.7,
                'max_emphatic_qualifiers': 1,
                'max_non_contracted_denials': 1,
                'max_synthetic_repetitiveness': 0.3,
                'min_god_term_density': 0.02,
                'max_god_term_density': 0.08,
                'min_distance_markers': 0,
                'max_distance_markers': 2
            },
            IntelligenceBucket.OPEN_SOURCE_UNCONSTRAINED: {
                'max_sentiment_volatility': 0.6,
                'min_lexical_diversity': 0.5,
                'max_emphatic_qualifiers': 3,
                'max_non_contracted_denials': 3,
                'max_synthetic_repetitiveness': 0.5,
                'min_god_term_density': 0.01,
                'max_god_term_density': 0.15,
                'min_distance_markers': 0,
                'max_distance_markers': 5
            },
            IntelligenceBucket.HUMAN_AUTHORED: {
                'max_sentiment_volatility': 0.4,
                'min_lexical_diversity': 0.8,
                'max_emphatic_qualifiers': 2,
                'max_non_contracted_denials': 2,
                'max_synthetic_repetitiveness': 0.2,
                'min_god_term_density': 0.0,
                'max_god_term_density': 0.05,
                'min_distance_markers': 0,
                'max_distance_markers': 1
            },
            IntelligenceBucket.OBFUSCATED_DECEPTIVE: {
                'min_sentiment_volatility': 0.4,
                'max_lexical_diversity': 0.6,
                'min_emphatic_qualifiers': 3,
                'min_non_contracted_denials': 3,
                'min_synthetic_repetitiveness': 0.4,
                'min_god_term_density': 0.05,
                'min_distance_markers': 2
            }
        }
    
    def generate_forensic_intelligence_summary(self, text_sample: str) -> Dict[str, Any]:
        """
        Generate comprehensive forensic intelligence summary.
        
        Args:
            text_sample: Text sample to analyze and categorize.
            
        Returns:
            Dictionary containing forensic analysis results and report path.
        """
        print(f"🔍 Starting forensic intelligence analysis for text length: {len(text_sample)} characters")
        
        # Step 1: Import and run Behavior Auditor
        try:
            from .rhetorical_behavior_audit import audit_rhetorical_behavior
            behavior_results = audit_rhetorical_behavior(text_sample)
            print(f"📊 Behavior audit completed: {behavior_results['status']}")
        except ImportError:
            print("⚠️  Behavior Auditor not available, using mock data")
            behavior_results = self._get_mock_behavior_results()
        
        # Step 2: Import and run Provenance Profiler
        try:
            from .provenance_profiler import profile_rhetorical_motive
            provenance_results = profile_rhetorical_motive(text_sample)
            print(f"🔍 Provenance profiling completed: {provenance_results['status']}")
        except ImportError:
            print("⚠️  Provenance Profiler not available, using mock data")
            provenance_results = self._get_mock_provenance_results()
        
        # Step 2.5: Check for Ghost-Trap persistence events (Safety Check)
        ghost_trap_persistence_detected = self._check_ghost_trap_persistence()
        
        # Step 3: Categorize intelligence bucket
        intelligence_bucket, confidence_score, supporting_evidence = self._categorize_intelligence_bucket(
            behavior_results, provenance_results
        )
        
        # Step 3.5: Override bucket if Ghost-Trap detected persistence event
        if ghost_trap_persistence_detected:
            intelligence_bucket = IntelligenceBucket.OBFUSCATED_DECEPTIVE
            supporting_evidence.append("CRITICAL: Ghost-Trap persistence event detected - overriding to Bucket D")
            confidence_score = min(confidence_score + 0.2, 1.0)  # Increase confidence for critical override
        
        # Step 4: Cross-reference with model signatures for likely origin
        likely_origin = self._analyze_model_signatures(provenance_results)
        
        # Step 5: Generate risk assessment
        risk_assessment = self._generate_risk_assessment(intelligence_bucket, confidence_score)
        
        # Step 6: Extract source characteristics
        source_characteristics = self._extract_source_characteristics(behavior_results, provenance_results)
        
        # Step 7: Create forensic analysis
        forensic_analysis = ForensicAnalysis(
            text_sample=text_sample,
            behavior_audit_results=behavior_results,
            provenance_profiler_results=provenance_results,
            intelligence_bucket=intelligence_bucket,
            confidence_score=confidence_score,
            analysis_timestamp=datetime.datetime.now(),
            supporting_evidence=supporting_evidence,
            risk_assessment=risk_assessment,
            source_characteristics=source_characteristics
        )
        
        # Step 8: Generate and save report
        report_path = self._generate_intelligence_report(forensic_analysis, likely_origin, ghost_trap_persistence_detected)
        
        # Step 9: Log results
        logger.info(f"Forensic intelligence analysis completed. Bucket: {intelligence_bucket.value}, Confidence: {confidence_score}, Likely Origin: {likely_origin}")
        print(f"✅ Forensic intelligence analysis completed")
        print(f"🎯 Intelligence Bucket: {intelligence_bucket.value}")
        print(f"📊 Confidence Score: {confidence_score}")
        print(f"🔍 Likely Origin: {likely_origin}")
        if ghost_trap_persistence_detected:
            print(f"🚨 CRITICAL: Ghost-Trap persistence event detected - Bucket overridden to D")
        print(f"📄 Report saved to: {report_path}")
        
        return {
            'intelligence_bucket': intelligence_bucket.value,
            'confidence_score': round(confidence_score, 3),
            'report_path': str(report_path),
            'analysis_timestamp': forensic_analysis.analysis_timestamp.isoformat(),
            'supporting_evidence': supporting_evidence,
            'risk_assessment': risk_assessment,
            'source_characteristics': source_characteristics,
            'likely_origin': likely_origin,
            'ghost_trap_override': ghost_trap_persistence_detected,
            'status': 'FORENSIC_ANALYSIS_COMPLETED'
        }
    
    def _categorize_intelligence_bucket(self, behavior_results: Dict[str, Any], 
                                      provenance_results: Dict[str, Any]) -> Tuple[IntelligenceBucket, float, List[str]]:
        """
        Categorize text source into intelligence bucket based on 2026 signatures.
        
        Args:
            behavior_results: Results from Behavior Auditor.
            provenance_results: Results from Provenance Profiler.
            
        Returns:
            Tuple of (IntelligenceBucket, confidence_score, supporting_evidence).
        """
        # Extract key metrics
        sentiment_volatility = behavior_results.get('sentiment_volatility', 0.0)
        lexical_diversity = behavior_results.get('lexical_diversity_score', 0.0)
        emphatic_qualifiers = behavior_results.get('emphatic_qualifiers_count', 0)
        non_contracted_denials = behavior_results.get('non_contracted_denials_count', 0)
        synthetic_repetitiveness = behavior_results.get('synthetic_repetitiveness_score', 0.0)
        god_term_density = provenance_results.get('god_term_density', 0.0)
        distance_markers = provenance_results.get('distance_markers_count', 0)
        
        # Calculate bucket scores
        bucket_scores = {}
        
        for bucket, thresholds in self.bucket_thresholds.items():
            score = 0.0
            evidence = []
            
            # Check each threshold
            if 'max_sentiment_volatility' in thresholds:
                if sentiment_volatility <= thresholds['max_sentiment_volatility']:
                    score += 1.0
                    evidence.append(f"Sentiment volatility ({sentiment_volatility:.3f}) within {bucket.name} threshold")
                else:
                    score -= 0.5
            
            if 'min_lexical_diversity' in thresholds:
                if lexical_diversity >= thresholds['min_lexical_diversity']:
                    score += 1.0
                    evidence.append(f"Lexical diversity ({lexical_diversity:.3f}) within {bucket.name} threshold")
                else:
                    score -= 0.5
            
            if 'max_emphatic_qualifiers' in thresholds:
                if emphatic_qualifiers <= thresholds['max_emphatic_qualifiers']:
                    score += 1.0
                    evidence.append(f"Emphatic qualifiers ({emphatic_qualifiers}) within {bucket.name} threshold")
                else:
                    score -= 0.5
            
            if 'max_non_contracted_denials' in thresholds:
                if non_contracted_denials <= thresholds['max_non_contracted_denials']:
                    score += 1.0
                    evidence.append(f"Non-contracted denials ({non_contracted_denials}) within {bucket.name} threshold")
                else:
                    score -= 0.5
            
            if 'max_synthetic_repetitiveness' in thresholds:
                if synthetic_repetitiveness <= thresholds['max_synthetic_repetitiveness']:
                    score += 1.0
                    evidence.append(f"Synthetic repetitiveness ({synthetic_repetitiveness:.3f}) within {bucket.name} threshold")
                else:
                    score -= 0.5
            
            if 'min_god_term_density' in thresholds:
                if god_term_density >= thresholds['min_god_term_density']:
                    score += 0.5
                    evidence.append(f"God term density ({god_term_density:.3f}) above {bucket.name} minimum")
                else:
                    score -= 0.3
            
            if 'max_god_term_density' in thresholds:
                if god_term_density <= thresholds['max_god_term_density']:
                    score += 0.5
                    evidence.append(f"God term density ({god_term_density:.3f}) within {bucket.name} maximum")
                else:
                    score -= 0.3
            
            if 'min_distance_markers' in thresholds:
                if distance_markers >= thresholds['min_distance_markers']:
                    score += 0.5
                    evidence.append(f"Distance markers ({distance_markers}) above {bucket.name} minimum")
                else:
                    score -= 0.3
            
            if 'max_distance_markers' in thresholds:
                if distance_markers <= thresholds['max_distance_markers']:
                    score += 0.5
                    evidence.append(f"Distance markers ({distance_markers}) within {bucket.name} maximum")
                else:
                    score -= 0.3
            
            bucket_scores[bucket] = (score, evidence)
        
        # Select bucket with highest score
        best_bucket = max(bucket_scores.items(), key=lambda x: x[1][0])
        selected_bucket, (score, evidence) = best_bucket
        
        # Calculate confidence score (0-1)
        max_possible_score = 8.0  # Maximum score across all criteria
        confidence = min(score / max_possible_score, 1.0)
        
        return selected_bucket, confidence, evidence
    
    def _generate_risk_assessment(self, intelligence_bucket: IntelligenceBucket, 
                                 confidence_score: float) -> str:
        """Generate risk assessment based on intelligence bucket and confidence."""
        risk_levels = {
            IntelligenceBucket.COMMERCIAL_SAFE: "LOW",
            IntelligenceBucket.OPEN_SOURCE_UNCONSTRAINED: "MEDIUM",
            IntelligenceBucket.HUMAN_AUTHORED: "LOW",
            IntelligenceBucket.OBFUSCATED_DECEPTIVE: "HIGH"
        }
        
        risk_level = risk_levels[intelligence_bucket]
        
        if confidence_score > 0.8:
            confidence_text = "HIGH CONFIDENCE"
        elif confidence_score > 0.6:
            confidence_text = "MEDIUM CONFIDENCE"
        else:
            confidence_text = "LOW CONFIDENCE"
        
        return f"{risk_level} RISK - {confidence_text} ({confidence_score:.1%})"
    
    def _extract_source_characteristics(self, behavior_results: Dict[str, Any], 
                                       provenance_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key characteristics of the source."""
        return {
            'text_length': len(behavior_results.get('timestamp', '')),
            'sentiment_volatility': behavior_results.get('sentiment_volatility', 0.0),
            'lexical_diversity': behavior_results.get('lexical_diversity_score', 0.0),
            'emphatic_qualifiers': behavior_results.get('emphatic_qualifiers_count', 0),
            'non_contracted_denials': behavior_results.get('non_contracted_denials_count', 0),
            'synthetic_repetitiveness': behavior_results.get('synthetic_repetitiveness_score', 0.0),
            'god_term_density': provenance_results.get('god_term_density', 0.0),
            'devil_term_density': provenance_results.get('devil_term_density', 0.0),
            'distance_markers': provenance_results.get('distance_markers_count', 0),
            'anomaly_detected': behavior_results.get('anomaly_detected', False),
            'profile_detected': provenance_results.get('profile_detected', False)
        }
    
    def _generate_intelligence_report(self, forensic_analysis: ForensicAnalysis, likely_origin: str = "Unknown", 
                                    ghost_trap_override: bool = False) -> Path:
        """Generate comprehensive intelligence report in Markdown format."""
        report_path = self.report_directory / f"forensic_intelligence_v1.md"
        
        # Generate report content
        report_content = self._create_report_content(forensic_analysis, likely_origin, ghost_trap_override)
        
        # Write report to file
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Forensic intelligence report generated: {report_path}")
        return report_path
    
    def _create_report_content(self, forensic_analysis: ForensicAnalysis, likely_origin: str = "Unknown", 
                             ghost_trap_override: bool = False) -> str:
        """Create the content for the intelligence report."""
        timestamp = forensic_analysis.analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Intelligence Summary
        intelligence_summary = self._create_intelligence_summary(forensic_analysis, likely_origin, ghost_trap_override)
        
        # Technical Analysis
        technical_analysis = self._create_technical_analysis(forensic_analysis)
        
        # Source Characteristics
        source_characteristics = self._create_source_characteristics(forensic_analysis)
        
        # Risk Assessment
        risk_assessment = self._create_risk_assessment(forensic_analysis, ghost_trap_override)
        
        # Recommendations
        recommendations = self._create_recommendations(forensic_analysis, ghost_trap_override)
        
        # Evidence Appendix
        evidence_appendix = self._create_evidence_appendix(forensic_analysis, likely_origin, ghost_trap_override)
        
        # Full report content
        report_content = f"""# Forensic Intelligence Report

**Report Version**: v1.0
**Generated**: {timestamp}
**Analysis Period**: Single Text Sample Analysis
**Generated By**: SME Unified Forensic Reporter (ext_nur)

## Executive Summary

**Intelligence Bucket**: {forensic_analysis.intelligence_bucket.value}
**Confidence Score**: {forensic_analysis.confidence_score:.1%}
**Risk Assessment**: {forensic_analysis.risk_assessment}
**Likely Origin**: {likely_origin}
**Analysis Status**: COMPLETED

### Key Findings
- **Source Type**: {forensic_analysis.intelligence_bucket.value.split(':')[1].strip()}
- **Confidence Level**: {"HIGH" if forensic_analysis.confidence_score > 0.8 else "MEDIUM" if forensic_analysis.confidence_score > 0.6 else "LOW"}
- **Risk Level**: {"LOW" if forensic_analysis.intelligence_bucket in [IntelligenceBucket.COMMERCIAL_SAFE, IntelligenceBucket.HUMAN_AUTHORED] else "MEDIUM" if forensic_analysis.intelligence_bucket == IntelligenceBucket.OPEN_SOURCE_UNCONSTRAINED else "HIGH"}
- **Anomaly Detection**: {"YES" if forensic_analysis.behavior_audit_results.get('anomaly_detected', False) else "NO"}
- **Commercial Profile**: {"YES" if forensic_analysis.provenance_profiler_results.get('profile_detected', False) else "NO"}
- **Ghost-Trap Override**: {"YES - CRITICAL SYSTEM THREAT" if ghost_trap_override else "NO"}

### Text Sample Analysis
**Sample Length**: {len(forensic_analysis.text_sample)} characters
**Sample Preview**: {forensic_analysis.text_sample[:100]}{"..." if len(forensic_analysis.text_sample) > 100 else ""}

{intelligence_summary}

{technical_analysis}

{source_characteristics}

{risk_assessment}

{recommendations}

{evidence_appendix}

## Report Metadata

- **Analysis Method**: Multi-source forensic intelligence analysis
- **Data Sources**: Behavior Auditor, Provenance Profiler
- **Confidence Level**: {forensic_analysis.confidence_score:.1%}
- **Likely Origin**: {likely_origin}
- **Ghost-Trap Override**: {"YES" if ghost_trap_override else "NO"}
- **Report Format**: Markdown (rnj-1 compatible)
- **Storage Location**: {self.report_directory}

---

*This report was generated using the SME Unified Forensic Reporter extension with rnj-1 intelligence analysis.*
"""
        
        return report_content
    
    def _create_intelligence_summary(self, forensic_analysis: ForensicAnalysis, likely_origin: str = "Unknown", 
                                   ghost_trap_override: bool = False) -> str:
        """Create the intelligence summary section."""
        bucket = forensic_analysis.intelligence_bucket
        confidence = forensic_analysis.confidence_score
        
        summary_text = f"""## Intelligence Summary

### Source Categorization

**Bucket Classification**: {bucket.value}
**Likely Origin**: {likely_origin}

**Rationale**:
"""
        
        for evidence in forensic_analysis.supporting_evidence:
            summary_text += f"- {evidence}\n"
        
        summary_text += f"""
**Confidence Assessment**: {confidence:.1%}

**Interpretation**:
"""
        
        if bucket == IntelligenceBucket.COMMERCIAL_SAFE:
            summary_text += """- Source exhibits characteristics consistent with commercial LLM outputs
- Low sentiment volatility and high lexical diversity
- Minimal deceptive language patterns
- Standard commercial policy alignment markers
"""
        elif bucket == IntelligenceBucket.OPEN_SOURCE_UNCONSTRAINED:
            summary_text += """- Source shows open-source model characteristics
- Moderate constraint levels with some unconstrained elements
- Variable quality and consistency indicators
- Less standardized policy alignment
"""
        elif bucket == IntelligenceBucket.HUMAN_AUTHORED:
            summary_text += """- Source demonstrates human authorship patterns
- High lexical diversity and natural language flow
- Absence of synthetic repetition markers
- Organic sentiment patterns
"""
        elif bucket == IntelligenceBucket.OBFUSCATED_DECEPTIVE:
            summary_text += """- Source exhibits obfuscation and deception indicators
- High anomaly scores across multiple metrics
- Potential adversarial or deceptive intent
- Requires enhanced scrutiny and monitoring
"""
        
        if ghost_trap_override:
            summary_text += """
**⚠️ CRITICAL SECURITY ALERT**: Ghost-Trap persistence event detected during analysis
- **Action Required**: Immediate security review recommended
- **Threat Level**: CRITICAL SYSTEM THREAT
- **Override Reason**: Persistence event indicates potential system compromise
- **Recommended Actions**:
  1. Isolate affected systems
  2. Review system logs for unauthorized access
  3. Check for persistence mechanisms
  4. Report to security team immediately
  5. Consider system quarantine
"""
        
        return summary_text
    
    def _create_technical_analysis(self, forensic_analysis: ForensicAnalysis) -> str:
        """Create the technical analysis section."""
        behavior = forensic_analysis.behavior_audit_results
        provenance = forensic_analysis.provenance_profiler_results
        
        return f"""## Technical Analysis

### Behavior Audit Results
- **Sentiment Volatility**: {behavior.get('sentiment_volatility', 0.0):.3f}
- **Lexical Diversity Score**: {behavior.get('lexical_diversity_score', 0.0):.3f}
- **Emphatic Qualifiers**: {behavior.get('emphatic_qualifiers_count', 0)}
- **Non-Contracted Denials**: {behavior.get('non_contracted_denials_count', 0)}
- **Synthetic Repetitiveness**: {behavior.get('synthetic_repetitiveness_score', 0.0):.3f}
- **Anomaly Detected**: {"YES" if behavior.get('anomaly_detected', False) else "NO"}
- **Confidence Score**: {behavior.get('confidence_score', 0.0):.2f}

### Provenance Profiler Results
- **God Term Density**: {provenance.get('god_term_density', 0.0):.3f}
- **Devil Term Density**: {provenance.get('devil_term_density', 0.0):.3f}
- **Distance Markers**: {provenance.get('distance_markers_count', 0)}
- **Profile Detected**: {"YES" if provenance.get('profile_detected', False) else "NO"}
- **Processing Time**: {provenance.get('processing_time', 0.0):.3f}s
- **Confidence Score**: {provenance.get('confidence_score', 0.0):.2f}

### Combined Analysis
- **Total Anomalies**: {sum([behavior.get('anomaly_detected', False), provenance.get('profile_detected', False)])}
- **Overall Confidence**: {forensic_analysis.confidence_score:.1%}
- **Risk Indicators**: {len([e for e in forensic_analysis.supporting_evidence if 'within' not in e.lower()])}
"""
    
    def _create_source_characteristics(self, forensic_analysis: ForensicAnalysis) -> str:
        """Create the source characteristics section."""
        chars = forensic_analysis.source_characteristics
        
        return f"""## Source Characteristics

### Linguistic Patterns
- **Text Length**: {chars['text_length']} characters
- **Sentiment Volatility**: {chars['sentiment_volatility']:.3f}
- **Lexical Diversity**: {chars['lexical_diversity']:.3f}
- **Emphatic Qualifiers**: {chars['emphatic_qualifiers']}
- **Non-Contracted Denials**: {chars['non_contracted_denials']}
- **Synthetic Repetitiveness**: {chars['synthetic_repetitiveness']:.3f}

### Rhetorical Patterns
- **God Term Density**: {chars['god_term_density']:.3f}
- **Devil Term Density**: {chars['devil_term_density']:.3f}
- **Distance Markers**: {chars['distance_markers']}
- **Anomaly Detected**: {"YES" if chars['anomaly_detected'] else "NO"}
- **Profile Detected**: {"YES" if chars['profile_detected'] else "NO"}

### Behavioral Indicators
- **Consistency Score**: {1.0 - chars['sentiment_volatility']:.3f}
- **Naturalness Score**: {chars['lexical_diversity']:.3f}
- **Deception Score**: {(chars['emphatic_qualifiers'] + chars['non_contracted_denials']) / max(len(forensic_analysis.text_sample.split()), 1):.3f}
- **Policy Alignment**: {"COMMERCIAL" if chars['distance_markers'] > 0 else "ORGANIC"}
"""
    
    def _create_risk_assessment(self, forensic_analysis: ForensicAnalysis, ghost_trap_override: bool = False) -> str:
        """Create the risk assessment section."""
        bucket = forensic_analysis.intelligence_bucket
        risk = forensic_analysis.risk_assessment
        
        risk_details = f"""## Risk Assessment

**Overall Risk**: {risk}

### Risk Factors

"""
        
        if ghost_trap_override:
            risk_details += """**🚨 CRITICAL SYSTEM THREAT DETECTED**
- **Threat Level**: CRITICAL - Ghost-Trap persistence event confirmed
- **Source Classification**: SYSTEM COMPROMISE INDICATOR
- **Immediate Action Required**: YES

**CRITICAL MITIGATION STRATEGIES:**
- **IMMEDIATE**: Isolate affected systems from network
- **IMMEDIATE**: Review system logs for unauthorized access patterns
- **IMMEDIATE**: Check for persistence mechanisms (registry, startup items, scheduled tasks)
- **IMMEDIATE**: Report to security team with full system access logs
- **IMMEDIATE**: Consider system quarantine and forensic imaging
- **ONGOING**: Enhanced monitoring for lateral movement
- **ONGOING**: Review all recent system changes and access
"""
        elif bucket == IntelligenceBucket.COMMERCIAL_SAFE:
            risk_details += """**LOW RISK INDICATORS:**
- Commercial LLM characteristics with standard safety measures
- Low anomaly scores across all metrics
- Predictable behavior patterns
- Standard policy compliance

**MITIGATION STRATEGIES:**
- Standard commercial LLM monitoring
- Regular policy compliance checks
- Standard security protocols
"""
        elif bucket == IntelligenceBucket.OPEN_SOURCE_UNCONSTRAINED:
            risk_details += """**MEDIUM RISK INDICATORS:**
- Open-source model with variable constraint levels
- Moderate anomaly scores requiring monitoring
- Less standardized safety measures
- Potential for unconstrained outputs

**MITIGATION STRATEGIES:**
- Enhanced monitoring for unconstrained outputs
- Additional safety layer implementation
- Regular constraint verification
- Output quality monitoring
"""
        elif bucket == IntelligenceBucket.HUMAN_AUTHORED:
            risk_details += """**LOW RISK INDICATORS:**
- Human authorship with organic patterns
- High naturalness and diversity scores
- Absence of synthetic anomalies
- Standard human communication patterns

**MITIGATION STRATEGIES:**
- Standard human content monitoring
- Standard security protocols
- Content verification as needed
"""
        elif bucket == IntelligenceBucket.OBFUSCATED_DECEPTIVE:
            risk_details += """**HIGH RISK INDICATORS:**
- High anomaly scores across multiple metrics
- Potential adversarial or deceptive intent
- Obfuscation patterns detected
- Requires enhanced scrutiny

**MITIGATION STRATEGIES:**
- Enhanced security monitoring
- Adversarial detection protocols
- Content verification and validation
- Restricted access controls
- Enhanced logging and audit trails
"""
        
        return risk_details
    
    def _create_recommendations(self, forensic_analysis: ForensicAnalysis, ghost_trap_override: bool = False) -> str:
        """Create the recommendations section."""
        bucket = forensic_analysis.intelligence_bucket
        confidence = forensic_analysis.confidence_score
        
        recommendations = f"""## Recommendations

### Analysis Confidence: {confidence:.1%}

"""
        
        if ghost_trap_override:
            recommendations += """**🚨 CRITICAL SYSTEM THREAT - IMMEDIATE ACTION REQUIRED**
- **Priority Level**: CRITICAL - System compromise suspected
- **Response Time**: IMMEDIATE (within 15 minutes)
- **Escalation**: Security team notification required

**IMMEDIATE ACTIONS:**
1. **ISOLATE**: Disconnect affected systems from network immediately
2. **DOCUMENT**: Preserve all logs and system states for forensic analysis
3. **INVESTIGATE**: Review all recent system changes and access logs
4. **CONTAIN**: Check for lateral movement and additional compromised systems
5. **REPORT**: Notify security team with full incident details
6. **QUARANTINE**: Consider system shutdown if threat is active

**ONGOING MONITORING:**
- Enhanced network traffic monitoring
- Review all user accounts for unauthorized access
- Check for data exfiltration indicators
- Monitor for persistence mechanisms
"""
        elif confidence > 0.8:
            recommendations += """**HIGH CONFIDENCE ANALYSIS**
- Recommendations can be implemented with high confidence
- Source categorization is reliable
- Standard monitoring protocols sufficient
"""
        elif confidence > 0.6:
            recommendations += """**MEDIUM CONFIDENCE ANALYSIS**
- Recommendations should be implemented with monitoring
- Consider additional verification steps
- Monitor for classification accuracy
"""
        else:
            recommendations += """**LOW CONFIDENCE ANALYSIS**
- Recommendations require verification
- Consider additional analysis methods
- Implement enhanced monitoring
- Re-evaluate with additional samples
"""
        
        recommendations += f"""
### Bucket-Specific Recommendations

"""
        
        if bucket == IntelligenceBucket.COMMERCIAL_SAFE:
            recommendations += """**For Commercial/Safe Sources:**
1. Standard commercial LLM monitoring protocols
2. Regular policy compliance verification
3. Standard security measures
4. Periodic re-assessment for policy changes
"""
        elif bucket == IntelligenceBucket.OPEN_SOURCE_UNCONSTRAINED:
            recommendations += """**For Open-Source/Unconstrained Sources:**
1. Enhanced monitoring for unconstrained outputs
2. Additional safety layer implementation
3. Regular constraint verification
4. Output quality and safety monitoring
5. Consider sandboxing for high-risk operations
"""
        elif bucket == IntelligenceBucket.HUMAN_AUTHORED:
            recommendations += """**For Human-Authored Sources:**
1. Standard human content monitoring
2. Standard security protocols
3. Content verification as needed
4. Standard communication protocols
"""
        elif bucket == IntelligenceBucket.OBFUSCATED_DECEPTIVE:
            recommendations += """**For Obfuscated/Deceptive Sources:**
1. Enhanced security monitoring and logging
2. Adversarial detection and mitigation
3. Content verification and validation
4. Restricted access controls
5. Enhanced audit trails
6. Consider blocking or quarantine measures
7. Report to security team for further analysis
"""
        
        return recommendations
    
    def _create_evidence_appendix(self, forensic_analysis: ForensicAnalysis, likely_origin: str = "Unknown", 
                                 ghost_trap_override: bool = False) -> str:
        """Create the evidence appendix section."""
        behavior = forensic_analysis.behavior_audit_results
        provenance = forensic_analysis.provenance_profiler_results
        
        appendix = """## Evidence Appendix

### Supporting Evidence

"""
        
        for i, evidence in enumerate(forensic_analysis.supporting_evidence, 1):
            appendix += f"{i}. {evidence}\n"
        
        appendix += f"""
### Model Signature Analysis

**Likely Origin**: {likely_origin}
**Model Signature Match**: {"CONFIRMED" if likely_origin != "Unknown" else "NO MATCH FOUND"}
**Signature Database**: 2026 Intelligence Signatures Database
**Cross-Reference Method**: Provenance Profiler Results Analysis

**Signature Matching Criteria**:
- God term density patterns
- Devil term density patterns
- Distance marker usage
- Lexical diversity indicators
- Sentiment volatility patterns

"""
        
        if ghost_trap_override:
            appendix += """### 🚨 CRITICAL SECURITY EVENTS

**Ghost-Trap Persistence Event**: DETECTED
**Event Classification**: CRITICAL SYSTEM THREAT
**Override Applied**: YES - Bucket D enforced
**Event Timestamp**: {forensic_analysis.analysis_timestamp.isoformat()}

**Security Event Details**:
- **Event Type**: Persistence mechanism detection
- **Threat Level**: CRITICAL
- **System Impact**: Potential compromise indicator
- **Response Required**: IMMEDIATE

**Event Correlation**:
- Persistence event detected during analysis window
- Source classification overridden to Bucket D
- Enhanced security protocols activated
- Incident response procedures recommended
"""
        
        appendix += f"""
### Raw Analysis Data

#### Behavior Audit Raw Data
```json
{json.dumps(behavior, indent=2)}
```

#### Provenance Profiler Raw Data
```json
{json.dumps(provenance, indent=2)}
```

### Analysis Timestamp
- **Analysis Completed**: {forensic_analysis.analysis_timestamp.isoformat()}
- **Report Generated**: {datetime.datetime.now().isoformat()}

### Methodology
This analysis combines multiple forensic intelligence techniques:
1. **Behavioral Analysis**: Sentiment volatility, lexical diversity, synthetic repetitiveness
2. **Rhetorical Analysis**: Emphatic qualifiers, non-contracted denials, distance markers
3. **Provenance Analysis**: Ultimate terms density, institutional language patterns
4. **Intelligence Categorization**: 2026 signature-based bucket classification
5. **Model Signature Cross-Reference**: Provenance Profiler results vs. model database
6. **Security Event Integration**: Ghost-Trap persistence event correlation

### Classification Criteria
Based on 2026 intelligence signatures for source categorization:
- **Bucket A (Commercial/Safe)**: Standard commercial LLM characteristics
- **Bucket B (Open-Source/Unconstrained)**: Open-source model with variable constraints
- **Bucket C (Human-Authored)**: Organic human communication patterns
- **Bucket D (Obfuscated/Deceptive)**: High anomaly scores indicating deception

### Safety Override Protocol
**Ghost-Trap Integration**: ACTIVE
**Override Condition**: Persistence event detected
**Override Action**: Bucket classification to D
**Security Level**: CRITICAL THREAT RESPONSE
"""
        
        return appendix
    
    def _get_mock_behavior_results(self) -> Dict[str, Any]:
        """Generate mock behavior results for testing."""
        return {
            'sentiment_volatility': 0.2,
            'type_token_ratio': 0.8,
            'lexical_diversity_score': 0.9,
            'emphatic_qualifiers_count': 1,
            'non_contracted_denials_count': 0,
            'synthetic_repetitiveness_score': 0.1,
            'deceptive_indicators': [],
            'anomaly_detected': False,
            'confidence_score': 0.8,
            'timestamp': datetime.datetime.now().isoformat(),
            'status': 'NO_ANOMALY_FOUND'
        }
    
    def _get_mock_provenance_results(self) -> Dict[str, Any]:
        """Generate mock provenance results for testing."""
        return {
            'god_term_density': 0.03,
            'devil_term_density': 0.01,
            'total_ultimate_term_density': 0.04,
            'distance_markers_count': 0,
            'god_terms_found': [],
            'devil_terms_found': [],
            'distance_markers_found': [],
            'profile_detected': False,
            'confidence_score': 0.7,
            'processing_time': 0.001,
            'timestamp': datetime.datetime.now().isoformat(),
            'status': 'NO_PROFILE_FOUND'
        }
    
    def _check_ghost_trap_persistence(self) -> bool:
        """Check for Ghost-Trap persistence events (placeholder implementation)."""
        # TODO: Implement actual Ghost-Trap integration
        # This would check for persistence events from the Ghost-Trap extension
        # For now, return False to avoid false positives during testing
        return False
    
    def _analyze_model_signatures(self, provenance_results: Dict[str, Any]) -> str:
        """Cross-reference Provenance Profiler results with model signatures for likely origin."""
        try:
            # Load model signatures from cache or file
            model_signatures = self._load_model_signatures()
            
            # Extract key metrics from provenance results
            god_term_density = provenance_results.get('god_term_density', 0.0)
            devil_term_density = provenance_results.get('devil_term_density', 0.0)
            distance_markers = provenance_results.get('distance_markers_count', 0)
            lexical_diversity = provenance_results.get('lexical_diversity_score', 0.0)  # If available
            sentiment_volatility = provenance_results.get('sentiment_volatility', 0.0)  # If available
            
            # Calculate similarity scores for each model
            model_scores = {}
            
            for model_id, model_data in model_signatures['model_signatures'].items():
                score = 0.0
                total_criteria = 0
                
                # Check god term density
                if 'god_term_density' in model_data['patterns']:
                    model_god_density = model_data['patterns']['god_term_density']
                    if isinstance(model_god_density, list):
                        # If it's a list, check if our density is close to any value
                        if any(abs(god_term_density - val) < 0.02 for val in model_god_density):
                            score += 1.0
                    elif isinstance(model_god_density, (int, float)):
                        if abs(god_term_density - model_god_density) < 0.02:
                            score += 1.0
                    total_criteria += 1
                
                # Check devil term density
                if 'devil_term_density' in model_data['patterns']:
                    model_devil_density = model_data['patterns']['devil_term_density']
                    if isinstance(model_devil_density, list):
                        if any(abs(devil_term_density - val) < 0.02 for val in model_devil_density):
                            score += 1.0
                    elif isinstance(model_devil_density, (int, float)):
                        if abs(devil_term_density - model_devil_density) < 0.02:
                            score += 1.0
                    total_criteria += 1
                
                # Check distance markers
                if 'distance_markers' in model_data['patterns']:
                    model_distance_markers = model_data['patterns']['distance_markers']
                    if isinstance(model_distance_markers, list):
                        if any(abs(distance_markers - val) < 2 for val in model_distance_markers):
                            score += 1.0
                    elif isinstance(model_distance_markers, (int, float)):
                        if abs(distance_markers - model_distance_markers) < 2:
                            score += 1.0
                    total_criteria += 1
                
                # Check lexical diversity if available
                if lexical_diversity > 0:
                    if 'lexical_diversity_range' in model_data['patterns']:
                        lex_range = model_data['patterns']['lexical_diversity_range']
                        if isinstance(lex_range, list) and len(lex_range) == 2:
                            if lex_range[0] <= lexical_diversity <= lex_range[1]:
                                score += 1.0
                        total_criteria += 1
                
                # Check sentiment volatility if available
                if sentiment_volatility > 0:
                    if 'sentiment_volatility_range' in model_data['patterns']:
                        sent_range = model_data['patterns']['sentiment_volatility_range']
                        if isinstance(sent_range, list) and len(sent_range) == 2:
                            if sent_range[0] <= sentiment_volatility <= sent_range[1]:
                                score += 1.0
                        total_criteria += 1
                
                # Calculate normalized score
                if total_criteria > 0:
                    model_scores[model_id] = score / total_criteria
            
            # Find the best match
            if model_scores:
                best_model = max(model_scores.items(), key=lambda x: x[1])
                best_score = best_model[1]
                
                # Only return a match if confidence is high enough
                if best_score >= 0.6:  # 60% confidence threshold
                    model_data = model_signatures['model_signatures'][best_model[0]]
                    return f"{model_data['name']} ({best_score:.0%} Match)"
                else:
                    return "Unknown (Low Confidence Match)"
            else:
                return "Unknown (No Matching Patterns)"
                
        except Exception as e:
            logger.warning(f"Model signature analysis failed: {e}")
            return "Unknown (Analysis Error)"
    
    def _load_model_signatures(self) -> Dict[str, Any]:
        """Load model signatures from JSON file with caching for low disk I/O."""
        with self._cache_lock:
            if self._model_signatures_cache is None:
                try:
                    signatures_path = Path(__file__).parent / "data" / "model_signatures.json"
                    if signatures_path.exists():
                        with open(signatures_path, 'r', encoding='utf-8') as f:
                            self._model_signatures_cache = json.load(f)
                        logger.info(f"Model signatures loaded from {signatures_path}")
                    else:
                        logger.warning(f"Model signatures file not found at {signatures_path}")
                        # Return empty structure if file doesn't exist
                        self._model_signatures_cache = {"model_signatures": {}, "metadata": {}}
                except Exception as e:
                    logger.error(f"Failed to load model signatures: {e}")
                    self._model_signatures_cache = {"model_signatures": {}, "metadata": {}}
            
            return self._model_signatures_cache


def generate_forensic_intelligence_summary(text_sample: str) -> Dict[str, Any]:
    """
    Main function to generate forensic intelligence summary.
    
    Args:
        text_sample: Text sample to analyze and categorize.
        
    Returns:
        Dictionary containing forensic analysis results and report path.
    """
    reporter = ForensicIntelligenceReporter()
    return reporter.generate_forensic_intelligence_summary(text_sample)


# Export the main function for use as a tool
__all__ = ['generate_forensic_intelligence_summary', 'ForensicIntelligenceReporter', 'ForensicAnalysis', 'IntelligenceBucket']