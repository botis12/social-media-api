"""Typed, validated configuration loaded from config.yaml.

Every tunable number lives in config.yaml; this module only defines the
schema and sanity limits. Loading fails loudly on unknown keys or values
outside the allowed ranges so a typo can never silently change behaviour.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Literal, Optional, Union
from zoneinfo import ZoneInfo

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _parse_hhmm(v: str) -> dt.time:
    try:
        h, m = v.split(":")
        return dt.time(int(h), int(m))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"expected HH:MM, got {v!r}") from exc


def _check_tz(v: str) -> str:
    ZoneInfo(v)  # raises if unknown
    return v


class Window(_Strict):
    tz: str
    start: str
    end: str

    @field_validator("tz")
    @classmethod
    def _tz(cls, v: str) -> str:
        return _check_tz(v)

    @field_validator("start", "end")
    @classmethod
    def _hhmm(cls, v: str) -> str:
        _parse_hhmm(v)
        return v

    @property
    def start_time(self) -> dt.time:
        return _parse_hhmm(self.start)

    @property
    def end_time(self) -> dt.time:
        return _parse_hhmm(self.end)

    @model_validator(mode="after")
    def _order(self) -> "Window":
        if self.start_time >= self.end_time:
            raise ValueError("window start must be before end (same calendar day)")
        return self


class ForceClose(_Strict):
    tz: str
    time: str

    @field_validator("tz")
    @classmethod
    def _tz(cls, v: str) -> str:
        return _check_tz(v)

    @field_validator("time")
    @classmethod
    def _hhmm(cls, v: str) -> str:
        _parse_hhmm(v)
        return v

    @property
    def clock(self) -> dt.time:
        return _parse_hhmm(self.time)


class SymbolCfg(_Strict):
    name: str
    contract_size: float = Field(gt=0)
    tick_size: float = Field(gt=0)
    volume_min: float = Field(gt=0)
    volume_max: float = Field(gt=0)
    volume_step: float = Field(gt=0)


class TimeCfg(_Strict):
    trading_day_tz: str
    display_tz: str

    @field_validator("trading_day_tz", "display_tz")
    @classmethod
    def _tz(cls, v: str) -> str:
        return _check_tz(v)


class SessionsCfg(_Strict):
    asia: Window
    asia_min_coverage: float = Field(gt=0, le=1)
    killzones: dict[str, Window]
    force_close: ForceClose


class StrategyCfg(_Strict):
    atr_period: int = Field(ge=2)
    swing_lookback: int = Field(ge=1, le=10)
    htf_swing_lookback: int = Field(ge=1, le=10)
    htf_alignment: Literal["ny_close", "utc"]
    require_h4_agreement: bool
    mss_max_bars: int = Field(ge=1)
    require_mss_close_inside_range: bool
    min_displacement_atr: float = Field(ge=0)
    entry_mode: Literal["fvg_only", "ob_only", "fvg_then_ob"]
    fvg_entry: Literal["proximal", "mid"]
    min_fvg_atr: float = Field(ge=0)
    ob_entry: Literal["open", "mid"]
    ob_search_bars: int = Field(ge=1)
    entry_expiry_bars: int = Field(ge=1)
    sl_buffer_atr: float = Field(ge=0)
    sl_buffer_min: float = Field(ge=0)
    min_sl_distance: float = Field(gt=0)
    max_sl_distance: float = Field(gt=0)
    min_rr: float = Field(ge=2.0)  # spec: minimum R:R 1:2 is non-negotiable
    max_setups_per_killzone: int = Field(ge=1)


class RiskCfg(_Strict):
    # Spec: 0.5–1% of equity per trade. Enforced here so config can't exceed it.
    risk_per_trade_pct: float = Field(ge=0.5, le=1.0)
    max_trades_per_day: int = Field(ge=1, le=2)
    max_open_positions: int = Field(ge=1, le=1)
    daily_loss_limit_pct: float = Field(gt=0, le=2.0)
    close_positions_on_daily_limit: bool
    cap_risk_to_daily_budget: bool
    max_drawdown_pct: float = Field(gt=0, le=8.0)
    max_spread: float = Field(gt=0)
    max_margin_usage_pct: float = Field(gt=0, le=100)
    state_file: str
    kill_switch_file: str


class CostsCfg(_Strict):
    commission_per_lot_rt: float = Field(ge=0)
    spread_source: Literal["data", "fixed"]
    spread_fixed: float = Field(ge=0)
    spread_multiplier: float = Field(ge=1.0)
    spread_min: float = Field(ge=0)
    slippage_stop: float = Field(ge=0)
    limit_fill_penetration: float = Field(ge=0)
    initial_equity: float = Field(gt=0)


class NewsCfg(_Strict):
    minutes_before: int = Field(ge=0)
    minutes_after: int = Field(ge=0)
    currencies: list[str]
    impacts: list[str]
    keywords: list[str]
    live_block_all_high_impact: bool
    sources: list[str]
    refresh_minutes: int = Field(ge=15)
    cache_dir: str
    historical_file: str
    manual_file: str
    on_unavailable: Literal["block", "allow"]
    cancel_pending_in_blackout: bool


class ExecutionCfg(_Strict):
    magic: int
    poll_seconds: float = Field(gt=0)
    deviation_points: int = Field(ge=0)
    max_order_retries: int = Field(ge=1)
    reconnect_max_attempts: int = Field(ge=0)
    reconnect_backoff_max_s: float = Field(gt=0)
    server_utc_offset_hours: Union[Literal["auto"], int]
    history_m5_bars: int = Field(ge=1000)
    order_comment: str = Field(max_length=31)


class TelegramCfg(_Strict):
    enabled: bool
    send_timeout_s: float = Field(gt=0)
    poll_commands: bool


class PathsCfg(_Strict):
    data_file: str
    logs_dir: str
    reports_dir: str


class BacktestCfg(_Strict):
    start: dt.date
    end: dt.date


class WFCriteria(_Strict):
    min_holdout_trades: int = Field(ge=1)
    max_p_value_vs_random: float = Field(gt=0, lt=1)
    require_ci_lower_above_zero: bool


class WalkForwardCfg(_Strict):
    holdout_fraction: float = Field(gt=0, lt=1)
    train_months: int = Field(ge=1)
    test_months: int = Field(ge=1)
    min_train_trades: int = Field(ge=1)
    bootstrap_samples: int = Field(ge=100)
    random_baseline_runs: int = Field(ge=10)
    seed: int
    grid: dict[str, list]
    criteria: WFCriteria


class Config(_Strict):
    symbol: SymbolCfg
    time: TimeCfg
    sessions: SessionsCfg
    strategy: StrategyCfg
    risk: RiskCfg
    costs: CostsCfg
    news: NewsCfg
    execution: ExecutionCfg
    telegram: TelegramCfg
    paths: PathsCfg
    backtest: BacktestCfg
    walkforward: WalkForwardCfg

    def path(self, rel: str) -> Path:
        """Resolve a config path relative to the project root."""
        p = Path(rel)
        return p if p.is_absolute() else PROJECT_ROOT / p

    def with_strategy(self, **overrides) -> "Config":
        """Copy with some strategy params replaced (used by walk-forward)."""
        strat = self.strategy.model_copy(update=overrides)
        StrategyCfg.model_validate(strat.model_dump())  # re-validate
        return self.model_copy(update={"strategy": strat})


def load_config(path: Optional[Union[str, Path]] = None) -> Config:
    p = Path(path) if path else PROJECT_ROOT / "config.yaml"
    with open(p, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return Config.model_validate(raw)
