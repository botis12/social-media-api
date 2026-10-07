import datetime as dt
import lzma

import numpy as np
import pandas as pd
import pytest

from data.dukascopy import RECORD, decode_bi5
from data.loader import load_m5, resample_m1_to_m5, save_m5, validate


def _bi5(rows):
    arr = np.array(rows, dtype=RECORD)
    return lzma.compress(arr.tobytes(), format=lzma.FORMAT_ALONE)


def test_decode_bi5_candles():
    raw = _bi5([(0, 2000123, 2000500, 1999900, 2000800, 1.5), (60, 2000500, 2000400, 2000100, 2000900, 2.0)])
    df = decode_bi5(raw, dt.date(2024, 3, 5), 1000.0)
    assert df.index[1] == pd.Timestamp("2024-03-05 00:01", tz="UTC")
    row = df.iloc[0]
    assert (row.open, row.high, row.low, row.close) == pytest.approx((2000.123, 2000.8, 1999.9, 2000.5))


def test_decode_rejects_wrong_divisor():
    raw = _bi5([(0, 2000123, 2000500, 1999900, 2000800, 1.5)])
    with pytest.raises(ValueError, match="implausible"):
        decode_bi5(raw, dt.date(2024, 3, 5), 1.0)


def test_empty_file_is_empty_frame():
    assert decode_bi5(b"", dt.date(2024, 3, 9), 1000.0).empty


def test_m1_to_m5_and_roundtrip(tmp_path):
    idx = pd.date_range("2024-03-05 00:00", periods=10, freq="1min", tz="UTC")
    m1 = pd.DataFrame({"open": np.arange(10) + 2000.0, "high": np.arange(10) + 2001.0, "low": np.arange(10) + 1999.0,
                       "close": np.arange(10) + 2000.5, "volume": 1.0, "spread": 0.2}, index=idx)
    m5 = resample_m1_to_m5(m1)
    assert len(m5) == 2
    assert m5.iloc[0].open == 2000 and m5.iloc[0].high == 2005 and m5.iloc[0].close == 2004.5
    p = tmp_path / "x.csv.gz"
    save_m5(m5, p)
    back = load_m5(p)
    pd.testing.assert_frame_equal(back, m5, check_freq=False, check_names=False)


def test_validate_drops_bad_rows_and_dupes():
    idx = pd.DatetimeIndex(["2024-03-05 00:00", "2024-03-05 00:05", "2024-03-05 00:05", "2024-03-05 00:10"], tz="UTC")
    df = pd.DataFrame({"open": [1, 1, 1, 1.0], "high": [2, 2, 2, 0.5], "low": [0.5, 0.5, 0.5, 0.4],
                       "close": [1.5, 1.5, 1.5, 0.45]}, index=idx)
    out, q = validate(df)
    assert q.duplicates_dropped == 1 and q.bad_ohlc_dropped == 1 and len(out) == 2
