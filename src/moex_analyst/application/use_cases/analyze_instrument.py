"""Use case: analyse one instrument end-to-end.

Orchestrates the existing services — MOEX candle/quote/instrument services, the
deterministic :class:`AnalysisEngine` and the :class:`AlertDetector` — into a
single :class:`InstrumentAnalysis`. No presentation concerns; no fake data.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from moex_analyst.application.exceptions import (
    DataSourceError,
    EmptyDataError,
    InstrumentNotFoundError,
    RateLimitError,
    TickerNotFoundError,
)
from moex_analyst.application.use_cases._common import lookback_date_from
from moex_analyst.application.use_cases.dto import InstrumentAnalysis
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.moex import (
    MoexEmptyDataError,
    MoexError,
    MoexNotFoundError,
    MoexRateLimitedError,
    resolve_instrument,
)
from moex_analyst.infrastructure.moex.mapping import candle_series_to_domain

if TYPE_CHECKING:
    from moex_analyst.domain.alerts import AlertDetector
    from moex_analyst.domain.analysis import AnalysisEngine
    from moex_analyst.infrastructure.moex import (
        CandleService,
        InstrumentService,
        QuoteService,
    )

__all__ = ["AnalyzeInstrumentUseCase"]


def _translate_moex_error(exc: BaseException) -> BaseException:
    """Map known MOEX infrastructure exceptions to application-level exceptions."""
    mapping = (
        (MoexNotFoundError, InstrumentNotFoundError),
        (MoexEmptyDataError, EmptyDataError),
        (MoexRateLimitedError, RateLimitError),
        (MoexError, DataSourceError),
    )
    for src_type, dst_type in mapping:
        if isinstance(exc, src_type):
            return dst_type(str(exc))
    return exc


class AnalyzeInstrumentUseCase:
    """Fetch candles for a ticker, analyse them and detect alerts."""

    def __init__(
        self,
        candles: CandleService,
        quotes: QuoteService,
        instruments: InstrumentService,
        engine: AnalysisEngine,
        detector: AlertDetector,
    ) -> None:
        self._candles = candles
        self._quotes = quotes
        self._instruments = instruments
        self._engine = engine
        self._detector = detector

    async def execute(
        self,
        ticker: str,
        timeframe: Timeframe = Timeframe.D1,
    ) -> InstrumentAnalysis:
        """Analyse ``ticker`` at ``timeframe``.

        Raises:
            KeyError: ``ticker`` is not a tracked instrument.
            InsufficientDataError: too few candles to analyse.
            MoexError: the candle fetch (the required input) failed.

        Instrument metadata and the live quote are *best-effort*: if either ISS
        call fails the field is left ``None`` and analysis still proceeds.
        """
        try:
            ref = resolve_instrument(ticker)
        except KeyError as exc:
            raise TickerNotFoundError(str(exc)) from exc
        date_from = lookback_date_from(timeframe)

        series_dto, instrument, quote = await asyncio.gather(
            self._candles.get_candles(ref.ticker, timeframe, date_from=date_from),
            self._instruments.get_instrument(ref.ticker),
            self._quotes.get_quote(ref.ticker),
            return_exceptions=True,
        )
        if isinstance(series_dto, BaseException):
            raise _translate_moex_error(series_dto)

        domain_series = candle_series_to_domain(series_dto)
        analysis = self._engine.analyse(domain_series)  # InsufficientDataError
        alerts = tuple(self._detector.detect(analysis))

        return InstrumentAnalysis(
            ticker=ref.ticker,
            timeframe=timeframe,
            analysis=analysis,
            alerts=alerts,
            instrument=None if isinstance(instrument, BaseException) else instrument,
            quote=None if isinstance(quote, BaseException) else quote,
        )
