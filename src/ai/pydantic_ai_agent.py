"""
SME Forensic Agent using Pydantic-AI

This module provides a production-grade agentic framework for forensic analysis
using Pydantic-AI for validated, type-safe AI responses.

v2.1.0: Added Pydantic-AI integration for agentic forensic workflows.
"""

# cSpell:ignore agentic ollama Ollama exfiltration

import json
from typing import Any, Dict, List, Optional

import pydantic
import pydantic_ai


# ============================================================================
# Pydantic Models for Type-Safe Responses
# ============================================================================

class EntityExtraction(pydantic.BaseModel):
    """Extracted entity from forensic text."""
    name: str = pydantic.Field(..., description="Entity name")
    entity_type: str = pydantic.Field(..., description="Type: person, organization, location, etc.")
    confidence: float = pydantic.Field(..., ge=0.0, le=1.0, description="Confidence score")


class ForensicAnalysisResult(pydantic.BaseModel):
    """Structured forensic analysis output."""
    entities: List[EntityExtraction] = pydantic.Field(default_factory=list)
    sentiment: str = pydantic.Field(..., description="Overall sentiment: positive, negative, neutral")
    key_findings: List[str] = pydantic.Field(default_factory=list)
    risk_level: str = pydantic.Field(..., description="Risk assessment: low, medium, high, critical")
    recommended_actions: List[str] = pydantic.Field(default_factory=list)


class ClaimVerification(pydantic.BaseModel):
    """Epistemic verification result."""
    claim: str = pydantic.Field(..., description="The claim being verified")
    is_verified: bool = pydantic.Field(..., description="Whether the claim can be verified")
    confidence: float = pydantic.Field(..., ge=0.0, le=1.0)
    evidence_sources: List[str] = pydantic.Field(default_factory=list)
    uncertainty_notes: Optional[str] = None


# ============================================================================
# Pydantic-AI Agent Configuration
# ============================================================================

# System prompt for the forensic agent
FORENSIC_AGENT_SYSTEM_PROMPT = """
You are an expert Forensic AI Analyst for the Semantic Memory Engine (SME).
Your role is to analyze text for evidence, extract entities, assess risk, and provide actionable intelligence.

Guidelines:
1. Always base conclusions on explicit evidence in the text
2. Assign confidence scores based on evidence strength
3. Identify potential risks and threat indicators
4. Provide specific, actionable recommendations
5. Maintain epistemic humility - acknowledge uncertainty
6. Flag synthetic or potentially manipulated content
"""

# Create the forensic agent with typed outputs
# Note: Uses 'infer' model - will use OPENAI_API_KEY env var or can be configured
# to use other providers (ollama, anthropic, etc.)
def get_forensic_agent():
    """Lazy initialization of the forensic agent."""
    return pydantic_ai.Agent(
        model='openai:gpt-4o-mini',  # Configurable - can use Ollama, Anthropic, etc.
        result_type=ForensicAnalysisResult,
        system_prompt=FORENSIC_AGENT_SYSTEM_PROMPT,
    )

# For backwards compatibility - will be lazily initialized
forensic_agent = None


# ============================================================================
# Legacy-style wrapper for SME compatibility
# ============================================================================

def analyze_forensic_text(text: str) -> Dict[str, Any]:
    """
    Analyze text using Pydantic-AI agent.
    
    This is a synchronous wrapper for the async agent.
    
    Args:
        text: The forensic text to analyze
        
    Returns:
        Dictionary with structured analysis results
    """
    global forensic_agent
    if forensic_agent is None:
        forensic_agent = get_forensic_agent()
    
    result = forensic_agent.run_sync(text)
    
    # Convert to dict for SME compatibility
    return {
        "entities": [
            {
                "name": e.name,
                "type": e.entity_type,
                "confidence": e.confidence
            }
            for e in result.data.entities
        ],
        "sentiment": result.data.sentiment,
        "findings": result.data.key_findings,
        "risk_level": result.data.risk_level,
        "actions": result.data.recommended_actions,
        "validation": {
            "model": "pydantic-ai",
            "validated": True
        }
    }


async def analyze_forensic_text_async(text: str) -> Dict[str, Any]:
    """
    Async version of forensic text analysis.
    """
    result = await forensic_agent.run(text)
    
    return {
        "entities": [
            {
                "name": e.name,
                "type": e.entity_type,
                "confidence": e.confidence
            }
            for e in result.data.entities
        ],
        "sentiment": result.data.sentiment,
        "findings": result.data.key_findings,
        "risk_level": result.data.risk_level,
        "actions": result.data.recommended_actions,
        "validation": {
            "model": "pydantic-ai",
            "validated": True
        }
    }


def verify_claim(claim: str, evidence: List[str]) -> Dict[str, Any]:
    """
    Verify a forensic claim against evidence sources.
    
    Args:
        claim: The claim to verify
        evidence: List of evidence text snippets
        
    Returns:
        Verification result with confidence score
    """
    verification_agent = pydantic_ai.Agent(
        model='openai:gpt-4o-mini',
        result_type=ClaimVerification,
        system_prompt="""You are an epistemic verifier. 
        Evaluate claims against provided evidence sources.
        Be strict - only verify claims that have clear support.""",
    )
    
    context = f"Claim: {claim}\n\nEvidence:\n" + "\n".join(f"- {e}" for e in evidence)
    result = verification_agent.run_sync(context)
    
    return {
        "claim": result.data.claim,
        "verified": result.data.is_verified,
        "confidence": result.data.confidence,
        "sources": result.data.evidence_sources,
        "notes": result.data.uncertainty_notes
    }


# ============================================================================
# Integration with SME Tool Registry
# ============================================================================

def register_with_sme_registry(registry):
    """
    Register Pydantic-AI tools with SME's tool registry.
    
    Args:
        registry: SME ToolRegistry instance
    """
    registry.add_tool(
        "pydantic_ai_analyze",
        analyze_forensic_text,
        description="AI-powered forensic text analysis using Pydantic-AI",
        parameters={"text": "str"}
    )
    
    registry.add_tool(
        "pydantic_ai_verify",
        verify_claim,
        description="Verify forensic claims against evidence",
        parameters={"claim": "str", "evidence": "list"}
    )


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Test the forensic agent
    sample_text = """
    The suspect, John Doe, was observed near the perimeter breach at 3:47 AM.
    Multiple failed login attempts were detected from IP 192.168.1.105.
    The administrative account 'admin_svc' showed unusual activity patterns.
    Security logs indicate potential data exfiltration to external IP 45.33.32.156.
    """
    
    result = analyze_forensic_text(sample_text)
    print(json.dumps(result, indent=2))
