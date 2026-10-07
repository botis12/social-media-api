"""MetaTrader 5 adapter (Windows only — the MetaTrader5 package talks to a
running terminal over IPC).

* Credentials come from the environment (.env), never from code/config.
* Every call goes through `_call`, which detects a dropped terminal/IPC
  link and reconnects with exponential backoff.
* MT5 timestamps are broker *server* time encoded as epoch seconds. The
  server's UTC offset is derived from the live tick (or set in config) and
  every time is converted to real UTC at this boundary.
* Orders are validated with order_check before order_send; transient
  retcodes are retried, an unsupported filling mode falls back to the
  others the symbol allows.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd

from core.config import ExecutionCfg
from core.models import LONG, SHORT
from execution.broker import (
    AccountInfo,
    Broker,
    BrokerOrder,
    BrokerPosition,
    ClosedPosition,
    OrderResult,
    SymbolSpec,
    Tick,
)

log = logging.getLogger(__name__)

RET_DONE = {10008, 10009, 10010}  # PLACED, DONE, DONE_PARTIAL
RET_RETRY = {10004, 10012, 10020, 10021, 10024, 10031}  # requote, timeout, price changed/off, too many, no connection
RET_INVALID_FILL = 10030
FILLING_FOK, FILLING_IOC, FILLING_RETURN = 0, 1, 2  # ORDER_FILLING_* values
SYM_FILL_FOK, SYM_FILL_IOC = 1, 2  # SYMBOL_FILLING_* flags


class MT5Error(RuntimeError):
    pass


def _import_mt5():
    try:
        import MetaTrader5 as mt5  # type: ignore
    except ImportError as exc:  # pragma: no cover - platform dependent
        raise MT5Error(
            "MetaTrader5 package not available. It only works on Windows with a running MT5 terminal: "
            "pip install MetaTrader5"
        ) from exc
    return mt5


class MT5Broker(Broker):
    def __init__(self, symbol: str, cfg: ExecutionCfg, mt5_module: Any = None,
                 env: Optional[dict] = None, sleep: Callable[[float], None] = time.sleep,
                 now: Callable[[], float] = time.time):
        self.symbol = symbol
        self.cfg = cfg
        self.mt5 = mt5_module or _import_mt5()
        env = env if env is not None else os.environ
        try:
            self._login = int(env["MT5_LOGIN"])
            self._password = env["MT5_PASSWORD"]
            self._server = env["MT5_SERVER"]
        except (KeyError, ValueError) as exc:
            raise MT5Error("MT5_LOGIN / MT5_PASSWORD / MT5_SERVER must be set in .env") from exc
        self._path = env.get("MT5_PATH") or None
        self._sleep = sleep
        self._now = now
        self._offset_h: Optional[int] = None if cfg.server_utc_offset_hours == "auto" else int(cfg.server_utc_offset_hours)
        self._offset_checked = 0.0
        self._spec: Optional[SymbolSpec] = None

    # ------------------------------------------------------------ connection
    def connect(self) -> bool:
        kwargs = dict(login=self._login, password=self._password, server=self._server, timeout=60_000)
        if self._path:
            kwargs["path"] = self._path
        if not self.mt5.initialize(**kwargs):
            log.error("mt5: initialize failed: %s", self.mt5.last_error())
            return False
        if not self.mt5.symbol_select(self.symbol, True):
            log.error("mt5: symbol_select(%s) failed: %s", self.symbol, self.mt5.last_error())
            return False
        acct = self.mt5.account_info()
        if acct is None or int(acct.login) != self._login:
            log.error("mt5: logged-in account does not match MT5_LOGIN")
            return False
        self._spec = None
        log.info("mt5: connected to %s as %s", self._server, self._login)
        return True

    def _healthy(self) -> bool:
        ti = self.mt5.terminal_info()
        return ti is not None and bool(ti.connected) and self.mt5.account_info() is not None

    def ensure_connected(self, max_attempts: Optional[int] = None) -> bool:
        """Reconnect with exponential backoff. max_attempts=None → config value
        (0 = forever). The live loop passes 1 so it keeps checking the kill
        switch between attempts; open positions keep their server-side SL/TP."""
        if self._healthy():
            return True
        limit = self.cfg.reconnect_max_attempts if max_attempts is None else max_attempts
        attempt, delay = 0, 2.0
        while True:
            attempt += 1
            log.warning("mt5: connection lost — reconnect attempt %d", attempt)
            try:
                self.mt5.shutdown()
            except Exception:  # noqa: BLE001
                pass
            if self.connect() and self._healthy():
                log.info("mt5: reconnected after %d attempt(s)", attempt)
                return True
            if limit and attempt >= limit:
                log.error("mt5: giving up after %d attempts", attempt)
                return False
            self._sleep(delay)
            delay = min(delay * 2, self.cfg.reconnect_backoff_max_s)

    def shutdown(self) -> None:
        try:
            self.mt5.shutdown()
        except Exception:  # noqa: BLE001
            pass

    def _call(self, fn_name: str, *args, **kwargs):
        """Call an mt5 function; on None (IPC failure) reconnect once and retry."""
        fn = getattr(self.mt5, fn_name)
        res = fn(*args, **kwargs)
        if res is None:
            err = self.mt5.last_error()
            log.warning("mt5: %s returned None (%s)", fn_name, err)
            if not self._healthy() and self.ensure_connected(max_attempts=1):
                res = fn(*args, **kwargs)
        return res

    # ------------------------------------------------------------ time
    def _server_offset_h(self) -> int:
        if self._offset_h is not None and self.cfg.server_utc_offset_hours != "auto":
            return self._offset_h
        if self._offset_h is not None and self._now() - self._offset_checked < 60:
            return self._offset_h
        self._offset_checked = self._now()
        tk = self.mt5.symbol_info_tick(self.symbol)
        if tk is not None:
            diff_h = (float(tk.time) - self._now()) / 3600.0
            cand = int(round(diff_h))
            # only trust a fresh tick (market open): fractional part small, plausible range
            if abs(diff_h - cand) < 0.1 and -12 <= cand <= 14:
                if self._offset_h != cand:
                    log.info("mt5: server UTC offset = %+d h", cand)
                self._offset_h = cand
        if self._offset_h is None:
            raise MT5Error("cannot determine server UTC offset (market closed?). Set execution.server_utc_offset_hours")
        return self._offset_h

    def _to_utc(self, server_epoch_s) -> pd.Timestamp:
        return pd.Timestamp(int(server_epoch_s) - self._server_offset_h() * 3600, unit="s", tz="UTC")

    # ------------------------------------------------------------ info
    def account(self) -> AccountInfo:
        a = self._call("account_info")
        if a is None:
            raise MT5Error(f"account_info failed: {self.mt5.last_error()}")
        mode = int(a.trade_mode)
        return AccountInfo(
            login=int(a.login), server=str(a.server), currency=str(a.currency), balance=float(a.balance),
            equity=float(a.equity), margin_free=float(a.margin_free), leverage=int(a.leverage),
            is_demo=mode in (self.mt5.ACCOUNT_TRADE_MODE_DEMO, self.mt5.ACCOUNT_TRADE_MODE_CONTEST),
            is_real=mode == self.mt5.ACCOUNT_TRADE_MODE_REAL,
        )

    def symbol_spec(self) -> SymbolSpec:
        s = self._call("symbol_info", self.symbol)
        if s is None:
            raise MT5Error(f"symbol_info({self.symbol}) failed: {self.mt5.last_error()}")
        self._spec = SymbolSpec(
            name=s.name, digits=int(s.digits), point=float(s.point), tick_size=float(s.trade_tick_size),
            tick_value=float(s.trade_tick_value), contract_size=float(s.trade_contract_size),
            volume_min=float(s.volume_min), volume_max=float(s.volume_max), volume_step=float(s.volume_step),
            stops_level_points=int(s.trade_stops_level), filling_mode=int(s.filling_mode),
            trade_allowed=int(s.trade_mode) == getattr(self.mt5, "SYMBOL_TRADE_MODE_FULL", 4),
        )
        return self._spec

    def _spec_cached(self) -> SymbolSpec:
        return self._spec or self.symbol_spec()

    def tick(self) -> Optional[Tick]:
        t = self._call("symbol_info_tick", self.symbol)
        if t is None:
            return None
        return Tick(self._to_utc(t.time), float(t.bid), float(t.ask))

    def rates_m5(self, count: int) -> pd.DataFrame:
        r = self._call("copy_rates_from_pos", self.symbol, self.mt5.TIMEFRAME_M5, 0, count)
        if r is None or len(r) == 0:
            raise MT5Error(f"copy_rates_from_pos failed: {self.mt5.last_error()}")
        off = self._server_offset_h() * 3600
        point = self._spec_cached().point
        times = pd.to_datetime(np.asarray(r["time"], dtype=np.int64) - off, unit="s", utc=True).as_unit("ns")
        df = pd.DataFrame(
            {
                "open": r["open"], "high": r["high"], "low": r["low"], "close": r["close"],
                "volume": r["tick_volume"].astype(float), "spread": r["spread"].astype(float) * point,
            },
            index=times,
        )
        now = pd.Timestamp(self._now(), unit="s", tz="UTC")
        return df[df.index + pd.Timedelta(minutes=5) <= now]  # drop the still-forming bar

    def positions(self) -> list[BrokerPosition]:
        ps = self._call("positions_get", symbol=self.symbol)
        if ps is None:
            raise MT5Error(f"positions_get failed: {self.mt5.last_error()}")
        return [
            BrokerPosition(int(p.ticket), LONG if p.type == self.mt5.POSITION_TYPE_BUY else SHORT, float(p.volume),
                           float(p.price_open), float(p.sl), float(p.tp), self._to_utc(p.time), float(p.profit), str(p.comment))
            for p in ps if int(p.magic) == self.cfg.magic
        ]

    def orders(self) -> list[BrokerOrder]:
        os_ = self._call("orders_get", symbol=self.symbol)
        if os_ is None:
            raise MT5Error(f"orders_get failed: {self.mt5.last_error()}")
        out = []
        for o in os_:
            if int(o.magic) != self.cfg.magic:
                continue
            d = LONG if o.type in (self.mt5.ORDER_TYPE_BUY_LIMIT, self.mt5.ORDER_TYPE_BUY_STOP) else SHORT
            out.append(BrokerOrder(int(o.ticket), d, float(o.volume_current), float(o.price_open), float(o.sl),
                                   float(o.tp), self._to_utc(o.time_setup), str(o.comment)))
        return out

    # ------------------------------------------------------------ trading
    def _norm(self, price: float) -> float:
        spec = self._spec_cached()
        ts = spec.tick_size or spec.point
        return round(round(price / ts) * ts, spec.digits)

    def _fillings(self, market: bool) -> list[int]:
        fm = self._spec_cached().filling_mode
        allowed = []
        if fm & SYM_FILL_IOC:
            allowed.append(FILLING_IOC)
        if fm & SYM_FILL_FOK:
            allowed.append(FILLING_FOK)
        if market:
            return allowed or [FILLING_RETURN]
        return [FILLING_RETURN] + allowed  # pending orders: RETURN is the norm

    def _send(self, request: dict, market: bool) -> OrderResult:
        last = OrderResult(False, message="not sent")
        for filling in self._fillings(market):
            req = {**request, "type_filling": filling}
            for attempt in range(1, self.cfg.max_order_retries + 1):
                if market:
                    tk = self.mt5.symbol_info_tick(self.symbol)
                    if tk is None:
                        last = OrderResult(False, message="no tick")
                        continue
                    req["price"] = tk.ask if req["type"] == self.mt5.ORDER_TYPE_BUY else tk.bid
                chk = self._call("order_check", req)
                if chk is None:
                    last = OrderResult(False, message=f"order_check failed: {self.mt5.last_error()}")
                    continue
                if int(chk.retcode) not in (0, *RET_DONE):
                    last = OrderResult(False, retcode=int(chk.retcode), message=f"order_check: {chk.comment}")
                    if int(chk.retcode) == RET_INVALID_FILL:
                        break
                    if int(chk.retcode) in RET_RETRY:
                        self._sleep(0.5 * attempt)
                        continue
                    return last
                res = self._call("order_send", req)
                if res is None:
                    last = OrderResult(False, message=f"order_send failed: {self.mt5.last_error()}")
                    self._sleep(0.5 * attempt)
                    continue
                rc = int(res.retcode)
                if rc in RET_DONE:
                    return OrderResult(True, ticket=int(res.order or res.deal), retcode=rc, message=str(res.comment), price=float(res.price))
                last = OrderResult(False, retcode=rc, message=str(res.comment))
                if rc == RET_INVALID_FILL:
                    break
                if rc in RET_RETRY:
                    self._sleep(0.5 * attempt)
                    continue
                return last
        return last

    def place_limit(self, direction, volume, price, sl, tp, comment) -> OrderResult:
        spec = self._spec_cached()
        tk = self.tick()
        if tk is None:
            return OrderResult(False, message="no tick")
        price, sl, tp = self._norm(price), self._norm(sl), self._norm(tp)
        min_dist = spec.stops_level_points * spec.point
        ref = tk.ask if direction == LONG else tk.bid
        if (direction == LONG and price > ref - min_dist) or (direction == SHORT and price < ref + min_dist):
            return OrderResult(False, message=f"limit {price} not beyond current price {ref} by stops level {min_dist}")
        if abs(price - sl) < min_dist or abs(tp - price) < min_dist:
            return OrderResult(False, message=f"SL/TP closer than stops level {min_dist}")
        req = {
            "action": self.mt5.TRADE_ACTION_PENDING,
            "symbol": self.symbol,
            "volume": float(volume),
            "type": self.mt5.ORDER_TYPE_BUY_LIMIT if direction == LONG else self.mt5.ORDER_TYPE_SELL_LIMIT,
            "price": price, "sl": sl, "tp": tp,
            "deviation": self.cfg.deviation_points,
            "magic": self.cfg.magic,
            "comment": comment[:31],
            "type_time": self.mt5.ORDER_TIME_GTC,
        }
        return self._send(req, market=False)

    def cancel_order(self, ticket: int) -> OrderResult:
        req = {"action": self.mt5.TRADE_ACTION_REMOVE, "order": int(ticket), "magic": self.cfg.magic}
        res = self._call("order_send", req)
        if res is None:
            return OrderResult(False, message=str(self.mt5.last_error()))
        return OrderResult(int(res.retcode) in RET_DONE, ticket=ticket, retcode=int(res.retcode), message=str(res.comment))

    def close_position(self, pos: BrokerPosition) -> OrderResult:
        req = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": pos.volume,
            "type": self.mt5.ORDER_TYPE_SELL if pos.direction == LONG else self.mt5.ORDER_TYPE_BUY,
            "position": pos.ticket,
            "price": 0.0,
            "deviation": self.cfg.deviation_points,
            "magic": self.cfg.magic,
            "comment": "close",
            "type_time": self.mt5.ORDER_TIME_GTC,
        }
        return self._send(req, market=True)

    def loss_per_lot(self, direction: int, entry: float, sl: float) -> float:
        typ = self.mt5.ORDER_TYPE_BUY if direction == LONG else self.mt5.ORDER_TYPE_SELL
        p = self._call("order_calc_profit", typ, self.symbol, 1.0, float(entry), float(sl))
        if p is None:
            raise MT5Error(f"order_calc_profit failed: {self.mt5.last_error()}")
        return abs(float(p))

    def margin_required(self, direction: int, volume: float, price: float) -> Optional[float]:
        typ = self.mt5.ORDER_TYPE_BUY if direction == LONG else self.mt5.ORDER_TYPE_SELL
        m = self._call("order_calc_margin", typ, self.symbol, float(volume), float(price))
        return None if m is None else float(m)

    def closed_position(self, position_id: int) -> Optional[ClosedPosition]:
        deals = self._call("history_deals_get", position=int(position_id))
        if not deals:
            return None
        out_deals = [d for d in deals if int(d.entry) in (self.mt5.DEAL_ENTRY_OUT, getattr(self.mt5, "DEAL_ENTRY_OUT_BY", 3))]
        if not out_deals:
            return None
        last = max(out_deals, key=lambda d: d.time_msc)
        net = sum(float(d.profit) + float(d.commission) + float(d.swap) + float(getattr(d, "fee", 0.0)) for d in deals)
        reasons = {getattr(self.mt5, "DEAL_REASON_SL", 4): "sl", getattr(self.mt5, "DEAL_REASON_TP", 5): "tp",
                   getattr(self.mt5, "DEAL_REASON_SO", 6): "stop_out"}
        return ClosedPosition(int(position_id), self._to_utc(last.time), float(last.price), net,
                              reasons.get(int(last.reason), "manual/expert"))
