"""Higher-timeframe directional bias from market structure.

Rule (applied to CLOSED HTF bars only):
  * swings are fractal highs/lows with `n` bars each side, known n bars later;
  * a close above the most recent unbroken swing high  -> bias = +1 (bullish);
  * a close below the most recent unbroken swing low   -> bias = -1 (bearish);
  * otherwise the previous bias persists (0 until the first break).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategy.indicators import swing_points


def structural_bias(htf: pd.DataFrame, n: int) -> np.ndarray:
    high = htf["high"].to_numpy()
    low = htf["low"].to_numpy()
    close = htf["close"].to_numpy()
    sh, sl = swing_points(high, low, n)
    bias = np.zeros(len(htf), dtype=np.int8)
    last_sh = np.nan
    last_sl = np.nan
    state = 0
    for k in range(len(htf)):
        j = k - n
        if j >= 0:
            if sh[j]:
                last_sh = high[j]
            if sl[j]:
                last_sl = low[j]
        if not np.isnan(last_sh) and close[k] > last_sh:
            state = 1
            last_sh = np.nan
        elif not np.isnan(last_sl) and close[k] < last_sl:
            state = -1
            last_sl = np.nan
        bias[k] = state
    return bias


def bias_at_decisions(htf: pd.DataFrame, bias: np.ndarray, decision_times: pd.DatetimeIndex) -> np.ndarray:
    """Bias known at each decision instant: from the last HTF bar whose
    `available_at` <= decision time. 0 when no HTF bar is complete yet."""
    if len(htf) == 0:
        return np.zeros(len(decision_times), dtype=np.int8)
    avail = pd.DatetimeIndex(htf["available_at"]).tz_convert("UTC").tz_localize(None).to_numpy(dtype="datetime64[ns]")
    order = np.argsort(avail, kind="stable")
    avail = avail[order]
    b = bias[order]
    t = decision_times.tz_convert("UTC").tz_localize(None).to_numpy(dtype="datetime64[ns]")
    pos = np.searchsorted(avail, t, side="right") - 1
    out = np.where(pos >= 0, b[np.clip(pos, 0, None)], 0)
    return out.astype(np.int8)
