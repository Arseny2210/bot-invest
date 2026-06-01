"""Low-level async HTTP client for the MOEX ISS API.

Owns the single :class:`httpx.AsyncClient`, applies the rate limiter before
every request (including retries), runs the tenacity retry policy, and
translates HTTP/transport failures into the typed :mod:`errors` hierarchy.
It returns decoded JSON; turning that into DTOs is the services' job.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import httpx
from loguru import logger

from moex_analyst.infrastructure.moex.errors import (
    MoexClientError,
    MoexNotFoundError,
    MoexRateLimitedError,
    MoexResponseError,
    MoexServerError,
    MoexTimeoutError,
    MoexTransportError,
)
from moex_analyst.infrastructure.moex.transport.rate_limiter import TokenBucketRateLimiter
from moex_analyst.infrastructure.moex.transport.retry import build_retrying

if TYPE_CHECKING:
    from types import TracebackType

    from tenacity import RetryCallState

    from moex_analyst.core.settings import MoexSettings

__all__ = ["MoexHttpClient"]

# ISS query params shared by every request: drop metadata, return JSON.
_COMMON_PARAMS: dict[str, str] = {"iss.meta": "off"}


class MoexHttpClient:
    """Async ISS transport. Use as an async context manager or manage via DI.

    The client is reusable and concurrency-safe (httpx pools connections); a
    single instance should be shared process-wide.
    """

    def __init__(
        self,
        settings: MoexSettings,
        *,
        client: httpx.AsyncClient | None = None,
        rate_limiter: TokenBucketRateLimiter | None = None,
    ) -> None:
        self._settings = settings
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=settings.base_url,
            timeout=httpx.Timeout(
                settings.request_timeout,
                connect=settings.connect_timeout,
            ),
            headers={"User-Agent": settings.user_agent},
            follow_redirects=True,
        )
        self._limiter = rate_limiter or TokenBucketRateLimiter(
            rate=settings.rate_limit_rps,
            burst=settings.rate_limit_burst,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying client if this instance created it."""
        if self._owns_client:
            await self._client.aclose()

    async def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """GET ``path`` (relative to base) and return decoded JSON.

        Applies rate limiting + retries. Raises a typed :class:`MoexError`
        subclass on failure.
        """
        retrying = build_retrying(
            max_attempts=self._settings.max_retries + 1,
            backoff_base=self._settings.backoff_base,
            before_sleep=_log_retry,
        )
        merged = {**_COMMON_PARAMS, **(params or {})}

        async for attempt in retrying:
            with attempt:
                await self._limiter.acquire()
                return await self._request(path, merged)
        # AsyncRetrying(reraise=True) guarantees we either return or raise above.
        raise AssertionError("unreachable: retrying exhausted without raising")

    async def _request(self, path: str, params: dict[str, Any]) -> Any:
        try:
            response = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise MoexTimeoutError(f"Timeout requesting {path}") from exc
        except httpx.TransportError as exc:
            raise MoexTransportError(f"Transport error requesting {path}: {exc}") from exc

        self._raise_for_status(response)

        try:
            return response.json()
        except ValueError as exc:
            raise MoexResponseError(f"ISS returned non-JSON body for {path}") from exc

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        status = response.status_code
        if status < 400:
            return
        if status == 429:
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
            raise MoexRateLimitedError(retry_after)
        if status == 404:
            raise MoexNotFoundError(f"ISS 404 for {response.request.url}")
        if 400 <= status < 500:
            raise MoexClientError(status)
        raise MoexServerError(status)


def _parse_retry_after(raw: str | None) -> float | None:
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _log_retry(retry_state: RetryCallState) -> None:
    """Structured-log a retry attempt before sleeping."""
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.bind(service="moex").warning(
        "MOEX ISS request failed (attempt {}), retrying: {}",
        retry_state.attempt_number,
        type(exc).__name__ if exc else "unknown",
    )
