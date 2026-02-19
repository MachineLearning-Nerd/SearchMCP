import asyncio
import pytest

from web_mcp.utils.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_create_rate_limiter(self):
        limiter = RateLimiter(max_requests=10, period_seconds=60)
        assert limiter.remaining() == 10
        assert limiter.is_limited() is False

    def test_reset(self):
        limiter = RateLimiter(max_requests=2, period_seconds=60)
        limiter._timestamps.append(1.0)
        limiter._timestamps.append(2.0)
        limiter.reset()
        assert limiter.remaining() == 2

    @pytest.mark.asyncio
    async def test_acquire_under_limit(self):
        limiter = RateLimiter(max_requests=3, period_seconds=60)

        await limiter.acquire()
        await limiter.acquire()
        await limiter.acquire()

        assert limiter.remaining() == 0
        assert limiter.is_limited() is True

    @pytest.mark.asyncio
    async def test_remaining_decreases(self):
        limiter = RateLimiter(max_requests=5, period_seconds=60)

        assert limiter.remaining() == 5

        await limiter.acquire()
        assert limiter.remaining() == 4

        await limiter.acquire()
        assert limiter.remaining() == 3

    @pytest.mark.asyncio
    async def test_concurrent_acquire(self):
        limiter = RateLimiter(max_requests=5, period_seconds=60)

        async def acquire_one():
            await limiter.acquire()

        await asyncio.gather(*[acquire_one() for _ in range(5)])

        assert limiter.is_limited() is True
        assert limiter.remaining() == 0
