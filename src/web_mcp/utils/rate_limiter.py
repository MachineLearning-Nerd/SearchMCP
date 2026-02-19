import asyncio
import time
from collections import deque
from typing import Deque

from web_mcp.config import settings


class RateLimiter:
    def __init__(self, max_requests: int | None = None, period_seconds: int | None = None):
        self._max_requests = (
            max_requests if max_requests is not None else settings.RATE_LIMIT_REQUESTS
        )
        self._period_seconds = (
            period_seconds if period_seconds is not None else settings.RATE_LIMIT_PERIOD
        )
        self._timestamps: Deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            self._cleanup()
            while len(self._timestamps) >= self._max_requests:
                wait_time = self._timestamps[0] + self._period_seconds - time.monotonic()
                if wait_time <= 0:
                    break
                self._lock.release()
                try:
                    await asyncio.sleep(wait_time)
                finally:
                    await self._lock.acquire()
                self._cleanup()
            self._timestamps.append(time.monotonic())

    def reset(self) -> None:
        self._timestamps.clear()

    def is_limited(self) -> bool:
        cutoff = time.monotonic() - self._period_seconds
        count = sum(1 for ts in self._timestamps if ts >= cutoff)
        return count >= self._max_requests

    def remaining(self) -> int:
        cutoff = time.monotonic() - self._period_seconds
        count = sum(1 for ts in self._timestamps if ts >= cutoff)
        return max(0, self._max_requests - count)

    def _cleanup(self) -> None:
        cutoff = time.monotonic() - self._period_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
