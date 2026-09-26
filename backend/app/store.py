from __future__ import annotations

import asyncio
import json
from pathlib import Path

from .config import settings
from .models import Session


class Store:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.data_path
        self.sessions: dict[str, Session] = {}
        self.cards: dict[str, dict] = {}
        self.lock = asyncio.Lock()

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

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "sessions": {code: session.to_dict() for code, session in self.sessions.items()},
            "cards": self.cards,
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        temporary.replace(self.path)

    def get(self, code: str) -> Session | None:
        return self.sessions.get(code.upper())


store = Store()
store.load()
