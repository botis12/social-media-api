"""Position sizing from stop distance.

volume = floor_to_step( equity × risk% / loss_per_lot )

`loss_per_lot` is the account-currency loss of 1.0 lot if the stop is hit,
INCLUDING expected stop slippage and round-turn commission, so the realised
loss at the stop stays within the risk budget. For XAUUSD with a USD
account: (|entry − sl| + slippage) × 100 oz + commission. Live, the broker
adapter computes it with order_calc_profit (correct for non-USD accounts).

Rounding is always DOWN. If even the minimum volume would exceed the
budget, the trade is rejected — never rounded up.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SizeResult:
    volume: float
    risk_amount: float  # expected loss at SL for `volume` (incl. costs)
    reason: str = ""  # non-empty => rejected

    @property
    def ok(self) -> bool:
        return not self.reason and self.volume > 0


def loss_per_lot(entry: float, sl: float, contract_size: float, slippage: float = 0.0,
                 commission_per_lot_rt: float = 0.0) -> float:
    dist = abs(entry - sl)
    if dist <= 0:
        raise ValueError("stop distance must be > 0")
    return (dist + slippage) * contract_size + commission_per_lot_rt


def _decimals(step: float) -> int:
    s = f"{step:.10f}".rstrip("0")
    return len(s.split(".")[1]) if "." in s else 0


def position_size(equity: float, risk_pct: float, per_lot_loss: float, volume_min: float,
                  volume_max: float, volume_step: float) -> SizeResult:
    if equity <= 0:
        return SizeResult(0.0, 0.0, "equity <= 0")
    if risk_pct <= 0:
        return SizeResult(0.0, 0.0, "risk budget exhausted")
    if per_lot_loss <= 0 or not math.isfinite(per_lot_loss):
        return SizeResult(0.0, 0.0, f"invalid loss per lot {per_lot_loss}")
    budget = equity * risk_pct / 100.0
    raw = budget / per_lot_loss
    steps = math.floor(raw / volume_step + 1e-9)
    vol = round(steps * volume_step, _decimals(volume_step))
    vol = min(vol, math.floor(volume_max / volume_step + 1e-9) * volume_step)
    vol = round(vol, _decimals(volume_step))
    if vol < volume_min - 1e-12:
        return SizeResult(
            0.0, 0.0,
            f"min volume {volume_min} would risk {volume_min * per_lot_loss:.2f} > budget {budget:.2f}",
        )
    return SizeResult(vol, vol * per_lot_loss)
