"""Free historical XAUUSD data from Dukascopy's public datafeed.

Downloads per-day 1-minute BID and ASK candle files (.bi5 = LZMA-compressed
big-endian records), derives the real historical bid/ask spread per minute,
and aggregates to M5. Raw files are cached so reruns only fetch what's new.

Record layout (24 bytes): uint32 seconds-from-day-start, uint32 open,
uint32 close, uint32 low, uint32 high, float32 volume. Prices are integers
scaled by 1/point_divisor (1000 for XAUUSD). Month in the URL is 0-based.

Note: Dukascopy is an ECN feed; your broker's prices and spreads differ
slightly. Cross-check with `python main.py export-mt5` on your terminal.
"""
from __future__ import annotations

import datetime as dt
import logging
import lzma
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import requests

from data.loader import resample_m1_to_m5

log = logging.getLogger(__name__)

URL = "https://datafeed.dukascopy.com/datafeed/{sym}/{y:04d}/{m:02d}/{d:02d}/{side}_candles_min_1.bi5"
RECORD = np.dtype([("t", ">u4"), ("o", ">u4"), ("c", ">u4"), ("l", ">u4"), ("h", ">u4"), ("v", ">f4")])
POINT_DIVISOR = {"XAUUSD": 1000.0}
SANE_PRICE = (100.0, 100_000.0)


def decode_bi5(raw: bytes, day: dt.date, divisor: float) -> pd.DataFrame:
    if not raw:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    buf = lzma.decompress(raw)
    if len(buf) % RECORD.itemsize:
        raise ValueError(f"corrupt bi5 for {day}: {len(buf)} bytes")
    arr = np.frombuffer(buf, dtype=RECORD)
    base = pd.Timestamp(day, tz="UTC")
    idx = base + pd.to_timedelta(arr["t"].astype(np.int64), unit="s")
    df = pd.DataFrame(
        {
            "open": arr["o"] / divisor,
            "high": arr["h"] / divisor,
            "low": arr["l"] / divisor,
            "close": arr["c"] / divisor,
            "volume": arr["v"].astype(float),
        },
        index=idx,
    )
    lo, hi = SANE_PRICE
    if len(df) and not df["close"].between(lo, hi).all():
        raise ValueError(f"implausible prices for {day} — wrong point divisor?")
    return df


class DukascopyDownloader:
    def __init__(self, symbol: str, cache_dir: Path, workers: int = 4, retries: int = 4):
        self.symbol = symbol.upper()
        if self.symbol not in POINT_DIVISOR:
            raise ValueError(f"no point divisor known for {self.symbol}")
        self.divisor = POINT_DIVISOR[self.symbol]
        self.cache_dir = Path(cache_dir) / self.symbol
        self.workers = workers
        self.retries = retries
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "xauusd-agent-research/1.0"

    def _cache_path(self, day: dt.date, side: str) -> Path:
        return self.cache_dir / f"{day:%Y}" / f"{day:%m}" / f"{day:%d}_{side}.bi5"

    def _fetch(self, day: dt.date, side: str) -> bytes:
        p = self._cache_path(day, side)
        if p.exists():
            return p.read_bytes()
        url = URL.format(sym=self.symbol, y=day.year, m=day.month - 1, d=day.day, side=side)
        delay = 2.0
        for attempt in range(1, self.retries + 1):
            try:
                r = self.session.get(url, timeout=30)
                if r.status_code == 404:
                    content = b""
                else:
                    r.raise_for_status()
                    content = r.content
                p.parent.mkdir(parents=True, exist_ok=True)
                tmp = p.with_suffix(".tmp")
                tmp.write_bytes(content)
                tmp.replace(p)
                return content
            except requests.RequestException as exc:
                if attempt == self.retries:
                    raise
                log.warning("dukascopy %s %s attempt %d failed: %s", day, side, attempt, exc)
                time.sleep(delay)
                delay *= 2
        return b""

    def day_m1(self, day: dt.date) -> Optional[pd.DataFrame]:
        bid = decode_bi5(self._fetch(day, "BID"), day, self.divisor)
        ask = decode_bi5(self._fetch(day, "ASK"), day, self.divisor)
        if bid.empty:
            return None
        # Weekend/holiday files contain flat zero-volume candles: drop them.
        bid = bid[bid["volume"] > 0]
        if bid.empty:
            return None
        if not ask.empty:
            spread = (ask["close"] - bid["close"]).reindex(bid.index)
            bid = bid.assign(spread=spread.clip(lower=0))
        return bid

    def download(self, start: dt.date, end: dt.date) -> pd.DataFrame:
        days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
        days = [d for d in days if d.weekday() != 5]  # Saturday: market closed
        frames: list[pd.DataFrame] = []
        done = 0
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {ex.submit(self.day_m1, d): d for d in days}
            for fut in as_completed(futs):
                df = fut.result()
                if df is not None:
                    frames.append(df)
                done += 1
                if done % 50 == 0 or done == len(days):
                    log.info("dukascopy: %d/%d days", done, len(days))
        if not frames:
            raise RuntimeError("no data downloaded")
        m1 = pd.concat(frames).sort_index()
        m1 = m1[~m1.index.duplicated()]
        m5 = resample_m1_to_m5(m1)
        if "spread" in m5.columns:
            m5["spread"] = m5["spread"].ffill()
        return m5
