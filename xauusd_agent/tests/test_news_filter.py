from pathlib import Path

import pandas as pd
import pytest

from news.calendar import LiveNewsCalendar, NewsEvent, NewsFilter, backtest_filter, load_csv, parse_ff_json


def ev(t, title="CPI m/m", cur="USD", impact="High"):
    return NewsEvent(pd.Timestamp(t, tz="UTC"), title, cur, impact, "test")


def test_window_boundaries(cfg):
    f = NewsFilter([ev("2024-03-12 12:30")], cfg.news)
    assert f.blocking_event(pd.Timestamp("2024-03-12 12:00", tz="UTC"))  # exactly −30'
    assert f.blocking_event(pd.Timestamp("2024-03-12 13:00", tz="UTC"))  # exactly +30'
    assert f.blocking_event(pd.Timestamp("2024-03-12 12:30", tz="UTC"))
    assert f.blocking_event(pd.Timestamp("2024-03-12 11:59", tz="UTC")) is None
    assert f.blocking_event(pd.Timestamp("2024-03-12 13:01", tz="UTC")) is None


def test_filters_currency_impact_keywords(cfg):
    events = [ev("2024-03-12 12:30", "German CPI", cur="EUR"), ev("2024-03-13 12:30", impact="Medium"),
              ev("2024-03-14 12:30", "Retail Sales m/m"), ev("2024-03-15 12:30", "Non-Farm Employment Change"),
              ev("2024-03-20 18:00", "FOMC Statement"), ev("2024-03-29 12:30", "Core PCE Price Index m/m")]
    f = NewsFilter(events, cfg.news)
    titles = [e.title for e in f.events]
    assert titles == ["Non-Farm Employment Change", "FOMC Statement", "Core PCE Price Index m/m"]
    f_all = NewsFilter(events, cfg.news, match_all_high_impact=True)
    assert "Retail Sales m/m" in [e.title for e in f_all.events]
    assert "German CPI" not in [e.title for e in f_all.events]


def test_window_overlaps(cfg):
    f = NewsFilter([ev("2024-03-12 12:30")], cfg.news)
    assert f.window_overlaps(pd.Timestamp("2024-03-12 11:55", tz="UTC"), pd.Timestamp("2024-03-12 12:00", tz="UTC"))
    assert f.window_overlaps(pd.Timestamp("2024-03-12 11:50", tz="UTC"), pd.Timestamp("2024-03-12 11:55", tz="UTC")) is None


def test_csv_dst_conversion(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("# comment\ndatetime,tz,currency,impact,title,status\n"
                 "2024-03-08 08:30,America/New_York,USD,High,Non-Farm Employment Change,x\n"
                 "2024-03-12 08:30,America/New_York,USD,High,CPI m/m,x\n")
    e = load_csv(p)
    assert e[0].time == pd.Timestamp("2024-03-08 13:30", tz="UTC")  # EST (UTC−5)
    assert e[1].time == pd.Timestamp("2024-03-12 12:30", tz="UTC")  # EDT (UTC−4) after US DST


def test_parse_forexfactory_json():
    payload = [
        {"title": "CPI m/m", "country": "USD", "date": "2026-10-14T08:30:00-04:00", "impact": "High"},
        {"title": "bad", "country": "USD", "date": "not a date", "impact": "High"},
        {"title": "no tz", "country": "USD", "date": "2026-10-14T08:30:00", "impact": "High"},
    ]
    e = parse_ff_json(payload)
    assert len(e) == 1
    assert e[0].time == pd.Timestamp("2026-10-14 12:30", tz="UTC")


def test_historical_file_is_complete_and_parses(cfg):
    f = backtest_filter(cfg.news, cfg.path)
    titles = [e.title for e in f.events]
    assert sum("CPI" in t for t in titles) >= 45
    assert sum("Non-Farm" in t for t in titles) >= 45
    assert sum("PCE" in t for t in titles) >= 45
    assert sum("FOMC Statement" in t for t in titles) == 32
    times = [e.time for e in f.events]
    assert len(times) == len(set(zip(times, titles)))
    # NFP 2024-07-05 08:30 ET → blocked 12:00–13:00 UTC
    assert f.blocking_event(pd.Timestamp("2024-07-05 12:10", tz="UTC"))


class _Resp:
    def __init__(self, payload=None, fail=False):
        self.payload, self.fail = payload, fail

    def raise_for_status(self):
        if self.fail:
            raise RuntimeError("http 500")

    def json(self):
        return self.payload


def _cal(cfg, tmp_path, http_get, now, csv_rows=""):
    news = cfg.news.model_copy(update={"cache_dir": str(tmp_path / "cache"),
                                       "historical_file": str(tmp_path / "hist.csv"),
                                       "manual_file": str(tmp_path / "manual.csv")})
    (tmp_path / "hist.csv").write_text("datetime,tz,currency,impact,title,status\n" + csv_rows)
    resolve = Path
    return LiveNewsCalendar(news, resolve, http_get=http_get, clock=lambda: pd.Timestamp(now, tz="UTC"))


def test_live_blocks_and_allows(cfg, tmp_path):
    payload = [{"title": "Retail Sales m/m", "country": "USD", "date": "2026-10-15T08:30:00-04:00", "impact": "High"}]
    cal = _cal(cfg, tmp_path, lambda url: _Resp(payload), "2026-10-15 12:10")
    ok, why = cal.check()
    assert not ok and "Retail Sales" in why  # live blocks ALL high-impact USD by default
    ok, _ = cal.check(pd.Timestamp("2026-10-15 14:00", tz="UTC"))
    assert ok


def test_live_uses_cache_when_fetch_fails(cfg, tmp_path):
    payload = [{"title": "CPI m/m", "country": "USD", "date": "2026-10-14T08:30:00-04:00", "impact": "High"}]
    cal = _cal(cfg, tmp_path, lambda url: _Resp(payload), "2026-10-14 12:20")
    assert not cal.check()[0]
    cal2 = _cal(cfg, tmp_path, lambda url: _Resp(fail=True), "2026-10-14 12:20")
    ok, why = cal2.check()
    assert not ok and "CPI" in why


def test_live_falls_back_to_csv(cfg, tmp_path):
    rows = "2026-10-14 08:30,America/New_York,USD,High,CPI m/m,manual\n2026-12-31 08:30,America/New_York,USD,High,CPI m/m,manual\n"
    cal = _cal(cfg, tmp_path, lambda url: _Resp(fail=True), "2026-10-14 12:20", rows)
    ok, why = cal.check()
    assert not ok and "CPI" in why
    assert cal.check(pd.Timestamp("2026-10-14 15:00", tz="UTC"))[0]


def test_live_fail_safe_when_no_source(cfg, tmp_path):
    cal = _cal(cfg, tmp_path, lambda url: _Resp(fail=True), "2026-10-14 15:00")
    ok, why = cal.check()
    assert not ok and "unavailable" in why
