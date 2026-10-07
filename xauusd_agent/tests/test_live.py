from pathlib import Path
from typing import Optional

import pandas as pd
import pytest

from core.models import LONG, SHORT, Signal
from execution.broker import (AccountInfo, Broker, BrokerOrder, BrokerPosition, ClosedPosition, OrderResult,
                              SymbolSpec, Tick)
from execution.live import LiveAgent, PreflightError
from news.calendar import LiveNewsCalendar
from notifier.daily_report import DailyReporter
from notifier.logs import DecisionJournal
from notifier.telegram import Notifier, TelegramNotifier
from risk.killswitch import KillSwitch
from risk.manager import RiskManager, StateStore

NOW = pd.Timestamp("2026-10-06 08:50", tz="UTC")  # Tuesday, inside London KZ


class FakeBroker(Broker):
    def __init__(self, real=False, equity=10_000.0):
        self.acct = AccountInfo(123, "Demo-Server", "USD", equity, equity, equity, 100, not real, real)
        self.spec = SymbolSpec("XAUUSD", 2, 0.01, 0.01, 1.0, 100, 0.01, 50, 0.01, 0, 2, True)
        self._tick = Tick(NOW, 1995.0, 1995.2)
        self.pos: list[BrokerPosition] = []
        self.ords: list[BrokerOrder] = []
        self.placed, self.closed, self.cancelled = [], [], []
        self.connected = True
        self._next = 1000

    def connect(self): return self.connected
    def ensure_connected(self, max_attempts=None): return self.connected
    def shutdown(self): pass
    def account(self): return self.acct
    def symbol_spec(self): return self.spec
    def tick(self): return self._tick
    def rates_m5(self, count): return pd.DataFrame()
    def positions(self): return list(self.pos)
    def orders(self): return list(self.ords)

    def place_limit(self, direction, volume, price, sl, tp, comment):
        self._next += 1
        self.placed.append((direction, volume, price, sl, tp))
        self.ords.append(BrokerOrder(self._next, direction, volume, price, sl, tp, NOW, comment))
        return OrderResult(True, ticket=self._next)

    def cancel_order(self, ticket):
        self.cancelled.append(ticket)
        self.ords = [o for o in self.ords if o.ticket != ticket]
        return OrderResult(True, ticket=ticket)

    def close_position(self, pos):
        self.closed.append(pos.ticket)
        self.pos = [p for p in self.pos if p.ticket != pos.ticket]
        return OrderResult(True, ticket=pos.ticket)

    def loss_per_lot(self, direction, entry, sl): return abs(entry - sl) * 100
    def margin_required(self, direction, volume, price): return volume * price * 100 / 100
    def closed_position(self, position_id) -> Optional[ClosedPosition]:
        return ClosedPosition(position_id, NOW, 1990.0, 90.0, "tp")


class RecNotifier(Notifier):
    def __init__(self):
        self.msgs = []

    def send(self, text):
        self.msgs.append(text)


class OkNews:
    def __init__(self, ok=True, why="ok"):
        self.ok, self.why = ok, why

    def check(self, t=None):
        return self.ok, self.why


def make_agent(cfg, tmp_path, broker=None, news=None, now=NOW):
    broker = broker or FakeBroker()
    risk = RiskManager(cfg.risk, cfg.time.trading_day_tz, StateStore(tmp_path / "risk.json"))
    agent = LiveAgent(cfg, broker, RecNotifier(), news or OkNews(), risk, KillSwitch(tmp_path / "STOP"),
                      DecisionJournal(tmp_path / "decisions.jsonl"), DailyReporter(tmp_path / "reports"),
                      tmp_path / "agent_state.json", clock=lambda: now, sleep=lambda s: None)
    return agent, broker


