import numpy as np
from typing import List, Dict, Any, Union

class EntropyMapper:
    """
    Analyzes spatial entropy across byte-streams.
    Optimized with __slots__.
    """
    __slots__ = ()

    def calculate_shannon_entropy(self, data: np.ndarray) -> float:
        """Calculates the Shannon entropy of a byte array."""
        if len(data) == 0:
            return 0.0
        _, counts = np.unique(data, return_counts=True)
        probs = counts / len(data)
        return -np.sum(probs * np.log2(probs))

    def map_stream_entropy(self, stream: Union[bytes, List[int], np.ndarray], window_size: int = 256, step_size: int = 64) -> Dict[str, Any]:
        """
        Implements a Sliding Window Shannon Entropy across a byte-stream.
        Returns an array of entropy scores representing different sections of the stream.
        """
        data = np.frombuffer(stream, dtype=np.uint8) if isinstance(stream, bytes) else np.asarray(stream, dtype=np.uint8)
        n = len(data)
        
        if n < window_size:
            # Fallback to single entropy score if stream is smaller than window
            return {
                "entropy_map": [float(self.calculate_shannon_entropy(data))],
                "window_size": window_size,
                "step_size": step_size,
                "status": "Single Window (Stream < Window)"
            }
            
        entropy_scores = []
        for i in range(0, n - window_size + 1, step_size):
            window = data[i:i + window_size]
            entropy_scores.append(float(self.calculate_shannon_entropy(window)))
            
        return {
            "entropy_map": [round(s, 4) for s in entropy_scores],
            "window_size": window_size,
            "step_size": step_size,
            "mean_entropy": round(float(np.mean(entropy_scores)), 4),
            "max_entropy": round(float(np.max(entropy_scores)), 4),
            "status": "Success"
        }

def map_stream_entropy(stream: Union[bytes, List[int]], window_size: int = 256) -> Dict[str, Any]:
    """Standalone wrapper for sliding window entropy mapping."""
    mapper = EntropyMapper()
    return mapper.map_stream_entropy(stream, window_size=window_size)
