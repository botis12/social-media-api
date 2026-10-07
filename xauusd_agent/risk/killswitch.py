"""Kill switch: a file named STOP (configurable) or a Telegram /stop command.
When triggered, the live loop closes all positions, cancels orders and exits."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional


class KillSwitch:
    def __init__(self, path: Path):
        self.path = path
        self._reason: Optional[str] = None
        self._lock = threading.Lock()

    def trigger(self, reason: str) -> None:
        with self._lock:
            if self._reason is None:
                self._reason = reason

    def check(self) -> Optional[str]:
        """Reason string if triggered, else None."""
        if self.path.exists():
            self.trigger(f"kill-switch file {self.path} present")
        with self._lock:
            return self._reason
