"""
SME Forensic Agent using Smolagents

This module provides a lightweight but powerful agent framework from Hugging Face
for building intelligent agents that can write code and call tools.

v2.3.0: Added Smolagents for agentic AI workflows.
"""

import json
import re
from typing import List

import smolagents
from smolagents import tools as tools_mod


# ============================================================================
# Custom SME Tools for Smolagents
# ============================================================================

@tools_mod.tool
def analyze_stylometry(text: str) -> str:
    """
    Analyze text for stylometric fingerprinting.
    
    Args:
        text: The text to analyze
        
    Returns:
        JSON string with stylometric analysis
    """
    # This would call the actual SME stylometry tools
    words = text.split()
    unique_words = set(words)
    
    return json.dumps({
        "word_count": len(words),
        "unique_words": len(unique_words),
        "lexical_diversity": len(unique_words) / len(words) if words else 0,
        "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
    })


@tools_mod.tool
def check_source_trust(url: str) -> str:
    """
    Check the trust score of a web source.
    
    Args:
        url: The URL to check
        
    Returns:
        JSON string with trust analysis
    """
    # Simulated trust checking
    trust_indicators = ["edu", "gov", "org"]  # Generally more trustworthy
    
    base_domain = url.split("/")[2] if "/" in url else url
    trust_level = "high" if any(ind in base_domain for ind in trust_indicators) else "medium"
    
    return json.dumps({
        "url": url,
        "trust_level": trust_level,
        "domain": base_domain,
    })


@tools_mod.tool
def extract_entities(text: str) -> str:
    """
    Extract named entities from text.
    
    Args:
        text: Text to extract entities from
        
    Returns:
        JSON string with extracted entities
    """
    # Find potential entities (capitalized words)
    entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    
    return json.dumps({
        "entities": list(set(entities)),
        "count": len(set(entities)),
    })


@tools_mod.tool
def calculate_risk_score(indicators: List[str]) -> str:
    """
    Calculate risk score from behavioral indicators.
    
    Args:
        indicators: List of risk indicators
        
    Returns:
        JSON string with risk analysis
    """
    risk_keywords = {
        "critical": ["breach", "attack", "exploit", "malware"],
        "high": ["suspicious", "unauthorized", "failed", "denied"],
        "medium": ["unusual", "anomaly", "warning"],
        "low": ["normal", "expected", "verified"],
    }
    
    score = 0
    detected = []
    
    for indicator in indicators:
        indicator_lower = indicator.lower()
        for level, keywords in risk_keywords.items():
            if any(kw in indicator_lower for kw in keywords):
                level_score = {"critical": 100, "high": 75, "medium": 50, "low": 25}[level]
                if level_score > score:
                    score = level_score
                detected.append(level)
                break
    
    return json.dumps({
        "risk_score": score,
        "risk_level": "critical" if score > 75 else "high" if score > 50 else "medium" if score > 25 else "low",
        "indicators_detected": detected,
    })


# ============================================================================
# Smolagent Configuration
# ============================================================================

# Create a forensic investigation agent
forensic_agent = smolagents.ToolCallingAgent(
    model="ollama:llama3.2",  # Configurable - can use HF Inference API, OpenAI, etc.
    tools=[
        analyze_stylometry,
        check_source_trust,
        extract_entities,
        calculate_risk_score,
        # smolagents.DuckDuckGoSearchTool(),  # Requires 'ddgs' package
    ],
    max_steps=10,
)


# ============================================================================
# Code Agent for Complex Analysis
# ============================================================================

code_agent = smolagents.CodeAgent(
    model="ollama:llama3.2",
    tools=[
        analyze_stylometry,
        extract_entities,
        calculate_risk_score,
    ],
    max_steps=15,
)


# ============================================================================
# SME Integration Functions
# ============================================================================

def run_forensic_investigation(query: str) -> str:
    """
    Run a forensic investigation using the Smolagent.
    
    Args:
        query: The investigation query
        
    Returns:
        Agent's response
    """
    result = forensic_agent.run(query)
    return result


def run_code_analysis(code: str) -> str:
    """
    Run code-based forensic analysis.
    
    Args:
        code: Python code to execute
        
    Returns:
        Analysis result
    """
    result = code_agent.run(code)
    return result


async def run_forensic_investigation_async(query: str) -> str:
    """
    Async version of forensic investigation.
    """
    result = await forensic_agent.run_async(query)
    return result


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Test the forensic agent
    test_query = """
    Investigate the following scenario:
    Multiple failed login attempts were detected from IP 192.168.1.105.
    The user 'admin_svc' showed unusual activity patterns.
    Check if this is a potential security breach.
    """
    
    # Note: Requires ollama or other LLM to be running
    # result = run_forensic_investigation(test_query)
    # print(result)
    
    print("Smolagents forensic agent configured.")
    print("Tools available: analyze_stylometry, check_source_trust, extract_entities, calculate_risk_score")
