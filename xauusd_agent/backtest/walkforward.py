"""Overfitting / edge evaluation.

Protocol (fixed BEFORE looking at results):
 1. Split data: the last `holdout_fraction` is a holdout that is touched
    exactly once, at the end, with the parameters chosen beforehand.
 2. Default parameters (config.yaml, chosen ex-ante from the ICT rules,
    not tuned) are backtested on the in-sample part and on the holdout.
 3. Rolling walk-forward inside the in-sample part: optimise a small,
    pre-declared grid on `train_months`, trade the best combo on the next
    `test_months`; stitch all test segments → walk-forward OOS result.
    WF efficiency = OOS expectancy / IS expectancy.
 4. Parameter sensitivity: share of grid combos with positive expectancy.
    A real edge should not live on one lucky combination.
 5. Random-entry baseline: same killzones, same sizes of stop and target
    (R:R), same costs, random direction and timing. p-value = share of
    random runs whose expectancy >= the strategy's.
 6. Bootstrap 95% CI of the holdout mean R.
Verdict: EDGE only if holdout expectancy > 0, its CI lower bound > 0,
p-value vs random < threshold and holdout trades >= minimum. Otherwise the
honest answer is NO EDGE (or INCONCLUSIVE when the sample is too small).
"""
from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from backtest import metrics
from backtest.engine import BacktestResult, flat_zone_mask, run_backtest
from core.config import Config
from core.models import LONG, SHORT, Signal
from core.timeutils import in_window_mask
from data.loader import M5
from news.calendar import NewsFilter
from strategy.ict import IctStrategy, StrategyOutput

log = logging.getLogger(__name__)


@dataclass
class WFReport:
    split: pd.Timestamp
    default_is: dict
    default_holdout: dict
    holdout_result: BacktestResult
    wf_segments: list[dict] = field(default_factory=list)
    wf_oos: dict = field(default_factory=dict)
    wf_efficiency: float = float("nan")
    sensitivity: list[dict] = field(default_factory=list)
    random_p_value: float = float("nan")
    random_expectancies: list[float] = field(default_factory=list)
    holdout_ci: tuple[float, float] = (float("nan"), float("nan"))
    mc_dd: dict = field(default_factory=dict)
    verdict: str = ""
    verdict_reasons: list[str] = field(default_factory=list)


def _grid(cfg: Config) -> list[dict]:
    keys = list(cfg.walkforward.grid)
    return [dict(zip(keys, vals)) for vals in itertools.product(*(cfg.walkforward.grid[k] for k in keys))]


def _bt(m5, cfg, news, start, end, out: StrategyOutput | None = None) -> BacktestResult:
    return run_backtest(m5, cfg, news, start=start, end=end, strategy_output=out)


def _months(ts: pd.Timestamp, n: int) -> pd.Timestamp:
    return ts + pd.DateOffset(months=n)


def random_baseline(m5: pd.DataFrame, cfg: Config, news: NewsFilter, signals: list[Signal],
                    start, end, runs: int, seed: int) -> list[float]:
    """Expectancy (R) of random-direction limit setups placed at random
    killzone bars, with stop distances and R:R drawn from the strategy's own
    signals. Same engine, costs, news filter and risk limits."""
    if not signals:
        return []
    rng = np.random.default_rng(seed)
    idx = m5.index
    ns = idx.as_unit("ns").asi8
    i0 = int(np.searchsorted(ns, pd.Timestamp(start).value))
    i1 = int(np.searchsorted(ns, pd.Timestamp(end).value))
    kz_mask = np.zeros(len(idx), dtype=bool)
    for w in cfg.sessions.killzones.values():
        kz_mask |= in_window_mask(idx, w)
    kz_mask &= ~flat_zone_mask(idx, cfg)
    cand = np.flatnonzero(kz_mask[i0:i1]) + i0
    cand = cand[cand > i0 + 300]
    if len(cand) == 0:
        return []
    dists = np.array([s.risk_distance for s in signals])
    rrs = np.array([s.rr for s in signals])
    # entry offset from the decision close, as fraction of stop distance
    offs = np.array([abs(s.entry - (m5["close"].iloc[s.bar_index])) / s.risk_distance for s in signals])
    c = m5["close"].to_numpy()
    out = []
    n = len(signals)
    for _ in range(runs):
        bars = np.sort(rng.choice(cand, size=min(n, len(cand)), replace=False))
        sigs = []
        for k, b in enumerate(bars):
            d = LONG if rng.random() < 0.5 else SHORT
            j = rng.integers(len(dists))
            dist, rr, off = dists[j], rrs[j], offs[j]
            entry = c[b] - d * off * dist
            sl = entry - d * dist
            tp = entry + d * rr * dist
            t = idx[b] + M5
            sigs.append(Signal(f"rnd{k}", t, int(b), d, entry, sl, tp, rr, "random", "random",
                               t + cfg.strategy.entry_expiry_bars * M5, 0, 0, 0, 0))
        res = run_backtest(m5, cfg, news, start=start, end=end, strategy_output=StrategyOutput(sigs, []))
        r = [t.r_multiple for t in res.trades]
        out.append(float(np.mean(r)) if r else 0.0)
    return out


