"""ICT Asian-range sweep → M5 market-structure shift → FVG/OB entry.

The strategy is a pure function of closed bars: given the same M5 history
it always produces the same signals, and a signal stamped at time t only
depends on bars that closed at or before t. Backtest and live both call
`generate_signals`, so the rules being tested are the rules being traded.

Rules (every number comes from config.strategy / config.sessions):

1. Asian range: high/low of M5 bars opening inside sessions.asia on day D.
2. A level is *intact* until any bar after the Asian session trades
   through it. Only the first trade through an intact level, inside a
   killzone, is a sweep. A level taken outside a killzone is consumed.
3. Sweep of the Asian HIGH → bearish candidate; of the LOW → bullish.
   The candidate tracks the sweep extreme (highest high / lowest low).
4. MSS: within `mss_max_bars` of the sweep, an M5 CLOSE beyond the most
   recent confirmed swing (opposite side) that formed before the extreme.
   Optional: that close must be back inside the Asian range.
5. Displacement: the largest candle body between the extreme and the MSS
   bar must be >= min_displacement_atr × ATR.
6. Bias: H1 structural bias must equal the trade direction (and H4 too if
   require_h4_agreement).
7. Entry: latest unmitigated FVG of size >= min_fvg_atr × ATR formed in
   the displacement leg (proximal edge or midpoint); else, if allowed, the
   order block = last opposite-colour candle before the extreme.
8. Stop: sweep extreme ± max(sl_buffer_atr × ATR, sl_buffer_min).
   Target: the opposite Asian extreme. Rejected if R:R < min_rr — the
   target is never stretched to make the numbers work.
9. Limit order valid for entry_expiry_bars, never past the killzone end.
"""
from __future__ import annotations

import bisect
import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from core.config import Config
from core.models import LONG, SHORT, Decision, Signal, side_name
from core.timeutils import fmt, window_bounds_utc
from data.loader import M5, resample_htf
from strategy.bias import bias_at_decisions, structural_bias
from strategy.indicators import atr, swing_points


@dataclass
class Prepared:
    index: pd.DatetimeIndex
    ns: np.ndarray  # int64 ns since epoch (UTC) of bar open
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    atr: np.ndarray
    swing_hi_idx: list[int]
    swing_lo_idx: list[int]
    bias_h1: np.ndarray
    bias_h4: np.ndarray


def prepare(m5: pd.DataFrame, cfg: Config) -> Prepared:
    s = cfg.strategy
    o, h, l, c = (m5[k].to_numpy(dtype=float) for k in ("open", "high", "low", "close"))
    sh, sl = swing_points(h, l, s.swing_lookback)
    decision_times = m5.index + M5
    h1 = resample_htf(m5, 1, s.htf_alignment)
    h4 = resample_htf(m5, 4, s.htf_alignment)
    b1 = bias_at_decisions(h1, structural_bias(h1, s.htf_swing_lookback), decision_times) if len(h1) else np.zeros(len(m5), np.int8)
    b4 = bias_at_decisions(h4, structural_bias(h4, s.htf_swing_lookback), decision_times) if len(h4) else np.zeros(len(m5), np.int8)
    return Prepared(
        index=m5.index,
        ns=m5.index.as_unit("ns").asi8,
        o=o, h=h, l=l, c=c,
        atr=atr(h, l, c, s.atr_period),
        swing_hi_idx=list(np.flatnonzero(sh)),
        swing_lo_idx=list(np.flatnonzero(sl)),
        bias_h1=b1,
        bias_h4=b4,
    )


@dataclass
class _Candidate:
    direction: int
    killzone: str
    kz_end_ns: int
    sweep_idx: int
    ext_idx: int
    ext: float
    level: float


@dataclass
class StrategyOutput:
    signals: list[Signal] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)


