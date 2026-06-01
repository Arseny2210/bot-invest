"""Async token-bucket rate limiter protecting the ISS API from bursts.

A single shared instance (app-scoped) is acquired before every HTTP request,
including retries, so the effective request rate to ISS stays bounded.
"""

from __future__ import annotations

import asyncio
import time

__all__ = ["TokenBucketRateLimiter"]


class TokenBucketRateLimiter:
    """Classic token bucket with async ``acquire``.

    Tokens refill continuously at ``rate`` per second up to ``burst`` capacity.
    :meth:`acquire` waits until a token is available, then consumes one. A lock
    serializes the check-and-consume so concurrent callers share fairly.
    """

    def __init__(self, rate: float, burst: int) -> None:
        if rate <= 0:
            raise ValueError("rate must be positive")
        if burst < 1:
            raise ValueError("burst must be >= 1")
        self._rate = rate
        self._capacity = float(burst)
        self._tokens = float(burst)
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._updated
        if elapsed > 0:
            self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
            self._updated = now

    async def acquire(self) -> None:
        """Block until one token is available, then consume it."""
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                deficit = 1.0 - self._tokens
                wait_for = deficit / self._rate
            # Sleep outside the lock so refills can be observed fairly.
            await asyncio.sleep(wait_for)
