"""
The Curator: Lexicon Auto-Calibration & Closed-Loop Learning
Feedback loop that calibrates signal weights based on user corrections.
Implements dynamic signal adjustment for intelligent learning.
"""

from mcp.server.fastmcp import FastMCP
import json
import os
import sqlite3
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import defaultdict
import math

mcp = FastMCP("LexiconCurator")

SIGNALS_PATH = os.path.normpath("D:/mcp_servers/storage/compiled_signals.json")
CALIBRATION_LOG = os.path.normpath("D:/mcp_servers/storage/calibration_log.json")
DB_PATH = os.path.normpath("D:/mcp_servers/storage/laboratory.db")

class SignalCurator:
    """Manages signal weight calibration through feedback."""
    
    def __init__(self, signals_path: str, cal_log_path: str):
        self.signals_path = signals_path
        self.cal_log_path = cal_log_path
        self.signals = self._load_signals()
        self.calibration_history = self._load_calibration_log()
    
    def _load_signals(self) -> Dict[str, Any]:
        """Loads current compiled signals."""
        try:
            if os.path.exists(self.signals_path):
                with open(self.signals_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading signals: {e}")
        return {}
    
    def _load_calibration_log(self) -> List[Dict[str, Any]]:
        """Loads calibration history."""
        try:
            if os.path.exists(self.cal_log_path):
                with open(self.cal_log_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading calibration log: {e}")
        return []
    
    def _save_signals(self):
        """Persists updated signals to disk."""
        with open(self.signals_path, 'w') as f:
            json.dump(self.signals, f, indent=2)
    
    def _save_calibration_log(self):
        """Persists calibration log."""
        with open(self.cal_log_path, 'w') as f:
            json.dump(self.calibration_history, f, indent=2, default=str)
    
    def _adaptive_adjustment(self, old_weight: float, correction_type: str, strength: float = 0.5) -> float:
        """Calculates new weight based on correction."""
        if correction_type == "too_high":
            # Reduce negative weight (make less negative) or positive weight
            adjustment = abs(old_weight) * (0.5 - strength * 0.3)
            return old_weight - adjustment if old_weight < 0 else old_weight - adjustment
        
        elif correction_type == "too_low":
            # Increase magnitude (more negative or more positive)
            adjustment = abs(old_weight) * (0.5 + strength * 0.3)
            return old_weight - adjustment if old_weight < 0 else old_weight + adjustment
        
        elif correction_type == "neutral":
            # Move toward 0
            return old_weight * 0.7
        
        elif correction_type == "context_dependent":
            # Split weight - mark as needing contextual handling
            return old_weight * 0.3  # Reduce confidence
        
        return old_weight
    
    def calibrate_term(self, term: str, correction_type: str, moral_foundation: str = "", 
                      rationale: str = "", strength: float = 0.5) -> Dict[str, Any]:
        """
        Applies a calibration correction to a signal term.
        correction_type: 'too_high', 'too_low', 'neutral', 'context_dependent'
        """
        try:
            old_weight = self.signals.get(term, 0)
            new_weight = self._adaptive_adjustment(old_weight, correction_type, strength)
            
            # Log the calibration
            calibration_record = {
                'timestamp': datetime.now().isoformat(),
                'term': term,
                'old_weight': old_weight,
                'new_weight': round(new_weight, 4),
                'correction_type': correction_type,
                'moral_foundation': moral_foundation,
                'rationale': rationale,
                'strength': strength,
                'automatic_adjustment': True
            }
            
            # Apply correction
            self.signals[term] = round(new_weight, 4)
            self.calibration_history.append(calibration_record)
            
            # Persist
            self._save_signals()
            self._save_calibration_log()
            
            return {
                'status': 'calibrated',
                'term': term,
                'old_weight': old_weight,
                'new_weight': new_weight,
                'adjustment_magnitude': abs(new_weight - old_weight),
                'correction_type': correction_type
            }
        
        except Exception as e:
            return {'error': str(e), 'term': term}
    
    def bulk_calibrate(self, corrections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Applies multiple calibrations at once."""
        results = {
            'corrections_applied': 0,
            'corrections_failed': 0,
            'details': []
        }
        
        for correction in corrections:
            result = self.calibrate_term(
                correction.get('term'),
                correction.get('correction_type'),
                correction.get('moral_foundation', ''),
                correction.get('rationale', ''),
                correction.get('strength', 0.5)
            )
            
            if 'error' not in result:
                results['corrections_applied'] += 1
            else:
                results['corrections_failed'] += 1
            
            results['details'].append(result)
        
        return results
    
    def get_calibration_stats(self) -> Dict[str, Any]:
        """Returns statistics on calibration activity."""
        if not self.calibration_history:
            return {'total_calibrations': 0, 'status': 'no_data'}
        
        correction_counts = defaultdict(int)
        term_adjustments = defaultdict(list)
        
        for record in self.calibration_history:
            correction_counts[record['correction_type']] += 1
            term_adjustments[record['term']].append({
                'timestamp': record['timestamp'],
                'adjustment': record['new_weight'] - record['old_weight']
            })
        
        most_calibrated_terms = sorted(
            [(term, len(adjusts)) for term, adjusts in term_adjustments.items()],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            'total_calibrations': len(self.calibration_history),
            'correction_types': dict(correction_counts),
            'most_calibrated_terms': most_calibrated_terms,
            'total_signals': len(self.signals),
            'last_calibration': self.calibration_history[-1]['timestamp'] if self.calibration_history else None
        }
    
    def revert_calibration(self, steps: int = 1) -> Dict[str, Any]:
        """Reverts the last N calibrations."""
        if steps > len(self.calibration_history):
            return {'error': 'Not enough calibration history'}
        
        reverted = []
        for i in range(steps):
            record = self.calibration_history.pop()
            # Restore original weight
            self.signals[record['term']] = record['old_weight']
            reverted.append(record['term'])
        
        self._save_signals()
        self._save_calibration_log()
        
        return {
            'status': 'reverted',
            'steps_reverted': steps,
            'terms_restored': reverted
        }
    
    def suggest_calibrations(self, threshold_anomalies: float = 2.0) -> List[Dict[str, Any]]:
        """Suggests calibrations based on signal anomalies."""
        suggestions = []
        weights = list(self.signals.values())
        
        if not weights:
            return suggestions
        
        mean_weight = sum(weights) / len(weights)
        variance = sum((w - mean_weight) ** 2 for w in weights) / len(weights)
        std_dev = math.sqrt(variance)
        
        # Find outliers
        for term, weight in self.signals.items():
            if abs(weight - mean_weight) > (threshold_anomalies * std_dev):
                suggestions.append({
                    'term': term,
                    'current_weight': weight,
                    'anomaly_score': abs(weight - mean_weight) / (std_dev + 0.001),
                    'suggested_action': 'review_and_calibrate',
                    'reason': 'outlier_weight'
                })
        
        return sorted(suggestions, key=lambda x: x['anomaly_score'], reverse=True)


class FeedbackProcessor:
    """Processes user feedback from Watcher flags."""
    
    @staticmethod
    def process_watcher_feedback(flag_event: Dict[str, Any], user_correction: str, 
                                curator: SignalCurator) -> Dict[str, Any]:
        """
        Processes correction feedback from Watcher.
        user_correction format: "term1:correction_type1|term2:correction_type2"
        """
        try:
            corrections = []
            
            for correction_pair in user_correction.split('|'):
                if ':' not in correction_pair:
                    continue
                
                term, corr_type = correction_pair.split(':')
                term = term.strip()
                corr_type = corr_type.strip()
                
                if corr_type not in ['too_high', 'too_low', 'neutral', 'context_dependent']:
                    continue
                
                corrections.append({
                    'term': term,
                    'correction_type': corr_type,
                    'moral_foundation': flag_event.get('moral_foundation', ''),
                    'rationale': f"User feedback from {flag_event.get('source_file', 'unknown')}",
                    'strength': 0.6
                })
            
            result = curator.bulk_calibrate(corrections)
            
            return {
                'status': 'processed',
                'feedback_source': flag_event.get('source_file'),
                'corrections_applied': result['corrections_applied'],
                'details': result['details']
            }
        
        except Exception as e:
            return {'error': str(e)}


@mcp.tool()
def calibrate_signal_term(term: str, correction_type: str, moral_foundation: str = "", 
                         rationale: str = "", strength: float = 0.5) -> str:
    """
    Calibrates a single signal term weight.
    correction_type: 'too_high' | 'too_low' | 'neutral' | 'context_dependent'
    strength: 0-1 scale for adjustment magnitude
    """
    try:
        curator = SignalCurator(SIGNALS_PATH, CALIBRATION_LOG)
        result = curator.calibrate_term(term, correction_type, moral_foundation, rationale, strength)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def bulk_calibrate_signals(corrections_json: str) -> str:
    """
    Applies multiple calibrations at once.
    corrections_json format: [{"term": "word", "correction_type": "too_high", ...}, ...]
    """
    try:
        corrections = json.loads(corrections_json) if isinstance(corrections_json, str) else corrections_json
        curator = SignalCurator(SIGNALS_PATH, CALIBRATION_LOG)
        result = curator.bulk_calibrate(corrections)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def get_calibration_statistics() -> str:
    """Returns statistics on signal calibration history."""
    try:
        curator = SignalCurator(SIGNALS_PATH, CALIBRATION_LOG)
        result = curator.get_calibration_stats()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def suggest_signal_calibrations(threshold: float = 2.0) -> str:
    """
    Suggests calibrations based on statistical anomalies.
    threshold: standard deviations from mean
    """
    try:
        curator = SignalCurator(SIGNALS_PATH, CALIBRATION_LOG)
        suggestions = curator.suggest_calibrations(threshold)
        return json.dumps({
            'suggestions': suggestions,
            'count': len(suggestions),
            'status': 'complete'
        }, indent=2)
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def revert_calibrations(steps: int = 1) -> str:
    """Reverts the last N calibration steps."""
    try:
        curator = SignalCurator(SIGNALS_PATH, CALIBRATION_LOG)
        result = curator.revert_calibration(steps)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({'error': str(e)})


@mcp.tool()
def process_watcher_feedback(flag_event_json: str, user_correction: str) -> str:
    """
    Processes user feedback from Watcher flag.
    correction format: "term1:correction_type|term2:correction_type"
    Example: "vermin:too_high|parasite:too_high|entities:neutral"
    """
    try:
        flag_event = json.loads(flag_event_json) if isinstance(flag_event_json, str) else flag_event_json
        curator = SignalCurator(SIGNALS_PATH, CALIBRATION_LOG)
        result = FeedbackProcessor.process_watcher_feedback(flag_event, user_correction, curator)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({'error': str(e)})


if __name__ == "__main__":
    mcp.run()
