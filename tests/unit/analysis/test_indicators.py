"""Unit tests for deterministic indicators."""

from __future__ import annotations

import pytest

from moex_analyst.domain.analysis.indicators import (
    atr,
    ema,
    ema_last,
    rma,
    rsi,
    rsi_last,
    sma,
    true_ranges,
)


class TestSMA:
    def test_returns_none_when_too_short(self) -> None:
        assert sma([1.0, 2.0], 3) is None

    def test_average_of_last_period(self) -> None:
        # SMA of the last 2 values: (3 + 4) / 2 = 3.5
        assert sma([1.0, 2.0, 3.0, 4.0], 2) == 3.5

    def test_rejects_nonpositive_period(self) -> None:
        with pytest.raises(ValueError, match="period must be positive"):
            sma([1.0], 0)


class TestEMA:
    def test_empty_when_too_short(self) -> None:
        assert ema([1.0, 2.0], 3) == []

    def test_seed_is_sma_of_first_window(self) -> None:
        # First EMA value must equal the SMA of the first `period` samples.
        series = ema([2.0, 4.0, 6.0, 8.0], 2)
        assert series[0] == pytest.approx(3.0)  # SMA(2,4)

    def test_constant_series_is_constant(self) -> None:
        series = ema([5.0] * 10, 3)
        assert all(v == pytest.approx(5.0) for v in series)

    def test_known_values(self) -> None:
        # multiplier = 2/(3+1) = 0.5; seed = SMA(1,2,3) = 2
        # next: (4-2)*0.5+2 = 3 ; next: (5-3)*0.5+3 = 4
        assert ema([1.0, 2.0, 3.0, 4.0, 5.0], 3) == pytest.approx([2.0, 3.0, 4.0])

    def test_ema_last_none_when_short(self) -> None:
        assert ema_last([1.0], 3) is None


class TestRMA:
    def test_seed_is_simple_average(self) -> None:
        series = rma([2.0, 4.0, 6.0], 2)
        assert series[0] == pytest.approx(3.0)

    def test_known_recursion(self) -> None:
        # seed = avg(1,2,3)=2 over period 3; next = (2*2 + 4)/3 = 2.6667
        series = rma([1.0, 2.0, 3.0, 4.0], 3)
        assert series == pytest.approx([2.0, 8.0 / 3.0])


class TestRSI:
    def test_empty_when_too_short(self) -> None:
        assert rsi([1.0] * 10, 14) == []

    def test_all_gains_gives_100(self) -> None:
        closes = [float(i) for i in range(1, 30)]
        assert rsi_last(closes, 14) == pytest.approx(100.0)

    def test_all_losses_gives_low(self) -> None:
        closes = [float(i) for i in range(30, 1, -1)]
        # Strictly falling -> avg_gain 0 -> RSI 0
        assert rsi_last(closes, 14) == pytest.approx(0.0)

    @pytest.mark.parametrize("seed", [101, 202, 303])
    def test_bounded_0_100(self, seed: int) -> None:
        # deterministic pseudo-walk without RNG
        closes = [100.0]
        for i in range(1, 50):
            step = ((i * seed) % 7) - 3
            closes.append(max(1.0, closes[-1] + step))
        for value in rsi(closes, 14):
            assert 0.0 <= value <= 100.0

    def test_flat_series_is_neutral(self) -> None:
        # No gains and no losses -> defined as 50.
        assert rsi_last([100.0] * 30, 14) == pytest.approx(50.0)


class TestTrueRangeATR:
    def test_first_tr_is_high_minus_low(self) -> None:
        tr = true_ranges([10.0], [8.0], [9.0])
        assert tr == [2.0]

    def test_tr_accounts_for_gap(self) -> None:
        # prev close 9; bar2 high 20 low 19 -> max(1, |20-9|, |19-9|) = 11
        tr = true_ranges([10.0, 20.0], [8.0, 19.0], [9.0, 19.5])
        assert tr[1] == pytest.approx(11.0)

    def test_atr_none_when_short(self) -> None:
        assert atr([1.0], [0.0], [0.5], 14) is None

    def test_atr_nonnegative(self) -> None:
        highs = [10.0 + (i % 3) for i in range(30)]
        lows = [8.0 - (i % 2) for i in range(30)]
        closes = [9.0 for _ in range(30)]
        result = atr(highs, lows, closes, 14)
        assert result is not None
        assert result >= 0.0

    def test_atr_mismatched_lengths(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            true_ranges([1.0, 2.0], [1.0], [1.0])


def test_determinism_same_input_same_output() -> None:
    closes = [100.0 + (i % 5) for i in range(40)]
    assert rsi(closes, 14) == rsi(closes, 14)
    assert ema(closes, 20) == ema(closes, 20)
