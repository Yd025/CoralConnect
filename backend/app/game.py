from __future__ import annotations

import asyncio
import secrets
import time

from .carbon import (
    WEB_LOOKUP_TOKENS,
    carbon_grams,
    clamp_health,
    count_tokens,
    event_type,
    excess_kg_at_scale,
    explain,
    grade_for,
    lookup_cost,
    reef_delta,
    score_for,
)
from .challenges import get_challenge
from .config import settings
from .grok import complete, describe_pair, finalize_verdict, imagine, review_call
from .hub import hub
from .models import ChatMessage, Player, ReefEvent, Session, Squad, Submission, Thread, player_bounds
from .serialize import public_session
from .store import store

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CREATURES = ("Seagull", "Turtle", "Dolphin", "Octopus", "Whale", "Crab", "Ray", "Heron")
LANGUAGES = (
    "Python",
    "JavaScript",
    "TypeScript",
    "Java",
    "C++",
    "Go",
    "Rust",
    "Other",
)
EVENT_TITLES = {
    "turtle": "{actor} spawned a sea turtle",
    "bloom": "{actor} grew a coral bloom",
    "fish": "{actor} kept the reef steady",
    "murk": "{actor} clouded the water",
    "sludge": "{actor} dropped a sludge barrel",
}


class GameError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _code() -> str:
    for _ in range(20):
        candidate = "".join(secrets.choice(ALPHABET) for _ in range(4))
        if candidate not in store.sessions:
            return candidate
    return secrets.token_hex(3).upper()


def _id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def _must(code: str) -> Session:
    session = store.get(code)
    if session is None:
        raise GameError(404, "No game with that code. Create a new one on the admin screen.")
    return session


def _check_admin(session: Session, admin_token: str) -> None:
    if not admin_token or not secrets.compare_digest(admin_token, session.admin_token):
        raise GameError(403, "That admin key doesn't match this game.")


def _player(session: Session, player_id: str, player_token: str) -> Player:
    player = next((p for p in session.players if p.id == player_id), None)
    if player is None or not secrets.compare_digest(player.token, player_token):
        raise GameError(403, "Rejoin this game from the phone that entered it.")
    return player


def _roster(session: Session) -> list[Player]:
    return [player for player in session.players if player.id != "p_rehearsal"]


def _squad_for(session: Session, player: Player) -> Squad | None:
    if not player.squad_id:
        return None
    return next((s for s in session.squads if s.id == player.squad_id), None)


def _normalize_language(language: str) -> str:
    cleaned = " ".join(language.strip().split())[:24]
    if not cleaned:
        return "Other"
    for option in LANGUAGES:
        if option.lower() == cleaned.lower():
            return option
    return cleaned


def _normalize_answer(answer: str) -> str:
    return " ".join(answer.strip().split())[:80]


def _needs_every_fact(beat, mode: str) -> bool:
    return mode == "collaborate" and len(getattr(beat, "parts", ())) >= 2


def _facts_for(beat, mode: str) -> tuple[str, ...]:
    if _needs_every_fact(beat, mode):
        return tuple(part.anchor for part in beat.parts if part.anchor)
    return beat.anchors


def _every_fact_cost(prompt: str, facts: tuple[str, ...]) -> int:
    folded = prompt.lower()
    if facts and all(fact.lower() in folded for fact in facts):
        return 0
    return WEB_LOOKUP_TOKENS


def _profiles(members: list[Player]) -> list[dict]:
    return [
        {"id": member.id, "name": member.name, "builds": member.builds, "cares": member.cares}
        for member in members
    ]


def _local_connection(members: list[Player]) -> dict[str, str]:
    if len(members) == 1:
        person = members[0]
        return {
            "name": f"{person.name}'s seat",
            "shared": f"{person.name} is waiting for someone to work with.",
            "distinct": f"{person.name} builds {person.builds or 'something they have not named yet'}.",
        }
    names = " and ".join(member.name for member in members)
    shared = " ".join(
        f"{member.name} wants the work to care about {member.cares or 'something they have not named yet'}."
        for member in members
    )
    distinct = " ".join(
        f"Only {member.name} builds {member.builds or 'something they have not named yet'}."
        for member in members
    )
    return {"name": names, "shared": shared, "distinct": distinct}