def evaluate(m5: pd.DataFrame, cfg: Config, news: NewsFilter, progress=print) -> WFReport:
    wf = cfg.walkforward
    start, end = m5.index[0], m5.index[-1] + M5
    split = start + (end - start) * (1 - wf.holdout_fraction)
    split = split.normalize()
    progress(f"in-sample {start:%Y-%m-%d} → {split:%Y-%m-%d}, holdout {split:%Y-%m-%d} → {end:%Y-%m-%d}")

    strat_default = IctStrategy(cfg).generate_signals(m5)
    is_res = _bt(m5, cfg, news, start, split, strat_default)
    ho_res = _bt(m5, cfg, news, split, end, strat_default)
    tz = cfg.time.trading_day_tz
    rep = WFReport(
        split=split,
        default_is=metrics.compute(is_res.trades, is_res.equity, is_res.initial_equity, tz),
        default_holdout=metrics.compute(ho_res.trades, ho_res.equity, ho_res.initial_equity, tz),
        holdout_result=ho_res,
    )

    # --- grid: precompute signals once per combo (strategy is deterministic)
    combos = _grid(cfg)
    outputs = {}
    for combo in combos:
        c2 = cfg.with_strategy(**combo)
        outputs[tuple(sorted(combo.items()))] = (c2, IctStrategy(c2).generate_signals(m5))

    # --- sensitivity over the in-sample period
    for key, (c2, out) in outputs.items():
        r = _bt(m5, c2, news, start, split, out)
        m = metrics.compute(r.trades, r.equity, r.initial_equity, tz)
        rep.sensitivity.append({**dict(key), "trades": m["trades"], "expectancy_r": m["expectancy_r"], "pf": m["profit_factor"]})
    progress(f"sensitivity: {sum(s['expectancy_r'] > 0 for s in rep.sensitivity)}/{len(rep.sensitivity)} combos positive in-sample")

    # --- rolling walk-forward within in-sample
    seg_start = start.normalize()
    oos_trades, is_exps = [], []
    while _months(seg_start, wf.train_months + wf.test_months) <= split + pd.Timedelta(days=1):
        tr0, tr1 = seg_start, _months(seg_start, wf.train_months)
        te1 = _months(tr1, wf.test_months)
        best, best_key = None, None
        for key, (c2, out) in outputs.items():
            r = _bt(m5, c2, news, tr0, tr1, out)
            if len(r.trades) < wf.min_train_trades:
                continue
            e = float(np.mean([t.r_multiple for t in r.trades]))
            if best is None or e > best:
                best, best_key = e, key
        if best_key is None:
            rep.wf_segments.append({"train": f"{tr0:%Y-%m-%d}→{tr1:%Y-%m-%d}", "test": f"{tr1:%Y-%m-%d}→{te1:%Y-%m-%d}",
                                    "params": None, "note": f"no combo with ≥{wf.min_train_trades} train trades — segment skipped"})
        else:
            c2, out = outputs[best_key]
            r = _bt(m5, c2, news, tr1, te1, out)
            oos_trades += r.trades
            is_exps.append(best)
            rep.wf_segments.append({
                "train": f"{tr0:%Y-%m-%d}→{tr1:%Y-%m-%d}", "test": f"{tr1:%Y-%m-%d}→{te1:%Y-%m-%d}",
                "params": dict(best_key), "is_expectancy_r": best, "oos_trades": len(r.trades),
                "oos_expectancy_r": float(np.mean([t.r_multiple for t in r.trades])) if r.trades else 0.0,
            })
        seg_start = _months(seg_start, wf.test_months)
    if oos_trades:
        r = np.array([t.r_multiple for t in oos_trades])
        rep.wf_oos = {"trades": len(r), "expectancy_r": float(r.mean()), "win_rate": float((r > 0).mean())}
        is_mean = float(np.mean(is_exps)) if is_exps else float("nan")
        rep.wf_efficiency = rep.wf_oos["expectancy_r"] / is_mean if is_mean and is_mean > 0 else float("nan")
    progress(f"walk-forward: {len(rep.wf_segments)} segments, OOS {rep.wf_oos}")

    # --- holdout statistics (default params, untouched)
    r_ho = np.array([t.r_multiple for t in ho_res.trades])
    rep.holdout_ci = metrics.bootstrap_mean_ci(r_ho, wf.bootstrap_samples, wf.seed)
    rep.mc_dd = metrics.monte_carlo_drawdown(
        np.array([t.r_multiple for t in is_res.trades + ho_res.trades]), cfg.risk.risk_per_trade_pct, 2000, wf.seed)
    progress(f"random baseline: {wf.random_baseline_runs} runs …")
    ho_signals = [s for s in strat_default.signals if s.time >= split]
    rep.random_expectancies = random_baseline(m5, cfg, news, ho_signals, split, end, wf.random_baseline_runs, wf.seed)
    if rep.random_expectancies and len(r_ho):
        rep.random_p_value = float(np.mean(np.array(rep.random_expectancies) >= r_ho.mean()))

    _verdict(rep, cfg)
    return rep


