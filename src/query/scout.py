"""
The Scout: Adaptive Retrieval Engine
Modulates search depth based on query complexity.
Implements SimpleMem's query complexity estimation.
"""

from mcp.server.fastmcp import FastMCP
import sqlite3
import json
import os
from typing import Dict, List, Tuple, Any
from datetime import datetime
import re

mcp = FastMCP("AdaptiveScout")

DB_PATH = os.path.normpath("D:/mcp_servers/storage/laboratory.db")

class QueryComplexityEstimator:
    """Estimates query complexity to determine retrieval depth."""
    
    @staticmethod
    def estimate_complexity(query: str) -> Dict[str, Any]:
        """Estimates complexity of a query (0-10 scale)."""
        complexity_score = 0
        factors = []
        
        query_lower = query.lower()
        
        # Factor 1: Question complexity
        question_words = ['how', 'why', 'what if', 'compare', 'analyze', 'relationship']
        if any(word in query_lower for word in question_words):
            complexity_score += 3
            factors.append('complex_question')
        
        # Factor 2: Multiple entities
        capitalized_words = len(re.findall(r'\b[A-Z][a-z]+\b', query))
        if capitalized_words > 2:
            complexity_score += 2
            factors.append(f'{capitalized_words}_entities')
        
        # Factor 3: Temporal constraints
        temporal_terms = ['when', 'before', 'after', 'during', 'since', 'until']
        if any(term in query_lower for term in temporal_terms):
            complexity_score += 2
            factors.append('temporal_constraint')
        
        # Factor 4: Negation/contradiction
        negation_terms = ['not', 'unlike', 'different', 'contrast', 'but']
        if any(term in query_lower for term in negation_terms):
            complexity_score += 2
            factors.append('negation_present')
        
        # Factor 5: Rhetorical intent
        rhetorical_terms = ['moral', 'ethics', 'justify', 'reasoning', 'argument']
        if any(term in query_lower for term in rhetorical_terms):
            complexity_score += 2
            factors.append('rhetorical_analysis')
        
        # Normalize to 0-10
        complexity_score = min(complexity_score, 10)
        
        return {
            'query': query,
            'complexity_score': complexity_score,
            'complexity_level': QueryComplexityEstimator._level_name(complexity_score),
            'contributing_factors': factors,
            'recommended_depth': QueryComplexityEstimator._depth_for_complexity(complexity_score)
        }
    
    @staticmethod
    def _level_name(score: float) -> str:
        """Names the complexity level."""
        if score < 2:
            return 'simple'
        elif score < 5:
            return 'moderate'
        elif score < 8:
            return 'complex'
        else:
            return 'highly_complex'
    
    @staticmethod
    def _depth_for_complexity(score: float) -> Dict[str, int]:
        """Recommends retrieval depth based on complexity."""
        # Simple: 3 facts, Moderate: 8 facts, Complex: 15 facts, Highly complex: 25+ facts
        if score < 2:
            return {'num_facts': 3, 'search_radius': 'local', 'temporal_window_days': 7}
        elif score < 5:
            return {'num_facts': 8, 'search_radius': 'local_extended', 'temporal_window_days': 30}
        elif score < 8:
            return {'num_facts': 15, 'search_radius': 'full', 'temporal_window_days': 90}
        else:
            return {'num_facts': 25, 'search_radius': 'full_deep', 'temporal_window_days': 365}


class AdaptiveRetriever:
    """Retrieves facts at appropriate depth level."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def retrieve_by_complexity(self, query: str) -> Dict[str, Any]:
        """Retrieves facts adjusted to query complexity."""
        try:
            complexity_info = QueryComplexityEstimator.estimate_complexity(query)
            depth_params = complexity_info['recommended_depth']
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Retrieve sentiment logs within temporal window
            cursor.execute(f'''
                SELECT source_file, timestamp, neg, neu, pos, compound
                FROM sentiment_logs
                WHERE timestamp >= datetime('now', ?)
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (f"-{depth_params['temporal_window_days']} days", depth_params['num_facts']))
            
            results = cursor.fetchall()
            conn.close()
            
            facts = []
            for row in results:
                facts.append({
                    'source': row[0],
                    'timestamp': row[1],
                    'sentiment': {
                        'neg': row[2],
                        'neu': row[3],
                        'pos': row[4],
                        'compound': row[5]
                    }
                })
            
            return {
                'query': query,
                'complexity_analysis': {
                    'score': complexity_info['complexity_score'],
                    'level': complexity_info['complexity_level'],
                    'factors': complexity_info['contributing_factors']
                },
                'retrieval_parameters': depth_params,
                'facts_retrieved': len(facts),
                'facts': facts,
                'context_window_estimate': sum(len(f['source'].split()) for f in facts)
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def search_deep(self, query: str, focus_area: str = "") -> Dict[str, Any]:
        """Performs deep search for complex queries."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Search across all temporal data
            if focus_area:
                cursor.execute('''
                    SELECT source_file, timestamp, compound, COUNT(*) as frequency
                    FROM sentiment_logs
                    WHERE source_file LIKE ?
                    GROUP BY source_file
                    ORDER BY frequency DESC
                    LIMIT 50
                ''', (f'%{focus_area}%',))
            else:
                cursor.execute('''
                    SELECT source_file, timestamp, compound, COUNT(*) as frequency
                    FROM sentiment_logs
                    GROUP BY source_file
                    ORDER BY frequency DESC
                    LIMIT 50
                ''')
            
            results = cursor.fetchall()
            conn.close()
            
            # Analyze patterns
            patterns = {
                'high_negative': [r for r in results if r[2] < -0.5],
                'high_positive': [r for r in results if r[2] > 0.5],
                'neutral': [r for r in results if -0.5 <= r[2] <= 0.5],
            }
            
            return {
                'query': query,
                'focus_area': focus_area,
                'total_entries_analyzed': len(results),
                'sentiment_patterns': {
                    'high_negative': len(patterns['high_negative']),
                    'high_positive': len(patterns['high_positive']),
                    'neutral': len(patterns['neutral']),
                },
                'top_results': [
                    {
                        'source': r[0],
                        'timestamp': r[1],
                        'compound_sentiment': r[2],
                        'frequency': r[3]
                    }
                    for r in results[:10]
                ]
            }
        
        except Exception as e:
            return {'error': str(e)}


@mcp.tool()
def estimate_query_complexity(query: str) -> str:
    """
    Estimates the complexity of a query (0-10 scale).
    Returns complexity factors and recommended retrieval depth.
    """
    try:
        result = QueryComplexityEstimator.estimate_complexity(query)
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def adaptive_retrieval(query: str) -> str:
    """
    Retrieves facts with depth adapted to query complexity.
    Simple queries get 3 facts, complex queries get 25+.
    Automatically estimates context window usage.
    """
    try:
        retriever = AdaptiveRetriever(DB_PATH)
        result = retriever.retrieve_by_complexity(query)
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def deep_search(query: str, focus_area: str = "") -> str:
    """
    Performs deep search across all temporal data.
    Identifies sentiment patterns and behavioral trends.
    Use for complex rhetorical analysis queries.
    """
    try:
        retriever = AdaptiveRetriever(DB_PATH)
        result = retriever.search_deep(query, focus_area)
        
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


if __name__ == "__main__":
    mcp.run()