def _pair(players: list[Player]) -> list[list[Player]]:
    ordered = sorted(
        (player for player in players if player.connected),
        key=lambda player: (player.joined_at, player.id),
    )
    squads: list[list[Player]] = []
    pool = list(ordered)
    while len(pool) >= 2:
        squads.append([pool.pop(0), pool.pop(0)])
    if pool:
        squads.append(pool)
    return squads


def _groups_from_match(players: list[Player], matched: list[dict] | None) -> list[tuple[list[Player], dict | None]]:
    if not matched:
        return [(members, None) for members in _pair(players)]
    by_id = {player.id: player for player in players if player.connected}
    seen: list[str] = []
    groups: list[tuple[list[Player], dict | None]] = []
    for item in matched:
        ids = [str(player_id) for player_id in item.get("playerIds") or []]
        if not ids or any(player_id not in by_id or player_id in seen for player_id in ids):
            return [(members, None) for members in _pair(players)]
        seen.extend(ids)
        groups.append(([by_id[player_id] for player_id in ids], item))
    if set(seen) != set(by_id):
        return [(members, None) for members in _pair(players)]
    return groups


def _local_closing(members: list[Player]) -> str:
    builds = " and ".join(member.builds for member in members if member.builds) or "software"
    cares = " and ".join(dict.fromkeys(member.cares for member in members if member.cares)) or "the living world"
    return (
        f"You found each other. Talk about the environment before you split up. "
        f"You build {builds}, and you care about {cares}. "
        f"What would you change so that work costs the ocean less?"
    )


def _next_creature(session: Session) -> str:
    used = {squad.creature for squad in session.squads if squad.creature}
    for creature in CREATURES:
        if creature not in used:
            return creature
    return CREATURES[len(used) % len(CREATURES)]


def _apply_connection(squad: Squad, members: list[Player], meta: dict | None) -> None:
    local = _local_connection(members)
    source = meta or {}
    squad.shared = str(source.get("shared") or local["shared"])[:240]
    squad.distinct = str(source.get("distinct") or local["distinct"])[:240]
    squad.closing = str(source.get("closing") or squad.closing or _local_closing(members))[:280]
    squad.name = squad.creature or str(source.get("name") or local["name"])[:48]
    squad.icebreaker = f"{squad.shared} {squad.distinct}".strip()


def _persist(session: Session) -> None:
    session.revision += 1
    store.save()


async def _broadcast(session: Session) -> None:
    await hub.broadcast(session.code, {"type": "state", "session": public_session(session)})


async def create_session(mode: str, challenge_id: str) -> tuple[Session, str]:
    if mode not in {"collaborate", "compete"}:
        raise GameError(400, "Mode must be collaborate or compete.")
    challenge = get_challenge(challenge_id)
    if challenge is None:
        raise GameError(400, "Pick a challenge from the list.")
    async with store.lock:
        session = Session(
            code=_code(),
            admin_token=secrets.token_urlsafe(18),
            mode=mode,
            status="lobby",
            challenge_id=challenge.id,
            reef_health=100,
            players=[],
            squads=[],
            submissions=[],
            events=[],
            created_at=time.time(),
        )
        store.sessions[session.code] = session
        _persist(session)
    await _broadcast(session)
    return session, session.admin_token


async def open_collaborate() -> Session:
    """The standing pair room. People join it from their own phones, with no admin start."""
    async with store.lock:
        _, maximum = player_bounds("collaborate")
        open_rooms = [
            session
            for session in store.sessions.values()
            if session.mode == "collaborate"
            and session.status != "ended"
            and len(_roster(session)) < maximum
        ]
        if open_rooms:
            return min(open_rooms, key=lambda session: session.created_at)
        challenge = get_challenge("invoice-bug")
        if challenge is None:
            raise GameError(500, "The pair room has no challenge to run.")
        session = Session(
            code=_code(),
            admin_token=secrets.token_urlsafe(18),
            mode="collaborate",
            status="lobby",
            challenge_id=challenge.id,
            reef_health=100,
            players=[],
            squads=[],
            submissions=[],
            events=[],
            created_at=time.time(),
        )
        store.sessions[session.code] = session
        _persist(session)
    await _broadcast(session)
    return session


