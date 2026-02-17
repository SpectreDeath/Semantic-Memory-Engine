import numpy as np
from typing import List, Dict, Any

def audit_benford_distribution(data: List[float]) -> Dict[str, Any]:
    """
    vectorized Benford's Law calculator.
    Measures how well the leading digits of a dataset follow the expected logarithmic distribution.
    Useful for detecting potential fraud or manual manipulation in numeric logs.
    
    Args:
        data: A list of numbers to audit.
        
    Returns:
        A dictionary containing the audit results and a 'Confidence Score'.
    """
    if not data:
        return {"confidence_score": 0.0, "status": "Empty Dataset"}

    # Convert to NumPy array and remove zeros/negatives
    arr = np.asarray(data, dtype=float)
    arr = arr[arr > 0]
    
    if arr.size == 0:
        return {"confidence_score": 0.0, "status": "No Positive Data"}

    # Extract leading digits
    # Using log10 to find the scale, then dividing to get the first digit
    # E.g., 123 -> log10(123) = 2.08 -> 123 / 10^2 = 1.23 -> floor(1.23) = 1
    leading_digits = np.floor(arr / (10 ** np.floor(np.log10(arr)))).astype(int)
    
    # Calculate actual frequencies for digits 1-9
    counts = np.bincount(leading_digits, minlength=10)[1:10]
    actual_probs = counts / counts.sum()

    # Expected Benford probabilities: log10(1 + 1/d)
    digits = np.arange(1, 10)
    expected_probs = np.log10(1 + 1 / digits)

    # Calculate Mean Absolute Error (MAE)
    mae = np.mean(np.abs(actual_probs - expected_probs))
    
    # Confidence Score: 1.0 is a perfect match, 0.0 is completely diverged
    # MAE typically ranges from 0 to ~0.3. We'll map 0.05+ to low confidence.
    confidence_score = max(0.0, 1.0 - (mae / 0.15))
    
    return {
        "confidence_score": round(confidence_score, 4),
        "actual_distribution": {int(d): round(float(p), 4) for d, p in zip(digits, actual_probs)},
        "expected_distribution": {int(d): round(float(p), 4) for d, p in zip(digits, expected_probs)},
        "mean_absolute_error": round(float(mae), 4),
        "sample_size": int(arr.size),
        "status": "Success"
    }
