import numpy as np
import pandas as pd
import pytest

import strategy.ict as ict
from core.models import SHORT
from data.synthetic import make_m5
from strategy.bias import structural_bias
from strategy.indicators import atr, swing_points


@pytest.fixture
def force_bias(monkeypatch):
    def _set(value):
        monkeypatch.setattr(ict, "bias_at_decisions", lambda htf, b, t: np.full(len(t), value, dtype=np.int8))
    return _set


def test_swing_points_confirmed_n_bars_later():
    h = np.array([1, 2, 3, 2, 1, 2, 3, 4, 3, 2], float)
    l = h - 1
    sh, sl = swing_points(h, l, 2)
    assert list(np.flatnonzero(sh)) == [2, 7]
    assert list(np.flatnonzero(sl)) == [4]
    # the last n bars can never be swings yet (not confirmed)
    assert not sh[-2:].any() and not sl[-2:].any()


def test_atr_is_causal():
    rng = np.random.default_rng(0)
    c = 2000 + np.cumsum(rng.standard_normal(200))
    h, l = c + 1, c - 1
    full = atr(h, l, c, 14)
    part = atr(h[:120], l[:120], c[:120], 14)
    np.testing.assert_allclose(full[:120], part, equal_nan=True)


def test_structural_bias():
    # up-leg with swing high at bar 2, then close above it → +1; later break of a swing low → −1
    close = [10, 11, 12, 11, 10, 11, 13, 12, 11, 10, 9, 8, 7]
    df = pd.DataFrame({"high": np.array(close) + 0.5, "low": np.array(close) - 0.5, "close": close})
    b = structural_bias(df, 2)
    assert b[5] == 0 and b[6] == 1  # close 13 > swing high 12.5
    assert b[-1] == -1


def test_bearish_setup_produces_signal(cfg, bearish_setup_bars, force_bias):
    force_bias(-1)
    out = ict.IctStrategy(cfg).generate_signals(bearish_setup_bars)
    assert len(out.signals) == 1
    s = out.signals[0]
    assert s.direction == SHORT and s.killzone == "london" and s.entry_type == "fvg"
    assert s.time == pd.Timestamp("2024-03-05 08:50", tz="UTC")  # close of the 08:45 MSS bar
    assert s.entry == pytest.approx((2000.5 + 1997.2) / 2, abs=0.01)
    assert s.tp == pytest.approx(1985.0)
    assert s.sl > 2003.0 and s.sl == pytest.approx(2003 + max(0.1 * s.atr, 0.30), abs=0.01)
    assert s.rr >= cfg.strategy.min_rr
    assert s.expiry == s.time + cfg.strategy.entry_expiry_bars * pd.Timedelta(minutes=5)
    kinds = [d.kind for d in out.decisions]
    assert kinds.index("SWEEP") < kinds.index("MSS") < kinds.index("SIGNAL")


def test_setup_rejected_against_h1_bias(cfg, bearish_setup_bars, force_bias):
    force_bias(+1)
    out = ict.IctStrategy(cfg).generate_signals(bearish_setup_bars)
    assert out.signals == []
    assert any(d.kind == "REJECT" and "H1 bias" in d.message for d in out.decisions)


def test_min_rr_rejects_instead_of_stretching_target(cfg, bearish_setup_bars, force_bias):
    force_bias(-1)
    bars = bearish_setup_bars.copy()
    bars.loc[pd.Timestamp("2024-03-05 05:00", tz="UTC"), "low"] = 1990.0  # Asia low closer → R:R < 2
    out = ict.IctStrategy(cfg).generate_signals(bars)
    assert out.signals == []
    rej = [d for d in out.decisions if d.kind == "REJECT"]
    assert rej and "R:R" in rej[0].message


def test_sweep_outside_killzone_consumes_level(cfg, bearish_setup_bars, force_bias):
    force_bias(-1)
    bars = bearish_setup_bars.copy()
    # take the Asian high at 07:30 UTC (09:30 Athens) — before London opens
    bars.loc[pd.Timestamp("2024-03-05 07:30", tz="UTC"), "high"] = 2000.5
    out = ict.IctStrategy(cfg).generate_signals(bars)
    assert out.signals == []
    assert any(d.kind == "LEVEL_CONSUMED" for d in out.decisions)


def test_no_lookahead_signals_identical_on_truncated_data(cfg):
    """A signal stamped at time t must be reproducible from data ending at t."""
    m5 = make_m5("2024-01-01", "2024-09-01", seed=11)
    strat = ict.IctStrategy(cfg)
    full = strat.generate_signals(m5)
    assert full.signals, "synthetic sample should contain at least one setup"
    for s in full.signals:
        cut = m5[m5.index < s.time]  # only bars closed by decision time
        part = strat.generate_signals(cut)
        assert part.signals and part.signals[-1] == s


def test_decisions_explain_every_killzone(cfg):
    m5 = make_m5("2024-02-05", "2024-02-10", seed=2)
    out = ict.IctStrategy(cfg).generate_signals(m5)
    days = {d.data.get("day") for d in out.decisions if d.kind == "ASIA_RANGE"}
    assert len(days) >= 4
