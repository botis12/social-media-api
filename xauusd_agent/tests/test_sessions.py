import datetime as dt

import pandas as pd

from core.timeutils import force_close_utc, trading_day, window_bounds_utc
from data.loader import resample_htf
from tests.conftest import flat_bars


def utc(s):
    return pd.Timestamp(s, tz="UTC")


def test_london_killzone_tracks_athens_dst(cfg):
    w = cfg.sessions.killzones["london"]
    assert window_bounds_utc(w, dt.date(2024, 1, 15)) == (utc("2024-01-15 08:00"), utc("2024-01-15 11:00"))  # EET
    assert window_bounds_utc(w, dt.date(2024, 7, 15)) == (utc("2024-07-15 07:00"), utc("2024-07-15 10:00"))  # EEST


def test_newyork_killzone_follows_new_york_clock(cfg):
    w = cfg.sessions.killzones["newyork"]
    # both on standard time: 08:30 ET = 13:30 UTC = 15:30 Athens
    s, _ = window_bounds_utc(w, dt.date(2024, 3, 5))
    assert s == utc("2024-03-05 13:30") and s.tz_convert("Europe/Athens").strftime("%H:%M") == "15:30"
    # US on DST (from 10 Mar), EU not yet (31 Mar): 08:30 ET = 12:30 UTC = 14:30 Athens
    s, _ = window_bounds_utc(w, dt.date(2024, 3, 12))
    assert s == utc("2024-03-12 12:30") and s.tz_convert("Europe/Athens").strftime("%H:%M") == "14:30"
    # both on DST: back to 15:30 Athens
    s, _ = window_bounds_utc(w, dt.date(2024, 4, 10))
    assert s.tz_convert("Europe/Athens").strftime("%H:%M") == "15:30"
    # EU back to standard (27 Oct), US not yet (3 Nov): 14:30 Athens
    s, _ = window_bounds_utc(w, dt.date(2024, 10, 29))
    assert s.tz_convert("Europe/Athens").strftime("%H:%M") == "14:30"


def test_asia_window(cfg):
    a, b = window_bounds_utc(cfg.sessions.asia, dt.date(2024, 1, 15))
    assert (a, b) == (utc("2024-01-15 00:00"), utc("2024-01-15 07:00"))


def test_force_close_and_trading_day(cfg):
    assert force_close_utc(cfg.sessions.force_close, dt.date(2024, 7, 1)) == utc("2024-07-01 20:45")
    assert trading_day(utc("2024-07-01 21:30"), "Europe/Athens") == dt.date(2024, 7, 2)  # 00:30 Athens
    assert trading_day(utc("2024-07-01 20:30"), "Europe/Athens") == dt.date(2024, 7, 1)


def test_htf_bars_only_available_after_close():
    m5 = flat_bars("2024-03-04 00:00", "2024-03-05 00:00")
    h1 = resample_htf(m5, 1, "ny_close")
    assert (h1["available_at"] == h1.index + pd.Timedelta(hours=1)).all()
    h4 = resample_htf(m5, 4, "ny_close")
    # buckets anchored at 17:00 New York (22:00 UTC in winter): 22,02,06,10,14,18 UTC
    assert set(h4.index.hour) <= {22, 2, 6, 10, 14, 18}
    # a partial bucket at the end of data is dropped
    h4_partial = resample_htf(m5.iloc[:-3], 4, "ny_close")
    assert h4_partial["available_at"].max() <= m5.index[-4] + pd.Timedelta(minutes=5)
