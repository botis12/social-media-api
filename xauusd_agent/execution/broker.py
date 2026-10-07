"""Broker abstraction used by the live agent. MT5Broker implements it;
tests use a fake. Every timestamp crossing this boundary is UTC."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import pandas as pd


@dataclass(frozen=True)
class AccountInfo:
    login: int
    server: str
    currency: str
    balance: float
    equity: float
    margin_free: float
    leverage: int
    is_demo: bool
    is_real: bool


@dataclass(frozen=True)
class SymbolSpec:
    name: str
    digits: int
    point: float
    tick_size: float
    tick_value: float
    contract_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    stops_level_points: int
    filling_mode: int
    trade_allowed: bool


@dataclass(frozen=True)
class Tick:
    time: pd.Timestamp
    bid: float
    ask: float

    @property
    def spread(self) -> float:
        return self.ask - self.bid


@dataclass(frozen=True)
class BrokerPosition:
    ticket: int
    direction: int
    volume: float
    price_open: float
    sl: float
    tp: float
    time: pd.Timestamp
    profit: float
    comment: str


@dataclass(frozen=True)
class BrokerOrder:
    ticket: int
    direction: int
    volume: float
    price: float
    sl: float
    tp: float
    time_setup: pd.Timestamp
    comment: str


@dataclass(frozen=True)
class OrderResult:
    ok: bool
    ticket: int = 0
    retcode: int = 0
    message: str = ""
    price: float = 0.0


@dataclass(frozen=True)
class ClosedPosition:
    position_id: int
    exit_time: pd.Timestamp
    exit_price: float
    net_profit: float  # profit + commission + swap + fees
    reason: str


class Broker(ABC):
    @abstractmethod
    def connect(self) -> bool: ...

    @abstractmethod
    def ensure_connected(self, max_attempts: Optional[int] = None) -> bool: ...

    @abstractmethod
    def shutdown(self) -> None: ...

    @abstractmethod
    def account(self) -> AccountInfo: ...

    @abstractmethod
    def symbol_spec(self) -> SymbolSpec: ...

    @abstractmethod
    def tick(self) -> Optional[Tick]: ...

    @abstractmethod
    def rates_m5(self, count: int) -> pd.DataFrame:
        """CLOSED M5 bars, UTC open-time index, columns open/high/low/close/volume/spread."""

    @abstractmethod
    def positions(self) -> list[BrokerPosition]: ...

    @abstractmethod
    def orders(self) -> list[BrokerOrder]: ...

    @abstractmethod
    def place_limit(self, direction: int, volume: float, price: float, sl: float, tp: float, comment: str) -> OrderResult: ...

    @abstractmethod
    def cancel_order(self, ticket: int) -> OrderResult: ...

    @abstractmethod
    def close_position(self, pos: BrokerPosition) -> OrderResult: ...

    @abstractmethod
    def loss_per_lot(self, direction: int, entry: float, sl: float) -> float:
        """Account-currency loss of 1.0 lot from entry to sl (positive number)."""

    @abstractmethod
    def margin_required(self, direction: int, volume: float, price: float) -> Optional[float]: ...

    @abstractmethod
    def closed_position(self, position_id: int) -> Optional[ClosedPosition]: ...
