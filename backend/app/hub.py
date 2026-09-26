from __future__ import annotations

import logging

from fastapi import WebSocket

logger = logging.getLogger("coralconnect.hub")


class Hub:
    def __init__(self) -> None:
        self.rooms: dict[str, set[WebSocket]] = {}

    def add(self, code: str, socket: WebSocket) -> None:
        self.rooms.setdefault(code, set()).add(socket)

    def remove(self, code: str, socket: WebSocket) -> None:
        room = self.rooms.get(code)
        if not room:
            return
        room.discard(socket)
        if not room:
            self.rooms.pop(code, None)

    async def broadcast(self, code: str, message: dict) -> None:
        room = list(self.rooms.get(code, ()))
        dead: list[WebSocket] = []
        for socket in room:
            try:
                await socket.send_json(message)
            except Exception:
                logger.debug("dropping closed socket in %s", code)
                dead.append(socket)
        for socket in dead:
            self.remove(code, socket)


hub = Hub()
