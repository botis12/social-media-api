"""Write backtest artefacts: trades.csv, decisions.csv, equity.csv,
summary.json, report.md and equity.png."""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from backtest.engine import BacktestResult  # noqa: E402
from backtest.metrics import fmt_summary  # noqa: E402


def _json_safe(o):
    if isinstance(o, float) and (math.isinf(o) or math.isnan(o)):
        return str(o)
    if isinstance(o, dict):
        return {str(k): _json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_json_safe(v) for v in o]
    return o


def plot_equity(equity: pd.Series, path: Path, title: str, tz: str, marks: dict[str, pd.Timestamp] | None = None) -> None:
    eq = equity.tz_convert(tz).resample("1h").last().dropna()
    dd = (eq.cummax() - eq) / eq.cummax() * 100
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax1.plot(eq.index, eq.values, color="#1f5fa8", lw=1.2)
    ax1.set_title(title)
    ax1.set_ylabel("Equity ($)")
    ax1.grid(alpha=0.3)
    for label, ts in (marks or {}).items():
        ax1.axvline(pd.Timestamp(ts).tz_convert(tz), color="#c0392b", ls="--", lw=1)
        ax1.text(pd.Timestamp(ts).tz_convert(tz), ax1.get_ylim()[1], f" {label}", va="top", color="#c0392b", fontsize=9)
    ax2.fill_between(dd.index, -dd.values, 0, color="#c0392b", alpha=0.35)
    ax2.set_ylabel("Drawdown (%)")
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def write_report(res: BacktestResult, metrics: dict, out_dir: Path, title: str, tz: str, extra_md: str = "") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    res.trades_frame().to_csv(out_dir / "trades.csv", index=False)
    pd.DataFrame([d.to_dict() for d in res.decisions]).to_csv(out_dir / "decisions.csv", index=False)
    res.equity.to_csv(out_dir / "equity.csv")
    (out_dir / "summary.json").write_text(json.dumps(_json_safe(metrics), indent=2, default=str), encoding="utf-8")
    plot_equity(res.equity, out_dir / "equity.png", title, tz)
    md = [f"# {title}", "", "```", fmt_summary(metrics), "```", ""]
    if res.shutdown_at is not None:
        md += [f"**Max-drawdown shutdown triggered at {res.shutdown_at}.**", ""]
    md += ["![equity](equity.png)", "", extra_md]
    (out_dir / "report.md").write_text("\n".join(md), encoding="utf-8")
    return out_dir
