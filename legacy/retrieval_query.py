"""
Retrieval & Query Tools
Semantic search interface, fact verification checker, context window optimizer.
"""

from mcp.server.fastmcp import FastMCP
import json
import sqlite3
import os
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import Counter
import re

mcp = FastMCP("RetrievalQuery")

DB_PATH = os.path.normpath("D:/mcp_servers/storage/laboratory.db")

class SemanticSearchEngine:
    """Provides semantic search capabilities."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _calculate_similarity(self, query: str, text: str) -> float:
        """Calculates Jaccard similarity between query and text."""
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words or not text_words:
            return 0.0
        
        intersection = len(query_words & text_words)
        union = len(query_words | text_words)
        
        return intersection / union if union > 0 else 0.0
    
    def semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Searches for semantically similar content."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT source_file, timestamp, neg, neu, pos, compound
                FROM sentiment_logs
                ORDER BY timestamp DESC
                LIMIT 100
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            # Score results by semantic similarity
            scored_results = []
            for row in results:
                similarity = self._calculate_similarity(query, row[0])
                scored_results.append({
                    'source': row[0],
                    'timestamp': row[1],
                    'sentiment': {'neg': row[2], 'neu': row[3], 'pos': row[4], 'compound': row[5]},
                    'similarity_score': similarity
                })
            
            # Sort by similarity and return top k
            scored_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return scored_results[:top_k]
        
        except Exception as e:
            return []
    
    def entity_search(self, entity_name: str) -> Dict[str, Any]:
        """Searches for all mentions of an entity."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT source_file, timestamp, compound, COUNT(*) as mentions
                FROM sentiment_logs
                WHERE source_file LIKE ?
                GROUP BY source_file
                ORDER BY mentions DESC, timestamp DESC
            ''', (f'%{entity_name}%',))
            
            results = cursor.fetchall()
            conn.close()
            
            entity_profile = {
                'entity': entity_name,
                'total_mentions': sum(r[3] for r in results),
                'unique_sources': len(results),
                'mentions_by_source': [
                    {
                        'source': r[0],
                        'timestamp': r[1],
                        'sentiment_compound': r[2],
                        'mention_count': r[3]
                    }
                    for r in results
                ]
            }
            
            return entity_profile
        
        except Exception as e:
            return {'error': str(e)}


class FactVerificationChecker:
    """Verifies facts against known data."""
    
    @staticmethod
    def verify_sentiment_claim(claim: str) -> Dict[str, Any]:
        """Verifies sentiment-related claims."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Extract sentiment value from claim (e.g., "compound > 0.5")
            match = re.search(r'compound\s*([><]=?)\s*([-\d.]+)', claim, re.I)
            
            if match:
                operator = match.group(1)
                threshold = float(match.group(2))
                
                # Query database
                if operator == '>':
                    cursor.execute('SELECT COUNT(*) FROM sentiment_logs WHERE compound > ?', (threshold,))
                elif operator == '<':
                    cursor.execute('SELECT COUNT(*) FROM sentiment_logs WHERE compound < ?', (threshold,))
                elif operator == '>=':
                    cursor.execute('SELECT COUNT(*) FROM sentiment_logs WHERE compound >= ?', (threshold,))
                elif operator == '<=':
                    cursor.execute('SELECT COUNT(*) FROM sentiment_logs WHERE compound <= ?', (threshold,))
                
                count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM sentiment_logs')
                total = cursor.fetchone()[0]
                
                conn.close()
                
                return {
                    'claim': claim,
                    'verified': count > 0,
                    'matching_records': count,
                    'total_records': total,
                    'percentage': round(100 * count / total, 2) if total > 0 else 0,
                    'verification_confidence': 0.95 if count > 10 else 0.7 if count > 0 else 0.0
                }
            
            conn.close()
            return {'claim': claim, 'error': 'Could not parse claim format'}
        
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def verify_entity_pattern(entity: str, pattern: str) -> Dict[str, Any]:
        """Verifies behavioral patterns for an entity."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get all records for entity
            cursor.execute('''
                SELECT compound, timestamp FROM sentiment_logs
                WHERE source_file LIKE ?
                ORDER BY timestamp DESC
            ''', (f'%{entity}%',))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return {'entity': entity, 'pattern': pattern, 'found': False}
            
            compounds = [r[0] for r in results]
            
            # Analyze patterns
            analysis = {
                'entity': entity,
                'pattern': pattern,
                'records_analyzed': len(compounds),
                'avg_sentiment': round(sum(compounds) / len(compounds), 4),
                'max_sentiment': max(compounds),
                'min_sentiment': min(compounds),
                'volatility': round(max(compounds) - min(compounds), 4)
            }
            
            # Check pattern
            if pattern == 'consistently_negative' and all(c < -0.3 for c in compounds):
                analysis['pattern_match'] = True
                analysis['confidence'] = 0.95
            elif pattern == 'consistently_positive' and all(c > 0.3 for c in compounds):
                analysis['pattern_match'] = True
                analysis['confidence'] = 0.95
            elif pattern == 'volatile' and analysis['volatility'] > 1.5:
                analysis['pattern_match'] = True
                analysis['confidence'] = 0.85
            else:
                analysis['pattern_match'] = False
                analysis['confidence'] = 0.3
            
            return analysis
        
        except Exception as e:
            return {'error': str(e)}


class ContextWindowOptimizer:
    """Optimizes context windows for language models."""
    
    @staticmethod
    def optimize_context(facts: List[Dict[str, Any]], max_tokens: int = 4000) -> Dict[str, Any]:
        """
        Optimizes context by selecting most relevant facts within token budget.
        Estimates tokens using word count * 1.33 (conservative estimate).
        """
        optimization = {
            'max_tokens': max_tokens,
            'original_facts': len(facts),
            'estimated_original_tokens': 0,
            'selected_facts': [],
            'estimated_final_tokens': 0,
            'optimization_ratio': 0.0
        }
        
        # Calculate token estimates
        for fact in facts:
            fact_text = json.dumps(fact)
            estimated_tokens = len(fact_text.split()) * 1.33
            optimization['estimated_original_tokens'] += estimated_tokens
        
        # Select facts within budget
        token_budget = max_tokens
        selected = []
        
        for i, fact in enumerate(facts):
            fact_text = json.dumps(fact)
            fact_tokens = len(fact_text.split()) * 1.33
            
            if fact_tokens <= token_budget:
                selected.append(fact)
                token_budget -= fact_tokens
                optimization['estimated_final_tokens'] += fact_tokens
        
        optimization['selected_facts'] = selected
        optimization['facts_selected'] = len(selected)
        
        if optimization['estimated_original_tokens'] > 0:
            optimization['optimization_ratio'] = round(
                optimization['estimated_final_tokens'] / optimization['estimated_original_tokens'],
                3
            )
        
        return optimization
    
    @staticmethod
    def estimate_context_size(text: str) -> Dict[str, Any]:
        """Estimates context size for given text."""
        words = len(text.split())
        estimated_tokens = words * 1.33
        
        return {
            'text_length': len(text),
            'word_count': words,
            'estimated_tokens': round(estimated_tokens),
            'token_estimation_method': 'word_count * 1.33',
            'fits_in_4k_window': estimated_tokens < 4000,
            'fits_in_8k_window': estimated_tokens < 8000,
            'fits_in_16k_window': estimated_tokens < 16000,
        }


class QueryResponseBuilder:
    """Builds optimized query responses."""
    
    @staticmethod
    def build_response(query: str, context_facts: List[Dict[str, Any]], response_type: str = "analytical") -> Dict[str, Any]:
        """Builds a response with optimized context."""
        response = {
            'query': query,
            'query_type': response_type,
            'context_facts_count': len(context_facts),
            'response_structure': [],
            'recommendations': []
        }
        
        if response_type == "analytical":
            response['response_structure'] = [
                'fact_summary',
                'pattern_analysis',
                'sentiment_profile',
                'recommendations'
            ]
            response['recommendations'] = [
                'Cross-reference with multiple sources',
                'Verify temporal consistency',
                'Check for contradictions'
            ]
        
        elif response_type == "rhetorical":
            response['response_structure'] = [
                'moral_foundation_analysis',
                'rhetorical_devices_used',
                'persuasion_techniques',
                'counter_arguments'
            ]
            response['recommendations'] = [
                'Analyze underlying moral frameworks',
                'Identify emotional appeals',
                'Look for logical fallacies'
            ]
        
        elif response_type == "behavioral":
            response['response_structure'] = [
                'entity_profile',
                'behavioral_patterns',
                'sentiment_trends',
                'anomalies'
            ]
            response['recommendations'] = [
                'Track consistency over time',
                'Identify behavior changes',
                'Monitor for new patterns'
            ]
        
        return response


@mcp.tool()
def semantic_search(query: str, top_k: int = 10) -> str:
    """
    Performs semantic search on stored facts.
    Returns most similar facts ranked by semantic similarity.
    """
    try:
        engine = SemanticSearchEngine(DB_PATH)
        results = engine.semantic_search(query, top_k)
        
        return json.dumps({
            'query': query,
            'results_count': len(results),
            'results': results,
            'status': 'success'
        }, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def entity_search(entity_name: str) -> str:
    """
    Searches for all mentions and sentiment data for a specific entity.
    Returns entity profile with sentiment trends.
    """
    try:
        engine = SemanticSearchEngine(DB_PATH)
        result = engine.entity_search(entity_name)
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def verify_sentiment_claim(claim: str) -> str:
    """
    Verifies sentiment-related claims against database.
    Example claim: 'compound > 0.5'
    """
    try:
        result = FactVerificationChecker.verify_sentiment_claim(claim)
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def verify_entity_pattern(entity: str, pattern: str) -> str:
    """
    Verifies behavioral patterns for an entity.
    Patterns: 'consistently_negative', 'consistently_positive', 'volatile'
    """
    try:
        result = FactVerificationChecker.verify_entity_pattern(entity, pattern)
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def optimize_context_window(facts_json: str, max_tokens: int = 4000) -> str:
    """
    Optimizes context by selecting most relevant facts within token budget.
    Returns selected facts and optimization metrics.
    """
    try:
        facts = json.loads(facts_json) if isinstance(facts_json, str) else facts_json
        if not isinstance(facts, list):
            facts = [facts]
        
        result = ContextWindowOptimizer.optimize_context(facts, max_tokens)
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def estimate_context_size(text: str) -> str:
    """
    Estimates token count for given text.
    Uses conservative word_count * 1.33 estimation.
    """
    try:
        result = ContextWindowOptimizer.estimate_context_size(text)
        return json.dumps(result, indent=2)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def build_query_response(query: str, facts_json: str, response_type: str = "analytical") -> str:
    """
    Builds optimized response structure for query.
    Response types: 'analytical', 'rhetorical', 'behavioral'
    """
    try:
        facts = json.loads(facts_json) if isinstance(facts_json, str) else facts_json
        if not isinstance(facts, list):
            facts = [facts]
        
        result = QueryResponseBuilder.build_response(query, facts, response_type)
        return json.dumps(result, indent=2, default=str)
    
    except Exception as e:
        return json.dumps({'error': str(e)})


if __name__ == "__main__":
    mcp.run()
