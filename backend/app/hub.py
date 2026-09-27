from __future__ import annotations

import logging

from fastapi import WebSocket

logger = logging.getLogger("coralconnect.hub")


class Hub:
    def __init__(self) -> None:
        self.rooms: dict[str, set[WebSocket]] = {}
        self.who: dict[WebSocket, tuple[str, str]] = {}

    def add(self, code: str, socket: WebSocket) -> None:
        self.rooms.setdefault(code, set()).add(socket)

    def identify(self, code: str, socket: WebSocket, player_id: str) -> None:
        self.who[socket] = (code, player_id)

    def online(self, code: str, player_id: str) -> bool:
        room = self.rooms.get(code, ())
        return any(self.who.get(socket) == (code, player_id) and socket in room for socket in room)

    def remove(self, code: str, socket: WebSocket) -> tuple[str, str] | None:
        room = self.rooms.get(code)
        if room:
            room.discard(socket)
            if not room:
                self.rooms.pop(code, None)
        return self.who.pop(socket, None)

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
