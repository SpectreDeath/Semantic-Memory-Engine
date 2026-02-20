import time
import threading
import logging
from collections import deque
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe sliding window rate limiter.

    NOTE: There is a separate rate limiter in src/api/rate_limiter.py for the
    operator API layer.  These two run independently on their respective ports
    (gateway on 8089 / MCP, operator on 8000 / HTTP).  A future consolidation
    into a shared Redis-backed limiter would unify enforcement across both.
    """

    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self.window = 60  # seconds
        self.clients: Dict[str, deque] = {}
        self._lock = threading.Lock()

    def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        Check if request is allowed for client_id.
        Returns (is_allowed, remaining_requests).
        Thread-safe via a lock on the shared clients dict.
        """
        now = time.time()

        with self._lock:
            if client_id not in self.clients:
                self.clients[client_id] = deque()

            requests = self.clients[client_id]

            # Remove expired requests outside the sliding window
            while requests and requests[0] < now - self.window:
                requests.popleft()

            if len(requests) < self.limit:
                requests.append(now)
                return True, self.limit - len(requests)

        return False, 0


_rate_limiter: Optional[RateLimiter] = None
_rate_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    with _rate_limiter_lock:
        if _rate_limiter is None:
            _rate_limiter = RateLimiter()
    return _rate_limiter
