import asyncio
import time


class RateLimiter:
    """Fixed-window rate limiter with asyncio safety."""

    def __init__(self, limit: int, window_seconds: int = 3600):
        self._limit = limit
        self._window = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def check(self, ip: str) -> tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, seconds_until_retry)."""
        async with self._lock:
            now = time.time()
            cutoff = now - self._window

            # Get or create entry, filter expired
            timestamps = [t for t in self._requests.get(ip, []) if t > cutoff]
            self._requests[ip] = timestamps

            if len(timestamps) >= self._limit:
                oldest = timestamps[0]
                retry_after = int(oldest + self._window - now) + 1
                return False, retry_after

            timestamps.append(now)
            self._requests[ip] = timestamps

            # Inline cleanup: remove IPs with no recent requests
            # Only do this occasionally to avoid overhead
            if len(self._requests) > 100:
                self._requests = {
                    k: [t for t in v if t > cutoff]
                    for k, v in self._requests.items()
                    if any(t > cutoff for t in v)
                }

            return True, 0
