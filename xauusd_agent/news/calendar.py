"""High-impact news blackout.

No new position from `minutes_before` before until `minutes_after` after a
matching event. Sources:
  * live: ForexFactory weekly JSON (free, via nfs.faireconomy.media),
    cached locally and refreshed at most every `refresh_minutes`;
  * fallback / backtest: CSV files (historical schedule + your manual file).
If no source covers the current time, `on_unavailable: block` refuses new
trades (fail-safe) rather than trading blind.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

import pandas as pd
import requests

from core.config import NewsCfg

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewsEvent:
    time: pd.Timestamp  # UTC
    title: str
    currency: str
    impact: str
    source: str

    def __str__(self) -> str:
        return f"{self.currency} {self.title} @ {self.time:%Y-%m-%d %H:%M} UTC ({self.source})"


# ------------------------------------------------------------------ parsing
def parse_ff_json(payload: list[dict], source: str = "forexfactory") -> list[NewsEvent]:
    out = []
    for e in payload:
        try:
            t = pd.Timestamp(e["date"])  # ISO with offset, e.g. 2026-10-02T08:30:00-04:00
            if t.tzinfo is None:
                continue
            out.append(
                NewsEvent(t.tz_convert("UTC"), str(e.get("title", "")), str(e.get("country", "")).upper(),
                          str(e.get("impact", "")), source)
            )
        except (KeyError, ValueError, TypeError):
            log.warning("news: skipping malformed event %r", e)
    return out


def load_csv(path: Path, source: Optional[str] = None) -> list[NewsEvent]:
    if not path.exists():
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        rows = csv.DictReader(line for line in fh if line.strip() and not line.lstrip().startswith("#"))
        for r in rows:
            try:
                t = pd.Timestamp(r["datetime"]).tz_localize(r["tz"]).tz_convert("UTC")
                out.append(NewsEvent(t, r["title"], r["currency"].upper(), r["impact"], source or path.name))
            except (KeyError, ValueError) as exc:
                log.warning("news: bad row in %s: %r (%s)", path, r, exc)
    return out


# ------------------------------------------------------------------ filter
class NewsFilter:
    """Pure, time-indexed blackout check over a fixed list of events."""

    def __init__(self, events: Iterable[NewsEvent], cfg: NewsCfg, match_all_high_impact: bool = False):
        self.cfg = cfg
        self.before = pd.Timedelta(minutes=cfg.minutes_before)
        self.after = pd.Timedelta(minutes=cfg.minutes_after)
        cur = {c.upper() for c in cfg.currencies}
        imp = {i.lower() for i in cfg.impacts}
        kws = [k.lower() for k in cfg.keywords]

        def relevant(e: NewsEvent) -> bool:
            if e.currency.upper() not in cur or e.impact.lower() not in imp:
                return False
            return match_all_high_impact or any(k in e.title.lower() for k in kws)

        uniq = {(e.time, e.title): e for e in events if relevant(e)}
        self.events = sorted(uniq.values(), key=lambda e: e.time)

    def blocking_event(self, t: pd.Timestamp) -> Optional[NewsEvent]:
        t = pd.Timestamp(t).tz_convert("UTC")
        for e in self.events:
            if e.time - self.before <= t <= e.time + self.after:
                return e
            if e.time - self.before > t:
                break
        return None

    def window_overlaps(self, start: pd.Timestamp, end: pd.Timestamp) -> Optional[NewsEvent]:
        """First event whose blackout intersects [start, end]."""
        for e in self.events:
            if e.time - self.before <= end and e.time + self.after >= start:
                return e
        return None

    def upcoming(self, t: pd.Timestamp, hours: float = 24) -> list[NewsEvent]:
        t = pd.Timestamp(t).tz_convert("UTC")
        return [e for e in self.events if t <= e.time <= t + pd.Timedelta(hours=hours)]


def backtest_filter(cfg: NewsCfg, resolve: Callable[[str], Path]) -> NewsFilter:
    events = load_csv(resolve(cfg.historical_file), "historical") + load_csv(resolve(cfg.manual_file), "manual")
    if not events:
        raise FileNotFoundError("no historical news events found — backtest would ignore the news filter")
    return NewsFilter(events, cfg)


# ------------------------------------------------------------------ live
class LiveNewsCalendar:
    """Fetches/caches the online calendar and answers 'may I open a trade now?'."""

    def __init__(self, cfg: NewsCfg, resolve: Callable[[str], Path], http_get=None, clock=None):
        self.cfg = cfg
        self.resolve = resolve
        self.cache_dir = resolve(cfg.cache_dir)
        self.http_get = http_get or (lambda url: requests.get(url, timeout=15, headers={"User-Agent": "xauusd-agent/1.0"}))
        self.clock = clock or (lambda: pd.Timestamp.now(tz="UTC"))
        self._last_refresh = 0.0
        self._online: list[NewsEvent] = []
        self._online_coverage: tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]] = (None, None)
        self._filter: Optional[NewsFilter] = None
        self._fallback = load_csv(resolve(cfg.historical_file), "historical") + load_csv(resolve(cfg.manual_file), "manual")

    def _cache_file(self, url: str) -> Path:
        return self.cache_dir / (Path(url).stem + ".json")

    def refresh(self, force: bool = False) -> None:
        now_mono = time.monotonic()
        if not force and self._filter is not None and now_mono - self._last_refresh < self.cfg.refresh_minutes * 60:
            return
        events: list[NewsEvent] = []
        for url in self.cfg.sources:
            payload = None
            try:
                r = self.http_get(url)
                r.raise_for_status()
                payload = r.json()
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                tmp = self._cache_file(url).with_suffix(".tmp")
                tmp.write_text(json.dumps(payload), encoding="utf-8")
                tmp.replace(self._cache_file(url))
            except Exception as exc:  # noqa: BLE001 — any failure → try cache
                log.warning("news: fetch %s failed (%s); trying cache", url, exc)
                cf = self._cache_file(url)
                if cf.exists():
                    try:
                        payload = json.loads(cf.read_text(encoding="utf-8"))
                    except ValueError:
                        payload = None
            if payload:
                events += parse_ff_json(payload)
        self._online = events
        if events:
            times = [e.time for e in events]
            # FF weekly files cover Sunday..Saturday; coverage = span of their weeks
            lo = min(times).normalize() - pd.Timedelta(days=min(times).dayofweek + 1)
            hi = max(times).normalize() + pd.Timedelta(days=7 - max(times).dayofweek)
            self._online_coverage = (lo, hi)
        else:
            self._online_coverage = (None, None)
        self._filter = NewsFilter(events + self._fallback, self.cfg, match_all_high_impact=False)
        self._filter_all = NewsFilter(events, self.cfg, match_all_high_impact=True)
        self._last_refresh = now_mono
        log.info("news: %d online events, %d fallback events; coverage %s", len(events), len(self._fallback), self._online_coverage)

    def _covered(self, t: pd.Timestamp) -> bool:
        lo, hi = self._online_coverage
        if lo is not None and lo <= t <= hi:
            return True
        # fallback CSV counts as coverage up to its last listed event
        return bool(self._fallback) and t <= max(e.time for e in self._fallback)

    def check(self, t: Optional[pd.Timestamp] = None) -> tuple[bool, str]:
        """(allowed, reason)."""
        self.refresh()
        t = pd.Timestamp(t if t is not None else self.clock()).tz_convert("UTC")
        if not self._covered(t):
            if self.cfg.on_unavailable == "block":
                return False, "news calendar unavailable for current week (fail-safe block)"
            log.warning("news: calendar unavailable — trading allowed by config")
        e = self._filter.blocking_event(t)
        if e is None and self.cfg.live_block_all_high_impact:
            e = self._filter_all.blocking_event(t)
        if e is not None:
            return False, f"news blackout: {e}"
        return True, "no high-impact news within window"

    def upcoming(self, hours: float = 24) -> list[NewsEvent]:
        self.refresh()
        t = self.clock()
        evs = self._filter.upcoming(t, hours)
        if self.cfg.live_block_all_high_impact:
            evs = sorted({(e.time, e.title): e for e in evs + self._filter_all.upcoming(t, hours)}.values(), key=lambda e: e.time)
        return evs
