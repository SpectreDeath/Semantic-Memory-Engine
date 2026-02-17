import numpy as np
import hashlib
from typing import List, Dict, Any

class SimHash:
    """
    Locality Sensitive Hashing (SimHash) for high-speed near-duplicate detection.
    Optimized with __slots__ for memory efficiency.
    """
    __slots__ = ['hash_size']

    def __init__(self, hash_size: int = 64):
        self.hash_size = hash_size

    def calculate(self, tokens: List[str]) -> int:
        """Vectorized SimHash calculation using NumPy."""
        if not tokens:
            return 0
        
        # Initialize the v-vector (fingerprint accumulator)
        v = np.zeros(self.hash_size, dtype=int)
        
        for token in tokens:
            # Create a traditional 64-bit hash for the token using MD5
            h = int(hashlib.md5(token.encode('utf-8')).hexdigest()[:16], 16)
            
            for i in range(self.hash_size):
                bit = (h >> i) & 1
                if bit:
                    v[i] += 1
                else:
                    v[i] -= 1
        
        # Build the final hash from the fingerprint
        ans = 0
        for i in range(self.hash_size):
            if v[i] >= 0:
                ans |= (1 << i)
        return int(ans)

    def distance(self, hash1: int, hash2: int) -> int:
        """Calculate Hamming distance between two SimHashes."""
        x = hash1 ^ hash2
        return bin(x).count('1')

def calculate_simhash(tokens: List[str], hash_size: int = 64) -> int:
    """
    Standalone function to calculate SimHash for a token list.
    """
    sh = SimHash(hash_size)
    return sh.calculate(tokens)

def calculate_simhash_similarity(h1: int, h2: int, hash_size: int = 64) -> float:
    """
    Returns a similarity score [0, 1] based on Hamming distance.
    """
    sh = SimHash(hash_size)
    dist = sh.distance(h1, h2)
    return 1.0 - (dist / hash_size)
