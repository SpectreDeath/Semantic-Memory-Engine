"""
Self-Correcting Epistemic Gates: SLM-based Recursive Trust Validation

Implements:
- Small local classifier trained on past Gatekeeper failures
- Recursive trust validation loop with feedback
- Lightweight model for 4GB VRAM constraint
- Real-time learning from false positives/negatives

Technical Targets:
- VRAM Floor: 4GB (lightweight classifier)
- Processing Latency: <1s for trust evaluation
- Scalability: Efficient batch processing
"""

import os
import json
import time
import hashlib
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque
import numpy as np

# For lightweight ML
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib

# Import existing gatekeeper logic
from gateway.gatekeeper_logic import (
    calculate_entropy,
    calculate_burstiness,
    calculate_vault_proximity,
    calculate_trust_score,
    analyze_model_origin
)

# Constants
GATE_MODEL_PATH = "data/aether/gate_model.pkl"
GATE_FAILURES_PATH = "data/aether/gate_failures.json"
GATE_STATS_PATH = "data/aether/gate_stats.json"
FEEDBACK_HISTORY_SIZE = 1000
MIN_SAMPLES_FOR_TRAINING = 50


class GateDecision(Enum):
    """Epistemic gate decision outcomes."""
    ALLOW = "allow"           # High trust - allow through
    BLOCK = "block"           # Low trust - block
    REVIEW = "review"         # Uncertain - require manual review
    QUARANTINE = "quarantine" # Potential adversarial - isolate


class FailureType(Enum):
    """Types of gatekeeper failures."""
    FALSE_POSITIVE = "false_positive"   # Flagged as synthetic but was human
    FALSE_NEGATIVE = "false_negative"   # Passed as human but was synthetic
    TRUE_POSITIVE = "true_positive"    # Correctly identified synthetic
    TRUE_NEGATIVE = "true_negative"     # Correctly identified human


