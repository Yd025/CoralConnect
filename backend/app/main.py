from __future__ import annotations

import asyncio
import logging

import secrets
from typing import Literal

from fastapi import FastAPI, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import game, grok, judge
from .carbon import FORMULA
from .challenges import get_challenge, public_challenges
from .config import settings
from .game import GameError
from .grading import beat_for, build_prompt_score
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


class HistoryItem(BaseModel):
    role: Literal["user", "assistant"] = "user"
    content: str = Field(default="", max_length=8000)


class JudgeContext(BaseModel):
    # With a challengeId, the judge uses that round's answer key (game mode).
    challengeId: str | None = None
    turn: int = Field(default=1, ge=1, le=10)
    history: list[HistoryItem] = Field(default_factory=list, max_length=20)
    # Collaborate mode also grades each partner's piece (grading.beat_for).
    gameMode: Literal["compete", "collaborate"] = "compete"


class JudgeBody(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    mode: Literal["fast", "full"] = "fast"
    context: JudgeContext | None = None


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
            "edit the pair's project files",
            "answer the player's prompt",
            "judge that prompt from the solver API call",
            "pair people from what they build and what they want the work to care about",
        ],
        "lanIp": game.lan_ip(),
        "techDomain": settings.tech_domain,
        "formula": FORMULA,
        "judge": {
            "endpoint": "/api/judge",
            "fullModeOpen": bool(settings.judge_api_key) and configured,
            "reviewerModel": settings.grok_judge_model,
            "fullPerMinute": settings.judge_full_per_minute,
        },
    }


@app.post("/api/judge")
async def judge_prompt(body: JudgeBody, x_judge_key: str = Header(default="")):
    """Judge one prompt. The game's phones, the plugin, and a Claude Code hook all call this.

    fast: rules only, free and instant. full: adds the Grok reviewer and real
    measured runs. Full mode needs the server's JUDGE_API_KEY in X-Judge-Key.
    Game mode (context.challengeId) never reveals the answer key and stays fast.
    """
    context = body.context or JudgeContext()
    history = [item.model_dump() for item in context.history]
    beat = None
    challenge = None
    if context.challengeId:
        challenge = get_challenge(context.challengeId)
        if challenge is None:
            return JSONResponse({"error": "Unknown challengeId."}, status_code=400)
        if context.turn > len(challenge.beats):
            return JSONResponse({"error": "That challenge has fewer turns."}, status_code=400)
        beat = beat_for(challenge.beats[context.turn - 1], context.gameMode)

    mode = body.mode
    note = ""
    if mode == "full":
        if beat is not None:
            mode, note = "fast", "Full judging runs when you send the turn."
        elif not settings.judge_api_key:
            mode, note = "fast", "Full mode is off on this server. Set JUDGE_API_KEY to turn it on."
        elif not secrets.compare_digest(x_judge_key, settings.judge_api_key):
            return JSONResponse({"error": "X-Judge-Key doesn't match this server's JUDGE_API_KEY."}, status_code=403)
        elif not grok.live():
            mode, note = "fast", "No Grok key on this server, so only the rules ran."
        elif not judge.allow_full():
            mode, note = "fast", "Full judging is busy right now. The rules ran instead."

    result = await judge.judge(body.prompt, beat=beat, history=history, mode=mode)
    judge.log_judgment(
        "api",
        body.prompt,
        result,
        beat=beat,
        challenge_id=context.challengeId or "",
        turn=context.turn if beat else 0,
        mode=mode,
    )
    verdict = judge.public_verdict(
        result,
        reveal=beat is None,
        vague_saving=judge.saved_vs_vague(result, beat),
        note=note,
    )
    verdict["modeUsed"] = mode
    if challenge is not None and challenge.files and context.gameMode == "collaborate":
        verdict["score"] = build_prompt_score(result, body.prompt)
    return verdict


@app.get("/api/challenges")
def challenges() -> dict:
    return {"challenges": public_challenges()}


@app.get("/api/cards/{card_id}")
def read_card(card_id: str):
    card = store.cards.get(card_id.upper())
    if card is None:
        return JSONResponse({"error": "No saved result with that link."}, status_code=404)
    return {"card": card}


@app.get("/api/pairs")
def pair_board():
    rows = [card for card in store.cards.values() if card.get("kind") == "collaborate"]
    rows.sort(key=lambda card: (-(card.get("score") or 0), card.get("team") or "", -(card.get("createdAt") or 0)))
    return {"pairs": rows}


@app.get("/api/collaborate")
async def open_collaborate():
    try:
        session = await game.open_collaborate()
    except GameError as exc:
        return _error(exc)
    return {"session": public_session(session)}


@app.post("/api/sessions")
async def create_session(body: CreateBody):
    try:
        session, admin_token = await game.create_session(body.mode, body.challengeId)
    except GameError as exc:
        return _error(exc)
    return {"adminToken": admin_token, "session": public_session(session)}


@app.get("/api/sessions/{code}")
async def read_session(code: str):
    if store.get(code) is None:
        return JSONResponse({"error": "No game with that code."}, status_code=404)
    try:
        session = await game.sweep_pair_clocks(code)
    except GameError as exc:
        return _error(exc)
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


@app.post("/api/sessions/{code}/ready")
async def ready(code: str, body: PlayerBody):
    try:
        session = await game.tap_start(code, body.playerId, body.playerToken)
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


@app.post("/api/sessions/{code}/next-group")
async def next_group(code: str, x_admin_token: str = Header(default="")):
    try:
        session = await game.next_group(code, x_admin_token)
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
            if data.get("type") == "hello":
                player_id = str(data.get("playerId") or "")
                if await game.note_presence(normalized, player_id, str(data.get("playerToken") or "")):
                    hub.identify(normalized, websocket, player_id)
            elif data.get("type") == "draft":
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
        owner = hub.remove(normalized, websocket)
        if owner and not hub.online(owner[0], owner[1]):
            asyncio.create_task(game.drop_absent_later(owner[0], owner[1]))
