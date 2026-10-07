"""Logging setup and the decision journal (one JSON line per decision:
why a trade was or wasn't taken)."""
from __future__ import annotations

import json
import logging
import logging.handlers
import threading
from pathlib import Path

from core.models import Decision


def setup_logging(logs_dir: Path, level: int = logging.INFO, name: str = "agent") -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)
    fh = logging.handlers.TimedRotatingFileHandler(logs_dir / f"{name}.log", when="midnight", backupCount=60, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(fh)
    root.addHandler(sh)
    for noisy in ("urllib3", "matplotlib"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


class DecisionJournal:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.log = logging.getLogger("decision")

    def write(self, d: Decision) -> None:
        self.log.info("[%s] %s", d.kind, d.message)
        with self._lock, open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(d.to_dict(), default=str, ensure_ascii=False) + "\n")
