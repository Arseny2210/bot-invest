"""Unit tests for structure, levels, volume, trend and probability."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from moex_analyst.domain.analysis.enums import (
    LevelKind,
    StructurePoint,
    TrendDirection,
    TrendStrength,
    VolumeCondition,
)
from moex_analyst.domain.analysis.levels import detect_levels
from moex_analyst.domain.analysis.probability import estimate_probabilities
from moex_analyst.domain.analysis.structure import detect_structure
from moex_analyst.domain.analysis.trend import detect_trend
from moex_analyst.domain.analysis.volume import classify_volume

_BASE = datetime(2024, 1, 1, tzinfo=UTC)


def _times(n: int) -> list[datetime]:
    return [_BASE + timedelta(hours=i) for i in range(n)]


def _dec(values: list[float]) -> list[Decimal]:
    return [Decimal(str(v)) for v in values]


class TestStructure:
    def test_zigzag_produces_swings(self) -> None:
        # clear alternating peaks/troughs, window=1
        highs = _dec([1, 3, 1, 4, 1, 5, 1])
        lows = _dec([0, 2, 0, 3, 0, 4, 0])
        state = detect_structure(highs, lows, _times(7), window=1)
        assert len(state.swings) > 0
        # rising peaks -> last high should be HH
        assert state.last_high == StructurePoint.HH

    def test_lower_highs_detected(self) -> None:
        highs = _dec([5, 9, 5, 7, 4, 5, 3])
        lows = _dec([1, 4, 1, 3, 0, 2, 0])
        state = detect_structure(highs, lows, _times(7), window=1)
        # peaks 9 then 7 then 5 -> lower highs
        assert state.last_high == StructurePoint.LH
        assert state.last_low == StructurePoint.LL

    def test_too_short_is_empty(self) -> None:
        state = detect_structure(_dec([1, 2]), _dec([0, 1]), _times(2), window=2)
        assert state.swings == ()


class TestLevels:
    def test_clusters_nearby_lows_into_support(self) -> None:
        highs = _dec([10, 12, 10, 12.02, 10, 12.01, 10])
        lows = _dec([8, 9, 8.01, 9, 7.99, 9, 8])
        state = detect_structure(highs, lows, _times(7), window=1)
        supports, resistances = detect_levels(state.swings, last_index=6)
        assert all(s.kind is LevelKind.SUPPORT for s in supports)
        assert all(r.kind is LevelKind.RESISTANCE for r in resistances)
        # the ~8 lows should cluster -> a support with >1 touch exists
        assert any(s.touches >= 2 for s in supports)

    def test_strength_in_unit_interval(self) -> None:
        highs = _dec([10, 14, 10, 13, 10, 15, 10])
        lows = _dec([8, 9, 8, 9, 8, 9, 8])
        state = detect_structure(highs, lows, _times(7), window=1)
        supports, resistances = detect_levels(state.swings, last_index=6)
        for lvl in (*supports, *resistances):
            assert 0.0 <= lvl.strength <= 1.0


class TestVolume:
    def test_unknown_when_short(self) -> None:
        assert classify_volume([100] * 5, window=20) is VolumeCondition.UNKNOWN

    def test_unknown_when_all_zero(self) -> None:
        assert classify_volume([0] * 25, window=20) is VolumeCondition.UNKNOWN

    def test_high_spike(self) -> None:
        vols = [100] * 24 + [10_000]
        assert classify_volume(vols, window=20) is VolumeCondition.HIGH

    def test_normal_steady(self) -> None:
        # Latest volume sits at the window mean (z ~ 0) -> NORMAL.
        vols = [90, 110] * 12 + [100]
        assert classify_volume(vols, window=20) is VolumeCondition.NORMAL


class TestTrend:
    def test_uptrend(self, uptrend_closes: list[float]) -> None:
        structure = detect_structure(
            _dec([c + 1 for c in uptrend_closes]),
            _dec([c - 1 for c in uptrend_closes]),
            _times(len(uptrend_closes)),
            window=2,
        )
        trend = detect_trend(uptrend_closes, structure)
        assert trend.direction is TrendDirection.UP
        assert trend.strength is TrendStrength.STRONG
        assert trend.score > 0

    def test_downtrend(self, downtrend_closes: list[float]) -> None:
        structure = detect_structure(
            _dec([c + 1 for c in downtrend_closes]),
            _dec([c - 1 for c in downtrend_closes]),
            _times(len(downtrend_closes)),
            window=2,
        )
        trend = detect_trend(downtrend_closes, structure)
        assert trend.direction is TrendDirection.DOWN
        assert trend.score < 0

    def test_flat_is_sideways(self, flat_closes: list[float]) -> None:
        structure = detect_structure(
            _dec([c + 1 for c in flat_closes]),
            _dec([c - 1 for c in flat_closes]),
            _times(len(flat_closes)),
            window=2,
        )
        trend = detect_trend(flat_closes, structure)
        assert trend.direction is TrendDirection.SIDEWAYS


class TestProbability:
    def _structure(self, closes: list[float], window: int = 2) -> object:
        return detect_structure(
            _dec([c + 1 for c in closes]),
            _dec([c - 1 for c in closes]),
            _times(len(closes)),
            window=window,
        )

    def test_sums_to_one(self, uptrend_closes: list[float]) -> None:
        structure = self._structure(uptrend_closes)
        trend = detect_trend(uptrend_closes, structure)
        dist = estimate_probabilities(trend, structure, 65.0, VolumeCondition.HIGH)
        assert abs(dist.bullish + dist.bearish + dist.sideways - 1.0) < 1e-9

    def test_bullish_dominates_in_uptrend(self, uptrend_closes: list[float]) -> None:
        structure = self._structure(uptrend_closes)
        trend = detect_trend(uptrend_closes, structure)
        dist = estimate_probabilities(trend, structure, 65.0, VolumeCondition.HIGH)
        assert dist.bullish > dist.bearish
        assert dist.bullish > dist.sideways

    def test_bearish_dominates_in_downtrend(self, downtrend_closes: list[float]) -> None:
        structure = self._structure(downtrend_closes)
        trend = detect_trend(downtrend_closes, structure)
        dist = estimate_probabilities(trend, structure, 35.0, VolumeCondition.HIGH)
        assert dist.bearish > dist.bullish

    def test_no_negative_or_certain(self, uptrend_closes: list[float]) -> None:
        structure = self._structure(uptrend_closes)
        trend = detect_trend(uptrend_closes, structure)
        dist = estimate_probabilities(trend, structure, 99.0, VolumeCondition.HIGH)
        for p in (dist.bullish, dist.bearish, dist.sideways):
            assert 0.0 < p < 1.0

    def test_determinism(self, uptrend_closes: list[float]) -> None:
        structure = self._structure(uptrend_closes)
        trend = detect_trend(uptrend_closes, structure)
        a = estimate_probabilities(trend, structure, 55.0, VolumeCondition.NORMAL)
        b = estimate_probabilities(trend, structure, 55.0, VolumeCondition.NORMAL)
        assert a == b
