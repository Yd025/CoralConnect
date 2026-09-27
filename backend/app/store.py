from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path

from .config import settings
from .models import Session

logger = logging.getLogger("coralconnect.store")

# Changes that land within this many seconds share one disk write.
SAVE_DELAY = 0.5


class Store:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.data_path
        self.sessions: dict[str, Session] = {}
        self.cards: dict[str, dict] = {}
        self.lock = asyncio.Lock()
        self._dirty = False
        self._flush_task: asyncio.Task | None = None

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if raw.get("version") != 1:
            return
        loaded: dict[str, Session] = {}
        for code, payload in raw.get("sessions", {}).items():
            try:
                loaded[code] = Session.from_dict(payload)
            except TypeError:
                continue
        self.sessions = loaded
        cards = raw.get("cards") or {}
        self.cards = cards if isinstance(cards, dict) else {}
        self.prune()

    def prune(self, now: float | None = None) -> int:
        """Drop games with no activity for IDLE_SESSION_HOURS. Result cards stay.

        Every game ever opened used to stay in the save file, and every change
        rewrote all of them. Returns how many games were dropped.
        """
        hours = settings.idle_session_hours
        if hours <= 0:
            return 0
        cutoff = (now if now is not None else time.time()) - hours * 3600
        stale = [
            code
            for code, session in self.sessions.items()
            if (session.updated_at or session.created_at or 0) < cutoff
        ]
        for code in stale:
            del self.sessions[code]
        return len(stale)

    def _payload(self) -> str:
        return json.dumps(
            {
                "version": 1,
                "sessions": {code: session.to_dict() for code, session in self.sessions.items()},
                "cards": self.cards,
            }
        )

    def _write(self, text: str) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(self.path)

    def save(self) -> None:
        """Write everything now. Game code calls request_save() instead."""
        self._dirty = False
        self._write(self._payload())

    def request_save(self) -> None:
        """Mark the store changed. One write happens SAVE_DELAY seconds later.

        Outside an event loop (scripts, some tests) it writes right away.
        """
        self._dirty = True
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self.save()
            return
        if self._flush_task is None or self._flush_task.done() or self._flush_task.get_loop() is not loop:
            self._flush_task = loop.create_task(self._flush_later())

    async def _flush_later(self) -> None:
        # Loop so a change that lands during a write gets its own write.
        while True:
            await asyncio.sleep(SAVE_DELAY)
            if not await self.flush() or not self._dirty:
                return

    async def flush(self) -> bool:
        """Write pending changes. The JSON is built under the lock; the disk write runs in a thread.

        Returns False if the write failed (the change stays pending for the next save).
        """
        if not self._dirty:
            return True
        async with self.lock:
            self.prune()
            self._dirty = False
            text = self._payload()
        try:
            await asyncio.to_thread(self._write, text)
        except OSError:
            logger.exception("Could not save games to %s", self.path)
            self._dirty = True
            return False
        return True

    def flush_now(self) -> None:
        """Synchronous write of pending changes, for shutdown."""
        if self._dirty:
            self.save()

    def get(self, code: str) -> Session | None:
        return self.sessions.get(code.upper())


store = Store()
store.load()
