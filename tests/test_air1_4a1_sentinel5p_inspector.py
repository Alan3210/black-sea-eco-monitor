from __future__ import annotations

import numpy as np

from tools.air1_4a1_sentinel5p_inspector import _finite_stats


def test_finite_stats_ignores_nan_and_reports_percentiles():
    arr = np.array([1.0, 2.0, np.nan, 3.0, 4.0, 5.0])
    stats = _finite_stats(arr)
    assert stats["count"] == 5
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["mean"] == 3.0
    assert stats["p50"] == 3.0


def test_finite_stats_empty_returns_null_metrics():
    arr = np.array([np.nan, np.inf, -np.inf])
    stats = _finite_stats(arr)
    assert stats["count"] == 0
    assert stats["min"] is None
    assert stats["p95"] is None
