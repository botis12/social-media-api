"""Causal indicator primitives. Value at index i uses bars <= i only,
except swings, which are explicitly 'confirmed' n bars later."""
from __future__ import annotations

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
    """Wilder ATR. out[i] is known at the close of bar i."""
    n = len(close)
    out = np.full(n, np.nan)
    if n < period:
        return out
    prev_close = np.concatenate([[close[0]], close[:-1]])
    tr = np.maximum.reduce([high - low, np.abs(high - prev_close), np.abs(low - prev_close)])
    tr[0] = high[0] - low[0]
    out[period - 1] = tr[:period].mean()
    alpha = 1.0 / period
    for i in range(period, n):
        out[i] = out[i - 1] + alpha * (tr[i] - out[i - 1])
    return out


def swing_points(high: np.ndarray, low: np.ndarray, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Fractal swings: bar j is a swing high if high[j] is strictly above the n
    bars to its left and >= the n bars to its right (with equal highs the
    first bar is the swing). A swing at j is only KNOWN at the close of bar j + n.

    Returns boolean arrays (is_swing_high, is_swing_low) indexed by j.
    """
    size = len(high)
    sh = np.zeros(size, dtype=bool)
    sl = np.zeros(size, dtype=bool)
    if size < 2 * n + 1:
        return sh, sl
    wh = sliding_window_view(high, 2 * n + 1)
    wl = sliding_window_view(low, 2 * n + 1)
    mid_h = wh[:, n]
    mid_l = wl[:, n]
    left_h = wh[:, :n].max(axis=1)
    right_h = wh[:, n + 1 :].max(axis=1)
    left_l = wl[:, :n].min(axis=1)
    right_l = wl[:, n + 1 :].min(axis=1)
    sh[n : size - n] = (mid_h > left_h) & (mid_h >= right_h)
    sl[n : size - n] = (mid_l < left_l) & (mid_l <= right_l)
    return sh, sl
