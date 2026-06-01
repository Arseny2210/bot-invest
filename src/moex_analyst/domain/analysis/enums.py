"""Enumerations for the deterministic analysis engine.

Pure value types shared across the analysis submodules. No I/O, no framework
dependencies — safe to import from anywhere in the domain layer.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "LevelKind",
    "StructurePoint",
    "TrendDirection",
    "TrendStrength",
    "VolumeCondition",
]


class TrendDirection(StrEnum):
    """Primary directional state of the market."""

    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"


class TrendStrength(StrEnum):
    """Confidence band for the detected trend."""

    STRONG = "strong"
    WEAK = "weak"
    NONE = "none"


class StructurePoint(StrEnum):
    """Swing-structure label relative to the previous swing of the same kind.

    HH/HL describe an up-structure; LH/LL describe a down-structure.
    """

    HH = "HH"  # higher high
    HL = "HL"  # higher low
    LH = "LH"  # lower high
    LL = "LL"  # lower low


class LevelKind(StrEnum):
    """Whether a price level acts as support or resistance."""

    SUPPORT = "support"
    RESISTANCE = "resistance"


class VolumeCondition(StrEnum):
    """Current volume regime relative to its recent moving average."""

    HIGH = "high"  # >= mean + k*std (or >= mult * SMA)
    NORMAL = "normal"
    LOW = "low"
    UNKNOWN = "unknown"  # insufficient data or index without real volume