def sig(direction=SHORT, entry=2000.0, sl=2005.0, tp=1985.0):
    t = NOW
    return Signal("s1", t, 0, direction, entry, sl, tp, 3.0, "london", "fvg", t + pd.Timedelta(hours=1),
                  2000, 1985, 2004.7, 2.0)


# ------------------------------------------------------------- preflight
def test_demo_by_default(cfg, tmp_path):
    agent, _ = make_agent(cfg, tmp_path)
    agent.preflight(live=False)
    assert agent.live is False


def test_refuses_real_account_without_live_flag(cfg, tmp_path):
    agent, _ = make_agent(cfg, tmp_path, FakeBroker(real=True))
    with pytest.raises(PreflightError, match="REAL"):
        agent.preflight(live=False)


def test_live_flag_refuses_demo_account(cfg, tmp_path):
    agent, _ = make_agent(cfg, tmp_path)
    with pytest.raises(PreflightError, match="NOT a real account"):
        agent.preflight(live=True, confirm=lambda p: "LIVE 123", isatty=lambda: True)


def test_live_requires_exact_typed_confirmation(cfg, tmp_path):
    agent, _ = make_agent(cfg, tmp_path, FakeBroker(real=True))
    with pytest.raises(PreflightError, match="mismatch"):
        agent.preflight(live=True, confirm=lambda p: "yes", isatty=lambda: True)
    with pytest.raises(PreflightError, match="interactive"):
        agent.preflight(live=True, confirm=lambda p: "LIVE 123", isatty=lambda: False)
    agent.preflight(live=True, confirm=lambda p: "LIVE 123", isatty=lambda: True)
    assert agent.live is True


def test_refuses_to_start_with_stop_file_or_shutdown(cfg, tmp_path):
    (tmp_path / "STOP").touch()
    agent, _ = make_agent(cfg, tmp_path)
    with pytest.raises(PreflightError, match="kill-switch"):
        agent.preflight(live=False)
    (tmp_path / "STOP").unlink()
    agent.risk.state.shutdown = True
    with pytest.raises(PreflightError, match="SHUTDOWN"):
        agent.preflight(live=False)


# ------------------------------------------------------------- signals
def _ready(agent):
    agent.risk.on_equity(NOW, agent.broker.account().equity)


def test_signal_places_sized_limit_order(cfg, tmp_path):
    agent, b = make_agent(cfg, tmp_path)
    _ready(agent)
    agent._handle_signal(NOW, sig())
    assert len(b.placed) == 1
    d, vol, price, sl, tp = b.placed[0]
    # $50 budget / ((5 + 0.1 slippage) × 100 + 7 commission) = 0.0967 → 0.09
    assert (d, vol, price, sl, tp) == (SHORT, pytest.approx(0.09), 2000.0, 2005.0, 1985.0)
    assert any("ORDER" in m for m in agent.notifier.msgs)


def test_signal_blocked_by_news(cfg, tmp_path):
    agent, b = make_agent(cfg, tmp_path, news=OkNews(False, "news blackout: CPI"))
    _ready(agent)
    agent._handle_signal(NOW, sig())
    assert b.placed == []


def test_signal_blocked_by_spread_and_open_position(cfg, tmp_path):
    agent, b = make_agent(cfg, tmp_path)
    _ready(agent)
    b._tick = Tick(NOW, 1995.0, 1996.0)  # $1 spread
    agent._handle_signal(NOW, sig())
    assert b.placed == []
    b._tick = Tick(NOW, 1995.0, 1995.2)
    b.pos.append(BrokerPosition(5, LONG, 0.1, 1990, 1985, 2000, NOW, 0.0, "x"))
    agent._handle_signal(NOW, sig())
    assert b.placed == []


