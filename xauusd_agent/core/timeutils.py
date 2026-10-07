"""Timezone / session helpers. All internal timestamps are tz-aware UTC.

Session windows are defined in their own IANA timezone, so DST is handled
by zoneinfo: e.g. the NY killzone anchored to America/New_York shifts
relative to Athens during the weeks the US and EU DST calendars differ.
"""
from __future__ import annotations

import datetime as dt
from functools import lru_cache
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from core.config import ForceClose, Window

UTC = dt.timezone.utc


@lru_cache(maxsize=None)
def tz(name: str) -> ZoneInfo:
    return ZoneInfo(name)


def to_utc(ts: dt.datetime) -> dt.datetime:
    if ts.tzinfo is None:
        raise ValueError("naive datetime not allowed; attach a timezone")
    return ts.astimezone(UTC)


def window_bounds_utc(window: Window, day: dt.date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """UTC [start, end) of `window` on calendar `day` in the window's own tz."""
    z = tz(window.tz)
    start = dt.datetime.combine(day, window.start_time, tzinfo=z)
    end = dt.datetime.combine(day, window.end_time, tzinfo=z)
    return pd.Timestamp(start).tz_convert("UTC"), pd.Timestamp(end).tz_convert("UTC")


def force_close_utc(fc: ForceClose, day: dt.date) -> pd.Timestamp:
    return pd.Timestamp(dt.datetime.combine(day, fc.clock, tzinfo=tz(fc.tz))).tz_convert("UTC")


def trading_day(ts: pd.Timestamp | dt.datetime, tz_name: str) -> dt.date:
    """Calendar date of `ts` in the trading-day timezone (daily limits reset at 00:00 there)."""
    return pd.Timestamp(ts).tz_convert(tz_name).date()


def in_window_mask(index: pd.DatetimeIndex, window: Window) -> np.ndarray:
    """Bars whose OPEN time falls in [start, end) of the window (local clock)."""
    local = index.tz_convert(window.tz)
    minutes = local.hour * 60 + local.minute
    s = window.start_time.hour * 60 + window.start_time.minute
    e = window.end_time.hour * 60 + window.end_time.minute
    return np.asarray((minutes >= s) & (minutes < e))


def local_dates(index: pd.DatetimeIndex, tz_name: str) -> np.ndarray:
    return np.asarray(index.tz_convert(tz_name).date)


def fmt(ts: pd.Timestamp | dt.datetime, tz_name: str) -> str:
    return pd.Timestamp(ts).tz_convert(tz_name).strftime("%Y-%m-%d %H:%M %Z")