async def join(
    code: str,
    name: str,
    language: str = "Python",
    builds: str = "",
    cares: str = "",
) -> tuple[Session, Player]:
    cleaned = " ".join(name.strip().split())
    if len(cleaned) < 1 or len(cleaned) > 20:
        raise GameError(400, "Use a name between 1 and 20 characters.")
    chosen = _normalize_language(language)
    chosen_builds = _normalize_answer(builds)
    chosen_cares = _normalize_answer(cares)
    async with store.lock:
        session = _must(code)
        if session.status == "ended":
            raise GameError(409, "This game has ended. Ask the table for a new QR code.")
        _, maximum = player_bounds(session.mode)
        if len(_roster(session)) >= maximum:
            if session.mode == "collaborate":
                raise GameError(409, "This room is full. It holds 8 players, two to a pair.")
            raise GameError(409, "This compete table is full. It holds up to 10 players.")
        player = Player(
            id=_id("p"),
            token=secrets.token_urlsafe(18),
            name=cleaned,
            language=chosen,
            builds=chosen_builds,
            cares=chosen_cares,
            connected=True,
            joined_at=time.time(),
        )
        session.players.append(player)
        paired_squad = None
        if session.mode == "collaborate":
            paired_squad = _seat_partner(session, player)
        _persist(session)
    await _broadcast(session)
    if paired_squad and settings.xai_api_key:
        asyncio.create_task(_rename_squad(code, paired_squad))
    return session, player


def _seat_partner(session: Session, player: Player) -> str | None:
    """Pair this person with whoever is waiting. Returns the squad id once both phones share an animal."""
    waiting = next((squad for squad in session.squads if len(squad.player_ids) == 1), None)
    if waiting:
        waiting.player_ids.append(player.id)
        player.squad_id = waiting.id
        waiting.creature = waiting.creature or _next_creature(session)
        mate = next(person for person in session.players if person.id == waiting.player_ids[0])
        _apply_connection(waiting, [mate, player], None)
        return waiting.id
    squad = Squad(
        id=_id("s"),
        name="Looking",
        player_ids=[player.id],
        icebreaker="Hold your phone up. Your pair has not walked in yet.",
        shared="Hold your phone up. Your pair has not walked in yet.",
    )
    player.squad_id = squad.id
    session.squads.append(squad)
    return None


def _release_partner(session: Session, player_id: str) -> None:
    squad = next((item for item in session.squads if player_id in item.player_ids), None)
    if squad is None:
        return
    squad.player_ids = [pid for pid in squad.player_ids if pid != player_id]
    if not squad.player_ids:
        session.squads = [item for item in session.squads if item.id != squad.id]
        return
    squad.creature = ""
    squad.name = "Looking"
    squad.shared = "Hold your phone up. Your pair has not walked in yet."
    squad.distinct = ""
    squad.closing = ""
    squad.icebreaker = squad.shared


async def leave(code: str, player_id: str, player_token: str) -> Session:
    async with store.lock:
        session = _must(code)
        player = _player(session, player_id, player_token)
        if session.status == "lobby":
            session.players = [p for p in session.players if p.id != player.id]
            if session.mode == "collaborate":
                _release_partner(session, player.id)
        else:
            player.connected = False
        _persist(session)
    await _broadcast(session)
    return session


async def start(code: str, admin_token: str) -> Session:
    async with store.lock:
        session = _must(code)
        _check_admin(session, admin_token)
        if session.status == "ended":
            raise GameError(409, "This game has ended. Ask the table for a new QR code.")
        connected = [p for p in _roster(session) if p.connected]
        minimum, maximum = player_bounds(session.mode)
        if session.mode == "collaborate":
            raise GameError(409, "Pairs start when both phones show the same animal. This room does not share one start.")
        elif len(connected) < minimum or len(connected) > maximum:
            raise GameError(409, "Compete needs 1 to 10 players before the round starts.")
        session.status = "playing"
        _persist(session)
    await _broadcast(session)
    return session


