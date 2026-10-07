"""XAUUSD ICT agent — command line.

  python main.py download   [--start 2023-01-01 --end 2026-09-30]   # Dukascopy M5 data
  python main.py export-mt5 [--start ... --end ...]                  # your broker's M5 data (Windows)
  python main.py backtest   [--start ... --end ...]                  # Phase 1
  python main.py walkforward                                         # Phase 2
  python main.py run                                                 # Phase 3: paper trading on DEMO (default)
  python main.py run --live                                          # Phase 4: REAL money (+ typed confirmation)
  python main.py news                                                # upcoming blackout events
  python main.py synthetic                                           # random-walk data for smoke tests
  python main.py reset-shutdown                                      # clear a max-drawdown shutdown
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from core.config import load_config  # noqa: E402
from notifier.logs import setup_logging  # noqa: E402

log = logging.getLogger("main")


def _date(s: str) -> dt.date:
    return dt.date.fromisoformat(s)


def cmd_download(cfg, a) -> int:
    from data.dukascopy import DukascopyDownloader
    from data.loader import save_m5, validate

    start = a.start or cfg.backtest.start
    end = a.end or cfg.backtest.end
    dl = DukascopyDownloader(cfg.symbol.name if cfg.symbol.name.upper() == "XAUUSD" else "XAUUSD",
                             cfg.path("data/store/raw/dukascopy"), workers=a.workers)
    m5 = dl.download(start, end)
    m5, q = validate(m5)
    save_m5(m5, cfg.path(cfg.paths.data_file))
    print(f"saved {cfg.paths.data_file}: {q.summary()}")
    return 0


def cmd_export_mt5(cfg, a) -> int:
    from dotenv import load_dotenv

    from data.loader import save_m5, validate
    from data.mt5_history import export_m5
    from execution.mt5_broker import MT5Broker

    load_dotenv(ROOT / ".env")
    b = MT5Broker(cfg.symbol.name, cfg.execution)
    if not b.connect():
        print("cannot connect to MT5", file=sys.stderr)
        return 2
    try:
        df = export_m5(b, a.start or cfg.backtest.start, a.end or cfg.backtest.end)
    finally:
        b.shutdown()
    df, q = validate(df)
    out = cfg.path(a.out or "data/store/XAUUSD_M5_mt5.csv.gz")
    save_m5(df, out)
    print(f"saved {out}: {q.summary()}")
    return 0


def cmd_synthetic(cfg, a) -> int:
    """Random-walk data to smoke-test the pipeline. It has NO edge by construction."""
    from data.loader import save_m5
    from data.synthetic import make_m5

    out = cfg.path("data/store/SYNTHETIC_M5.csv.gz")
    save_m5(make_m5(str(a.start or cfg.backtest.start), str(a.end or cfg.backtest.end), seed=a.seed), out)
    print(f"saved {out} — random walk, for pipeline tests only (expect no edge)")
    return 0


def _load_data(cfg, a):
    from data.loader import load_m5

    return load_m5(cfg.path(a.data or cfg.paths.data_file))


def cmd_backtest(cfg, a) -> int:
    import pandas as pd

    from backtest import metrics
    from backtest.engine import run_backtest
    from backtest.report import write_report
    from news.calendar import backtest_filter

    m5 = _load_data(cfg, a)
    start = pd.Timestamp(a.start or cfg.backtest.start, tz="UTC")
    end = pd.Timestamp(a.end or cfg.backtest.end, tz="UTC") + pd.Timedelta(days=1)
    res = run_backtest(m5, cfg, backtest_filter(cfg.news, cfg.path), start=start, end=end)
    m = metrics.compute(res.trades, res.equity, res.initial_equity, cfg.time.trading_day_tz)
    out = cfg.path(cfg.paths.reports_dir) / f"backtest_{dt.datetime.now():%Y%m%d_%H%M%S}"
    write_report(res, m, out, f"XAUUSD ICT backtest {start:%Y-%m-%d} → {end:%Y-%m-%d}", cfg.time.display_tz)
    print(metrics.fmt_summary(m, "BACKTEST"))
    if res.shutdown_at is not None:
        print(f"!! max-drawdown shutdown triggered at {res.shutdown_at}")
    print(f"\nreport: {out}/report.md")
    return 0


def cmd_walkforward(cfg, a) -> int:
    import json

    from backtest.report import plot_equity
    from backtest.walkforward import evaluate, format_report
    from news.calendar import backtest_filter

    m5 = _load_data(cfg, a)
    rep = evaluate(m5, cfg, backtest_filter(cfg.news, cfg.path), progress=lambda s: print("·", s))
    out = cfg.path(cfg.paths.reports_dir) / f"walkforward_{dt.datetime.now():%Y%m%d_%H%M%S}"
    out.mkdir(parents=True, exist_ok=True)
    text = format_report(rep)
    (out / "walkforward.md").write_text(text + "\n\n![holdout](holdout_equity.png)\n", encoding="utf-8")
    (out / "sensitivity.json").write_text(json.dumps(rep.sensitivity, indent=2, default=str), encoding="utf-8")
    plot_equity(rep.holdout_result.equity, out / "holdout_equity.png", "Holdout (default params)", cfg.time.display_tz)
    print(text)
    print(f"\nreport: {out}/walkforward.md")
    return 0


def cmd_run(cfg, a) -> int:
    from dotenv import load_dotenv

    from execution.mt5_broker import MT5Error
    from risk.killswitch import KillSwitch
    from risk.manager import RiskManager, StateStore

    load_dotenv(ROOT / ".env")
    mode = "live" if a.live else "demo"
    setup_logging(cfg.path(cfg.paths.logs_dir), name=f"agent_{mode}")
    state_dir = cfg.path("state") / mode  # separate risk state for demo and live
    risk = RiskManager(cfg.risk, cfg.time.trading_day_tz, StateStore(state_dir / Path(cfg.risk.state_file).name))
    kill = KillSwitch(cfg.path(cfg.risk.kill_switch_file))
    agent_ref = {}
    try:
        return _start_agent(cfg, a, mode, risk, kill, agent_ref)
    except (MT5Error, ValueError) as exc:
        log.error("not started: %s", exc)
        print(f"NOT STARTED: {exc}", file=sys.stderr)
        return 2


def _start_agent(cfg, a, mode, risk, kill, agent_ref) -> int:
    from execution.live import LiveAgent, PreflightError
    from execution.mt5_broker import MT5Broker
    from news.calendar import LiveNewsCalendar
    from notifier.daily_report import DailyReporter
    from notifier.logs import DecisionJournal
    from notifier.telegram import Notifier, TelegramNotifier

    state_dir = cfg.path("state") / mode
    if cfg.telegram.enabled:
        notifier = TelegramNotifier(
            os.environ.get("TELEGRAM_BOT_TOKEN", ""), os.environ.get("TELEGRAM_CHAT_ID", ""),
            cfg.telegram.send_timeout_s, cfg.telegram.poll_commands,
            on_command=lambda cmd, text: agent_ref["a"].on_command(cmd, text),
        )
    else:
        notifier = Notifier()
    agent = LiveAgent(
        cfg, MT5Broker(cfg.symbol.name, cfg.execution), notifier,
        LiveNewsCalendar(cfg.news, cfg.path), risk, kill,
        DecisionJournal(cfg.path(cfg.paths.logs_dir) / f"decisions_{mode}.jsonl"),
        DailyReporter(cfg.path(cfg.paths.reports_dir) / mode), state_dir / "agent_state.json",
    )
    agent_ref["a"] = agent
    try:
        agent.preflight(live=a.live)
    except PreflightError as exc:
        log.error("preflight failed: %s", exc)
        print(f"NOT STARTED: {exc}", file=sys.stderr)
        return 2
    notifier.start()
    try:
        return agent.run()
    finally:
        notifier.stop()
        agent.broker.shutdown()


def cmd_news(cfg, a) -> int:
    from news.calendar import LiveNewsCalendar

    cal = LiveNewsCalendar(cfg.news, cfg.path)
    ok, why = cal.check()
    print(f"now: {'ALLOWED' if ok else 'BLOCKED'} — {why}")
    for e in cal.upcoming(hours=24 * a.days):
        print(" ", e)
    return 0


def cmd_reset_shutdown(cfg, a) -> int:
    from risk.manager import RiskManager, StateStore

    mode = "live" if a.live else "demo"
    rm = RiskManager(cfg.risk, cfg.time.trading_day_tz,
                     StateStore(cfg.path("state") / mode / Path(cfg.risk.state_file).name))
    if not rm.state.shutdown:
        print(f"[{mode}] not in shutdown")
        return 0
    print(f"[{mode}] shutdown reason: {rm.state.shutdown_reason}")
    if input("Type RESET to clear it (the high-water mark is reset to current equity): ").strip() != "RESET":
        print("aborted")
        return 1
    rm.reset_shutdown()
    print("cleared")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="XAUUSD ICT trading agent")
    p.add_argument("--config", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("download")
    d.add_argument("--start", type=_date)
    d.add_argument("--end", type=_date)
    d.add_argument("--workers", type=int, default=4)
    e = sub.add_parser("export-mt5")
    e.add_argument("--start", type=_date)
    e.add_argument("--end", type=_date)
    e.add_argument("--out")
    for name in ("backtest", "walkforward"):
        b = sub.add_parser(name)
        b.add_argument("--data")
        b.add_argument("--start", type=_date)
        b.add_argument("--end", type=_date)
    sy = sub.add_parser("synthetic")
    sy.add_argument("--start", type=_date)
    sy.add_argument("--end", type=_date)
    sy.add_argument("--seed", type=int, default=7)
    r = sub.add_parser("run")
    r.add_argument("--live", action="store_true", help="trade REAL money (requires real account + typed confirmation)")
    nw = sub.add_parser("news")
    nw.add_argument("--days", type=int, default=14)
    rs = sub.add_parser("reset-shutdown")
    rs.add_argument("--live", action="store_true")
    a = p.parse_args(argv)
    cfg = load_config(a.config)
    if a.cmd != "run":
        setup_logging(cfg.path(cfg.paths.logs_dir), name=a.cmd)
    return {
        "download": cmd_download, "export-mt5": cmd_export_mt5, "backtest": cmd_backtest,
        "walkforward": cmd_walkforward, "run": cmd_run, "news": cmd_news, "reset-shutdown": cmd_reset_shutdown, "synthetic": cmd_synthetic,
    }[a.cmd](cfg, a)


if __name__ == "__main__":
    sys.exit(main())
