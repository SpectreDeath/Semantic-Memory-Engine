import numpy as np
from typing import List, Union, Dict, Any

class TemporalAnalyzer:
    """
    Analyzes temporal patterns in event logs.
    Optimized with __slots__ for minimal memory footprint.
    """
    __slots__ = ()

    def calculate_burstiness(self, timestamps: Union[List[float], np.ndarray]) -> Dict[str, Any]:
        """
        Calculates the Burstiness Score (B) for a series of events.
        B = (r - 1) / (r + 1), where r = std_dev / mean of inter-event times.
        
        Score ranges from -1 (perfectly periodic) to 1 (extremely bursty).
        0 indicates a memory-less Poisson process.
        """
        if len(timestamps) < 2:
            return {"burstiness_score": 0.0, "status": "Insufficient Data", "note": "Need at least 2 timestamps"}

        try:
            # Sort timestamps to ensure sequence
            ts = np.sort(np.asarray(timestamps, dtype=float))
            
            # Calculate inter-arrival times (intervals)
            intervals = np.diff(ts)
            
            # Avoid division by zero if all intervals are 0 (simultaneous events)
            mean_interval = np.mean(intervals)
            if mean_interval == 0:
                return {"burstiness_score": 1.0, "status": "Success", "note": "All events simultaneous"}
                
            std_interval = np.std(intervals)
            
            # r = coefficient of variation (std_dev / mean)
            r = std_interval / mean_interval
            
            # Burstiness Score formula
            burstiness = (r - 1) / (r + 1)
            
            return {
                "burstiness_score": round(float(burstiness), 6),
                "mean_interval": round(float(mean_interval), 4),
                "std_interval": round(float(std_interval), 4),
                "event_count": len(timestamps),
                "status": "Success"
            }
        except Exception as e:
            return {"error": str(e), "status": "Error"}

def calculate_burstiness(timestamps: List[float]) -> Dict[str, Any]:
    """Standalone wrapper for burstiness calculation."""
    analyzer = TemporalAnalyzer()
    return analyzer.calculate_burstiness(timestamps)