def _form_squads(session: Session, connected: list[Player], matched: list[dict] | None = None) -> None:
    session.squads = []
    for members, meta in _groups_from_match(connected, matched):
        squad = Squad(
            id=_id("s"),
            name="",
            player_ids=[member.id for member in members],
            icebreaker="",
            creature=_next_creature(session) if len(members) == 2 else "",
        )
        _apply_connection(squad, members, meta)
        session.squads.append(squad)
        member_ids = set(squad.player_ids)
        for player in session.players:
            if player.id in member_ids:
                player.squad_id = squad.id


async def _rename_squad(code: str, squad_id: str) -> None:
    async with store.lock:
        session = store.get(code)
        if session is None:
            return
        squad = next((s for s in session.squads if s.id == squad_id), None)
        if squad is None:
            return
        members = [p for p in session.players if p.id in squad.player_ids]
        profiles = _profiles(members)
    named = await describe_pair(profiles)
    if not named:
        return
    async with store.lock:
        session = store.get(code)
        if session is None or session.status == "ended":
            return
        squad = next((s for s in session.squads if s.id == squad_id), None)
        if squad is None:
            return
        members = [p for p in session.players if p.id in squad.player_ids]
        _apply_connection(squad, members, named)
        _persist(session)
    await _broadcast(session)


async def end(code: str, admin_token: str) -> Session:
    async with store.lock:
        session = _must(code)
        _check_admin(session, admin_token)
        session.status = "ended"
        _persist(session)
    await _broadcast(session)
    return session


async def set_challenge(code: str, admin_token: str, challenge_id: str) -> Session:
    challenge = get_challenge(challenge_id)
    if challenge is None:
        raise GameError(400, "Pick a challenge from the list.")
    async with store.lock:
        session = _must(code)
        _check_admin(session, admin_token)
        session.challenge_id = challenge.id
        session.threads = []
        for squad in session.squads:
            squad.prompt = ""
            squad.prompt_author_id = None
            squad.prompt_updated_at = 0
        if session.status == "ended":
            session.status = "lobby"
        _persist(session)
    await _broadcast(session)
    return session


async def update_draft(code: str, player_id: str, player_token: str, text: str) -> None:
    cleaned = text[:8000]
    async with store.lock:
        session = store.get(code)
        if session is None or session.mode != "collaborate" or session.status == "ended":
            return
        try:
            player = _player(session, player_id, player_token)
        except GameError:
            return
        squad = _squad_for(session, player)
        if squad is None or len(squad.player_ids) < 2 or squad.prompt == cleaned:
            return
        squad.prompt = cleaned
        squad.prompt_author_id = player.id
        squad.prompt_updated_at = time.time()
        _persist(session)
    await _broadcast(session)


