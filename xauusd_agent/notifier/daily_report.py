"""Daily CSV report and trade journal for live/paper trading."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

DAILY_FIELDS = ["date", "start_equity", "end_equity", "pnl", "pnl_pct", "trades", "wins", "losses",
                "sum_r", "daily_limit_hit", "shutdown"]
TRADE_FIELDS = ["signal_id", "side", "killzone", "entry_type", "entry_time", "entry_price", "sl", "tp", "volume",
                "risk_amount", "exit_time", "exit_price", "exit_reason", "net_pnl", "r_multiple"]


def _append(path: Path, fields: list[str], row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow(row)


@dataclass
class DayStats:
    date: str
    start_equity: float
    trades: int = 0
    wins: int = 0
    losses: int = 0
    pnl: float = 0.0
    sum_r: float = 0.0
    results: list = field(default_factory=list)

    def add(self, net: float, r: float) -> None:
        self.trades += 1
        self.wins += net > 0
        self.losses += net <= 0
        self.pnl += net
        self.sum_r += r


class DailyReporter:
    def __init__(self, reports_dir: Path):
        self.daily_path = reports_dir / "daily_report.csv"
        self.trades_path = reports_dir / "live_trades.csv"

    def write_trade(self, row: dict) -> None:
        _append(self.trades_path, TRADE_FIELDS, row)

    def write_day(self, st: DayStats, end_equity: float, daily_limit_hit: bool, shutdown: bool) -> None:
        _append(self.daily_path, DAILY_FIELDS, {
            "date": st.date, "start_equity": f"{st.start_equity:.2f}", "end_equity": f"{end_equity:.2f}",
            "pnl": f"{end_equity - st.start_equity:.2f}",
            "pnl_pct": f"{(end_equity / st.start_equity - 1) * 100 if st.start_equity else 0:.3f}",
            "trades": st.trades, "wins": st.wins, "losses": st.losses, "sum_r": f"{st.sum_r:.3f}",
            "daily_limit_hit": daily_limit_hit, "shutdown": shutdown,
        })
