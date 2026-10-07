"""Event-driven M5 backtester.

Execution model (deliberately conservative):
  * Bars are BID prices. Ask = bid + spread (per-bar spread from data, or
    fixed), × spread_multiplier, floored at spread_min.
  * Long fills when ask trades at/below the limit; short when bid trades
    at/above it (minus `limit_fill_penetration`). A gap through the limit
    fills at the (better) open.
  * Long exits on bid, short exits on ask. Stop-loss fills get
    `slippage_stop` against you; gaps through the stop fill at the open.
  * If SL and TP are both touched inside one bar → counted as SL.
  * On the fill bar only the SL can trigger (we don't know the intrabar
    path, so the TP is never credited on that bar).
  * Commission per lot round-turn is charged on exit.
  * Risk limits, the news blackout and the spread filter use the same
    objects as live trading, evaluated at the signal bar's close.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from core.config import Config
from core.models import LONG, SHORT, Decision, Signal, TradeRecord, side_name
from data.loader import M5
from news.calendar import NewsFilter
from risk.manager import RiskAction, RiskManager
from risk.sizing import loss_per_lot, position_size
from strategy.ict import IctStrategy, StrategyOutput

log = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    trades: list[TradeRecord]
    equity: pd.Series  # mark-to-market equity at each bar close
    decisions: list[Decision]
    signals: list[Signal]
    initial_equity: float
    shutdown_at: Optional[pd.Timestamp] = None
    meta: dict = field(default_factory=dict)

    def trades_frame(self) -> pd.DataFrame:
        return pd.DataFrame([t.to_dict() for t in self.trades])


@dataclass
class _Pending:
    sig: Signal
    volume: float
    risk_amount: float


def _utc(ts) -> Optional[pd.Timestamp]:
    if ts is None:
        return None
    ts = pd.Timestamp(ts)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def spread_series(m5: pd.DataFrame, cfg: Config) -> np.ndarray:
    c = cfg.costs
    if c.spread_source == "data" and "spread" in m5.columns:
        s = m5["spread"].astype(float).fillna(c.spread_fixed).to_numpy()
    else:
        s = np.full(len(m5), c.spread_fixed)
    return np.maximum(s * c.spread_multiplier, c.spread_min)


def flat_zone_mask(index: pd.DatetimeIndex, cfg: Config) -> np.ndarray:
    """Bars opening between the force-close time and 18:00 in its tz
    (gold reopens 18:00 New York) — positions must be flat here."""
    fc = cfg.sessions.force_close
    local = index.tz_convert(fc.tz)
    minutes = local.hour * 60 + local.minute
    start = fc.clock.hour * 60 + fc.clock.minute
    return np.asarray((minutes >= start) & (minutes < 18 * 60))


def run_backtest(
    m5: pd.DataFrame,
    cfg: Config,
    news: NewsFilter,
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
    strategy_output: Optional[StrategyOutput] = None,
    initial_equity: Optional[float] = None,
) -> BacktestResult:
    costs = cfg.costs
    sym = cfg.symbol
    cs = sym.contract_size
    eq0 = initial_equity if initial_equity is not None else costs.initial_equity

    start, end = _utc(start), _utc(end)
    if strategy_output is None:
        strategy_output = IctStrategy(cfg).generate_signals(m5, since=start)

    idx = m5.index
    ns = idx.as_unit("ns").asi8
    i0 = int(np.searchsorted(ns, start.value)) if start is not None else 0
    i1 = int(np.searchsorted(ns, end.value)) if end is not None else len(idx)
    o, h, l, c = (m5[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    spr = spread_series(m5, cfg)
    flat = flat_zone_mask(idx, cfg)
    # trading-day number of each bar's CLOSE (local midnight in trading_day_tz)
    close_local = (idx + M5).tz_convert(cfg.time.trading_day_tz).tz_localize(None)
    daynum = close_local.as_unit("ns").asi8 // 86_400_000_000_000

    by_bar: dict[int, list[Signal]] = {}
    for s in strategy_output.signals:
        if i0 <= s.bar_index < i1:
            by_bar.setdefault(s.bar_index, []).append(s)
    decisions = [d for d in strategy_output.decisions if (start is None or d.time >= start) and (end is None or d.time < end + M5)]

    risk = RiskManager(cfg.risk, cfg.time.trading_day_tz)
    equity = eq0
    pending: Optional[_Pending] = None
    pos: Optional[TradeRecord] = None
    trades: list[TradeRecord] = []
    eq_curve = np.full(i1 - i0, np.nan)
    shutdown_at = None

    def dlog(t, kind, msg, **data):
        decisions.append(Decision(pd.Timestamp(t), kind, msg, data))

    def close_pos(t, price, reason):
        nonlocal pos, equity
        p = pos
        gross = (price - p.entry_price) * p.direction * p.volume * cs
        comm = costs.commission_per_lot_rt * p.volume
        p.exit_time, p.exit_price, p.exit_reason = t, price, reason
        p.gross_pnl, p.commission = gross, comm
        p.net_pnl = gross - comm
        p.r_multiple = p.net_pnl / p.risk_amount if p.risk_amount else 0.0
        equity += p.net_pnl
        p.equity_after = equity
        trades.append(p)
        dlog(t, "EXIT", f"{side_name(p.direction)} closed ({reason}) @ {price:.2f}: {p.net_pnl:+.2f} ({p.r_multiple:+.2f}R)", signal_id=p.signal_id)
        pos = None

    day_str = ""
    last_daynum = None
    for i in range(i0, i1):
        sp = spr[i]
        new_day = daynum[i] != last_daynum
        # fast path: nothing to manage on this bar
        if pos is None and pending is None and not new_day and i not in by_bar:
            eq_curve[i - i0] = equity
            continue
        if new_day:
            last_daynum = daynum[i]
            day_str = str(pd.Timestamp(int(daynum[i]) * 86_400_000_000_000).date())
        t = idx[i]
        t_close = t + M5

        # 0) mandatory flat period before the daily break
        if flat[i]:
            if pos is not None:
                px = o[i] - costs.slippage_stop if pos.direction == LONG else o[i] + sp + costs.slippage_stop
                close_pos(t, px, "force_close")
            if pending is not None:
                dlog(t, "CANCEL", f"pending {pending.sig.id} cancelled: force-close time")
                pending = None

        # 1) pending order lifecycle
        filled_now = False
        if pending is not None:
            sg = pending.sig
            d = sg.direction
            if t >= sg.expiry:
                dlog(t, "CANCEL", f"pending {sg.id} expired unfilled")
                pending = None
            elif cfg.news.cancel_pending_in_blackout and (ev := news.window_overlaps(t, t_close)) is not None:
                dlog(t, "CANCEL", f"pending {sg.id} cancelled: news blackout ({ev.title})")
                pending = None
            else:
                pen = costs.limit_fill_penetration
                fill = (l[i] + sp <= sg.entry - pen) if d == LONG else (h[i] >= sg.entry + pen)
                tp_first = (h[i] >= sg.tp) if d == LONG else (l[i] + sp <= sg.tp)
                if fill:
                    if d == LONG:
                        px = min(sg.entry, o[i] + sp)
                    else:
                        px = max(sg.entry, o[i])
                    pos = TradeRecord(
                        signal_id=sg.id, direction=d, killzone=sg.killzone, entry_type=sg.entry_type,
                        signal_time=sg.time, entry_time=t, entry_price=px, sl=sg.sl, tp=sg.tp,
                        volume=pending.volume, risk_amount=abs(px - sg.sl) * pending.volume * cs,
                    )
                    risk.register_fill(t, day_str)
                    dlog(t, "FILL", f"{side_name(d)} {pending.volume} @ {px:.2f} (SL {sg.sl:.2f} TP {sg.tp:.2f})", signal_id=sg.id)
                    pending = None
                    filled_now = True
                elif tp_first:
                    dlog(t, "CANCEL", f"pending {sg.id} cancelled: target reached before entry")
                    pending = None

        # 2) open position: stops / targets
        if pos is not None:
            d = pos.direction
            if d == LONG:
                bid_o = o[i]
                if not filled_now and bid_o <= pos.sl:
                    close_pos(t, bid_o - costs.slippage_stop, "sl_gap")
                elif not filled_now and bid_o >= pos.tp:
                    close_pos(t, bid_o, "tp_gap")
                elif l[i] <= pos.sl:
                    close_pos(t, pos.sl - costs.slippage_stop, "sl")
                elif not filled_now and h[i] >= pos.tp:
                    close_pos(t, pos.tp, "tp")
            else:
                ask_o = o[i] + sp
                if not filled_now and ask_o >= pos.sl:
                    close_pos(t, ask_o + costs.slippage_stop, "sl_gap")
                elif not filled_now and ask_o <= pos.tp:
                    close_pos(t, ask_o, "tp_gap")
                elif h[i] + sp >= pos.sl:
                    close_pos(t, pos.sl + costs.slippage_stop, "sl")
                elif not filled_now and l[i] + sp <= pos.tp:
                    close_pos(t, pos.tp, "tp")

        # 3) mark-to-market + account limits
        unreal = 0.0
        if pos is not None:
            mark = c[i] if pos.direction == LONG else c[i] + sp
            unreal = (mark - pos.entry_price) * pos.direction * pos.volume * cs
        mtm = equity + unreal
        if shutdown_at is None:
            for act in risk.on_equity(t_close, mtm, day_str):
                if pos is not None:
                    px = c[i] - costs.slippage_stop if pos.direction == LONG else c[i] + sp + costs.slippage_stop
                    close_pos(t_close, px, act.value)
                if pending is not None:
                    dlog(t_close, "CANCEL", f"pending {pending.sig.id} cancelled: {act.value}")
                    pending = None
                if act == RiskAction.SHUTDOWN:
                    shutdown_at = t_close
                    dlog(t_close, "SHUTDOWN", risk.state.shutdown_reason)
            mtm = equity + (0.0 if pos is None else unreal)
        eq_curve[i - i0] = mtm

        # 4) new signals decided at this bar's close
        for sg in by_bar.get(i, []):
            if shutdown_at is not None:
                dlog(t_close, "RISK_BLOCK", f"{sg.id}: agent shut down", signal_id=sg.id)
                continue
            ev = news.blocking_event(t_close)
            if ev is not None:
                dlog(t_close, "NEWS_BLOCK", f"{sg.id}: blocked by news blackout ({ev})", signal_id=sg.id)
                continue
            open_count = (pos is not None) + (pending is not None)
            ok, why = risk.can_open(t_close, sp, open_count, day_str)
            if not ok:
                dlog(t_close, "RISK_BLOCK", f"{sg.id}: {why}", signal_id=sg.id)
                continue
            per_lot = loss_per_lot(sg.entry, sg.sl, cs, costs.slippage_stop, costs.commission_per_lot_rt)
            size = position_size(mtm, risk.risk_pct_for_trade(), per_lot, sym.volume_min, sym.volume_max, sym.volume_step)
            if not size.ok:
                dlog(t_close, "SIZE_REJECT", f"{sg.id}: {size.reason}", signal_id=sg.id)
                continue
            pending = _Pending(sg, size.volume, size.risk_amount)
            dlog(t_close, "ORDER", f"{sg.id}: {side_name(sg.direction)} LIMIT {size.volume} lots @ {sg.entry:.2f}, risk {size.risk_amount:.2f} ({size.risk_amount / mtm * 100:.2f}%)", signal_id=sg.id)

    if pos is not None and i1 > i0:
        last = i1 - 1
        px = c[last] if pos.direction == LONG else c[last] + spr[last]
        close_pos(idx[last] + M5, px, "end_of_data")
        eq_curve[-1] = equity

    eq = pd.Series(eq_curve, index=idx[i0:i1] + M5, name="equity")
    decisions.sort(key=lambda d: d.time)
    return BacktestResult(
        trades=trades, equity=eq, decisions=decisions,
        signals=[s for lst in by_bar.values() for s in lst], initial_equity=eq0, shutdown_at=shutdown_at,
    )