class IctStrategy:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.s = cfg.strategy
        self.tzd = cfg.time.display_tz

    # ------------------------------------------------------------------ api
    def generate_signals(self, m5: pd.DataFrame, since: Optional[pd.Timestamp] = None) -> StrategyOutput:
        """Run the rules over all days in `m5`. `since` limits which days are
        evaluated (earlier bars are still used for indicators/bias warm-up)."""
        out = StrategyOutput()
        if len(m5) < 50:
            return out
        p = prepare(m5, self.cfg)
        asia = self.cfg.sessions.asia
        first = pd.Timestamp(since) if since is not None else m5.index[0]
        days = pd.date_range(
            first.tz_convert(asia.tz).date(), m5.index[-1].tz_convert(asia.tz).date(), freq="D"
        ).date
        for day in days:
            self._run_day(p, day, out)
        return out

    # ----------------------------------------------------------- internals
    def _log(self, out: StrategyOutput, ns: int, kind: str, msg: str, **data) -> None:
        out.decisions.append(Decision(pd.Timestamp(ns, tz="UTC"), kind, msg, data))

    def _run_day(self, p: Prepared, day: dt.date, out: StrategyOutput) -> None:
        cfg, s = self.cfg, self.s
        a_start, a_end = window_bounds_utc(cfg.sessions.asia, day)
        kzs = []
        for name, w in cfg.sessions.killzones.items():
            ks, ke = window_bounds_utc(w, day)
            kzs.append((name, ks.value, ke.value))
        kzs.sort(key=lambda k: k[1])
        day_end = max(k[2] for k in kzs)

        i_a0 = int(np.searchsorted(p.ns, a_start.value, "left"))
        i_a1 = int(np.searchsorted(p.ns, a_end.value, "left"))
        i_end = int(np.searchsorted(p.ns, day_end, "left"))
        if i_a1 >= len(p.ns) or i_a0 >= i_a1:
            return  # no data for this day (weekend/holiday/end of data)
        expected = (a_end - a_start) / M5
        if (i_a1 - i_a0) < cfg.sessions.asia_min_coverage * expected:
            self._log(out, a_end.value, "SKIP_DAY", f"{day}: Asian session has {i_a1 - i_a0}/{int(expected)} bars — insufficient data", day=str(day))
            return
        asia_high = float(p.h[i_a0:i_a1].max())
        asia_low = float(p.l[i_a0:i_a1].min())
        self._log(out, a_end.value, "ASIA_RANGE", f"{day}: Asian range {asia_low:.2f}–{asia_high:.2f}", day=str(day), asia_high=asia_high, asia_low=asia_low)

        high_intact = low_intact = True
        setups = {k[0]: 0 for k in kzs}
        swept_in_kz = {k[0]: False for k in kzs}
        active: list[_Candidate] = []
        kz_closed_logged: set[str] = set()

        for i in range(i_a1, min(i_end, len(p.ns))):
            t = p.ns[i]
            kz = next(((n, ks, ke) for n, ks, ke in kzs if ks <= t < ke), None)
            # killzone end bookkeeping
            for n, ks, ke in kzs:
                if t >= ke and n not in kz_closed_logged:
                    kz_closed_logged.add(n)
                    if not swept_in_kz[n]:
                        self._log(out, ke, "NO_SETUP", f"{day} {n}: killzone ended without a sweep of an intact Asian level", day=str(day), killzone=n)

            # 1) sweeps of intact levels
            if high_intact and p.h[i] > asia_high:
                high_intact = False
                if kz and setups[kz[0]] < s.max_setups_per_killzone:
                    swept_in_kz[kz[0]] = True
                    active.append(_Candidate(SHORT, kz[0], kz[2], i, i, p.h[i], asia_high))
                    self._log(out, t + M5.value, "SWEEP", f"{kz[0]}: Asian HIGH {asia_high:.2f} swept (high {p.h[i]:.2f}) → watching for bearish MSS", killzone=kz[0], direction="SELL")
                else:
                    self._log(out, t + M5.value, "LEVEL_CONSUMED", f"Asian HIGH {asia_high:.2f} taken outside a killzone (or killzone already used) → no setup on this side", direction="SELL")
            if low_intact and p.l[i] < asia_low:
                low_intact = False
                if kz and setups[kz[0]] < s.max_setups_per_killzone:
                    swept_in_kz[kz[0]] = True
                    active.append(_Candidate(LONG, kz[0], kz[2], i, i, p.l[i], asia_low))
                    self._log(out, t + M5.value, "SWEEP", f"{kz[0]}: Asian LOW {asia_low:.2f} swept (low {p.l[i]:.2f}) → watching for bullish MSS", killzone=kz[0], direction="BUY")
                else:
                    self._log(out, t + M5.value, "LEVEL_CONSUMED", f"Asian LOW {asia_low:.2f} taken outside a killzone (or killzone already used) → no setup on this side", direction="BUY")

            # 2) progress candidates
            still: list[_Candidate] = []
            for cand in active:
                res = self._step_candidate(p, i, cand, asia_high, asia_low, day, setups, out)
                if res == "keep":
                    still.append(cand)
            active = still

        for n, ks, ke in kzs:
            if n not in kz_closed_logged and i_end < len(p.ns) and not swept_in_kz[n]:
                self._log(out, ke, "NO_SETUP", f"{day} {n}: killzone ended without a sweep of an intact Asian level", day=str(day), killzone=n)
        for cand in active:
            self._log(out, day_end, "EXPIRE", f"{cand.killzone}: {side_name(cand.direction)} candidate expired at end of data/day", killzone=cand.killzone)

    def _ref_swing(self, p: Prepared, cand: _Candidate, i: int) -> Optional[int]:
        """Most recent swing (opposite side) before the extreme, confirmed by bar i."""
        n = self.s.swing_lookback
        lst = p.swing_lo_idx if cand.direction == SHORT else p.swing_hi_idx
        k = bisect.bisect_left(lst, cand.ext_idx) - 1
        while k >= 0:
            j = lst[k]
            if j + n <= i:
                return j
            k -= 1
        return None

    def _step_candidate(self, p, i, cand: _Candidate, asia_high, asia_low, day, setups, out) -> str:
        s = self.s
        t_close = p.ns[i] + M5.value
        if p.ns[i] >= cand.kz_end_ns:
            self._log(out, p.ns[i], "EXPIRE", f"{cand.killzone}: killzone ended before a {side_name(cand.direction)} MSS", killzone=cand.killzone)
            return "drop"
        if i - cand.sweep_idx > s.mss_max_bars:
            self._log(out, t_close, "EXPIRE", f"{cand.killzone}: no MSS within {s.mss_max_bars} bars of the sweep", killzone=cand.killzone)
            return "drop"
        d = cand.direction
        if d == SHORT and p.h[i] > cand.ext:
            cand.ext, cand.ext_idx = p.h[i], i
        elif d == LONG and p.l[i] < cand.ext:
            cand.ext, cand.ext_idx = p.l[i], i

        j = self._ref_swing(p, cand, i)
        if j is None:
            return "keep"
        ref = p.l[j] if d == SHORT else p.h[j]
        mss = p.c[i] < ref if d == SHORT else p.c[i] > ref
        if not mss:
            return "keep"

        kz = cand.killzone
        side = side_name(d)
        base = dict(killzone=kz, direction=side, mss_level=float(ref))
        self._log(out, t_close, "MSS", f"{kz}: {side} MSS — close {p.c[i]:.2f} beyond swing {ref:.2f}", **base)

        def reject(reason: str, **extra) -> str:
            self._log(out, t_close, "REJECT", f"{kz}: {side} setup rejected — {reason}", **base, **extra)
            return "drop"

        a = p.atr[i]
        if np.isnan(a):
            return reject("ATR warming up")
        if p.bias_h1[i] != d:
            return reject(f"H1 bias is {int(p.bias_h1[i]):+d}, trade needs {d:+d}", h1=int(p.bias_h1[i]))
        if s.require_h4_agreement and p.bias_h4[i] != d:
            return reject(f"H4 bias is {int(p.bias_h4[i]):+d}, trade needs {d:+d}", h4=int(p.bias_h4[i]))
        if s.require_mss_close_inside_range and not (asia_low < p.c[i] < asia_high):
            return reject(f"MSS close {p.c[i]:.2f} is not back inside the Asian range")
        bodies = np.abs(p.c[cand.ext_idx : i + 1] - p.o[cand.ext_idx : i + 1])
        disp = float(bodies.max()) if len(bodies) else 0.0
        if disp < s.min_displacement_atr * a:
            return reject(f"no displacement (max body {disp:.2f} < {s.min_displacement_atr}×ATR {a:.2f})")

        entry, etype = self._find_entry(p, cand, i, a)
        if entry is None:
            return reject(f"no valid entry ({s.entry_mode}): no unmitigated FVG/OB in the leg")
        if (d == SHORT and entry <= p.c[i]) or (d == LONG and entry >= p.c[i]):
            return reject(f"entry {entry:.2f} already traded through (close {p.c[i]:.2f})")

        buf = max(s.sl_buffer_atr * a, s.sl_buffer_min)
        sl = cand.ext + buf if d == SHORT else cand.ext - buf
        tp = asia_low if d == SHORT else asia_high
        risk = abs(entry - sl)
        reward = (entry - tp) if d == SHORT else (tp - entry)
        if not (s.min_sl_distance <= risk <= s.max_sl_distance):
            return reject(f"stop distance {risk:.2f} outside [{s.min_sl_distance}, {s.max_sl_distance}]")
        rr = reward / risk
        if rr < s.min_rr:
            return reject(f"R:R {rr:.2f} < {s.min_rr} (target = opposite Asian level {tp:.2f})", rr=round(rr, 2))

        decided = pd.Timestamp(t_close, tz="UTC")
        kz_end = pd.Timestamp(cand.kz_end_ns, tz="UTC")
        expiry = min(decided + s.entry_expiry_bars * M5, kz_end)
        sig = Signal(
            id=f"{day:%Y%m%d}-{kz}-{side}-{decided.strftime('%H%M')}",
            time=decided,
            bar_index=i,
            direction=d,
            entry=round(entry, 2),
            sl=round(sl, 2),
            tp=round(tp, 2),
            rr=round(rr, 2),
            killzone=kz,
            entry_type=etype,
            expiry=expiry,
            asia_high=asia_high,
            asia_low=asia_low,
            sweep_extreme=float(cand.ext),
            atr=float(a),
        )
        setups[kz] += 1
        out.signals.append(sig)
        self._log(
            out, t_close, "SIGNAL",
            f"{kz}: {side} LIMIT {sig.entry:.2f} SL {sig.sl:.2f} TP {sig.tp:.2f} R:R {rr:.2f} ({etype}), valid until {fmt(expiry, self.tzd)}",
            **base, signal_id=sig.id, entry=sig.entry, sl=sig.sl, tp=sig.tp, rr=sig.rr,
        )
        return "drop"

    def _find_entry(self, p: Prepared, cand: _Candidate, i: int, a: float) -> tuple[Optional[float], str]:
        s = self.s
        d = cand.direction
        if s.entry_mode in ("fvg_only", "fvg_then_ob"):
            for k in range(i, cand.ext_idx + 1, -1):
                if d == SHORT and p.l[k - 2] > p.h[k]:
                    bottom, top = p.h[k], p.l[k - 2]
                    entry = bottom if s.fvg_entry == "proximal" else (top + bottom) / 2
                    mitigated = k < i and p.h[k + 1 : i + 1].max() >= entry
                elif d == LONG and p.h[k - 2] < p.l[k]:
                    bottom, top = p.h[k - 2], p.l[k]
                    entry = top if s.fvg_entry == "proximal" else (top + bottom) / 2
                    mitigated = k < i and p.l[k + 1 : i + 1].min() <= entry
                else:
                    continue
                if (top - bottom) >= s.min_fvg_atr * a and not mitigated:
                    return float(entry), "fvg"
        if s.entry_mode in ("ob_only", "fvg_then_ob"):
            lo = max(cand.ext_idx - s.ob_search_bars, 0)
            for k in range(cand.ext_idx, lo - 1, -1):
                bullish = p.c[k] > p.o[k]
                if (d == SHORT and bullish) or (d == LONG and not bullish and p.c[k] < p.o[k]):
                    entry = p.o[k] if s.ob_entry == "open" else (p.o[k] + p.c[k]) / 2
                    return float(entry), "ob"
        return None, ""
