"""Live / paper trading loop.

Paper trading = this loop against an MT5 DEMO account (the default).
Real money requires `--live`, a REAL account AND typing a confirmation
phrase in the terminal; any mismatch aborts before a single order.

Each iteration (every poll_seconds):
  1. kill switch (STOP file / Telegram /stop) → flatten + exit
  2. connection check / reconnect (bounded, so step 1 keeps running)
  3. equity → risk manager (daily loss limit, max drawdown → shutdown)
  4. sync with broker: detect fills and closed positions → notify, journal
  5. manage pending orders: expiry, news blackout, target-before-entry
  6. mandatory flat period before the daily break
  7. on a newly closed M5 bar: run the SAME strategy code as the backtest,
     gate each new signal (news, risk, spread, sizing, margin) and place
     the limit order. Every decision is journaled with its reason.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from core.config import Config
from core.models import LONG, Decision, side_name
from core.timeutils import fmt, trading_day
from data.loader import M5
from execution.broker import Broker, BrokerOrder, BrokerPosition
from news.calendar import LiveNewsCalendar
from notifier.daily_report import DailyReporter, DayStats
from notifier.logs import DecisionJournal
from notifier.telegram import Notifier
from risk.killswitch import KillSwitch
from risk.manager import RiskAction, RiskManager
from risk.sizing import position_size
from strategy.ict import IctStrategy

log = logging.getLogger(__name__)


class PreflightError(RuntimeError):
    pass


class LiveAgent:
    def __init__(self, cfg: Config, broker: Broker, notifier: Notifier, news: LiveNewsCalendar, risk: RiskManager,
                 kill: KillSwitch, journal: DecisionJournal, reporter: DailyReporter, state_path: Path,
                 clock: Callable[[], pd.Timestamp] = lambda: pd.Timestamp.now(tz="UTC"),
                 sleep: Callable[[float], None] = time.sleep):
        self.cfg = cfg
        self.broker = broker
        self.notifier = notifier
        self.news = news
        self.risk = risk
        self.kill = kill
        self.journal = journal
        self.reporter = reporter
        self.state_path = state_path
        self.clock = clock
        self.sleep = sleep
        self.strategy = IctStrategy(cfg)
        self.tzd = cfg.time.display_tz
        self.live = False
        self.exit_requested = False
        self._conn_down_since: Optional[float] = None
        self._day: Optional[DayStats] = None
        self.st = self._load_state()

    # ================================================================ state
    def _load_state(self) -> dict:
        base = {"processed_signals": [], "orders": {}, "positions": {}, "last_bar": None, "last_decision": None}
        if self.state_path.exists():
            base.update(json.loads(self.state_path.read_text(encoding="utf-8")))
        return base

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.st["processed_signals"] = self.st["processed_signals"][-500:]
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.st, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, self.state_path)

    def _decide(self, t, kind: str, msg: str, **data) -> None:
        self.journal.write(Decision(pd.Timestamp(t), kind, msg, data))

    # ============================================================ preflight
    def preflight(self, live: bool, confirm: Callable[[str], str] = input,
                  isatty: Callable[[], bool] = lambda: sys.stdin.isatty()) -> None:
        if self.kill.path.exists():
            raise PreflightError(f"kill-switch file {self.kill.path} exists — remove it to start")
        if self.risk.state.shutdown:
            raise PreflightError(f"agent is in SHUTDOWN ({self.risk.state.shutdown_reason}). "
                                 "Review, then run: python main.py reset-shutdown")
        if not self.broker.connect():
            raise PreflightError("cannot connect to MT5")
        acct = self.broker.account()
        spec = self.broker.symbol_spec()
        if not spec.trade_allowed:
            raise PreflightError(f"trading not allowed on {spec.name}")
        if abs(spec.contract_size - self.cfg.symbol.contract_size) > 1e-9:
            log.warning("broker contract size %s ≠ config %s — live sizing uses the broker value",
                        spec.contract_size, self.cfg.symbol.contract_size)
        if live:
            if not acct.is_real:
                raise PreflightError("--live was given but the logged-in account is NOT a real account. Refusing.")
            if not isatty():
                raise PreflightError("live trading requires an interactive terminal for the written confirmation")
            phrase = f"LIVE {acct.login}"
            print("\n" + "!" * 70)
            print(f"  REAL MONEY: account {acct.login} on {acct.server}, equity {acct.equity:.2f} {acct.currency}")
            print(f"  Risk/trade {self.cfg.risk.risk_per_trade_pct}%, daily limit {self.cfg.risk.daily_loss_limit_pct}%, "
                  f"max DD {self.cfg.risk.max_drawdown_pct}%")
            print("!" * 70)
            typed = confirm(f"Type exactly '{phrase}' to start trading real money: ")
            if typed.strip() != phrase:
                raise PreflightError("confirmation phrase mismatch — not starting")
        else:
            if not acct.is_demo:
                raise PreflightError("logged-in account is REAL but --live was not given. Refusing (default is demo).")
        self.live = live
        log.info("preflight ok: %s account %s, equity %.2f %s", "LIVE" if live else "DEMO", acct.login, acct.equity, acct.currency)

    # ============================================================ commands
    def on_command(self, cmd: str, text: str) -> Optional[str]:
        if cmd == "/stop":
            self.kill.trigger("Telegram /stop")
            return "🛑 STOP received — closing positions and shutting down."
        if cmd == "/status":
            return self.status_text()
        return "Commands: /status, /stop"

    def status_text(self) -> str:
        st = self.risk.state
        mode = "LIVE" if self.live else "DEMO"
        return (f"[{mode}] equity {st.last_equity:.2f}, day PnL {st.last_equity - st.day_start_equity:+.2f}, "
                f"trades today {st.trades_today}/{self.cfg.risk.max_trades_per_day}, "
                f"open {len(self.st['positions'])}, pending {len(self.st['orders'])}, "
                f"halted={'yes' if st.halted_day == st.day else 'no'}, shutdown={st.shutdown}")

    # ============================================================ main loop
    def run(self) -> int:
        self.notifier.send(f"▶️ XAUUSD agent started ({'LIVE' if self.live else 'DEMO'}). {self.status_text()}")
        try:
            while not self.exit_requested:
                started = time.monotonic()
                try:
                    self.step()
                except Exception as exc:  # noqa: BLE001 — never die silently mid-trade
                    log.exception("step failed: %s", exc)
                    self.notifier.send(f"⚠️ agent error: {type(exc).__name__}: {exc}")
                    self.sleep(min(30.0, self.cfg.execution.poll_seconds * 4))
                self.sleep(max(0.0, self.cfg.execution.poll_seconds - (time.monotonic() - started)))
        except KeyboardInterrupt:
            log.warning("Ctrl+C — leaving positions with their SL/TP in place and exiting")
            self.notifier.send("⏸ agent stopped by Ctrl+C (positions keep their SL/TP). Use STOP to flatten.")
        finally:
            self._save_state()
        return 0

    def step(self) -> None:
        reason = self.kill.check()
        if reason:
            self.emergency_stop(reason)
            return
        if not self.broker.ensure_connected(max_attempts=1):
            if self._conn_down_since is None:
                self._conn_down_since = time.monotonic()
                self.notifier.send("🔌 MT5 connection lost — reconnecting (server-side SL/TP remain active)")
            return
        if self._conn_down_since is not None:
            down = time.monotonic() - self._conn_down_since
            self._conn_down_since = None
            self.notifier.send(f"✅ MT5 reconnected after {down:.0f}s")

        now = self.clock()
        acct = self.broker.account()
        self._roll_day(now, acct.equity)
        for act in self.risk.on_equity(now, acct.equity):
            if act == RiskAction.SHUTDOWN:
                self.flatten(f"max drawdown: {self.risk.state.shutdown_reason}")
                self.notifier.send(f"⛔ SHUTDOWN — {self.risk.state.shutdown_reason}. All positions closed. "
                                   "Manual reset required.")
                self._decide(now, "SHUTDOWN", self.risk.state.shutdown_reason)
                self._write_day(acct.equity)
                self.exit_requested = True
                return
            if act == RiskAction.CLOSE_ALL_DAILY:
                self.flatten("daily loss limit")
                self.notifier.send(f"🟥 Daily loss limit {self.cfg.risk.daily_loss_limit_pct}% hit — "
                                   "positions closed, no new trades until tomorrow.")
                self._decide(now, "DAILY_LIMIT", "daily loss limit hit")

        positions = self.broker.positions()
        orders = self.broker.orders()
        self._sync(now, positions, orders, acct.equity)
        self._manage_pending(now, orders)
        self._force_flat(now)
        self._on_new_bar(now)
        self._save_state()

    # ============================================================ day roll
    def _roll_day(self, now: pd.Timestamp, equity: float) -> None:
        day = str(trading_day(now, self.cfg.time.trading_day_tz))
        if self._day is None:
            self._day = DayStats(day, self.risk.state.day_start_equity if self.risk.state.day == day else equity)
        elif self._day.date != day:
            self._write_day(equity)
            self._day = DayStats(day, equity)

    def _write_day(self, equity: float) -> None:
        if self._day is None:
            return
        st = self.risk.state
        self.reporter.write_day(self._day, equity, st.halted_day == self._day.date, st.shutdown)

    # ============================================================ sync
    def _sync(self, now, positions: list[BrokerPosition], orders: list[BrokerOrder], equity: float) -> None:
        pos_by = {p.ticket: p for p in positions}
        ord_by = {o.ticket: o for o in orders}
        # pending orders that disappeared: filled or cancelled
        for tk, info in list(self.st["orders"].items()):
            tki = int(tk)
            if tki in ord_by:
                continue
            del self.st["orders"][tk]
            p = pos_by.get(tki) or next((p for p in positions if p.comment == info["comment"]), None)
            if p is None:
                self._decide(now, "ORDER_GONE", f"order {tk} ({info['signal_id']}) no longer exists and no position found")
                continue
            info.update(position=p.ticket, entry_price=p.price_open, entry_time=str(p.time))
            self.st["positions"][str(p.ticket)] = info
            self.risk.register_fill(now)
            day_pnl = equity - self.risk.state.day_start_equity
            self._decide(now, "FILL", f"{info['signal_id']} filled @ {p.price_open:.2f}", signal_id=info["signal_id"])
            self.notifier.send(
                f"🟢 ENTRY {side_name(info['direction'])} {p.volume} XAUUSD @ {p.price_open:.2f}\n"
                f"SL {p.sl:.2f} | TP {p.tp:.2f} | R:R {info['rr']:.2f} | risk {info['risk_amount']:.2f}\n"
                f"{info['killzone']} / {info['entry_type']} | day PnL {day_pnl:+.2f}")
        # adopt unknown positions with our magic (e.g. state file lost)
        for p in positions:
            if str(p.ticket) not in self.st["positions"]:
                spec_cs = self.broker.symbol_spec().contract_size
                risk_amt = abs(p.price_open - p.sl) * p.volume * spec_cs if p.sl else 0.0
                self.st["positions"][str(p.ticket)] = {
                    "signal_id": f"adopted-{p.ticket}", "direction": p.direction, "rr": 0.0, "risk_amount": risk_amt,
                    "killzone": "?", "entry_type": "?", "comment": p.comment, "entry_price": p.price_open,
                    "entry_time": str(p.time), "sl": p.sl, "tp": p.tp, "volume": p.volume,
                }
                log.warning("adopted untracked position %s", p.ticket)
        # positions that disappeared: closed
        for tk, info in list(self.st["positions"].items()):
            if int(tk) in pos_by:
                continue
            res = self.broker.closed_position(int(tk))
            if res is None:
                info["missing_checks"] = info.get("missing_checks", 0) + 1
                if info["missing_checks"] < 12:
                    continue  # deal history may lag a few seconds
                self._decide(now, "EXIT_UNKNOWN", f"position {tk} closed but no deal history found")
                del self.st["positions"][tk]
                continue
            del self.st["positions"][tk]
            r = res.net_profit / info["risk_amount"] if info["risk_amount"] else 0.0
            if self._day:
                self._day.add(res.net_profit, r)
            acct = self.broker.account()
            day_pnl = acct.equity - self.risk.state.day_start_equity
            self.reporter.write_trade({
                "signal_id": info["signal_id"], "side": side_name(info["direction"]), "killzone": info["killzone"],
                "entry_type": info["entry_type"], "entry_time": info.get("entry_time"), "entry_price": info.get("entry_price"),
                "sl": info.get("sl"), "tp": info.get("tp"), "volume": info.get("volume"), "risk_amount": info["risk_amount"],
                "exit_time": str(res.exit_time), "exit_price": res.exit_price, "exit_reason": res.reason,
                "net_pnl": round(res.net_profit, 2), "r_multiple": round(r, 3),
            })
            self._decide(now, "EXIT", f"{info['signal_id']} closed ({res.reason}) {res.net_profit:+.2f} = {r:+.2f}R",
                         signal_id=info["signal_id"], r=r)
            icon = "✅" if res.net_profit > 0 else "🔻"
            self.notifier.send(
                f"{icon} EXIT {side_name(info['direction'])} @ {res.exit_price:.2f} ({res.reason})\n"
                f"Result {res.net_profit:+.2f} = {r:+.2f}R | day PnL {day_pnl:+.2f} "
                f"({day_pnl / self.risk.state.day_start_equity * 100 if self.risk.state.day_start_equity else 0:+.2f}%)")

    # ============================================================ pending / flat
    def _in_flat_zone(self, now: pd.Timestamp) -> bool:
        fc = self.cfg.sessions.force_close
        local = now.tz_convert(fc.tz)
        m = local.hour * 60 + local.minute
        return fc.clock.hour * 60 + fc.clock.minute <= m < 18 * 60

    def _cancel(self, now, tk: str, why: str) -> None:
        info = self.st["orders"].get(tk)
        res = self.broker.cancel_order(int(tk))
        if res.ok:
            self.st["orders"].pop(tk, None)  # on failure keep tracking; _sync resolves fills next step
        self._decide(now, "CANCEL", f"order {tk} ({info['signal_id'] if info else '?'}) cancelled: {why}"
                     + ("" if res.ok else f" [broker: {res.message}]"))

    def _manage_pending(self, now: pd.Timestamp, orders: list[BrokerOrder]) -> None:
        if not self.st["orders"]:
            return
        tick = self.broker.tick()
        news_ok, news_why = self.news.check(now)
        for tk, info in list(self.st["orders"].items()):
            if now >= pd.Timestamp(info["expiry"]):
                self._cancel(now, tk, "expired unfilled")
            elif self._in_flat_zone(now):
                self._cancel(now, tk, "force-close time")
            elif self.cfg.news.cancel_pending_in_blackout and not news_ok:
                self._cancel(now, tk, news_why)
            elif tick is not None and ((info["direction"] == LONG and tick.bid >= info["tp"]) or
                                       (info["direction"] != LONG and tick.ask <= info["tp"])):
                self._cancel(now, tk, "target reached before entry")

    def _force_flat(self, now: pd.Timestamp) -> None:
        if self._in_flat_zone(now) and (self.st["positions"] or self.st["orders"]):
            self.flatten("force-close time before daily break")

    def flatten(self, why: str) -> None:
        now = self.clock()
        for o in self.broker.orders():
            self._cancel(now, str(o.ticket), why)
        for p in self.broker.positions():
            for attempt in range(3):
                res = self.broker.close_position(p)
                if res.ok:
                    self._decide(now, "CLOSE", f"position {p.ticket} closed: {why}")
                    break
                log.error("close %s failed (%s), attempt %d", p.ticket, res.message, attempt + 1)
                self.sleep(1.0)
            else:
                self.notifier.send(f"‼️ FAILED to close position {p.ticket}: close it manually in MT5!")

    def emergency_stop(self, reason: str) -> None:
        log.critical("KILL SWITCH: %s", reason)
        self.notifier.send(f"🛑 KILL SWITCH: {reason} — closing everything and stopping.")
        try:
            if self.broker.ensure_connected(max_attempts=3):
                self.flatten(f"kill switch: {reason}")
                positions = self.broker.positions()
                orders = self.broker.orders()
                self._sync(self.clock(), positions, orders, self.broker.account().equity)
                self._write_day(self.broker.account().equity)
            else:
                self.notifier.send("‼️ Kill switch could not reach MT5 — close positions manually!")
        finally:
            self.exit_requested = True
            self._decide(self.clock(), "KILL", reason)

    # ============================================================ new bar
    def _on_new_bar(self, now: pd.Timestamp) -> None:
        if self.st["last_bar"] and now < pd.Timestamp(self.st["last_bar"]) + 2 * M5:
            return  # the next bar has not closed yet
        rates = self.broker.rates_m5(self.cfg.execution.history_m5_bars)
        if rates.empty:
            return
        last_open = rates.index[-1]
        if self.st["last_bar"] and pd.Timestamp(self.st["last_bar"]) >= last_open:
            return
        self.st["last_bar"] = str(last_open)
        last_close = last_open + M5
        if now - last_close > pd.Timedelta(minutes=10):
            return  # stale data: market closed or feed stalled
        out = self.strategy.generate_signals(rates, since=now - pd.Timedelta(days=1))
        prev = pd.Timestamp(self.st["last_decision"]) if self.st["last_decision"] else last_close - M5
        for d in out.decisions:
            if prev < d.time <= last_close:
                self.journal.write(d)
        self.st["last_decision"] = str(last_close)
        for sig in out.signals:
            if sig.time != last_close or sig.id in self.st["processed_signals"]:
                continue
            self.st["processed_signals"].append(sig.id)
            self._handle_signal(now, sig)

    def _handle_signal(self, now: pd.Timestamp, sig) -> None:
        ok, why = self.news.check(now)
        if not ok:
            self._decide(now, "NEWS_BLOCK", f"{sig.id}: {why}", signal_id=sig.id)
            return
        tick = self.broker.tick()
        spread = tick.spread if tick else None
        open_count = len(self.broker.positions()) + len(self.broker.orders())
        ok, why = self.risk.can_open(now, spread, open_count)
        if not ok:
            self._decide(now, "RISK_BLOCK", f"{sig.id}: {why}", signal_id=sig.id)
            return
        acct = self.broker.account()
        spec = self.broker.symbol_spec()
        slip = self.cfg.costs.slippage_stop
        sl_worst = sig.sl - sig.direction * slip
        per_lot = self.broker.loss_per_lot(sig.direction, sig.entry, sl_worst) + self.cfg.costs.commission_per_lot_rt
        size = position_size(acct.equity, self.risk.risk_pct_for_trade(), per_lot,
                             spec.volume_min, spec.volume_max, spec.volume_step)
        if not size.ok:
            self._decide(now, "SIZE_REJECT", f"{sig.id}: {size.reason}", signal_id=sig.id)
            return
        margin = self.broker.margin_required(sig.direction, size.volume, sig.entry)
        if margin is None or margin > acct.margin_free * self.cfg.risk.max_margin_usage_pct / 100:
            self._decide(now, "MARGIN_REJECT", f"{sig.id}: margin {margin} > {self.cfg.risk.max_margin_usage_pct}% of free margin",
                         signal_id=sig.id)
            return
        comment = f"{self.cfg.execution.order_comment}-{sig.time:%m%d%H%M}"
        res = self.broker.place_limit(sig.direction, size.volume, sig.entry, sig.sl, sig.tp, comment)
        if not res.ok:
            self._decide(now, "ORDER_FAIL", f"{sig.id}: broker rejected ({res.retcode}) {res.message}", signal_id=sig.id)
            self.notifier.send(f"⚠️ order rejected for {sig.id}: {res.retcode} {res.message}")
            return
        risk_amt = self.broker.loss_per_lot(sig.direction, sig.entry, sig.sl) * size.volume
        self.st["orders"][str(res.ticket)] = {
            "signal_id": sig.id, "direction": sig.direction, "volume": size.volume, "entry": sig.entry,
            "sl": sig.sl, "tp": sig.tp, "rr": sig.rr, "risk_amount": risk_amt, "expiry": str(sig.expiry),
            "killzone": sig.killzone, "entry_type": sig.entry_type, "comment": comment,
        }
        self._decide(now, "ORDER", f"{sig.id}: {side_name(sig.direction)} LIMIT {size.volume} @ {sig.entry:.2f} "
                     f"SL {sig.sl:.2f} TP {sig.tp:.2f} risk {risk_amt:.2f} ({risk_amt / acct.equity * 100:.2f}%)",
                     signal_id=sig.id, ticket=res.ticket)
        self.notifier.send(
            f"📝 ORDER {side_name(sig.direction)} LIMIT {size.volume} @ {sig.entry:.2f}\n"
            f"SL {sig.sl:.2f} | TP {sig.tp:.2f} | R:R {sig.rr:.2f} | risk {risk_amt:.2f}\n"
            f"{sig.killzone}/{sig.entry_type}, valid until {fmt(sig.expiry, self.tzd)}")
