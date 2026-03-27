from __future__ import annotations

import zlib
from typing import Any

import numpy as np


class ObfuscationAnalyzer:
    """
    Detects obfuscated or packed code using statistical complexity measures.
    Optimized with __slots__.
    """
    __slots__ = ()

    def calculate_hamming_weight(self, data: np.ndarray) -> float:
        """
        Calculates the average Hamming Weight (number of set bits) per byte.
        Range: 0 to 8. Normal ASCII is usually 2.5 to 4.5.
        """
        # Count bits in each byte
        bits = np.unpackbits(data)
        return float(np.sum(bits) / len(data))

    def analyze_obfuscation_score(self, content: str | bytes | list[int]) -> dict[str, Any]:
        """
        Detects obfuscated scripts using Hamming Weight and Compression-based Complexity.
        """
        data = content.encode('utf-8') if isinstance(content, str) else bytes(content)

        if not data:
            return {"obfuscation_score": 0.0, "status": "Empty Content"}

        arr = np.frombuffer(data, dtype=np.uint8)

        # 1. Hamming Weight
        h_weight = self.calculate_hamming_weight(arr)

        # 2. Compression Complexity (Lempel-Ziv proxy)
        # Ratio of compressed size to original size.
        compressed = zlib.compress(data)
        comp_ratio = len(compressed) / len(data)

        # Obfuscation heuristic:
        # - Packed/Encrypted data has high entropy and high compression ratio (close to 1.0)
        # - Highly repetitive (simple obfuscation) has very low ratio.
        # - High Hamming Weight (> 5.0) often indicates non-textual or binary-embedded payloads.

        # Score normalization: 0 to 1
        # High score means high probability of obfuscation/packing.
        # Simple heuristic combining entropy proxy (comp_ratio) and bit density.
        obfuscation_prob = (comp_ratio * 0.7) + (max(0, h_weight - 4) / 4 * 0.3)

        return {
            "obfuscation_score": round(float(min(1.0, obfuscation_prob)), 4),
            "hamming_weight": round(h_weight, 4),
            "compression_ratio": round(comp_ratio, 4),
            "is_likely_obfuscated": bool(obfuscation_prob > 0.7 or h_weight > 5.0),
            "status": "Success"
        }

def analyze_obfuscation_score(content: str | bytes) -> dict[str, Any]:
    """Standalone wrapper for obfuscation analysis."""
    analyzer = ObfuscationAnalyzer()
    return analyzer.analyze_obfuscation_score(content)
