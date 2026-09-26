from __future__ import annotations

import logging

from fastapi import FastAPI, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import game
from .carbon import FORMULA
from .challenges import public_challenges
from .config import settings
from .game import GameError
from .hub import hub
from .serialize import public_session, public_submission
from .store import store

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("coralconnect")

app = FastAPI(title="CoralConnect", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateBody(BaseModel):
    mode: str
    challengeId: str


class JoinBody(BaseModel):
    name: str
    language: str = "Python"
    builds: str = ""
    cares: str = ""


class PlayerBody(BaseModel):
    playerId: str
    playerToken: str


class SubmitBody(PlayerBody):
    prompt: str = Field(max_length=8000)


class ChallengeBody(BaseModel):
    challengeId: str


class SimulateBody(BaseModel):
    kind: str


def _error(exc: GameError) -> JSONResponse:
    return JSONResponse({"error": exc.message}, status_code=exc.status)


@app.get("/api/health")
def health() -> dict:
    configured = bool(settings.xai_api_key)
    return {
        "ok": True,
        "grokConfigured": configured,
        "chatModel": settings.grok_model,
        "imageModel": settings.grok_image_model,
        "imagesEnabled": configured and settings.grok_images,
        "grokRoles": [
            "answer the player's prompt",
            "judge that prompt from the solver API call",
            "pair people from what they build and what they want the work to care about",
        ],
        "lanIp": game.lan_ip(),
        "formula": FORMULA,
    }


@app.get("/api/challenges")
def challenges() -> dict:
    return {"challenges": public_challenges()}


@app.post("/api/sessions")
async def create_session(body: CreateBody):
    try:
        session, admin_token = await game.create_session(body.mode, body.challengeId)
    except GameError as exc:
        return _error(exc)
    return {"adminToken": admin_token, "session": public_session(session)}


@app.get("/api/sessions/{code}")
def read_session(code: str):
    session = store.get(code)
    if session is None:
        return JSONResponse({"error": "No game with that code."}, status_code=404)
    return {"session": public_session(session)}


@app.post("/api/sessions/{code}/join")
async def join(code: str, body: JoinBody):
    try:
        session, player = await game.join(code, body.name, body.language, body.builds, body.cares)
    except GameError as exc:
        return _error(exc)
    return {
        "playerToken": player.token,
        "player": {
            "id": player.id,
            "name": player.name,
            "language": player.language,
            "builds": player.builds,
            "cares": player.cares,
            "squadId": player.squad_id,
        },
        "session": public_session(session),
    }


@app.post("/api/sessions/{code}/leave")
async def leave(code: str, body: PlayerBody):
    try:
        session = await game.leave(code, body.playerId, body.playerToken)
    except GameError as exc:
        return _error(exc)
    return {"session": public_session(session)}


@app.post("/api/sessions/{code}/start")
async def start(code: str, x_admin_token: str = Header(default="")):
    try:
        session = await game.start(code, x_admin_token)
    except GameError as exc:
        return _error(exc)
    return {"session": public_session(session)}


@app.post("/api/sessions/{code}/end")
async def end(code: str, x_admin_token: str = Header(default="")):
    try:
        session = await game.end(code, x_admin_token)
    except GameError as exc:
        return _error(exc)
    return {"session": public_session(session)}


@app.post("/api/sessions/{code}/challenge")
async def set_challenge(code: str, body: ChallengeBody, x_admin_token: str = Header(default="")):
    try:
        session = await game.set_challenge(code, x_admin_token, body.challengeId)
    except GameError as exc:
        return _error(exc)
    return {"session": public_session(session)}


@app.post("/api/sessions/{code}/submit")
async def submit(code: str, body: SubmitBody):
    try:
        session, submission = await game.submit(code, body.playerId, body.playerToken, body.prompt)
    except GameError as exc:
        return _error(exc)
    return {"session": public_session(session), "submission": public_submission(submission)}


@app.post("/api/sessions/{code}/simulate")
async def simulate(code: str, body: SimulateBody, x_admin_token: str = Header(default="")):
    try:
        session, submission = await game.simulate(code, x_admin_token, body.kind)
    except GameError as exc:
        return _error(exc)
    return {"session": public_session(session), "submission": public_submission(submission)}


@app.websocket("/ws/{code}")
async def socket(code: str, websocket: WebSocket):
    await websocket.accept()
    normalized = code.upper()
    session = store.get(normalized)
    if session is None:
        await websocket.send_json({"type": "error", "message": "No game with that code."})
        await websocket.close()
        return
    hub.add(normalized, websocket)
    try:
        await websocket.send_json({"type": "state", "session": public_session(session)})
        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                continue
            if data.get("type") == "draft":
                await game.update_draft(
                    normalized,
                    str(data.get("playerId") or ""),
                    str(data.get("playerToken") or ""),
                    str(data.get("text") or ""),
                )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.debug("socket closed for %s", normalized, exc_info=True)
    finally:
        hub.remove(normalized, websocket)
