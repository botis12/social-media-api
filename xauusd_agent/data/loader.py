"""Load, validate and resample OHLC data.

Canonical frame: DatetimeIndex (UTC, bar OPEN time, 5-minute bars) with
columns open, high, low, close (BID prices), volume and, optionally,
spread (average ask-bid in price units over the bar).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

M5 = pd.Timedelta(minutes=5)
REQUIRED = ["open", "high", "low", "close"]
NY = "America/New_York"


@dataclass
class DataQuality:
    rows: int
    start: pd.Timestamp
    end: pd.Timestamp
    duplicates_dropped: int
    bad_ohlc_dropped: int
    weekday_gaps_over_30m: int
    largest_gap: pd.Timedelta

    def summary(self) -> str:
        return (
            f"{self.rows} bars {self.start} → {self.end}; dropped {self.duplicates_dropped} dupes, "
            f"{self.bad_ohlc_dropped} bad OHLC; {self.weekday_gaps_over_30m} weekday gaps >30m "
            f"(largest {self.largest_gap})"
        )


def load_m5(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Download data first: python main.py download (Dukascopy) "
            "or python main.py export-mt5 (on the MT5 machine)."
        )
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, parse_dates=["time"])
        df = df.set_index("time")
    df, q = validate(df)
    log.info("data: %s", q.summary())
    return df


def save_m5(df: pd.DataFrame, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out.index.name = "time"
    out.to_csv(path, float_format="%.3f")


def validate(df: pd.DataFrame) -> tuple[pd.DataFrame, DataQuality]:
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    idx = pd.DatetimeIndex(df.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    df = df.set_axis(idx.tz_convert("UTC").as_unit("ns")).sort_index()
    n0 = len(df)
    df = df[~df.index.duplicated(keep="last")]
    dupes = n0 - len(df)
    bad = (
        (df["high"] < df[["open", "close"]].max(axis=1))
        | (df["low"] > df[["open", "close"]].min(axis=1))
        | (df[REQUIRED] <= 0).any(axis=1)
        | df[REQUIRED].isna().any(axis=1)
    )
    df = df[~bad]
    if "volume" not in df.columns:
        df["volume"] = 0.0
    gaps = df.index.to_series().diff()
    weekday = df.index.dayofweek < 5
    big = (gaps > pd.Timedelta(minutes=30)) & weekday
    q = DataQuality(
        rows=len(df),
        start=df.index[0] if len(df) else pd.NaT,
        end=df.index[-1] if len(df) else pd.NaT,
        duplicates_dropped=dupes,
        bad_ohlc_dropped=int(bad.sum()),
        weekday_gaps_over_30m=int(big.sum()),
        largest_gap=gaps.max() if len(df) > 1 else pd.Timedelta(0),
    )
    return df, q


def resample_m1_to_m5(m1: pd.DataFrame) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    if "spread" in m1.columns:
        agg["spread"] = "mean"
    out = m1.resample("5min", label="left", closed="left").agg(agg).dropna(subset=["open"])
    return out.set_axis(out.index.as_unit("ns"))


def resample_htf(m5: pd.DataFrame, hours: int, alignment: str = "ny_close") -> pd.DataFrame:
    """Aggregate M5 into H1/H4 bars.

    Returns columns open/high/low/close plus `available_at`: the UTC instant
    the bar is complete (its scheduled end). A strategy may only use an HTF
    bar at times >= available_at — this is the no-look-ahead contract.
    Buckets that are not complete by the end of the data are dropped.

    alignment="ny_close" anchors buckets to 17:00 New York (the gold daily
    roll), which is how most MT5 brokers' H4 candles are built. DST changes
    occur on Sunday 02:00 NY while gold is closed, so the offset is constant
    within any traded bucket.
    """
    if m5.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "available_at"])
    idx = m5.index
    naive_utc = idx.tz_localize(None)
    if alignment == "ny_close":
        offset = idx.tz_convert(NY).tz_localize(None) - naive_utc  # -4h or -5h
        shift = offset + pd.Timedelta(hours=7)  # 17:00 NY -> 00:00 bucket clock
    else:
        shift = pd.to_timedelta(np.zeros(len(idx)), unit="s")
    clock = naive_utc + shift
    period = pd.Timedelta(hours=hours)
    key = clock.floor(f"{hours}h")
    start_utc = (key - shift).tz_localize("UTC")
    end_utc = start_utc + period
    g = pd.DataFrame(
        {
            "open": m5["open"].to_numpy(),
            "high": m5["high"].to_numpy(),
            "low": m5["low"].to_numpy(),
            "close": m5["close"].to_numpy(),
            "start": start_utc,
            "available_at": end_utc,
            "key": key,
        }
    )
    out = g.groupby("key", sort=True).agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        start=("start", "first"),
        available_at=("available_at", "first"),
    )
    data_end = idx[-1] + M5
    out = out[out["available_at"] <= data_end]
    return out.set_index("start")