def test_fill_and_exit_are_notified_with_r_and_day_pnl(cfg, tmp_path):
    agent, b = make_agent(cfg, tmp_path)
    _ready(agent)
    agent._handle_signal(NOW, sig())
    tk = b.ords[0].ticket
    # broker fills the order: order disappears, position with the same ticket appears
    b.ords = []
    b.pos = [BrokerPosition(tk, SHORT, 0.09, 2000.0, 2005.0, 1985.0, NOW, 0.0, "c")]
    agent._sync(NOW, b.positions(), b.orders(), 10_000)
    assert agent.risk.state.trades_today == 1
    assert any(m.startswith("🟢 ENTRY") for m in agent.notifier.msgs)
    b.pos = []
    agent._sync(NOW, b.positions(), b.orders(), 10_090)
    exit_msg = [m for m in agent.notifier.msgs if "EXIT" in m][0]
    assert "+2.00R" in exit_msg and "day PnL" in exit_msg  # 90 / (5 × 0.09 × 100)
    assert (tmp_path / "reports" / "live_trades.csv").exists()


# ------------------------------------------------------------- kill switch
def test_kill_switch_file_flattens_and_stops(cfg, tmp_path):
    agent, b = make_agent(cfg, tmp_path)
    b.pos = [BrokerPosition(7, LONG, 0.1, 1990, 1985, 2000, NOW, 0.0, "x")]
    b.ords = [BrokerOrder(8, SHORT, 0.1, 2000, 2005, 1985, NOW, "y")]
    (tmp_path / "STOP").touch()
    agent.step()
    assert b.closed == [7] and b.cancelled == [8]
    assert agent.exit_requested
    assert any("KILL SWITCH" in m for m in agent.notifier.msgs)


def test_telegram_stop_command_triggers_kill_switch(cfg, tmp_path):
    agent, b = make_agent(cfg, tmp_path)
    reply = agent.on_command("/stop", "/stop")
    assert "STOP" in reply
    b.pos = [BrokerPosition(7, LONG, 0.1, 1990, 1985, 2000, NOW, 0.0, "x")]
    agent.step()
    assert b.closed == [7] and agent.exit_requested


def test_max_drawdown_shutdown_flattens(cfg, tmp_path):
    agent, b = make_agent(cfg, tmp_path)
    agent.risk.on_equity(NOW - pd.Timedelta(days=3), 10_000)
    b.pos = [BrokerPosition(7, LONG, 0.1, 1990, 1985, 2000, NOW, 0.0, "x")]
    b.acct = AccountInfo(123, "s", "USD", 9_150, 9_150, 9_000, 100, True, False)
    agent.step()
    assert b.closed == [7] and agent.exit_requested and agent.risk.state.shutdown


def test_disconnect_does_not_trade_and_notifies_once(cfg, tmp_path):
    agent, b = make_agent(cfg, tmp_path)
    b.connected = False
    agent.step()
    agent.step()
    assert sum("connection lost" in m for m in agent.notifier.msgs) == 1
    b.connected = True
    agent.step()
    assert any("reconnected" in m for m in agent.notifier.msgs)


def test_pending_cancelled_on_expiry_and_news(cfg, tmp_path):
    agent, b = make_agent(cfg, tmp_path)
    _ready(agent)
    agent._handle_signal(NOW, sig())
    agent.news = OkNews(False, "news blackout: NFP")
    agent._manage_pending(NOW + pd.Timedelta(minutes=5), b.orders())
    assert b.cancelled and agent.st["orders"] == {}


# ------------------------------------------------------------- telegram auth
def test_telegram_ignores_unauthorised_and_stale_commands():
    calls = []
    tg = TelegramNotifier("tok", "42", on_command=lambda c, t: calls.append(c), session=object())
    now = tg._started_at + 5
    tg.handle_update({"message": {"chat": {"id": 999}, "text": "/stop", "date": now}})
    tg.handle_update({"message": {"chat": {"id": 42}, "text": "/stop", "date": tg._started_at - 100}})
    assert calls == []
    tg.handle_update({"message": {"chat": {"id": 42}, "text": "/stop@mybot", "date": now}})
    assert calls == ["/stop"]
