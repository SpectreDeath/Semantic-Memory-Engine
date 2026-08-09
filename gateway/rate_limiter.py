from __future__ import annotations

import logging
import threading
import time
from collections import deque

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
        self.clients: dict[str, deque] = {}
        self._lock = threading.Lock()

    def is_allowed(
        self,
        client_id: str,
        mcp_method: str | None = None,
        mcp_name: str | None = None,
    ) -> tuple[bool, int]:
        """
        Check if request is allowed for client_id.
        Supports MCP 2026-07-28 HTTP routing headers (MCP-Method and MCP-Name).

        Returns (is_allowed, remaining_requests).
        Thread-safe via a lock on the shared clients dict.
        """
        now = time.time()

        # Build granular rate limiting key if headers are provided
        key = client_id
        if mcp_method:
            key += f":{mcp_method}"
        if mcp_name:
            key += f":{mcp_name}"

        with self._lock:
            if key not in self.clients:
                self.clients[key] = deque()

            requests = self.clients[key]

            # Remove expired requests outside the sliding window
            while requests and requests[0] < now - self.window:
                requests.popleft()

            if len(requests) < self.limit:
                requests.append(now)
                return True, self.limit - len(requests)

        return False, 0


_rate_limiter: RateLimiter | None = None
_rate_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    with _rate_limiter_lock:
        if _rate_limiter is None:
            _rate_limiter = RateLimiter()
    return _rate_limiter
