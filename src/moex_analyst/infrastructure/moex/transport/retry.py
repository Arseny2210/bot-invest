"""Tenacity retry policy for MOEX ISS requests.

Only transient failures are retried: timeouts, transport errors, 5xx, and 429.
Permanent failures (4xx other than 429, malformed payloads) propagate
immediately. Backoff is exponential with jitter to avoid thundering herds; a
429's ``Retry-After`` is honored ahead of the computed backoff.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from moex_analyst.infrastructure.moex.errors import (
    MoexRateLimitedError,
    MoexServerError,
    MoexTimeoutError,
    MoexTransportError,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from tenacity import RetryCallState

__all__ = ["RETRYABLE_EXCEPTIONS", "build_retrying"]

# Exception types that justify a retry.
RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    MoexTimeoutError,
    MoexTransportError,
    MoexServerError,
    MoexRateLimitedError,
)


def build_retrying(
    *,
    max_attempts: int,
    backoff_base: float,
    before_sleep: Callable[[RetryCallState], None] | None = None,
) -> AsyncRetrying:
    """Construct an :class:`AsyncRetrying` configured for ISS requests.

    Args:
        max_attempts: total attempts (1 = no retries).
        backoff_base: initial backoff seconds for the exponential schedule.
        before_sleep: optional hook invoked before each backoff sleep
            (used for structured logging of retries).
    """
    base_wait = wait_exponential_jitter(initial=backoff_base, max=30.0)

    def wait(retry_state: RetryCallState) -> float:
        """Honor a 429 ``Retry-After`` else fall back to exponential jitter."""
        computed = base_wait(retry_state)
        outcome = retry_state.outcome
        if outcome is not None and outcome.failed:
            exc = outcome.exception()
            if isinstance(exc, MoexRateLimitedError) and exc.retry_after is not None:
                return max(exc.retry_after, computed)
        return computed

    return AsyncRetrying(
        stop=stop_after_attempt(max(1, max_attempts)),
        wait=wait,
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep,
        reraise=True,
    )
