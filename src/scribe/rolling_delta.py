import logging
import numpy as np
from typing import Dict, List, Generator, Any, Tuple
import re

logger = logging.getLogger(__name__)

class RollingDelta:
    """
    Performs sliding-window stylometric analysis (Rolling Delta).
    Tracks authorship signals across a document to detect shifts or collaborative writing.
    """

    def __init__(self):
        """Initialize with access to PyStyl."""
        from src.core.factory import ToolFactory
        try:
            self.pystyl = ToolFactory.create_pystyl_wrapper()
        except Exception as e:
            logger.error(f"RollingDelta failed to load PyStyl: {e}")
            self.pystyl = None

    def generate_windows(self, text: str, window_size: int = 5000, step: int = 500) -> Generator[Tuple[int, str], None, None]:
        """
        Yields text segments based on token count windowing.
        Generator implementation keeps memory footprint low.
        
        Args:
            text: Full text to analyze.
            window_size: Number of tokens per window.
            step: Advancement step in tokens.
            
        Yields:
            Tuple of (start_token_index, window_text)
        """
        # Simple whitespace splitting fits the requested lightweight profile
        # Use regex to be consistent with PyStyl behavior finding "words"
        tokens = re.findall(r'\b\w+\b', text)
        total_tokens = len(tokens)
        
        if total_tokens < window_size:
            logger.warning(f"Text length ({total_tokens}) shorter than window size ({window_size}). Returning single window.")
            yield (0, text)
            return

        current_idx = 0
        while current_idx + window_size <= total_tokens:
            end_idx = current_idx + window_size
            window_tokens = tokens[current_idx:end_idx]
            # Simple reconstruction (loses original whitespace formatting but sufficient for stylometry)
            yield (current_idx, " ".join(window_tokens))
            current_idx += step

    def analyze_rolling_delta(self, target_text: str, candidates: Dict[str, str], window_size: int = 5000, step: int = 500) -> Dict[str, Any]:
        """
        Analyzes the target text in windows against candidate profiles.
        
        Args:
            target_text: The document to analyze.
            candidates: Dictionary of {AuthorName: ReferenceText}.
            window_size: Tokens per window.
            step: Tokens to advance.
            
        Returns:
            JSON-compatible dict with 'series', 'volatility', and 'windows'.
        """
        if not self.pystyl:
            return {"error": "PyStylWrapper not initialized"}

        if not candidates:
            return {"error": "No candidates provided"}

        results = {
            "series": {author: [] for author in candidates},
            "windows": [],
            "volatility": {}
        }

        # Cache candidate vectors calculation could be optimized inside PyStyl, 
        # but for now we call compare_texts directly which recalculates.
        # Given strict memory limits, recalculation per window is actually safer than caching huge matrices if windows are many.
        
        logger.info(f"🔄 Starting Rolling Delta (Window: {window_size}, Step: {step})")
        
        for start_idx, window_text in self.generate_windows(target_text, window_size, step):
            label = f"{start_idx}-{start_idx + window_size}"
            results["windows"].append(start_idx) # Use integer index for x-axis charting
            
            for author, ref_text in candidates.items():
                # Using Chi-squared as a proxy for Delta distance in this lightweight version
                distance = self.pystyl.compare_texts(window_text, ref_text, top_n=100)
                results["series"][author].append(distance)

        # Calculate Volatility (Std Dev of distance)
        for author, distances in results["series"].items():
            if distances:
                results["volatility"][author] = float(np.std(distances))
            else:
                results["volatility"][author] = 0.0

        return results
