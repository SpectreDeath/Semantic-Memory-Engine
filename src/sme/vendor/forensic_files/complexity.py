import zlib
import os
from typing import Dict, Any

class StructuralComplexityTool:
    """
    Calculates compression ratio as a proxy for structural entropy.
    High ratio = Repetitive/Structured (text, logs).
    Low ratio = High Entropy (encrypted, compressed, or packed payloads).
    """
    __slots__ = ()

    def calculate(self, file_path: str) -> Dict[str, Any]:
        """Calculates the compression ratio of a file."""
        if not os.path.exists(file_path):
            return {"error": "File not found", "status": "Error"}

        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return {"complexity_ratio": 0.0, "status": "Success", "note": "Empty File"}

            # For very large files, we sample the first 1MB to keep memory low
            sample_size = min(file_size, 1024 * 1024)
            with open(file_path, 'rb') as f:
                data = f.read(sample_size)

            compressed_data = zlib.compress(data)
            comp_size = len(compressed_data)
            
            # Ratio: Compressed / Original
            # Lower ratio (e.g. 0.1) means highly compressible (simple)
            # Higher ratio (e.g. 0.9+) means already compressed or high entropy (complex)
            ratio = comp_size / len(data)

            return {
                "complexity_ratio": round(ratio, 4),
                "original_sample_size": len(data),
                "compressed_sample_size": comp_size,
                "is_high_entropy": ratio > 0.85,
                "status": "Success"
            }
        except Exception as e:
            return {"error": str(e), "status": "Error"}

def calculate_structural_complexity(file_path: str) -> Dict[str, Any]:
    """Standalone wrapper for structural complexity calculation."""
    tool = StructuralComplexityTool()
    return tool.calculate(file_path)
