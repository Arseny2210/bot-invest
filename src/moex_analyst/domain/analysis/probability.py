"""Deterministic probability engine.

Produces mutually-exclusive bullish / bearish / sideways probabilities from
already-computed factors (trend, structure, momentum, volume). No ML, no AI —
each factor casts a bounded directional vote; votes are blended with fixed
weights and mapped to probabilities via a softmax whose temperature widens when
the factors disagree (low agreement → flatter, more "sideways" distribution).

Inputs are pre-normalised scalars so the engine is independent of instrument
price scale.
"""

from __future__ import annotations

import math

from moex_analyst.domain.analysis.enums import (
    StructurePoint,
    TrendDirection,
    VolumeCondition,
)
from moex_analyst.domain.analysis.result import (
    ProbabilityDistribution,
    StructureState,
    TrendState,
)

__all__ = ["estimate_probabilities"]

# Factor weights (sum to 1.0).
_W_TREND = 0.40
_W_STRUCTURE = 0.30
_W_MOMENTUM = 0.20
_W_VOLUME = 0.10

_T_MIN = 0.35
_T_MAX = 1.20

# Base energy of the "sideways" class, scaled by (1 - |directional|). Tuned so
# that a directional conviction above ~0.38 outweighs sideways, while flat or
# conflicting signals (|directional| ~ 0) keep sideways dominant.
_SIDE_COEF = 0.60


def _structure_vote(structure: StructureState) -> float:
    score = 0.0
    if structure.last_high is StructurePoint.HH:
        score += 0.5
    elif structure.last_high is StructurePoint.LH:
        score -= 0.5
    if structure.last_low is StructurePoint.HL:
        score += 0.5
    elif structure.last_low is StructurePoint.LL:
        score -= 0.5
    return max(-1.0, min(1.0, score))


def _momentum_vote(rsi: float | None) -> float:
    """Map RSI(0..100) to a directional vote in [-1, 1], centred at 50.

    Saturating ``tanh`` keeps extreme RSI from dominating and injects mild
    mean-reversion caution at the extremes.
    """
    if rsi is None:
        return 0.0
    return math.tanh((rsi - 50.0) / 20.0)


def _volume_factor(volume: VolumeCondition) -> float:
    """Confirmation multiplier in [0, 1] applied to the directional signal."""
    match volume:
        case VolumeCondition.HIGH:
            return 1.0
        case VolumeCondition.NORMAL:
            return 0.7
        case VolumeCondition.LOW:
            return 0.4
        case VolumeCondition.UNKNOWN:
            return 0.6


def estimate_probabilities(
    trend: TrendState,
    structure: StructureState,
    rsi: float | None,
    volume: VolumeCondition,
) -> ProbabilityDistribution:
    """Blend factors into bullish / bearish / sideways probabilities."""
    trend_vote = trend.score  # already in [-1, 1]
    struct_vote = _structure_vote(structure)
    mom_vote = _momentum_vote(rsi)
    vol_factor = _volume_factor(volume)

    directional = (
        _W_TREND * trend_vote
        + _W_STRUCTURE * struct_vote
        + _W_MOMENTUM * mom_vote
    ) / (_W_TREND + _W_STRUCTURE + _W_MOMENTUM)
    # Volume confirms (scales) the directional conviction rather than steering it.
    directional *= vol_factor

    # Agreement: how aligned the directional votes are (1 = perfectly aligned).
    votes = [trend_vote, struct_vote, mom_vote]
    signed = [v for v in votes if v != 0.0]
    if signed:
        mean_sign = sum(1 if v > 0 else -1 for v in signed) / len(signed)
        agreement = abs(mean_sign)
    else:
        agreement = 0.0

    # Temperature: high agreement -> low T -> peaked; low agreement -> high T.
    temperature = _T_MAX - (_T_MAX - _T_MIN) * agreement

    # Energies for the three classes. Sideways gets energy from the *absence* of
    # directional conviction.
    e_up = directional
    e_down = -directional
    e_side = (1.0 - abs(directional)) * _SIDE_COEF

    energies = [e_up / temperature, e_down / temperature, e_side / temperature]
    m = max(energies)
    exps = [math.exp(e - m) for e in energies]
    total = sum(exps)
    p_up, p_down, p_side = (e / total for e in exps)

    # Clamp away from absolute certainty, then renormalise.
    eps = 0.02
    p_up = min(max(p_up, eps), 1.0 - eps)
    p_down = min(max(p_down, eps), 1.0 - eps)
    p_side = min(max(p_side, eps), 1.0 - eps)
    norm = p_up + p_down + p_side

    dist = ProbabilityDistribution(
        bullish=p_up / norm,
        bearish=p_down / norm,
        sideways=p_side / norm,
    )
    # Guard: if trend is explicitly sideways with no strength, ensure sideways
    # is at least competitive (defensive; softmax already favours it).
    if trend.direction is TrendDirection.SIDEWAYS and dist.sideways < max(
        dist.bullish, dist.bearish,
    ):
        # Re-centre slightly toward sideways without breaking the sum.
        boost = 0.05
        b = max(dist.bullish - boost / 2, 0.01)
        be = max(dist.bearish - boost / 2, 0.01)
        s = dist.sideways + boost
        norm2 = b + be + s
        return ProbabilityDistribution(
            bullish=b / norm2, bearish=be / norm2, sideways=s / norm2,
        )
    return dist
