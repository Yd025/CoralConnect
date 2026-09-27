from __future__ import annotations

import logging

from fastapi import WebSocket

logger = logging.getLogger("coralconnect.hub")


class Hub:
    def __init__(self) -> None:
        self.rooms: dict[str, set[WebSocket]] = {}
        # Which player each phone socket belongs to, once it says hello.
        self.owners: dict[WebSocket, tuple[str, str]] = {}

    def add(self, code: str, socket: WebSocket) -> None:
        self.rooms.setdefault(code, set()).add(socket)

    def bind(self, code: str, socket: WebSocket, player_id: str) -> None:
        self.owners[socket] = (code, player_id)

    def remove(self, code: str, socket: WebSocket) -> str | None:
        """Forget a socket. Returns the player id if that was their last open socket."""
        room = self.rooms.get(code)
        if room:
            room.discard(socket)
            if not room:
                self.rooms.pop(code, None)
        owner = self.owners.pop(socket, None)
        if owner is None:
            return None
        if any(other == owner for other in self.owners.values()):
            return None
        return owner[1]

    async def broadcast(self, code: str, message: dict) -> None:
        room = list(self.rooms.get(code, ()))
        for socket in room:
            try:
                await socket.send_json(message)
            except Exception:
                # The socket's own handler sees the disconnect and cleans up
                # (including the player's presence), so only drop it from the room here.
                logger.debug("dropping closed socket in %s", code)
                current = self.rooms.get(code)
                if current is not None:
                    current.discard(socket)
                    if not current:
                        self.rooms.pop(code, None)


hub = Hub()
