"""Synthetic M5 data — ONLY for tests and pipeline smoke runs.

A random walk has no edge by construction, so a backtest on it should show
expectancy ≈ 0 minus costs. That makes it a useful sanity check of the
backtester itself (a profitable result on random data = a bug), and nothing
more. Never draw trading conclusions from it.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def make_m5(start: str, end: str, seed: int = 0, price: float = 2000.0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, end, freq="5min", tz="UTC", inclusive="left", unit="ns")
    ny = idx.tz_convert("America/New_York")
    # Gold trades Sun 18:00 – Fri 17:00 NY with a daily 17:00–18:00 break.
    dow, hour = ny.dayofweek, ny.hour
    open_mask = ~(
        (dow == 5)
        | ((dow == 6) & (hour < 18))
        | ((dow == 4) & (hour >= 17))
        | (hour == 17)
    )
    idx = idx[open_mask]
    utc_h = idx.hour
    # Intraday volatility profile ($ per 5m): quiet Asia, active London/NY.
    vol = np.where((utc_h >= 7) & (utc_h < 11), 1.1, 0.55)
    vol = np.where((utc_h >= 12) & (utc_h < 16), 1.4, vol)
    vol = vol * price / 2000.0
    rets = rng.standard_normal(len(idx)) * vol
    close = price + np.cumsum(rets)
    close = np.maximum(close, price * 0.3)
    open_ = np.concatenate([[price], close[:-1]])
    wick = np.abs(rng.standard_normal((2, len(idx)))) * vol * 0.6
    high = np.maximum(open_, close) + wick[0]
    low = np.minimum(open_, close) - wick[1]
    spread = np.clip(0.18 + np.abs(rng.standard_normal(len(idx))) * 0.06, 0.1, 1.0)
    spread = np.where((utc_h >= 21) | (utc_h < 1), spread * 2.5, spread)
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": 100.0, "spread": spread},
        index=idx,
    )
