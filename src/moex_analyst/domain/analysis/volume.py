"""Volume regime analysis.

Classifies the latest bar's volume against the mean and standard deviation of a
trailing window. For instruments without meaningful volume (indices report 0),
the condition is :attr:`VolumeCondition.UNKNOWN`.
"""

from __future__ import annotations

import statistics
from typing import TYPE_CHECKING

from moex_analyst.domain.analysis.enums import VolumeCondition

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["DEFAULT_VOLUME_WINDOW", "classify_volume"]

DEFAULT_VOLUME_WINDOW = 20
# z-score thresholds for high / low classification.
_HIGH_Z = 1.5
_LOW_Z = -0.75


def classify_volume(
    volumes: Sequence[int],
    *,
    window: int = DEFAULT_VOLUME_WINDOW,
) -> VolumeCondition:
    """Classify the latest volume relative to its trailing window.

    Returns :attr:`VolumeCondition.UNKNOWN` when there is too little data or the
    series carries no real volume (all zeros, e.g. an index).
    """
    if window < 2:
        raise ValueError("window must be >= 2")
    if len(volumes) < window:
        return VolumeCondition.UNKNOWN

    window_vols = [float(v) for v in volumes[-window:]]
    latest = window_vols[-1]
    history = window_vols[:-1]

    if all(v == 0.0 for v in window_vols):
        return VolumeCondition.UNKNOWN

    mean = statistics.fmean(history)
    stdev = statistics.pstdev(history)
    if stdev == 0.0:
        return VolumeCondition.HIGH if latest > mean else VolumeCondition.NORMAL

    z = (latest - mean) / stdev
    if z >= _HIGH_Z:
        return VolumeCondition.HIGH
    if z <= _LOW_Z:
        return VolumeCondition.LOW
    return VolumeCondition.NORMAL
