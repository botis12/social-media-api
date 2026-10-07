import pandas as pd
import pytest

from backtest import metrics
from backtest.engine import run_backtest
from core.models import LONG, SHORT, Signal
from data.synthetic import make_m5
from news.calendar import NewsEvent, NewsFilter, backtest_filter
from strategy.ict import StrategyOutput
from tests.conftest import flat_bars, set_bar

T0 = "2024-03-05 08:45"


def _sig(bars, direction, entry, sl, tp, at=T0, expiry_bars=12):
    i = bars.index.get_loc(pd.Timestamp(at, tz="UTC"))
    t = bars.index[i] + pd.Timedelta(minutes=5)
    return Signal("t1", t, i, direction, entry, sl, tp, abs(tp - entry) / abs(entry - sl), "london", "fvg",
                  t + expiry_bars * pd.Timedelta(minutes=5), 0, 0, 0, 1.0)


def _run(cfg, bars, sig, news=None, **cost_overrides):
    costs = cfg.costs.model_copy(update={"spread_source": "fixed", "spread_fixed": 0.2, "spread_min": 0.0,
                                         "slippage_stop": 0.1, "commission_per_lot_rt": 7.0, **cost_overrides})
    c = cfg.model_copy(update={"costs": costs})
    return run_backtest(bars, c, news or NewsFilter([], cfg.news), strategy_output=StrategyOutput([sig], []))


@pytest.fixture
def bars():
    return flat_bars("2024-03-05 00:00", "2024-03-05 14:00", price=1995.0)


def test_short_fill_then_tp(cfg, bars):
    set_bar(bars, "2024-03-05 08:50", 1995, 2000.5, 1994, 1999)   # bid reaches 2000 → fill
    set_bar(bars, "2024-03-05 08:55", 1999, 1999.5, 1989, 1990)   # ask low 1989.2 ≤ 1990 → TP
    res = _run(cfg, bars, _sig(bars, SHORT, 2000.0, 2005.0, 1990.0))
    t = res.trades[0]
    assert t.exit_reason == "tp" and t.exit_price == 1990.0
    # 0.5% of 10k = 50; per lot (5+0.1)*100+7 = 517 → 0.09 lots
    assert t.volume == pytest.approx(0.09)
    assert t.gross_pnl == pytest.approx(10 * 0.09 * 100)
    assert t.net_pnl == pytest.approx(90 - 0.63)
    assert t.r_multiple == pytest.approx((90 - 0.63) / (5 * 0.09 * 100))


def test_same_bar_sl_and_tp_counts_as_loss(cfg, bars):
    set_bar(bars, "2024-03-05 08:50", 1995, 2000.5, 1994, 1999)
    set_bar(bars, "2024-03-05 08:55", 1999, 2006, 1989, 1995)
    res = _run(cfg, bars, _sig(bars, SHORT, 2000.0, 2005.0, 1990.0))
    t = res.trades[0]
    assert t.exit_reason == "sl" and t.exit_price == pytest.approx(2005.1)  # + slippage
    assert t.r_multiple < -1.0  # costs make a full stop worse than −1R


def test_fill_bar_can_stop_out_but_never_take_profit(cfg, bars):
    set_bar(bars, "2024-03-05 08:50", 1995, 2005.5, 1989, 1995)  # fills, touches SL and TP
    res = _run(cfg, bars, _sig(bars, SHORT, 2000.0, 2005.0, 1990.0))
    assert res.trades[0].exit_reason == "sl"


def test_long_needs_ask_to_reach_limit(cfg, bars):
    # bid low 1990.1 + spread 0.2 = 1990.3 > 1990.2 → no fill
    set_bar(bars, "2024-03-05 08:50", 1995, 1995.5, 1990.1, 1994)
    res = _run(cfg, bars, _sig(bars, LONG, 1990.2, 1985.0, 2005.0, expiry_bars=1))
    assert res.trades == []
    assert any(d.kind == "CANCEL" and "expired" in d.message for d in res.decisions)


def test_target_before_entry_cancels(cfg, bars):
    set_bar(bars, "2024-03-05 08:50", 1995, 1995.5, 1989, 1990)  # price runs to TP without filling the sell
    res = _run(cfg, bars, _sig(bars, SHORT, 2000.0, 2005.0, 1990.0))
    assert res.trades == []
    assert any("target reached before entry" in d.message for d in res.decisions)


def test_gap_through_stop_fills_at_open(cfg, bars):
    set_bar(bars, "2024-03-05 08:50", 1995, 2000.5, 1994, 1999)
    set_bar(bars, "2024-03-05 08:55", 2008, 2009, 2007, 2008)  # gaps above SL
    res = _run(cfg, bars, _sig(bars, SHORT, 2000.0, 2005.0, 1990.0))
    t = res.trades[0]
    assert t.exit_reason == "sl_gap" and t.exit_price == pytest.approx(2008 + 0.2 + 0.1)


def test_news_blackout_blocks_new_order(cfg, bars):
    news = NewsFilter([NewsEvent(pd.Timestamp("2024-03-05 09:00", tz="UTC"), "CPI m/m", "USD", "High", "t")], cfg.news)
    set_bar(bars, "2024-03-05 08:50", 1995, 2000.5, 1994, 1999)
    res = _run(cfg, bars, _sig(bars, SHORT, 2000.0, 2005.0, 1990.0), news=news)
    assert res.trades == []
    assert any(d.kind == "NEWS_BLOCK" for d in res.decisions)


def test_spread_filter_blocks(cfg, bars):
    res = _run(cfg, bars, _sig(bars, SHORT, 2000.0, 2005.0, 1990.0), spread_fixed=cfg.risk.max_spread + 0.5)
    assert res.trades == [] and any(d.kind == "RISK_BLOCK" and "spread" in d.message for d in res.decisions)


def test_force_close_before_daily_break(cfg):
    bars = flat_bars("2024-03-05 12:00", "2024-03-05 23:00", price=1995.0)
    set_bar(bars, "2024-03-05 13:55", 1995, 2000.5, 1994, 1999)
    res = _run(cfg, bars, _sig(bars, SHORT, 2000.0, 2010.0, 1980.0, at="2024-03-05 13:50"))
    t = res.trades[0]
    assert t.exit_reason == "force_close"
    assert t.exit_time == pd.Timestamp("2024-03-05 21:45", tz="UTC")  # 16:45 New York (EST)


def test_random_data_has_no_edge(cfg):
    """Sanity check of the whole pipeline: a random walk must not look profitable."""
    m5 = make_m5("2023-01-01", "2025-01-01", seed=5)
    res = run_backtest(m5, cfg, backtest_filter(cfg.news, cfg.path))
    m = metrics.compute(res.trades, res.equity, res.initial_equity, cfg.time.trading_day_tz)
    assert m["max_drawdown_pct"] < cfg.risk.max_drawdown_pct + 1.5
    if m["trades"] >= 10:
        assert m["expectancy_r"] < 0.5
