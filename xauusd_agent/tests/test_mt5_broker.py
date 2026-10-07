"""MT5 adapter against a fake MetaTrader5 module (the real one is Windows-only)."""
from types import SimpleNamespace as NS

import numpy as np
import pandas as pd
import pytest

from core.models import LONG, SHORT
from execution.mt5_broker import MT5Broker, MT5Error

NOW = 1_780_000_000.0  # fixed "real" UTC epoch


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO, ACCOUNT_TRADE_MODE_CONTEST, ACCOUNT_TRADE_MODE_REAL = 0, 1, 2
    TIMEFRAME_M5 = 5
    TRADE_ACTION_PENDING, TRADE_ACTION_DEAL, TRADE_ACTION_REMOVE = 5, 1, 8
    ORDER_TYPE_BUY, ORDER_TYPE_SELL, ORDER_TYPE_BUY_LIMIT, ORDER_TYPE_SELL_LIMIT = 0, 1, 2, 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TIME_GTC = 0
    POSITION_TYPE_BUY = 0
    DEAL_ENTRY_OUT = 1
    DEAL_REASON_SL, DEAL_REASON_TP = 4, 5

    def __init__(self, offset_h=3, filling_mode=2):
        self.offset = offset_h * 3600
        self.connected = True
        self.init_calls = 0
        self.sent = []
        self.reject_fillings = {2}  # RETURN unsupported → must fall back
        self.filling_mode = filling_mode

    def initialize(self, **kw):
        self.init_calls += 1
        self.connected = True
        return True

    def shutdown(self):
        self.connected = False

    def last_error(self):
        return (-10004, "No IPC connection")

    def terminal_info(self):
        return NS(connected=True) if self.connected else None

    def symbol_select(self, s, on):
        return True

    def account_info(self):
        if not self.connected:
            return None
        return NS(login=123, trade_mode=0, balance=1e4, equity=1e4, margin_free=1e4, currency="USD", leverage=100, server="S")

    def symbol_info(self, s):
        return NS(name=s, digits=2, point=0.01, trade_tick_size=0.01, trade_tick_value=1.0, trade_contract_size=100.0,
                  volume_min=0.01, volume_max=50.0, volume_step=0.01, trade_stops_level=10,
                  filling_mode=self.filling_mode, trade_mode=4)

    def symbol_info_tick(self, s):
        return NS(time=int(NOW + self.offset), bid=2000.0, ask=2000.25)

    def copy_rates_from_pos(self, s, tf, start, count):
        t0 = int(NOW + self.offset) // 300 * 300 - 300 * 3
        dt = np.dtype([("time", "i8"), ("open", "f8"), ("high", "f8"), ("low", "f8"), ("close", "f8"),
                       ("tick_volume", "i8"), ("spread", "i4"), ("real_volume", "i8")])
        return np.array([(t0 + 300 * k, 1, 2, 0.5, 1.5, 10, 25, 0) for k in range(4)], dtype=dt)

    def order_check(self, req):
        return NS(retcode=0, comment="ok")

    def order_send(self, req):
        self.sent.append(dict(req))
        if req.get("type_filling") in self.reject_fillings:
            return NS(retcode=10030, comment="Unsupported filling mode", order=0, deal=0, price=0)
        return NS(retcode=10009, comment="done", order=555, deal=0, price=req.get("price", 0))

    def order_calc_profit(self, typ, s, vol, a, b):
        return (b - a) * 100 * vol * (1 if typ == 0 else -1)


ENV = {"MT5_LOGIN": "123", "MT5_PASSWORD": "x", "MT5_SERVER": "S"}


def make(cfg, fake=None):
    fake = fake or FakeMT5()
    return MT5Broker("XAUUSD", cfg.execution, mt5_module=fake, env=ENV, sleep=lambda s: None, now=lambda: NOW), fake


def test_requires_credentials_from_env(cfg):
    with pytest.raises(MT5Error, match=".env"):
        MT5Broker("XAUUSD", cfg.execution, mt5_module=FakeMT5(), env={})


def test_server_offset_and_closed_bars_only(cfg):
    b, _ = make(cfg)
    b.connect()
    tk = b.tick()
    assert tk.time == pd.Timestamp(NOW, unit="s", tz="UTC")  # server +3h converted back to UTC
    df = b.rates_m5(10)
    assert (df.index + pd.Timedelta(minutes=5) <= pd.Timestamp(NOW, unit="s", tz="UTC")).all()
    assert df["spread"].iloc[0] == pytest.approx(0.25)


def test_pending_order_falls_back_to_supported_filling(cfg):
    b, fake = make(cfg)
    b.connect()
    res = b.place_limit(SHORT, 0.1, 2010.0, 2015.0, 1990.0, "c")
    assert res.ok and res.ticket == 555
    assert [r["type_filling"] for r in fake.sent] == [2, 1]  # RETURN rejected → IOC
    assert fake.sent[-1]["type"] == FakeMT5.ORDER_TYPE_SELL_LIMIT


def test_rejects_limit_on_wrong_side_or_inside_stops_level(cfg):
    b, fake = make(cfg)
    b.connect()
    assert not b.place_limit(LONG, 0.1, 2001.0, 1995.0, 2010.0, "c").ok  # buy limit above ask
    assert not b.place_limit(SHORT, 0.1, 2000.05, 2005.0, 1990.0, "c").ok  # within stops level
    assert fake.sent == []


def test_reconnects_when_terminal_drops(cfg):
    b, fake = make(cfg)
    b.connect()
    fake.connected = False
    assert b.ensure_connected(max_attempts=2)
    assert fake.init_calls == 2


def test_loss_per_lot_uses_broker_calc(cfg):
    b, _ = make(cfg)
    b.connect()
    assert b.loss_per_lot(LONG, 2000.0, 1995.0) == pytest.approx(500.0)
    assert b.loss_per_lot(SHORT, 2000.0, 2005.0) == pytest.approx(500.0)