@dataclass
class GateFailure:
    """Record of a gatekeeper failure for learning."""
    id: str
    text: str
    features: Dict[str, Any]
    original_decision: str
    actual_label: str  # human or synthetic
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "features": self.features,
            "original_decision": self.original_decision,
            "actual_label": self.actual_label,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GateFailure":
        return cls(
            id=data["id"],
            text=data["text"],
            features=data["features"],
            original_decision=data["original_decision"],
            actual_label=data["actual_label"],
            confidence=data["confidence"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )


@dataclass
class GateFeedback:
    """User feedback on gate decisions."""
    failure_id: str
    corrected_label: str
    notes: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "failure_id": self.failure_id,
            "corrected_label": self.corrected_label,
            "notes": self.notes,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class GateStats:
    """Statistics for gate performance tracking."""
    total_decisions: int = 0
    decisions_by_type: Dict[str, int] = field(default_factory=dict)
    corrections_received: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_positives: int = 0
    true_negatives: int = 0
    average_confidence: float = 0.0
    model_accuracy: float = 0.0
    last_training: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_decisions": self.total_decisions,
            "decisions_by_type": self.decisions_by_type,
            "corrections_received": self.corrections_received,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "true_positives": self.true_positives,
            "true_negatives": self.true_negatives,
            "average_confidence": self.average_confidence,
            "model_accuracy": self.model_accuracy,
            "last_training": self.last_training.isoformat() if self.last_training else None,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GateStats":
        return cls(
            total_decisions=data.get("total_decisions", 0),
            decisions_by_type=data.get("decisions_by_type", {}),
            corrections_received=data.get("corrections_received", 0),
            false_positives=data.get("false_positives", 0),
            false_negatives=data.get("false_negatives", 0),
            true_positives=data.get("true_positives", 0),
            true_negatives=data.get("true_negatives", 0),
            average_confidence=data.get("average_confidence", 0.0),
            model_accuracy=data.get("model_accuracy", 0.0),
            last_training=datetime.fromisoformat(data["last_training"]) if data.get("last_training") else None,
            last_updated=datetime.fromisoformat(data.get("last_updated", datetime.now().isoformat()))
        )


class EpistemicGate:
    """
    Self-Correcting Epistemic Gate with SLM-based trust validation.
    
    Features:
    - Lightweight classifier for 4GB VRAM constraint
    - Continuous learning from failures and feedback
    - Recursive trust validation loop
    - Multi-factor trust scoring
    """
    
    def __init__(
        self,
        node_id: str = "local_node",
        auto_train: bool = True,
        training_threshold: int = MIN_SAMPLES_FOR_TRAINING
    ):
        self.node_id = node_id
        self.auto_train = auto_train
        self.training_threshold = training_threshold
        
        # Ensure directories exist
        os.makedirs("data/aether", exist_ok=True)
        
        # Failure history
        self._failures: Dict[str, GateFailure] = {}
        self._failure_queue = deque(maxlen=FEEDBACK_HISTORY_SIZE)
        
        # Feedback history
        self._feedback_history: List[GateFeedback] = []
        
        # Stats
        self._stats = self._load_stats()
        
        # ML components - lightweight for 4GB VRAM
        self._classifier: Optional[SGDClassifier] = None
        self._scaler: Optional[StandardScaler] = None
        self._vectorizer: Optional[TfidfVectorizer] = None
        
        # Feature extraction for the classifier
        self._feature_names = [
            "entropy", "burstiness", "vault_proximity", "trust_score",
            "text_length", "word_count", "sentence_count", 
            "avg_word_length", "unique_word_ratio", "punctuation_ratio",
            "capital_ratio", "digit_ratio"
        ]
        
        # Load existing model if available
        self._load_model()
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        print(f"[Aether.EpistemicGate] Initialized for node: {node_id}")
        print(f"[Aether.EpistemicGate] Auto-train: {auto_train}, Threshold: {training_threshold}")
    
    def _load_stats(self) -> GateStats:
        """Load statistics from disk."""
        try:
            if os.path.exists(GATE_STATS_PATH):
                with open(GATE_STATS_PATH, 'r') as f:
                    return GateStats.from_dict(json.load(f))
        except Exception as e:
            print(f"[Aether.EpistemicGate] Error loading stats: {e}")
        return GateStats()
    
    def _save_stats(self) -> None:
        """Save statistics to disk."""
        try:
            self._stats.last_updated = datetime.now()
            with open(GATE_STATS_PATH, 'w') as f:
                json.dump(self._stats.to_dict(), f, indent=2)
        except Exception as e:
            print(f"[Aether.EpistemicGate] Error saving stats: {e}")
    
    def _load_model(self) -> bool:
        """Load existing model from disk."""
        try:
            if os.path.exists(GATE_MODEL_PATH):
                model_data = joblib.load(GATE_MODEL_PATH)
                self._classifier = model_data.get("classifier")
                self._scaler = model_data.get("scaler")
                self._vectorizer = model_data.get("vectorizer")
                
                if self._classifier and self._scaler and self._vectorizer:
                    print("[Aether.EpistemicGate] Loaded existing model")
                    return True
        except Exception as e:
            print(f"[Aether.EpistemicGate] Error loading model: {e}")
        return False
    
    def _save_model(self) -> None:
        """Save model to disk."""
        try:
            if self._classifier and self._scaler and self._vectorizer:
                model_data = {
                    "classifier": self._classifier,
                    "scaler": self._scaler,
                    "vectorizer": self._vectorizer,
                    "node_id": self.node_id,
                    "trained_at": datetime.now().isoformat()
                }
                joblib.dump(model_data, GATE_MODEL_PATH)
                print("[Aether.EpistemicGate] Model saved")
        except Exception as e:
            print(f"[Aether.EpistemicGate] Error saving model: {e}")
    
    def _extract_features(self, text: str) -> np.ndarray:
        """Extract features for the classifier."""
        # Get base features from gatekeeper
        entropy = calculate_entropy(text)
        burstiness = calculate_burstiness(text)
        vault_prox = calculate_vault_proximity(text)
        trust = calculate_trust_score(entropy, burstiness, vault_prox)
        
        # Additional text features
        words = text.split()
        sentences = [s for s in text.split('.') if s.strip()]
        
        text_length = len(text)
        word_count = len(words)
        sentence_count = len(sentences)
        avg_word_length = np.mean([len(w) for w in words]) if words else 0
        unique_word_ratio = len(set(words)) / max(1, word_count)
        punctuation_ratio = sum(1 for c in text if c in '.,!?;:"\'') / max(1, text_length)
        capital_ratio = sum(1 for c in text if c.isupper()) / max(1, text_length)
        digit_ratio = sum(1 for c in text if c.isdigit()) / max(1, text_length)
        
        features = [
            entropy,
            burstiness,
            vault_prox,
            trust["nts"] / 100.0,  # Normalize to 0-1
            text_length / 10000.0,  # Normalize
            word_count / 1000.0,   # Normalize
            sentence_count / 100.0, # Normalize
            avg_word_length / 20.0, # Normalize
            unique_word_ratio,
            punctuation_ratio,
            capital_ratio,
            digit_ratio
        ]
        
        return np.array(features)
    
    def _extract_text_features(self, texts: List[str]) -> np.ndarray:
        """Extract TF-IDF features from text."""
        if not self._vectorizer:
            # Use lightweight TF-IDF
            self._vectorizer = TfidfVectorizer(
                max_features=500,  # Keep small for VRAM
                ngram_range=(1, 2),
                stop_words='english',
                min_df=2,
                max_df=0.95
            )
        
        return self._vectorizer.fit_transform(texts).toarray()
    
    def _combine_features(
        self, 
        numeric_features: np.ndarray, 
        text_features: np.ndarray
    ) -> np.ndarray:
        """Combine numeric and text features."""
        # Limit text features to save memory
        text_features_limited = text_features[:, :100] if text_features.shape[1] > 100 else text_features
        
        # Handle dimension mismatch
        if numeric_features.ndim == 1:
            numeric_features = numeric_features.reshape(1, -1)
        if text_features_limited.ndim == 1:
            text_features_limited = text_features_limited.reshape(1, -1)
        
        return np.hstack([numeric_features, text_features_limited])
    
    def evaluate(
        self,
        text: str,
        return_features: bool = False
    ) -> Dict[str, Any]:
        """
        Evaluate text through the epistemic gate.
        
        Returns decision, confidence, and details.
        """
        with self._lock:
            # Extract features
            features = self._extract_features(text)
            
            # Get base gatekeeper decision
            entropy = calculate_entropy(text)
            burstiness = calculate_burstiness(text)
            vault_prox = calculate_vault_proximity(text)
            trust = calculate_trust_score(entropy, burstiness, vault_prox)
            attribution = analyze_model_origin(text)
            
            # Primary decision from gatekeeper
            base_decision = trust["nts"]
            base_label = trust["label"]
            
            # If model exists, use it for recursive validation
            model_decision = None
            model_confidence = None
            
            if self._classifier and self._scaler:
                try:
                    # Scale features
                    features_scaled = self._scaler.transform(features.reshape(1, -1))
                    
                    # Get prediction and probability
                    prediction = self._classifier.predict(features_scaled)[0]
                    probabilities = self._classifier.predict_proba(features_scaled)[0]
                    
                    # Class 1 = synthetic, Class 0 = human
                    synthetic_prob = probabilities[1] if len(probabilities) > 1 else 0.5
                    human_prob = probabilities[0] if len(probabilities) > 0 else 0.5
                    
                    model_confidence = max(synthetic_prob, human_prob)
                    
                    # Convert to decision
                    if prediction == 1:  # Synthetic
                        model_decision = "synthetic"
                    else:
                        model_decision = "human"
                        
                except Exception as e:
                    print(f"[Aether.EpistemicGate] Model evaluation error: {e}")
            
            # Combine decisions (recursive validation)
            final_decision = self._combine_decisions(
                base_decision, base_label,
                model_decision, model_confidence
            )
            
            # Update stats
            self._stats.total_decisions += 1
            decision_type = final_decision["decision"].value
            self._stats.decisions_by_type[decision_type] = (
                self._stats.decisions_by_type.get(decision_type, 0) + 1
            )
            
            result = {
                "decision": final_decision["decision"].value,
                "confidence": final_decision["confidence"],
                "reasons": final_decision["reasons"],
                "gatekeeper": {
                    "nts": trust["nts"],
                    "label": trust["label"],
                    "components": trust["components"]
                },
                "model": {
                    "prediction": model_decision,
                    "confidence": model_confidence,
                    "available": self._classifier is not None
                },
                "attribution": attribution,
                "features": {
                    "entropy": entropy,
                    "burstiness": burstiness,
                    "vault_proximity": vault_prox
                }
            }
            
            if return_features:
                result["raw_features"] = features.tolist()
            
            return result
    
    def _combine_decisions(
        self,
        base_score: float,
        base_label: str,
        model_pred: Optional[str],
        model_conf: Optional[float]
    ) -> Dict[str, Any]:
        """
        Recursively validate decision using both gatekeeper and model.
        
        Creates a feedback loop where model learnings inform the final decision.
        """
        reasons = []
        confidence = 0.5
        decision = GateDecision.REVIEW
        
        # Base decision from gatekeeper
        if base_score >= 80:
            base_verdict = "human"
        elif base_score < 50:
            base_verdict = "synthetic"
        else:
            base_verdict = "uncertain"
        
        # If no model, use base decision
        if model_pred is None or model_conf is None:
            if base_verdict == "human":
                decision = GateDecision.ALLOW
                confidence = base_score / 100.0
                reasons.append("High NTS score from gatekeeper")
            elif base_verdict == "synthetic":
                decision = GateDecision.BLOCK
                confidence = (100 - base_score) / 100.0
                reasons.append("Low NTS score from gatekeeper")
            else:
                decision = GateDecision.REVIEW
                confidence = 0.5
                reasons.append("Uncertain - requires review")
            
            return {
                "decision": decision,
                "confidence": confidence,
                "reasons": reasons
            }
        
        # Recursive validation - check for consensus
        consensus = (base_verdict == model_pred)
        
        if consensus:
            # Strong consensus
            if model_pred == "human":
                if model_conf > 0.8:
                    decision = GateDecision.ALLOW
                    confidence = min(0.95, model_conf + 0.1)
                else:
                    decision = GateDecision.ALLOW
                    confidence = model_conf
                reasons.append("Consensus: Human content detected")
            else:
                if model_conf > 0.8:
                    decision = GateDecision.BLOCK
                    confidence = min(0.95, model_conf + 0.1)
                else:
                    decision = GateDecision.QUARANTINE
                    confidence = model_conf
                reasons.append("Consensus: Synthetic content detected")
        else:
            # Disagreement - flag for review
            decision = GateDecision.REVIEW
            confidence = 0.5
            reasons.append(f"Disagreement: Gatekeeper={base_verdict}, Model={model_pred}")
            
            # Log potential failure for later analysis
            self._log_potential_failure(
                base_verdict, model_pred, 
                max(base_score / 100.0, model_conf)
            )
        
        return {
            "decision": decision,
            "confidence": confidence,
            "reasons": reasons
        }
    
    def _log_potential_failure(
        self,
        base_verdict: str,
        model_verdict: str,
        confidence: float
    ) -> None:
        """Log potential failure for later analysis."""
        # Only log significant disagreements
        if abs(confidence - 0.5) < 0.2:  # Both uncertain
            return
        
        # This would be expanded to capture full text for training
        # For now, just increment counter
        pass
    
    def report_feedback(
        self,
        text: str,
        original_decision: str,
        corrected_label: str,
        notes: str = ""
    ) -> str:
        """
        Report feedback on a gate decision.
        
        Used to train the model on false positives/negatives.
        """
        with self._lock:
            # Extract features
            features = self._extract_features(text)
            
            # Determine failure type
            if original_decision == "synthetic" and corrected_label == "human":
                failure_type = FailureType.FALSE_POSITIVE
            elif original_decision == "human" and corrected_label == "synthetic":
                failure_type = FailureType.FALSE_NEGATIVE
            elif original_decision == corrected_label:
                if original_decision == "synthetic":
                    failure_type = FailureType.TRUE_POSITIVE
                else:
                    failure_type = FailureType.TRUE_NEGATIVE
            else:
                failure_type = None
            
            # Create failure record
            failure = GateFailure(
                id=hashlib.sha256(os.urandom(8)).hexdigest()[:16],
                text=text[:1000],  # Limit stored text
                features={name: features[i] for i, name in enumerate(self._feature_names)},
                original_decision=original_decision,
                actual_label=corrected_label,
                confidence=0.5,
                metadata={"failure_type": failure_type.value if failure_type else "unknown"}
            )
            
            self._failures[failure.id] = failure
            self._failure_queue.append(failure.id)
            
            # Update stats
            self._stats.corrections_received += 1
            
            if failure_type == FailureType.FALSE_POSITIVE:
                self._stats.false_positives += 1
            elif failure_type == FailureType.FALSE_NEGATIVE:
                self._stats.false_negatives += 1
            elif failure_type == FailureType.TRUE_POSITIVE:
                self._stats.true_positives += 1
            elif failure_type == FailureType.TRUE_NEGATIVE:
                self._stats.true_negatives += 1
            
            # Check if we should retrain
            if self.auto_train:
                total_failures = (
                    self._stats.false_positives + 
                    self._stats.false_negatives
                )
                
                if total_failures >= self.training_threshold:
                    self.train()
            
            self._save_stats()
            
            return failure.id
    
    def train(self) -> Dict[str, Any]:
        """
        Train the classifier on recorded failures.
        
        Uses lightweight SGD classifier for 4GB VRAM constraint.
        """
        with self._lock:
            if len(self._failures) < MIN_SAMPLES_FOR_TRAINING:
                return {
                    "status": "insufficient_data",
                    "samples": len(self._failures),
                    "required": MIN_SAMPLES_FOR_TRAINING
                }
            
            # Prepare training data
            texts = []
            labels = []
            
            for failure in self._failures.values():
                texts.append(failure.text)
                # Label: 1 = synthetic, 0 = human
                labels.append(1 if failure.actual_label == "synthetic" else 0)
            
            # Extract features
            try:
                # Numeric features
                numeric_features = np.array([
                    [f.features.get(name, 0) for name in self._feature_names]
                    for f in self._failures.values()
                ])
                
                # Text features
                text_features = self._extract_text_features(texts)
                
                # Combine features
                X = self._combine_features(numeric_features, text_features)
                y = np.array(labels)
                
                # Train scaler
                self._scaler = StandardScaler()
                X_scaled = self._scaler.fit_transform(X)
                
                # Split for validation
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42
                )
                
                # Train lightweight classifier
                self._classifier = SGDClassifier(
                    loss='log_loss',  # Logistic regression
                    penalty='l2',
                    alpha=0.0001,
                    max_iter=1000,
                    tol=1e-3,
                    random_state=42,
                    class_weight='balanced',
                    n_jobs=1  # Single thread for memory efficiency
                )
                
                self._classifier.fit(X_train, y_train)
                
                # Evaluate
                y_pred = self._classifier.predict(X_test)
                
                # Calculate accuracy
                accuracy = np.mean(y_pred == y_test)
                self._stats.model_accuracy = accuracy
                
                # Update last training time
                self._stats.last_training = datetime.now()
                
                # Save model
                self._save_model()
                self._save_stats()
                
                return {
                    "status": "trained",
                    "samples": len(texts),
                    "accuracy": accuracy,
                    "train_size": len(X_train),
                    "test_size": len(X_test)
                }
                
            except Exception as e:
                return {
                    "status": "error",
                    "error": str(e)
                }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get gate statistics."""
        stats = self._stats.to_dict()
        
        # Calculate additional metrics
        total = (
            self._stats.true_positives + 
            self._stats.true_negatives + 
            self._stats.false_positives + 
            self._stats.false_negatives
        )
        
        if total > 0:
            stats["precision"] = (
                self._stats.true_positives / 
                max(1, self._stats.true_positives + self._stats.false_positives)
            )
            stats["recall"] = (
                self._stats.true_positives / 
                max(1, self._stats.true_positives + self._stats.false_negatives)
            )
            if stats["precision"] + stats["recall"] > 0:
                stats["f1_score"] = (
                    2 * stats["precision"] * stats["recall"] / 
                    (stats["precision"] + stats["recall"])
                )
        
        stats["model_loaded"] = self._classifier is not None
        stats["pending_failures"] = len(self._failures)
        
        return stats
    
    def get_recent_failures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent failure records."""
        recent_ids = list(self._failure_queue)[-limit:]
        return [
            self._failures[fid].to_dict() 
            for fid in recent_ids 
            if fid in self._failures
        ]
    
    def clear_failures(self) -> int:
        """Clear failure history."""
        count = len(self._failures)
        self._failures.clear()
        self._failure_queue.clear()
        self._save_stats()
        return count
    
    def export_model(self, path: str) -> bool:
        """Export model to file."""
        try:
            joblib.dump({
                "classifier": self._classifier,
                "scaler": self._scaler,
                "vectorizer": self._vectorizer,
                "node_id": self.node_id,
                "exported_at": datetime.now().isoformat()
            }, path)
            return True
        except Exception as e:
            print(f"[Aether.EpistemicGate] Export error: {e}")
            return False
    
    def import_model(self, path: str) -> bool:
        """Import model from file."""
        try:
            model_data = joblib.load(path)
            self._classifier = model_data.get("classifier")
            self._scaler = model_data.get("scaler")
            self._vectorizer = model_data.get("vectorizer")
            return True
        except Exception as e:
            print(f"[Aether.EpistemicGate] Import error: {e}")
            return False
    
    def close(self):
        """Clean up resources."""
        self._save_stats()
        print("[Aether.EpistemicGate] Closed")


# Singleton instance
_epistemic_gate: Optional[EpistemicGate] = None


def get_epistemic_gate(node_id: str = "local_node") -> EpistemicGate:
    """Get or create EpistemicGate singleton."""
    global _epistemic_gate
    
    if _epistemic_gate is None:
        _epistemic_gate = EpistemicGate(node_id=node_id)
    
    return _epistemic_gate
