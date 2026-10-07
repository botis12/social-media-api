import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import load_config  # noqa: E402


@pytest.fixture(scope="session")
def cfg():
    return load_config(ROOT / "config.yaml")


def flat_bars(start: str, end: str, price: float = 1995.0, rng: float = 1.0) -> pd.DataFrame:
    idx = pd.date_range(start, end, freq="5min", tz="UTC", inclusive="left", unit="ns")
    n = len(idx)
    return pd.DataFrame(
        {"open": np.full(n, price), "high": np.full(n, price + rng), "low": np.full(n, price - rng),
         "close": np.full(n, price), "volume": 1.0, "spread": 0.2},
        index=idx,
    )


def set_bar(df: pd.DataFrame, ts: str, o: float, h: float, l: float, c: float) -> None:
    t = pd.Timestamp(ts, tz="UTC")
    df.loc[t, ["open", "high", "low", "close"]] = [o, h, l, c]


@pytest.fixture
def bearish_setup_bars():
    """2024-03-05 (Athens UTC+2): Asia 00:00–07:00 UTC, London KZ 08:00–11:00 UTC.
    Asia high 2000 / low 1985; swing low 1993 at 08:10; sweep to 2003 at 08:35;
    displacement down with a bearish FVG 1997.2–2000.5 and MSS close 1991.5 at 08:45."""
    df = flat_bars("2024-03-04 00:00", "2024-03-05 12:00")
    set_bar(df, "2024-03-05 03:00", 1995, 2000, 1994, 1995)  # Asia high
    set_bar(df, "2024-03-05 05:00", 1995, 1996, 1985, 1995)  # Asia low
    set_bar(df, "2024-03-05 08:00", 1995, 1996, 1995, 1995.5)
    set_bar(df, "2024-03-05 08:05", 1995.5, 1996, 1994.5, 1994.6)
    set_bar(df, "2024-03-05 08:10", 1994.6, 1995.5, 1993, 1995)   # swing low 1993
    set_bar(df, "2024-03-05 08:15", 1995, 1996.5, 1995, 1996.3)
    set_bar(df, "2024-03-05 08:20", 1996.3, 1997.5, 1996, 1997.4)
    set_bar(df, "2024-03-05 08:25", 1997.4, 1998, 1997, 1997.9)
    set_bar(df, "2024-03-05 08:30", 1997.9, 2001.5, 1999, 2001)   # sweep of 2000
    set_bar(df, "2024-03-05 08:35", 2001, 2003, 2000.5, 2002)     # extreme 2003
    set_bar(df, "2024-03-05 08:40", 2002, 2002.2, 1996.8, 1997)   # displacement
    set_bar(df, "2024-03-05 08:45", 1997, 1997.2, 1991, 1991.5)   # MSS + FVG (2000.5 > 1997.2)
    for k, ts in enumerate(pd.date_range("2024-03-05 08:50", "2024-03-05 11:55", freq="5min")):
        set_bar(df, str(ts.tz_localize(None)), 1991.5, 1992.5, 1990.5, 1991.5)
    return df
