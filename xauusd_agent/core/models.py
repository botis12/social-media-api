"""Plain data objects shared by strategy, risk, backtest and live execution."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

import pandas as pd

LONG = 1
SHORT = -1


def side_name(direction: int) -> str:
    return "BUY" if direction == LONG else "SELL"


@dataclass(frozen=True)
class Signal:
    """A fully specified limit-order setup produced by the strategy.

    `time` is the close time of the M5 bar on which the decision was made;
    nothing after that instant was used to build it.
    """

    id: str
    time: pd.Timestamp
    bar_index: int
    direction: int
    entry: float
    sl: float
    tp: float
    rr: float
    killzone: str
    entry_type: str  # "fvg" | "ob"
    expiry: pd.Timestamp
    asia_high: float
    asia_low: float
    sweep_extreme: float
    atr: float

    @property
    def risk_distance(self) -> float:
        return abs(self.entry - self.sl)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["time"] = self.time.isoformat()
        d["expiry"] = self.expiry.isoformat()
        d["side"] = side_name(self.direction)
        return d


@dataclass(frozen=True)
class Decision:
    """One logged reasoning step: why something was or wasn't done."""

    time: pd.Timestamp
    kind: str  # e.g. SWEEP, MSS, SIGNAL, REJECT, EXPIRE, RISK_BLOCK, NEWS_BLOCK ...
    message: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"time": self.time.isoformat(), "kind": self.kind, "message": self.message, **self.data}


@dataclass
class TradeRecord:
    signal_id: str
    direction: int
    killzone: str
    entry_type: str
    signal_time: pd.Timestamp
    entry_time: pd.Timestamp
    entry_price: float
    sl: float
    tp: float
    volume: float
    risk_amount: float  # $ lost if SL hit at the planned price (excl. costs)
    exit_time: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    exit_reason: str = ""
    gross_pnl: float = 0.0
    commission: float = 0.0
    net_pnl: float = 0.0
    r_multiple: float = 0.0
    equity_after: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        for k in ("signal_time", "entry_time", "exit_time"):
            if d[k] is not None:
                d[k] = pd.Timestamp(d[k]).isoformat()
        d["side"] = side_name(self.direction)
        return d
