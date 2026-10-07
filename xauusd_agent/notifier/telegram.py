"""Telegram notifications + command channel.

* Messages are queued and sent from a background thread, so a slow or
  unreachable Telegram API can never stall the trading loop.
* Commands (/stop, /status) are accepted ONLY from the configured chat_id;
  everything else is ignored and logged. Messages sent before the agent
  started are ignored, so an old /stop in the chat can't fire on boot.
* Token/chat id come from the environment (.env), never from code.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Callable, Optional

import requests

log = logging.getLogger(__name__)
API = "https://api.telegram.org/bot{token}/{method}"


class Notifier:
    """No-op base (used when Telegram is disabled and in tests)."""

    def send(self, text: str) -> None:
        log.info("notify: %s", text)

    def start(self) -> None: ...

    def stop(self) -> None: ...


class TelegramNotifier(Notifier):
    def __init__(self, token: str, chat_id: str, timeout: float = 10.0, poll_commands: bool = True,
                 on_command: Optional[Callable[[str, str], Optional[str]]] = None, session=None):
        if not token or not chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        self.token = token
        self.chat_id = str(chat_id)
        self.timeout = timeout
        self.poll_commands = poll_commands
        self.on_command = on_command
        self.http = session or requests.Session()
        self._q: "queue.Queue[str]" = queue.Queue(maxsize=1000)
        self._stop = threading.Event()
        self._threads: list[threading.Thread] = []
        self._started_at = int(time.time())
        self._offset: Optional[int] = None

    def _url(self, method: str) -> str:
        return API.format(token=self.token, method=method)

    # ---------------------------------------------------------- sending
    def send(self, text: str) -> None:
        log.info("telegram ⇢ %s", text.replace("\n", " | "))
        try:
            self._q.put_nowait(text[:4000])
        except queue.Full:
            log.error("telegram: queue full, dropping message")

    def _sender(self) -> None:
        while not self._stop.is_set() or not self._q.empty():
            try:
                text = self._q.get(timeout=0.5)
            except queue.Empty:
                continue
            delay = 1.0
            for attempt in range(5):
                try:
                    r = self.http.post(self._url("sendMessage"), data={"chat_id": self.chat_id, "text": text},
                                       timeout=self.timeout)
                    if r.status_code == 429:
                        retry = float(r.json().get("parameters", {}).get("retry_after", delay))
                        time.sleep(retry)
                        continue
                    r.raise_for_status()
                    break
                except Exception as exc:  # noqa: BLE001 — network errors must never propagate
                    log.warning("telegram send failed (attempt %d): %s", attempt + 1, type(exc).__name__)
                    time.sleep(delay)
                    delay = min(delay * 2, 30)

    # ---------------------------------------------------------- commands
    def handle_update(self, upd: dict) -> None:
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = str(msg.get("chat", {}).get("id", ""))
        text = (msg.get("text") or "").strip()
        if not text.startswith("/"):
            return
        if chat != self.chat_id:
            log.warning("telegram: ignoring command %r from unauthorised chat %s", text, chat)
            return
        if int(msg.get("date", 0)) < self._started_at:
            log.info("telegram: ignoring stale command %r sent before start", text)
            return
        cmd = text.split()[0].split("@")[0].lower()
        if self.on_command:
            reply = self.on_command(cmd, text)
            if reply:
                self.send(reply)

    def _poller(self) -> None:
        delay = 2.0
        while not self._stop.is_set():
            try:
                params = {"timeout": 25, "allowed_updates": '["message","edited_message"]'}
                if self._offset is not None:
                    params["offset"] = self._offset
                r = self.http.get(self._url("getUpdates"), params=params, timeout=35)
                r.raise_for_status()
                for upd in r.json().get("result", []):
                    self._offset = int(upd["update_id"]) + 1
                    self.handle_update(upd)
                delay = 2.0
            except Exception as exc:  # noqa: BLE001
                log.warning("telegram poll failed: %s", type(exc).__name__)
                self._stop.wait(delay)
                delay = min(delay * 2, 60)

    def start(self) -> None:
        t = threading.Thread(target=self._sender, name="tg-send", daemon=True)
        t.start()
        self._threads.append(t)
        if self.poll_commands:
            p = threading.Thread(target=self._poller, name="tg-poll", daemon=True)
            p.start()
            self._threads.append(p)

    def stop(self) -> None:
        self._stop.set()
        for t in self._threads:
            if t.name == "tg-send":
                t.join(timeout=15)  # flush pending messages
