"""Typed exception hierarchy for the MOEX ISS integration.

Low-level failures (``httpx`` transport errors, JSON decode errors, unexpected
payload shapes) are caught at the boundary and re-raised as these typed errors,
so callers reason about failures abstractly. Transient subtypes are what the
retry policy keys on.
"""

from __future__ import annotations

__all__ = [
    "MoexClientError",
    "MoexEmptyDataError",
    "MoexError",
    "MoexNotFoundError",
    "MoexRateLimitedError",
    "MoexResponseError",
    "MoexServerError",
    "MoexTimeoutError",
    "MoexTransportError",
]


class MoexError(Exception):
    """Base class for every MOEX integration failure."""


# --- transient (retryable) ---------------------------------------------------
class MoexTransportError(MoexError):
    """Network-level failure talking to ISS (connect/read/connection reset)."""


class MoexTimeoutError(MoexTransportError):
    """A request to ISS exceeded its timeout."""


class MoexServerError(MoexError):
    """ISS returned a 5xx response."""

    def __init__(self, status_code: int, message: str | None = None) -> None:
        self.status_code = status_code
        super().__init__(message or f"MOEX ISS server error: HTTP {status_code}")


class MoexRateLimitedError(MoexError):
    """ISS returned HTTP 429. ``retry_after`` is seconds if provided."""

    def __init__(self, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        super().__init__("MOEX ISS rate limited (HTTP 429)")


# --- permanent (not retryable) -----------------------------------------------
class MoexClientError(MoexError):
    """ISS returned a non-429 4xx response — the request itself is wrong."""

    def __init__(self, status_code: int, message: str | None = None) -> None:
        self.status_code = status_code
        super().__init__(message or f"MOEX ISS client error: HTTP {status_code}")


class MoexNotFoundError(MoexClientError):
    """The requested security/board does not exist on ISS."""

    def __init__(self, message: str | None = None) -> None:
        super().__init__(404, message or "MOEX ISS resource not found")


class MoexResponseError(MoexError):
    """ISS responded, but the payload shape/format was not as expected."""


class MoexEmptyDataError(MoexResponseError):
    """A known ISS block was present but contained no data rows.

    Often legitimate (e.g. candles requested for a non-trading day); services
    decide whether to treat this as an empty result or an error.
    """
