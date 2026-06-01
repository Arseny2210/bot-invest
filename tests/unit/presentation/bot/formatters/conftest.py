"""Builders for formatter unit tests.

Construct the application DTOs (and the domain/MOEX values they wrap) directly,
so the pure formatters can be exercised without any network or DI.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from moex_analyst.application.use_cases.dto import (
    InstrumentAnalysis,
    MarketOverview,
    ScoredInstrument,
    WatchedInstrument,
    Watchlist,
)
from moex_analyst.domain.alerts import Alert, AlertDirection, AlertSeverity, AlertType
from moex_analyst.domain.analysis.enums import (
    LevelKind,
    StructurePoint,
    TrendDirection,
    TrendStrength,
    VolumeCondition,
)
from moex_analyst.domain.analysis.result import (
    AnalysisResult,
    IndicatorSnapshot,
    PriceLevel,
    ProbabilityDistribution,
    StructureState,
    TrendState,
)
from moex_analyst.domain.market.timeframe import Timeframe
from moex_analyst.infrastructure.moex import InstrumentDTO, MarketType, QuoteDTO

_AS_OF = datetime(2024, 6, 1, 15, 30, tzinfo=UTC)
_UNSET = object()  # distinguishes "argument omitted" from an explicit ``None``


def make_alert(
    *,
    type_: AlertType = AlertType.RSI_OVERBOUGHT,
    direction: AlertDirection = AlertDirection.BEARISH,
    severity: AlertSeverity = AlertSeverity.WARNING,
    message: str = "RSI14 72 is overbought",
    ticker: str = "SNGS",
) -> Alert:
    return Alert(
        type=type_,
        direction=direction,
        severity=severity,
        score=0.6,
        message=message,
        ticker=ticker,
        timeframe=Timeframe.D1,
        as_of=_AS_OF,
    )


def make_analysis_result(
    *,
    ticker: str = "SNGS",
    direction: TrendDirection = TrendDirection.UP,
    bullish: float = 0.6,
    bearish: float = 0.25,
    sideways: float = 0.15,
    with_levels: bool = True,
    with_indicators: bool = True,
) -> AnalysisResult:
    supports = (
        PriceLevel(kind=LevelKind.SUPPORT, price=Decimal("24.50"), touches=3, strength=0.8),
    ) if with_levels else ()
    resistances = (
        PriceLevel(kind=LevelKind.RESISTANCE, price=Decimal("28.10"), touches=2, strength=0.6),
    ) if with_levels else ()
    indicators = IndicatorSnapshot(
        rsi14=Decimal("72.00"),
        atr14=Decimal("0.5400"),
        ema20=Decimal("26.1200"),
        ema50=Decimal("25.4000"),
    ) if with_indicators else IndicatorSnapshot()
    return AnalysisResult(
        ticker=ticker,
        timeframe=Timeframe.D1,
        as_of=_AS_OF,
        candles_analysed=120,
        trend=TrendState(direction=direction, strength=TrendStrength.STRONG, score=0.72),
        structure=StructureState(
            swings=(), last_high=StructurePoint.HH, last_low=StructurePoint.HL,
        ),
        support_levels=supports,
        resistance_levels=resistances,
        volume_condition=VolumeCondition.HIGH,
        indicators=indicators,
        probabilities=ProbabilityDistribution(
            bullish=bullish, bearish=bearish, sideways=sideways,
        ),
    )


def make_instrument_dto(*, ticker: str = "SNGS", shortname: str = "Сургут") -> InstrumentDTO:
    return InstrumentDTO(
        ticker=ticker,
        secid=ticker,
        shortname=shortname,
        market_type=MarketType.SHARES,
        board="TQBR",
        currency="RUB",
        lot_size=10,
        decimals=2,
    )


def make_quote_dto(*, last: Decimal | None = Decimal("26.40")) -> QuoteDTO:
    return QuoteDTO(
        secid="SNGS",
        board="TQBR",
        last=last,
        open=Decimal("25.80"),
        volume_today=1_000_000,
    )


def make_instrument_analysis(
    *,
    ticker: str = "SNGS",
    alerts: tuple[Alert, ...] | None = None,
    instrument: InstrumentDTO | None | object = _UNSET,
    quote: QuoteDTO | None | object = _UNSET,
) -> InstrumentAnalysis:
    resolved_instrument = (
        make_instrument_dto(ticker=ticker) if instrument is _UNSET else instrument
    )
    resolved_quote = make_quote_dto() if quote is _UNSET else quote
    return InstrumentAnalysis(
        ticker=ticker,
        timeframe=Timeframe.D1,
        analysis=make_analysis_result(ticker=ticker),
        alerts=alerts if alerts is not None else (make_alert(ticker=ticker),),
        instrument=resolved_instrument,  # type: ignore[arg-type]
        quote=resolved_quote,  # type: ignore[arg-type]
    )


def make_market_overview(
    *,
    tickers: tuple[str, ...] = ("SNGS", "VTBR", "SGZH"),
    failed: tuple[str, ...] = (),
) -> MarketOverview:
    scored = []
    for i, ticker in enumerate(tickers):
        bullish = 0.7 - i * 0.2
        bearish = 0.2 + i * 0.2
        analysis = make_analysis_result(
            ticker=ticker,
            direction=TrendDirection.UP if bullish >= bearish else TrendDirection.DOWN,
            bullish=bullish,
            bearish=bearish,
            sideways=round(1.0 - bullish - bearish, 6),
        )
        scored.append(
            ScoredInstrument(analysis=analysis, alert_count=i, score=bullish - bearish),
        )
    scored.sort(key=lambda s: s.score, reverse=True)
    return MarketOverview(timeframe=Timeframe.D1, scored=tuple(scored), failed=failed)


def make_watchlist() -> Watchlist:
    return Watchlist(
        instruments=(
            WatchedInstrument(ticker="IMOEX", secid="IMOEX", market_type=MarketType.INDEX),
            WatchedInstrument(ticker="SNGS", secid="SNGS", market_type=MarketType.SHARES),
        ),
    )
