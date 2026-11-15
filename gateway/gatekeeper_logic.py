"""Backward-compatible re-export shim; canonical logic lives in src.core.gatekeeper_logic."""

from src.core.gatekeeper_logic import (
    SIGNATURES_PATH,
    VAULT_PATH,
    TrustScorer,
    _get_ngrams,
    analyze_model_origin,
    calculate_burstiness,
    calculate_entropy,
    calculate_trust_score,
    calculate_vault_proximity,
    load_vault,
)

__all__ = [
    "SIGNATURES_PATH",
    "VAULT_PATH",
    "TrustScorer",
    "_get_ngrams",
    "analyze_model_origin",
    "calculate_burstiness",
    "calculate_entropy",
    "calculate_trust_score",
    "calculate_vault_proximity",
    "load_vault",
]
