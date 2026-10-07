"""Account-level risk limits — the same object guards backtest and live.

* max trades per day / max open positions (pending orders count as open)
* daily loss limit, measured from equity at the start of the trading day:
  hit → no new trades until the next day (and optionally close positions)
* max drawdown from the equity high-water mark: hit → close everything and
  shut down. Shutdown is persisted and survives restarts; it can only be
  cleared manually (`python main.py reset-shutdown`).
* spread filter
State is persisted atomically so a crash/restart cannot reset the limits.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import pandas as pd

from core.config import RiskCfg
from core.timeutils import trading_day

log = logging.getLogger(__name__)


class RiskAction(str, Enum):
    CLOSE_ALL_DAILY = "close_all_daily_limit"
    SHUTDOWN = "shutdown_max_drawdown"


@dataclass
class RiskState:
    day: str = ""
    day_start_equity: float = 0.0
    trades_today: int = 0
    peak_equity: float = 0.0
    halted_day: str = ""
    shutdown: bool = False
    shutdown_reason: str = ""
    last_equity: float = 0.0


class StateStore:
    """JSON file store with atomic replace. path=None → in-memory (backtest)."""

    def __init__(self, path: Optional[Path]):
        self.path = path

    def load(self) -> RiskState:
        if self.path and self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return RiskState(**{k: v for k, v in data.items() if k in RiskState.__dataclass_fields__})
        return RiskState()

    def save(self, st: RiskState) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(asdict(st), fh, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.path)


class RiskManager:
    def __init__(self, cfg: RiskCfg, day_tz: str, store: Optional[StateStore] = None):
        self.cfg = cfg
        self.day_tz = day_tz
        self.store = store or StateStore(None)
        self.state = self.store.load()

    # ---------------------------------------------------------- equity feed
    def on_equity(self, t: pd.Timestamp, equity: float, day: Optional[str] = None) -> list[RiskAction]:
        st = self.state
        actions: list[RiskAction] = []
        day = day or str(trading_day(t, self.day_tz))
        changed = False
        if day != st.day:
            st.day = day
            st.day_start_equity = equity
            st.trades_today = 0
            changed = True
            log.info("risk: new trading day %s, start equity %.2f", day, equity)
        if equity > st.peak_equity:
            st.peak_equity = equity
            changed = True
        st.last_equity = equity

        if not st.shutdown and st.peak_equity > 0:
            dd = (st.peak_equity - equity) / st.peak_equity * 100
            if dd >= self.cfg.max_drawdown_pct:
                st.shutdown = True
                st.shutdown_reason = f"max drawdown {dd:.2f}% >= {self.cfg.max_drawdown_pct}% (peak {st.peak_equity:.2f}, equity {equity:.2f})"
                log.critical("risk: SHUTDOWN — %s", st.shutdown_reason)
                actions.append(RiskAction.SHUTDOWN)
                changed = True
        if not st.shutdown and st.halted_day != day and st.day_start_equity > 0:
            loss = (st.day_start_equity - equity) / st.day_start_equity * 100
            if loss >= self.cfg.daily_loss_limit_pct:
                st.halted_day = day
                log.error("risk: daily loss %.2f%% >= %.2f%% — no new trades until next day", loss, self.cfg.daily_loss_limit_pct)
                if self.cfg.close_positions_on_daily_limit:
                    actions.append(RiskAction.CLOSE_ALL_DAILY)
                changed = True
        if changed:
            self.store.save(st)
        return actions

    # ---------------------------------------------------------- gating
    def daily_loss_pct(self) -> float:
        st = self.state
        if st.day_start_equity <= 0:
            return 0.0
        return max(0.0, (st.day_start_equity - st.last_equity) / st.day_start_equity * 100)

    def can_open(self, t: pd.Timestamp, spread: Optional[float], open_count: int,
                 day: Optional[str] = None) -> tuple[bool, str]:
        st = self.state
        day = day or str(trading_day(t, self.day_tz))
        if st.shutdown:
            return False, f"agent shut down: {st.shutdown_reason}"
        if st.day != day:
            return False, "no equity update for current trading day yet"
        if st.halted_day == day:
            return False, f"daily loss limit {self.cfg.daily_loss_limit_pct}% reached — halted until next day"
        if st.trades_today >= self.cfg.max_trades_per_day:
            return False, f"max trades per day reached ({st.trades_today}/{self.cfg.max_trades_per_day})"
        if open_count >= self.cfg.max_open_positions:
            return False, f"max open positions/orders reached ({open_count}/{self.cfg.max_open_positions})"
        if spread is None:
            return False, "spread unknown"
        if spread > self.cfg.max_spread:
            return False, f"spread {spread:.2f} > max {self.cfg.max_spread:.2f}"
        return True, "ok"

    def risk_pct_for_trade(self) -> float:
        """Base risk%, capped so one more full loss cannot breach the daily limit."""
        base = self.cfg.risk_per_trade_pct
        if not self.cfg.cap_risk_to_daily_budget:
            return base
        remaining = self.cfg.daily_loss_limit_pct - self.daily_loss_pct()
        return max(0.0, min(base, remaining))

    def register_fill(self, t: pd.Timestamp, day: Optional[str] = None) -> None:
        day = day or str(trading_day(t, self.day_tz))
        if day != self.state.day:  # fill exactly at day roll before equity update
            self.state.day = day
            self.state.trades_today = 0
        self.state.trades_today += 1
        self.store.save(self.state)

    def reset_shutdown(self) -> None:
        self.state.shutdown = False
        self.state.shutdown_reason = ""
        self.state.peak_equity = self.state.last_equity
        self.store.save(self.state)