async def submit(
    code: str,
    player_id: str,
    player_token: str,
    prompt: str,
    *,
    use_model: bool = True,
) -> tuple[Session, Submission]:
    text = prompt.strip()
    if not text:
        raise GameError(400, "Write a prompt first.")
    if len(text) > 8000:
        raise GameError(400, "That prompt is past the 8,000 character limit.")

    async with store.lock:
        session = _must(code)
        player = _player(session, player_id, player_token)
        if session.status == "ended":
            raise GameError(409, "This game has ended. Ask the table for a new QR code.")
        if session.mode == "collaborate":
            squad_now = _squad_for(session, player)
            if squad_now is None or len(squad_now.player_ids) < 2:
                raise GameError(409, "Find the other person with your animal before you send a prompt.")
        elif session.status != "playing":
            raise GameError(409, "Wait for the host to start the round. Compete is one round for the room.")
        challenge = get_challenge(session.challenge_id)
        if challenge is None:
            raise GameError(500, "This game's challenge is missing.")
        squad = _squad_for(session, player)
        if session.mode == "collaborate":
            actor = squad.name if squad else player.name
            squad_id = squad.id if squad else None
            owner_id = squad.id if squad else player.id
        else:
            actor = player.name
            squad_id = None
            owner_id = player.id
        thread = next((item for item in session.threads if item.owner_id == owner_id), None)
        if thread and thread.done:
            raise GameError(409, "This thread is closed. Ask the host for the next challenge.")
        step = thread.step if thread else 0
        if step >= len(challenge.beats):
            raise GameError(409, "This thread is closed. Ask the host for the next challenge.")
        history = list(thread.messages) if thread else []
        beat = challenge.beats[step]
        challenge_id = challenge.id
        mode = session.mode

    tokens = count_tokens(text)
    facts = _facts_for(beat, mode)
    local_lookup = lookup_cost(text, facts) if not _needs_every_fact(beat, mode) else _every_fact_cost(text, facts)
    local_grams = carbon_grams(local_lookup)
    local_excess = excess_kg_at_scale(local_lookup, 0)
    local_reason = explain(
        local_lookup,
        local_grams,
        local_excess,
        turn=step + 1,
        turn_count=len(challenge.beats),
    )
    messages = [{"role": message.role, "content": message.content} for message in history]
    messages.append({"role": "user", "content": text})

    if use_model:
        answer, simulated, request, trace = await complete(messages, beat.simulated_reply)
        model_verdict = None
        if not simulated:
            model_verdict = await review_call(beat.ask, facts, request, trace)
        reasonable, verdict_reason, judged = finalize_verdict(
            model_verdict,
            trace,
            local_reasonable=local_lookup == 0,
            local_reason=local_reason,
        )
    else:
        answer, simulated = beat.simulated_reply, True
        trace = {"serverSideTools": 0}
        reasonable, verdict_reason, judged = local_lookup == 0, local_reason, False

    looked_up = 0 if reasonable else max(local_lookup, 1200)
    grade = grade_for(looked_up, 80)
    score = score_for(looked_up, 80)
    grams = carbon_grams(looked_up)
    excess_kg = excess_kg_at_scale(looked_up, 0)
    summary = verdict_reason if judged else explain(
        looked_up, grams, excess_kg, turn=step + 1, turn_count=len(challenge.beats)
    )
    if judged and looked_up > 0:
        summary = f"{verdict_reason} About {grams:.3f} g CO2e."
    delta = reef_delta(grade)
    kind = event_type(grade)
    server_side_tools = int(trace.get("serverSideTools") or 0)

    async with store.lock:
        session = _must(code)
        player = _player(session, player_id, player_token)
        if session.challenge_id != challenge_id or session.status == "ended":
            raise GameError(409, "The host moved on. Take a look at the new challenge.")
        if session.mode != "collaborate" and session.status != "playing":
            raise GameError(409, "Wait for the host to start the round. Compete is one round for the room.")
        squad = _squad_for(session, player)
        if session.mode == "collaborate" and squad:
            owner_id = squad.id
        else:
            owner_id = player.id
        thread = next((item for item in session.threads if item.owner_id == owner_id), None)
        if thread is None:
            thread = Thread(owner_id=owner_id, messages=[])
            session.threads.append(thread)
        if thread.done or thread.step != step:
            raise GameError(409, "The host moved on. Take a look at the new challenge.")
        thread.messages.append(ChatMessage(role="user", content=text))
        thread.messages.append(ChatMessage(role="assistant", content=answer))
        thread.step += 1
        thread.done = thread.step >= len(challenge.beats)
        thread.score_sum += score
        thread.turns_graded += 1
        averaged = round(thread.score_sum / thread.turns_graded)
        session.reef_health = clamp_health(session.reef_health + delta)
        if session.mode == "collaborate" and squad:
            squad.score = averaged
            squad.last_grade = grade
            squad.prompt = ""
            squad.prompt_author_id = player.id
            squad.prompt_updated_at = time.time()
            for member in session.players:
                if member.id in squad.player_ids:
                    member.score = averaged
                    member.last_grade = grade
            actor = squad.name
            squad_id = squad.id
        else:
            player.score = averaged
            player.last_grade = grade
            actor = player.name
            squad_id = None

        submission = Submission(
            id=_id("sub"),
            player_id=player.id,
            squad_id=squad_id,
            actor=actor,
            prompt=text,
            token_count=tokens,
            target_tokens=beat.target_tokens,
            lookup_tokens=looked_up,
            carbon_grams=grams,
            excess_kg_at_scale=excess_kg,
            grade=grade,
            score=score,
            reef_delta=delta,
            reef_health=session.reef_health,
            ai_response=answer,
            simulated=simulated,
            summary=summary,
            event_type=kind,
            created_at=time.time(),
            turn_index=step,
            turn_count=len(challenge.beats),
            reasonable=reasonable,
            verdict_reason=verdict_reason,
            judged_by_model=judged,
            server_side_tools=server_side_tools,
        )
        event = ReefEvent(
            id=_id("evt"),
            type=kind,
            title=EVENT_TITLES[kind].format(actor=actor),
            subtitle=summary,
            grade=grade,
            actor=actor,
            image_url=None,
            created_at=submission.created_at,
        )
        session.submissions.insert(0, submission)
        session.events.insert(0, event)
        del session.submissions[40:]
        del session.events[20:]
        _persist(session)
        event_id = event.id

    await _broadcast(session)
    if kind in {"turtle", "bloom"} and use_model and settings.xai_api_key and settings.grok_images:
        asyncio.create_task(_paint(session.code, event_id, kind, actor))
    return session, submission


