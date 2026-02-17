import numpy as np
from typing import List, Dict, Any

class SignalFrequencyAnalyzer:
    """
    Detects periodicities and dominant frequencies in event data.
    Optimized with __slots__.
    """
    __slots__ = ()

    def detect_event_periodicity(self, data: List[float]) -> Dict[str, Any]:
        """
        Uses Discrete Fourier Transform (DFT) via NumPy to identify dominant frequencies.
        Returns the top 3 dominant 'frequencies' (cycles per sample).
        """
        arr = np.asarray(data, dtype=float)
        n = len(arr)
        
        if n < 4:
            return {"dominant_frequencies": [], "status": "Insufficient Data", "note": "Need at least 4 data points"}
            
        # Remove DC component (mean centering)
        arr_centered = arr - np.mean(arr)
        
        # Calculate FFT
        fft_res = np.fft.rfft(arr_centered)
        magnitudes = np.abs(fft_res)
        
        # Get frequencies (cycles per sample)
        freqs = np.fft.rfftfreq(n)
        
        # Find peak indices (excluding the very first DC component if it remained)
        peak_indices = np.argsort(magnitudes)[::-1]
        
        top_peaks = []
        for idx in peak_indices:
            if freqs[idx] > 0 and len(top_peaks) < 3:
                top_peaks.append({
                    "frequency": round(float(freqs[idx]), 6),
                    "magnitude": round(float(magnitudes[idx]), 4),
                    "period_samples": round(float(1.0 / freqs[idx]), 2) if freqs[idx] > 0 else 0.0
                })
                
        return {
            "dominant_frequencies": top_peaks,
            "sample_count": n,
            "status": "Success"
        }

def detect_event_periodicity(data: List[float]) -> Dict[str, Any]:
    """Standalone wrapper for periodicity detection."""
    analyzer = SignalFrequencyAnalyzer()
    return analyzer.detect_event_periodicity(data)
