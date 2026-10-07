"""Performance statistics. All R figures are NET of spread, slippage and
commission, measured against the planned price risk |entry − SL|."""
from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd

from core.models import TradeRecord


def max_drawdown_pct(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    peak = equity.cummax()
    return float(((peak - equity) / peak).max() * 100)


def daily_returns(equity: pd.Series, tz: str) -> pd.Series:
    if equity.empty:
        return pd.Series(dtype=float)
    daily = equity.tz_convert(tz).resample("1D").last().dropna()
    return daily.pct_change().dropna()


def sharpe(equity: pd.Series, tz: str, periods: int = 252) -> float:
    r = daily_returns(equity, tz)
    if len(r) < 2 or r.std(ddof=1) == 0:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * math.sqrt(periods))


def longest_losing_streak(r: np.ndarray) -> int:
    best = cur = 0
    for x in r:
        cur = cur + 1 if x <= 0 else 0
        best = max(best, cur)
    return best


def compute(trades: list[TradeRecord], equity: pd.Series, initial_equity: float, tz: str) -> dict:
    n = len(trades)
    r = np.array([t.r_multiple for t in trades], dtype=float)
    pnl = np.array([t.net_pnl for t in trades], dtype=float)
    wins = pnl > 0
    gross_win = pnl[wins].sum()
    gross_loss = -pnl[~wins].sum()
    final = float(equity.iloc[-1]) if len(equity) else initial_equity
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9) if len(equity) > 1 else 0
    out = {
        "trades": n,
        "win_rate": float(wins.mean()) if n else 0.0,
        "avg_r": float(r.mean()) if n else 0.0,
        "expectancy_r": float(r.mean()) if n else 0.0,
        "expectancy_usd": float(pnl.mean()) if n else 0.0,
        "median_r": float(np.median(r)) if n else 0.0,
        "avg_win_r": float(r[wins].mean()) if wins.any() else 0.0,
        "avg_loss_r": float(r[~wins].mean()) if (~wins).any() else 0.0,
        "profit_factor": float(gross_win / gross_loss) if gross_loss > 0 else (math.inf if gross_win > 0 else 0.0),
        "net_profit": float(pnl.sum()),
        "total_return_pct": (final / initial_equity - 1) * 100,
        "cagr_pct": ((final / initial_equity) ** (1 / years) - 1) * 100 if years > 0 and final > 0 else 0.0,
        "max_drawdown_pct": max_drawdown_pct(equity),
        "sharpe": sharpe(equity, tz),
        "longest_losing_streak": longest_losing_streak(r),
        "trades_per_month": n / (years * 12) if years > 0 else 0.0,
        "total_commission": float(sum(t.commission for t in trades)),
        "exit_reasons": pd.Series([t.exit_reason for t in trades]).value_counts().to_dict() if n else {},
        "by_killzone": {k: {"trades": int(len(g)), "expectancy_r": float(g.mean())}
                        for k, g in pd.Series(r, index=[t.killzone for t in trades]).groupby(level=0)} if n else {},
        "by_side": {("BUY" if k == 1 else "SELL"): {"trades": int(len(g)), "expectancy_r": float(g.mean())}
                    for k, g in pd.Series(r, index=[t.direction for t in trades]).groupby(level=0)} if n else {},
        "start": str(equity.index[0]) if len(equity) else "",
        "end": str(equity.index[-1]) if len(equity) else "",
        "final_equity": final,
    }
    return out


def bootstrap_mean_ci(r: np.ndarray, samples: int, seed: int, alpha: float = 0.05) -> tuple[float, float]:
    if len(r) < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = rng.choice(r, size=(samples, len(r)), replace=True).mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def monte_carlo_drawdown(r: np.ndarray, risk_pct: float, runs: int, seed: int) -> dict:
    """Reshuffle the R sequence to see how bad drawdown could plausibly be."""
    if len(r) == 0:
        return {}
    rng = np.random.default_rng(seed)
    dds = np.empty(runs)
    for k in range(runs):
        seq = rng.permutation(r)
        eq = np.cumprod(1 + seq * risk_pct / 100)
        eq = np.concatenate([[1.0], eq])
        peak = np.maximum.accumulate(eq)
        dds[k] = ((peak - eq) / peak).max() * 100
    return {"dd_median_pct": float(np.median(dds)), "dd_p95_pct": float(np.quantile(dds, 0.95)),
            "dd_p99_pct": float(np.quantile(dds, 0.99))}


def fmt_summary(m: dict, title: Optional[str] = None) -> str:
    lines = [f"== {title} ==" if title else ""]
    lines += [
        f"Period            : {m['start'][:10]} → {m['end'][:10]}",
        f"Trades            : {m['trades']}  ({m['trades_per_month']:.1f}/month)",
        f"Win rate          : {m['win_rate'] * 100:.1f}%",
        f"Average R (net)   : {m['avg_r']:+.3f}   (avg win {m['avg_win_r']:+.2f}R, avg loss {m['avg_loss_r']:+.2f}R)",
        f"Expectancy        : {m['expectancy_r']:+.3f}R  /  {m['expectancy_usd']:+.2f} $ per trade",
        f"Profit factor     : {m['profit_factor']:.2f}",
        f"Net profit        : {m['net_profit']:+.2f} $  ({m['total_return_pct']:+.2f}%, CAGR {m['cagr_pct']:+.2f}%)",
        f"Max drawdown      : {m['max_drawdown_pct']:.2f}%",
        f"Sharpe (daily,ann): {m['sharpe']:.2f}",
        f"Longest loss run  : {m['longest_losing_streak']}",
        f"Commission paid   : {m['total_commission']:.2f} $",
        f"Exit reasons      : {m['exit_reasons']}",
        f"By killzone       : {m['by_killzone']}",
        f"By side           : {m['by_side']}",
    ]
    return "\n".join(x for x in lines if x)
