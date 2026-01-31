import time
import logging
from collections import deque
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Simple sliding window rate limiter.
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self.window = 60 # seconds
        self.clients: Dict[str, deque] = {}

    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for client_id.
        Returns (is_allowed, remaining_requests).
        """
        now = time.time()
        
        if client_id not in self.clients:
            self.clients[client_id] = deque()
        
        requests = self.clients[client_id]
        
        # Remove expired requests
        while requests and requests[0] < now - self.window:
            requests.popleft()
        
        if len(requests) < self.limit:
            requests.append(now)
            return True, self.limit - len(requests)
        
        return False, 0

_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
