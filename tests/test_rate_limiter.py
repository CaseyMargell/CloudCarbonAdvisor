import asyncio
import time
from unittest.mock import patch

import pytest

from rate_limiter import RateLimiter


@pytest.fixture
def limiter():
    return RateLimiter(limit=3, window_seconds=60)


@pytest.mark.asyncio
class TestRateLimiter:
    async def test_allows_under_limit(self, limiter):
        allowed, _ = await limiter.check("1.2.3.4")
        assert allowed is True

    async def test_allows_up_to_limit(self, limiter):
        for _ in range(3):
            allowed, _ = await limiter.check("1.2.3.4")
            assert allowed is True

    async def test_blocks_over_limit(self, limiter):
        for _ in range(3):
            await limiter.check("1.2.3.4")

        allowed, retry_after = await limiter.check("1.2.3.4")
        assert allowed is False
        assert retry_after > 0

    async def test_different_ips_independent(self, limiter):
        for _ in range(3):
            await limiter.check("1.1.1.1")

        # Different IP should still be allowed
        allowed, _ = await limiter.check("2.2.2.2")
        assert allowed is True

    async def test_window_expiry(self, limiter):
        # Fill up the limit
        for _ in range(3):
            await limiter.check("1.2.3.4")

        # Simulate time passing beyond window
        with patch("rate_limiter.time") as mock_time:
            mock_time.time.return_value = time.time() + 61
            allowed, _ = await limiter.check("1.2.3.4")
            assert allowed is True

    async def test_retry_after_is_positive(self, limiter):
        for _ in range(3):
            await limiter.check("1.2.3.4")

        _, retry_after = await limiter.check("1.2.3.4")
        assert retry_after > 0
        assert retry_after <= 61  # Should be at most window_seconds + 1

    async def test_concurrent_safety(self):
        """Verify asyncio.Lock prevents race conditions."""
        limiter = RateLimiter(limit=5, window_seconds=60)

        # Fire 10 concurrent requests from the same IP
        results = await asyncio.gather(*[limiter.check("1.2.3.4") for _ in range(10)])
        allowed_count = sum(1 for allowed, _ in results if allowed)
        assert allowed_count == 5  # Exactly the limit, no more
