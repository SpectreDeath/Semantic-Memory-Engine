from __future__ import annotations

import numpy as np


def calculate_entropy_divergence(p: list[float] | np.ndarray, q: list[float] | np.ndarray) -> float:
    """
    Calculates the Kullback-Leibler (KL) Divergence (Relative Entropy) between two distributions.
    P is the 'observed' distribution, Q is the 'baseline' distribution.
    Useful for detecting 'drift' in log data or stylistic patterns.

    Args:
        p: Observed probability distribution.
        q: Baseline/Reference probability distribution.

    Returns:
        The KL divergence value (Relative Entropy in bits if using log2).
        This implementation uses natural logarithm (nats).
    """
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)

    # Ensure they sum to 1.0 (True probability distributions)
    p = p / (np.sum(p) + 1e-12)
    q = q / (np.sum(q) + 1e-12)

    # Smoothing to avoid log(0) and division by zero
    epsilon = 1e-12
    p = np.clip(p, epsilon, 1.0)
    q = np.clip(q, epsilon, 1.0)

    # KL Divergence formula: Sum( P(i) * log(P(i) / Q(i)) )
    return float(np.sum(p * np.log(p / q)))


def calculate_shannon_entropy(p: list[float] | np.ndarray) -> float:
    """
    Calculates the Shannon Entropy of a distribution.
    """
    p = np.asarray(p, dtype=float)
    p = p / (np.sum(p) + 1e-12)
    p = np.clip(p, 1e-12, 1.0)
    return float(-np.sum(p * np.log2(p)))
