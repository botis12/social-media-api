import pandas as pd
import pytest
from pydantic import ValidationError

from core.config import RiskCfg
from risk.killswitch import KillSwitch
from risk.manager import RiskAction, RiskManager, StateStore

TZ = "Europe/Athens"


def ts(s):
    return pd.Timestamp(s, tz=TZ).tz_convert("UTC")


@pytest.fixture
def rm(cfg):
    m = RiskManager(cfg.risk, TZ)
    m.on_equity(ts("2024-03-05 09:00"), 10_000)
    return m


def test_initial_state_allows_trading(rm):
    ok, why = rm.can_open(ts("2024-03-05 10:00"), 0.2, 0)
    assert ok, why


def test_max_trades_per_day(rm):
    rm.register_fill(ts("2024-03-05 10:00"))
    assert rm.can_open(ts("2024-03-05 11:00"), 0.2, 0)[0]
    rm.register_fill(ts("2024-03-05 11:00"))
    ok, why = rm.can_open(ts("2024-03-05 12:00"), 0.2, 0)
    assert not ok and "max trades" in why
    # next day resets
    rm.on_equity(ts("2024-03-06 09:00"), 10_000)
    assert rm.can_open(ts("2024-03-06 10:00"), 0.2, 0)[0]


def test_max_one_open_position_or_order(rm):
    ok, why = rm.can_open(ts("2024-03-05 10:00"), 0.2, 1)
    assert not ok and "open" in why


def test_spread_filter(rm, cfg):
    assert rm.can_open(ts("2024-03-05 10:00"), cfg.risk.max_spread, 0)[0]
    ok, why = rm.can_open(ts("2024-03-05 10:00"), cfg.risk.max_spread + 0.01, 0)
    assert not ok and "spread" in why
    assert not rm.can_open(ts("2024-03-05 10:00"), None, 0)[0]


def test_daily_loss_limit_halts_until_next_day(rm):
    assert rm.on_equity(ts("2024-03-05 11:00"), 9_801) == []  # -1.99%
    acts = rm.on_equity(ts("2024-03-05 11:05"), 9_800)  # -2.00%
    assert RiskAction.CLOSE_ALL_DAILY in acts
    ok, why = rm.can_open(ts("2024-03-05 12:00"), 0.2, 0)
    assert not ok and "daily loss" in why
    # recovery the same day does not lift the halt
    rm.on_equity(ts("2024-03-05 15:00"), 10_050)
    assert not rm.can_open(ts("2024-03-05 15:05"), 0.2, 0)[0]
    # new trading day (00:00 Athens) lifts it
    rm.on_equity(ts("2024-03-06 00:05"), 10_050)
    assert rm.can_open(ts("2024-03-06 10:00"), 0.2, 0)[0]
    assert rm.state.day_start_equity == 10_050


def test_daily_limit_fires_once(rm):
    assert rm.on_equity(ts("2024-03-05 11:00"), 9_700)
    assert rm.on_equity(ts("2024-03-05 11:05"), 9_650) == []


def test_risk_capped_to_remaining_daily_budget(rm, cfg):
    assert rm.risk_pct_for_trade() == cfg.risk.risk_per_trade_pct
    rm.on_equity(ts("2024-03-05 11:00"), 9_820)  # -1.8% → 0.2% left
    assert rm.risk_pct_for_trade() == pytest.approx(0.2)


def test_max_drawdown_shutdown_from_high_water_mark(rm):
    rm.on_equity(ts("2024-03-05 11:00"), 10_500)  # new peak
    rm.on_equity(ts("2024-03-06 11:00"), 9_800)  # 6.7% from peak
    assert not rm.state.shutdown
    acts = rm.on_equity(ts("2024-03-07 11:00"), 9_660)  # 8.0% from 10,500
    assert RiskAction.SHUTDOWN in acts
    ok, why = rm.can_open(ts("2024-03-07 11:05"), 0.2, 0)
    assert not ok and "shut down" in why
    # stays shut down even after equity recovers / next day
    rm.on_equity(ts("2024-03-08 11:00"), 11_000)
    assert not rm.can_open(ts("2024-03-08 11:05"), 0.2, 0)[0]


def test_state_persists_across_restart(cfg, tmp_path):
    store = StateStore(tmp_path / "risk.json")
    a = RiskManager(cfg.risk, TZ, store)
    a.on_equity(ts("2024-03-05 09:00"), 10_000)
    a.register_fill(ts("2024-03-05 10:00"))
    a.on_equity(ts("2024-03-05 11:00"), 9_100)  # -9% → shutdown
    b = RiskManager(cfg.risk, TZ, StateStore(tmp_path / "risk.json"))
    assert b.state.shutdown and b.state.trades_today == 1
    assert not b.can_open(ts("2024-03-05 12:00"), 0.2, 0)[0]
    b.reset_shutdown()
    c = RiskManager(cfg.risk, TZ, StateStore(tmp_path / "risk.json"))
    assert not c.state.shutdown and c.state.peak_equity == 9_100


def test_restart_same_day_keeps_trade_count(cfg, tmp_path):
    a = RiskManager(cfg.risk, TZ, StateStore(tmp_path / "r.json"))
    a.on_equity(ts("2024-03-05 09:00"), 10_000)
    a.register_fill(ts("2024-03-05 10:00"))
    a.register_fill(ts("2024-03-05 11:00"))
    b = RiskManager(cfg.risk, TZ, StateStore(tmp_path / "r.json"))
    b.on_equity(ts("2024-03-05 12:00"), 10_000)
    assert not b.can_open(ts("2024-03-05 12:00"), 0.2, 0)[0]


@pytest.mark.parametrize("field,value", [("risk_per_trade_pct", 1.5), ("risk_per_trade_pct", 0.25),
                                         ("max_trades_per_day", 3), ("max_open_positions", 2),
                                         ("daily_loss_limit_pct", 2.5), ("max_drawdown_pct", 10.0)])
def test_config_cannot_loosen_non_negotiable_limits(cfg, field, value):
    data = cfg.risk.model_dump()
    data[field] = value
    with pytest.raises(ValidationError):
        RiskCfg.model_validate(data)


def test_kill_switch_file_and_trigger(tmp_path):
    ks = KillSwitch(tmp_path / "STOP")
    assert ks.check() is None
    (tmp_path / "STOP").touch()
    assert "STOP" in ks.check()
    ks2 = KillSwitch(tmp_path / "nope")
    ks2.trigger("Telegram /stop")
    assert ks2.check() == "Telegram /stop"