def _verdict(rep: WFReport, cfg: Config) -> None:
    c = cfg.walkforward.criteria
    ho = rep.default_holdout
    reasons = []
    ok = True
    if ho["trades"] < c.min_holdout_trades:
        reasons.append(f"only {ho['trades']} holdout trades (< {c.min_holdout_trades}) — sample too small to conclude")
        rep.verdict = "INCONCLUSIVE (insufficient trades) — treat as NO demonstrated edge"
        rep.verdict_reasons = reasons
        return
    if ho["expectancy_r"] <= 0:
        ok = False
        reasons.append(f"holdout expectancy {ho['expectancy_r']:+.3f}R ≤ 0")
    lo, hi = rep.holdout_ci
    if c.require_ci_lower_above_zero and not (lo > 0):
        ok = False
        reasons.append(f"95% CI of holdout mean R [{lo:+.3f}, {hi:+.3f}] includes 0")
    if not (rep.random_p_value < c.max_p_value_vs_random):
        ok = False
        reasons.append(f"p-value vs random entries {rep.random_p_value:.3f} ≥ {c.max_p_value_vs_random}")
    if rep.wf_oos and rep.wf_oos["expectancy_r"] <= 0:
        reasons.append(f"walk-forward OOS expectancy {rep.wf_oos['expectancy_r']:+.3f}R ≤ 0 (warning)")
    pos_share = np.mean([s["expectancy_r"] > 0 for s in rep.sensitivity]) if rep.sensitivity else 0
    if pos_share < 0.5:
        reasons.append(f"only {pos_share:.0%} of parameter combos are profitable in-sample (fragile)")
    rep.verdict = "EDGE (passes all pre-registered criteria)" if ok else "NO EDGE"
    rep.verdict_reasons = reasons or ["all criteria passed"]


def format_report(rep: WFReport) -> str:
    L = ["# Walk-forward / out-of-sample evaluation", ""]
    L += [f"**VERDICT: {rep.verdict}**", ""]
    L += [f"- {r}" for r in rep.verdict_reasons] + [""]
    L += ["## Default parameters (ex-ante, untuned)", "", "```",
          metrics.fmt_summary(rep.default_is, f"IN-SAMPLE (→ {rep.split:%Y-%m-%d})"), "",
          metrics.fmt_summary(rep.default_holdout, f"HOLDOUT ({rep.split:%Y-%m-%d} →)"), "```", ""]
    lo, hi = rep.holdout_ci
    L += [f"Holdout mean R 95% bootstrap CI: [{lo:+.3f}, {hi:+.3f}]", ""]
    if rep.random_expectancies:
        re = np.array(rep.random_expectancies)
        L += [f"Random-entry baseline ({len(re)} runs): mean {re.mean():+.3f}R, 95th pct {np.quantile(re, .95):+.3f}R; "
              f"p-value of strategy = {rep.random_p_value:.3f}", ""]
    L += ["## Rolling walk-forward (in-sample period)", "", "| train | test | params | IS exp R | OOS trades | OOS exp R |", "|---|---|---|---|---|---|"]
    for s in rep.wf_segments:
        if s.get("params") is None:
            L.append(f"| {s['train']} | {s['test']} | — | — | — | {s['note']} |")
        else:
            L.append(f"| {s['train']} | {s['test']} | {s['params']} | {s['is_expectancy_r']:+.3f} | {s['oos_trades']} | {s['oos_expectancy_r']:+.3f} |")
    L += ["", f"Stitched OOS: {rep.wf_oos or 'none'}; WF efficiency: {rep.wf_efficiency:.2f}", ""]
    L += ["## Parameter sensitivity (in-sample)", "", "| params | trades | exp R | PF |", "|---|---|---|---|"]
    for s in sorted(rep.sensitivity, key=lambda x: -x["expectancy_r"]):
        p = {k: v for k, v in s.items() if k not in ("trades", "expectancy_r", "pf")}
        L.append(f"| {p} | {s['trades']} | {s['expectancy_r']:+.3f} | {s['pf']:.2f} |")
    if rep.mc_dd:
        L += ["", f"Monte-Carlo drawdown at configured risk/trade (reshuffled trades): median {rep.mc_dd['dd_median_pct']:.1f}%, "
              f"95th pct {rep.mc_dd['dd_p95_pct']:.1f}%, 99th pct {rep.mc_dd['dd_p99_pct']:.1f}%"]
    return "\n".join(L)