async def _paint(code: str, event_id: str, kind: str, actor: str) -> None:
    url = await imagine(kind, actor)
    if not url:
        return
    async with store.lock:
        session = store.get(code)
        if session is None:
            return
        event = next((item for item in session.events if item.id == event_id), None)
        if event is None:
            return
        event.image_url = url
        _persist(session)
    await _broadcast(session)


async def simulate(code: str, admin_token: str, kind: str) -> tuple[Session, Submission]:
    if kind not in {"efficient", "bloated"}:
        raise GameError(400, "Simulate efficient or bloated.")
    async with store.lock:
        session = _must(code)
        _check_admin(session, admin_token)
        challenge = get_challenge(session.challenge_id)
        if challenge is None:
            raise GameError(500, "This game's challenge is missing.")
        if session.status == "lobby":
            connected = [p for p in session.players if p.connected and p.id != "p_rehearsal"]
            if session.mode == "collaborate" and connected and not any(len(squad.player_ids) == 2 for squad in session.squads):
                _form_squads(session, connected)
            session.status = "playing"
        if session.status != "playing":
            raise GameError(409, "Start a new round before rehearsing.")
        player = next((p for p in session.players if p.id == "p_rehearsal"), None)
        if player is None:
            player = Player(
                id="p_rehearsal",
                token=secrets.token_urlsafe(18),
                name="Rehearsal",
                language="Python",
                builds="booth check",
                cares="the reef",
                connected=True,
                joined_at=time.time(),
            )
            session.players.append(player)
            if session.mode == "collaborate":
                squad = Squad(
                    id="s_rehearsal",
                    name="Rehearsal Reef",
                    player_ids=[player.id],
                    icebreaker="This squad exists so you can test the reef without a phone.",
                    shared="Rehearsal is checking the reef.",
                    distinct="No partner is at the table.",
                )
                player.squad_id = squad.id
                session.squads.append(squad)
        prompts = challenge.example_efficient if kind == "efficient" else (challenge.example_bloated,)
        player_token = player.token
        player_id = player.id
        _persist(session)
    last_session = session
    last_submission: Submission | None = None
    for prompt in prompts:
        last_session, last_submission = await submit(
            code, player_id, player_token, prompt, use_model=False
        )
    if last_submission is None:
        raise GameError(500, "Rehearsal had nothing to send.")
    return last_session, last_submission


def lan_ip() -> str:
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        address = sock.getsockname()[0]
        sock.close()
        return address
    except OSError:
        return "127.0.0.1"
