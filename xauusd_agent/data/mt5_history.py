"""Export M5 history from your MT5 terminal (Windows) in the canonical CSV
format, to backtest on your broker's own prices/spreads or to cross-check
the Dukascopy data. Many brokers only keep a limited M5 history."""
from __future__ import annotations

import datetime as dt
import logging

import numpy as np
import pandas as pd

from execution.mt5_broker import MT5Broker, MT5Error

log = logging.getLogger(__name__)


def export_m5(broker: MT5Broker, start: dt.date, end: dt.date) -> pd.DataFrame:
    mt5 = broker.mt5
    spec = broker.symbol_spec()
    off_h = broker._server_offset_h()
    frames = []
    cur = pd.Timestamp(start)
    stop = pd.Timestamp(end) + pd.Timedelta(days=1)
    while cur < stop:
        nxt = min(cur + pd.DateOffset(months=1), stop)
        # copy_rates_range takes datetimes interpreted as server time
        r = mt5.copy_rates_range(broker.symbol, mt5.TIMEFRAME_M5,
                                 (cur + pd.Timedelta(hours=off_h)).to_pydatetime(),
                                 (nxt + pd.Timedelta(hours=off_h)).to_pydatetime())
        if r is not None and len(r):
            idx = pd.to_datetime(np.asarray(r["time"], dtype=np.int64) - off_h * 3600, unit="s", utc=True)
            frames.append(pd.DataFrame({
                "open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"],
                "volume": r["tick_volume"].astype(float), "spread": r["spread"].astype(float) * spec.point,
            }, index=idx))
            log.info("mt5 export %s → %s: %d bars", cur.date(), nxt.date(), len(r))
        else:
            log.warning("mt5 export %s → %s: no data (%s)", cur.date(), nxt.date(), mt5.last_error())
        cur = nxt
    if not frames:
        raise MT5Error("no history returned — increase 'Max bars in chart' in MT5 settings and scroll the M5 chart back")
    df = pd.concat(frames).sort_index()
    return df[~df.index.duplicated()]
