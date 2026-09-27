from __future__ import annotations

import asyncio
import secrets
import time

from . import grok, judge
from .carbon import clamp_health, count_tokens, event_type, grade_for_score, reef_delta
from .challenges import BUILD_IDS, get_challenge
from .config import settings
from .grading import beat_for, grade_prompt, redact, summary as turn_summary, waive_unused_lookups
from .grok import describe_pair, imagine
from .hub import hub
from .models import ChatMessage, Player, ReefEvent, Session, Squad, Submission, Thread, player_bounds
from .serialize import public_session
from .store import store
from .workspace import apply_named, project_passes

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CREATURES = ("Seagull", "Turtle", "Dolphin", "Octopus", "Whale", "Crab", "Ray", "Heron")
ROUND_SECONDS = 120
STALE_WAIT_SECONDS = 20 * 60
# A phone that closed its socket this long ago is treated as gone from the
# table. Shorter gaps (a locked screen, a quick app switch) don't count.
AWAY_GRACE_SECONDS = 60
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
# The admin's rehearsal buttons play as this fake player. It must never be
# paired with a real person or counted as someone waiting in the lobby.
REHEARSAL_PLAYER_ID = "p_rehearsal"
REHEARSAL_SQUAD_ID = "s_rehearsal"
REHEARSAL_KINDS = {"efficient", "bloated", "vague"}
# Background work (the better-prompt measured run) is awaited inline when this
# is True. Tests set it so they can check the result without an event loop.
RUN_BACKGROUND_INLINE = False
_background: set[asyncio.Task] = set()


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
    """Everyone except the rehearsal bot."""
    return [player for player in session.players if player.id != REHEARSAL_PLAYER_ID]


def _away(player: Player, now: float | None = None) -> bool:
    """True once a player's phone has been gone for AWAY_GRACE_SECONDS."""
    if player.connected:
        return False
    return (now if now is not None else time.time()) - (player.left_at or 0) >= AWAY_GRACE_SECONDS


def _present(session: Session) -> list[Player]:
    """Everyone still at the table: the roster minus phones that walked away."""
    now = time.time()
    return [player for player in _roster(session) if not _away(player, now)]


def _clear_round(session: Session, *, keep_players: bool) -> None:
    """Wipe the reef and every thread so a new round starts clean, on the same game code.

    keep_players=True is "play again": the same people stay and get re-paired on start.
    keep_players=False is "next group": the lobby empties for the next people at the booth.
    """
    session.threads = []
    session.submissions = []
    session.events = []
    session.squads = []
    session.reef_health = 100
    if not keep_players:
        session.players = []
        return
    session.players = _present(session)
    for player in session.players:
        player.squad_id = None
        player.score = 0
        player.last_grade = None


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
    cares = [member.cares or "something they have not named yet" for member in members]
    builds = [member.builds or "something they have not named yet" for member in members]
    who = " and ".join(member.name for member in members)
    if len(set(cares)) == 1:
        shared = f"{who} both want the work to care about {cares[0]}."
    else:
        shared = " ".join(f"{member.name} wants the work to care about {cares[index]}." for index, member in enumerate(members))
    if len(set(builds)) == 1:
        distinct = f"{who} both build {builds[0]}."
    else:
        distinct = " ".join(f"Only {member.name} builds {builds[index]}." for index, member in enumerate(members))
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
    source = dict(meta or {})
    # When both people gave the same answer, the plain line is the true one.
    # Grok is asked for "what each brings" and can invent a difference.
    if len(members) > 1 and len({member.builds for member in members}) == 1:
        source.pop("distinct", None)
    if len(members) > 1 and len({member.cares for member in members}) == 1:
        source.pop("shared", None)
    squad.shared = str(source.get("shared") or local["shared"])[:240]
    squad.distinct = str(source.get("distinct") or local["distinct"])[:240]
    squad.closing = str(source.get("closing") or squad.closing or _local_closing(members))[:280]
    squad.name = squad.creature or str(source.get("name") or local["name"])[:48]
    squad.icebreaker = f"{squad.shared} {squad.distinct}".strip()


def _persist(session: Session) -> None:
    session.revision += 1
    session.updated_at = time.time()
    store.request_save()


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
            and session.challenge_id in BUILD_IDS
            and len(_roster(session)) < maximum
        ]
        if open_rooms:
            session = min(open_rooms, key=lambda session: session.created_at)
            if _drop_stale_waiters(session):
                _persist(session)
            return session
        challenge = get_challenge("team-chat")
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


def _match_score(player: Player, mate: Player) -> int:
    """Same work counts more than the same care. Zero means they do not overlap."""
    score = 0
    if player.builds and player.builds == mate.builds:
        score += 2
    if player.cares and player.cares == mate.cares:
        score += 1
    return score


def _pick_waiter(session: Session, player: Player) -> Squad | None:
    """Prefer a waiting person who builds or cares about the same thing. Otherwise the one who has waited longest."""
    waiters = [
        squad
        for squad in session.squads
        if (
            len(squad.player_ids) == 1
            and not squad.scored
            and not squad.started_at
            and squad.id != REHEARSAL_SQUAD_ID
            and player.id not in squad.player_ids
        )
    ]
    if not waiters:
        return None

    by_id = {person.id: person for person in session.players}
    # A waiting seat whose phone walked away is not someone to pair with.
    waiters = [squad for squad in waiters if squad.player_ids[0] in by_id and not _away(by_id[squad.player_ids[0]])]
    if not waiters:
        return None

    def rank(squad: Squad) -> tuple[int, float]:
        mate = by_id[squad.player_ids[0]]
        return (-_match_score(player, mate), mate.joined_at)

    return min(waiters, key=rank)


def _mint_card(session: Session, thread: Thread, squad: Squad | None, player: Player) -> None:
    """A finished round gets a public card the player can show, and a row on the pair board."""
    if thread.card_id:
        return
    challenge = get_challenge(session.challenge_id)
    if squad is not None:
        members = [person for person in session.players if person.id in squad.player_ids]
        names = [person.name for person in members]
        detail = "  ×  ".join(
            f"{person.name} · {person.builds} · {person.cares}".strip(" ·") for person in members
        )
        score = squad.score
        grade = squad.last_grade or ""
        kind = "collaborate"
    else:
        names = [player.name]
        detail = " · ".join(part for part in (player.builds, player.cares) if part)
        score = player.score
        grade = player.last_grade or ""
        kind = "compete"
    card_id = _code()
    while card_id in store.cards or card_id in store.sessions:
        card_id = _code()
    store.cards[card_id] = {
        "id": card_id,
        "kind": kind,
        "names": names,
        "detail": detail,
        "score": score,
        "grade": grade,
        "challenge": challenge.title if challenge else "",
        "room": session.code,
        "team": f"Team {squad.creature}" if squad is not None and squad.creature else "",
        "createdAt": time.time(),
    }
    thread.card_id = card_id


def _job_map(challenge) -> dict[str, str]:
    jobs: dict[str, str] = {}
    for beat in challenge.beats:
        for part in beat.parts:
            if part.title.endswith(".py"):
                jobs[part.title] = part.anchor
    return jobs


def _pair_thread(session: Session, squad: Squad) -> Thread | None:
    return next((item for item in session.threads if item.owner_id == squad.id), None)


def _clock_up(squad: Squad) -> bool:
    return bool(squad.started_at) and time.time() >= squad.started_at + ROUND_SECONDS


def _publish_pair(session: Session, squad: Squad, grade: str | None) -> None:
    """Put the summed prompting score on the team once the coding session is over."""
    thread = _pair_thread(session, squad)
    if thread is None:
        thread = Thread(owner_id=squad.id, messages=[])
        session.threads.append(thread)
    if thread.done and squad.scored:
        return
    thread.done = True
    squad.score = round(thread.score_sum / thread.turns_graded) if thread.turns_graded else 0
    squad.scored = True
    squad.member_names = [person.name for person in session.players if person.id in squad.player_ids]
    if thread.turns_graded:
        squad.last_grade = grade_for_score(squad.score)
    elif grade:
        squad.last_grade = grade
    else:
        latest = next((item for item in session.submissions if item.squad_id == squad.id), None)
        if latest is not None:
            squad.last_grade = latest.grade
    for member in session.players:
        if member.id in squad.player_ids:
            member.score = squad.score
            member.last_grade = squad.last_grade
    actor = next((person for person in session.players if person.id in squad.player_ids), None)
    if actor is not None:
        _mint_card(session, thread, squad, actor)


def _expire_squad(session: Session, squad: Squad, challenge) -> bool:
    if challenge is None or not challenge.files or not squad.started_at or not _clock_up(squad):
        return False
    thread = _pair_thread(session, squad)
    if thread is not None and thread.done:
        return False
    _publish_pair(session, squad, None)
    return True


def _maybe_finish_compete(session: Session) -> bool:
    """End the room once every person still at the table has finished the challenge.

    A phone that walked away (closed for AWAY_GRACE_SECONDS) doesn't hold the
    room open. Returns True when this call ended the game.
    """
    if session.mode != "compete" or session.status != "playing":
        return False
    roster = _present(session)
    if not roster:
        return False

    def finished(person: Player) -> bool:
        thread = next((item for item in session.threads if item.owner_id == person.id), None)
        return thread is not None and thread.done

    if all(finished(person) for person in roster):
        session.status = "ended"
        return True
    return False


def _drop_stale_waiters(session: Session) -> bool:
    """Unfinished waiting seats should not sit in the pair room for hours."""
    if session.mode != "collaborate":
        return False
    now = time.time()
    stale: list[str] = []
    for squad in session.squads:
        if squad.scored or squad.started_at:
            continue
        members = [person for person in session.players if person.id in squad.player_ids]
        if not members:
            continue
        newest = max(person.joined_at or session.created_at for person in members)
        if now - newest >= STALE_WAIT_SECONDS:
            stale.extend(person.id for person in members)
    if not stale:
        return False
    for player_id in stale:
        _release_partner(session, player_id)
    session.players = [person for person in session.players if person.id not in stale]
    return True


async def sweep_pair_clocks(code: str) -> Session:
    """Close a build round whose 2 minutes have passed, even if nobody prompts again.

    Also ends a compete room once everyone still at the table is done, so one
    phone that walked away doesn't keep the host waiting.
    """
    changed = False
    async with store.lock:
        session = _must(code)
        if _drop_stale_waiters(session):
            changed = True
        challenge = get_challenge(session.challenge_id)
        for squad in session.squads:
            if _expire_squad(session, squad, challenge):
                changed = True
        if _maybe_finish_compete(session):
            changed = True
        if changed:
            _persist(session)
    if changed:
        await _broadcast(session)
    return session


async def tap_start(code: str, player_id: str, player_token: str) -> Session:
    """One person in a pair says they have found the other. The clock starts on the second tap."""
    async with store.lock:
        session = _must(code)
        player = _player(session, player_id, player_token)
        if session.mode != "collaborate":
            raise GameError(409, "Compete starts from the table, not from a phone.")
        squad = _squad_for(session, player)
        if squad is None or len(squad.player_ids) < 2:
            raise GameError(409, "Find the other person with your animal first.")
        challenge = get_challenge(session.challenge_id)
        if challenge is None or not challenge.files:
            raise GameError(409, "This room does not wait for a start tap.")
        if player.id not in squad.ready_ids:
            squad.ready_ids.append(player.id)
        both = set(squad.ready_ids) >= set(squad.player_ids)
        if both and not squad.started_at:
            squad.started_at = time.time()
            thread = _pair_thread(session, squad)
            if thread is None:
                session.threads.append(
                    Thread(owner_id=squad.id, messages=[], files=dict(challenge.files))
                )
            elif not thread.files:
                thread.files = dict(challenge.files)
        _persist(session)
    await _broadcast(session)
    return session


def _seat_partner(session: Session, player: Player) -> str | None:
    """Pair this person with a similar waiter. Returns the squad id once both phones share an animal."""
    waiting = _pick_waiter(session, player)
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
    """A person can walk away during the lobby or the round. A pair's finished card stays on the board."""
    async with store.lock:
        session = _must(code)
        player = _player(session, player_id, player_token)
        if session.mode == "collaborate":
            squad = next((item for item in session.squads if player.id in item.player_ids), None)
            if squad is None or not squad.scored:
                _release_partner(session, player.id)
        session.players = [p for p in session.players if p.id != player.id]
        _persist(session)
    await _broadcast(session)
    return session


async def start(code: str, admin_token: str) -> Session:
    async with store.lock:
        session = _must(code)
        _check_admin(session, admin_token)
        if session.status == "ended":
            raise GameError(409, "This game has ended. Ask the table for a new QR code.")
        connected = _present(session)
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


async def next_group(code: str, admin_token: str) -> Session:
    """Clear players, squads, threads, and the reef, but keep the same code and QR.

    The stage screen and the QR code on the table keep working, so the host
    can wave the next people over without reopening anything.
    """
    async with store.lock:
        session = _must(code)
        _check_admin(session, admin_token)
        _clear_round(session, keep_players=False)
        session.status = "lobby"
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
            # Same people, new challenge: start the next round from a clean reef.
            _clear_round(session, keep_players=True)
            session.status = "lobby"
        _persist(session)
    await _broadcast(session)
    return session


async def hello(code: str, player_id: str, player_token: str) -> bool:
    """A phone's socket says who it is. Marks the player present. False if the token is wrong."""
    async with store.lock:
        session = store.get(code)
        if session is None:
            return False
        try:
            player = _player(session, player_id, player_token)
        except GameError:
            return False
        if player.connected:
            return True
        player.connected = True
        player.left_at = 0
        _persist(session)
    await _broadcast(session)
    return True


async def gone(code: str, player_id: str) -> None:
    """The last socket for this player closed. The id was checked by hello()."""
    async with store.lock:
        session = store.get(code)
        if session is None:
            return
        player = next((item for item in session.players if item.id == player_id), None)
        if player is None or not player.connected:
            return
        player.connected = False
        player.left_at = time.time()
        _persist(session)
    await _broadcast(session)


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
        # Drafts change on every keystroke. Phones get them over the socket;
        # the save file doesn't need them, so this skips the disk write.
        session.revision += 1
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

    clock_closed = False
    async with store.lock:
        session = _must(code)
        player = _player(session, player_id, player_token)
        if session.status == "ended":
            raise GameError(409, "This game has ended. Ask the table for a new QR code.")
        if session.mode == "collaborate" and player.id != REHEARSAL_PLAYER_ID:
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
        limit = thread.turn_limit if thread and thread.turn_limit else max(1, len(challenge.beats))
        # Pieces are dealt only to a real pair. The rehearsal squad has one seat.
        mode = "collaborate" if session.mode == "collaborate" and squad and len(squad.player_ids) >= 2 else "compete"
        editing = bool(challenge.files)
        pair_round = editing and session.mode == "collaborate" and player.id != REHEARSAL_PLAYER_ID
        if pair_round:
            if squad is None or not squad.started_at:
                raise GameError(409, "Both of you tap Start once you've found each other.")
            if _clock_up(squad):
                _expire_squad(session, squad, challenge)
                _persist(session)
                clock_closed = True
        elif step >= limit:
            raise GameError(409, "This thread is closed. Ask the host for the next challenge.")
        history = list(thread.messages) if thread else []
        beat = challenge.beats[min(step, len(challenge.beats) - 1)]
        challenge_id = challenge.id
        workspace = dict(thread.files) if thread and thread.files else dict(challenge.files)
        solutions = dict(challenge.solutions)
        jobs = _job_map(challenge)
        check = challenge.check

    if clock_closed:
        await _broadcast(session)
        raise GameError(409, "The 2 minutes are up.")

    work_started = time.monotonic()

    # Collaborate mode also grades each partner's piece (grading.beat_for).
    beat = beat_for(beat, mode)
    # Layers 1 and 2 (the rules) grade the message on their own. They need no
    # key and always give the same answer for the same message.
    earlier = [{"role": message.role, "content": message.content} for message in history]
    earlier_user = [message.content for message in history if message.role == "user"]
    graded = grade_prompt(text, beat, earlier_user)
    # Credentials never reach Grok, the thread, or anyone else's screen.
    model_text = redact(text, beat)
    messages = [*earlier, {"role": "user", "content": model_text}]

    worked = False
    if editing:
        # Build rounds edit the pair's files. One coding call, no web search, no second grader.
        if use_model:
            workspace, answer, simulated, _trace = await grok.edit_project(workspace, model_text, solutions, jobs)
        else:
            workspace, answer = apply_named(workspace, model_text, solutions, jobs)
            simulated = True
        worked = project_passes(workspace, check)
    elif use_model:
        # Layer 3, the reviewer, reads only the prompt and the rules' findings,
        # so it runs at the same time as the solver instead of after it.
        review_task = None
        if not graded.leaked and grok.live():
            review_task = asyncio.create_task(grok.review_prompt(judge.review_packet(model_text, beat, graded)))
        try:
            answer, simulated, _request, trace = await grok.complete(messages, beat.simulated_reply)
        except BaseException:
            if review_task is not None:
                review_task.cancel()
            raise
        review = await review_task if review_task is not None else None
        if not simulated:
            # Layer 4: real usage from the solver call, web searches, asking back.
            history_tokens = count_tokens("\n".join(message.content for message in history))
            judge.apply_measured(graded, answer, trace, history_tokens=history_tokens)
            # Layer 3: the reviewer can only add cost, and its rewrite must pass our rules.
            judge.apply_review(graded, review, beat, earlier_user)
    else:
        answer, simulated = beat.simulated_reply, True
    if pair_round:
        paused = time.monotonic() - work_started
    else:
        paused = 0
    if not editing and step > 0 and not simulated and graded.searches == 0:
        # A follow-up the model answered without searching isn't billed for lookups it didn't do.
        waive_unused_lookups(graded)
    vague_saving = judge.saved_vs_vague(graded, beat) if graded.reasonable else 0
    judge.log_judgment(
        "game",
        text,
        graded,
        beat=beat,
        challenge_id=challenge_id,
        turn=step + 1,
        mode="full" if use_model and not simulated else "fast",
    )

    grade = graded.grade
    score = graded.score
    looked_up = graded.lookup_tokens
    grams = graded.grams
    excess_kg = graded.excess_kg
    summary = turn_summary(graded, turn=step + 1, turn_count=limit)
    delta = reef_delta(grade)
    kind = event_type(grade)
    server_side_tools = graded.searches

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
            thread = Thread(owner_id=owner_id, messages=[], turn_limit=limit)
            session.threads.append(thread)
        elif not thread.turn_limit:
            thread.turn_limit = limit
        if thread.done or thread.step != step:
            raise GameError(409, "The host moved on. Take a look at the new challenge.")
        if editing:
            thread.files = dict(workspace)
        if pair_round and squad and squad.started_at and paused > 0:
            squad.started_at += paused
        finishing = bool(pair_round and squad and (worked or _clock_up(squad)))
        if finishing and worked:
            answer = answer.rstrip() + " Both functions are in. The team score is on the board."
        elif finishing:
            answer = answer.rstrip() + " The 2 minutes are up. The team score is on the board."
        thread.messages.append(ChatMessage(role="user", content=model_text))
        thread.messages.append(ChatMessage(role="assistant", content=answer))
        thread.step += 1
        thread.score_sum += score
        thread.turns_graded += 1
        averaged = round(thread.score_sum / thread.turns_graded)
        session.reef_health = clamp_health(session.reef_health + delta)
        if pair_round and squad:
            squad.prompt = ""
            squad.prompt_author_id = player.id
            squad.prompt_updated_at = time.time()
            actor = squad.name
            squad_id = squad.id
            if finishing:
                _publish_pair(session, squad, grade)
        elif session.mode == "collaborate" and squad:
            thread.done = thread.step >= thread.turn_limit
            squad.score = averaged
            squad.last_grade = grade_for_score(averaged)
            squad.prompt = ""
            squad.prompt_author_id = player.id
            squad.prompt_updated_at = time.time()
            for member in session.players:
                if member.id in squad.player_ids:
                    member.score = averaged
                    member.last_grade = grade_for_score(averaged)
            actor = squad.name
            squad_id = squad.id
            if thread.done:
                squad.scored = True
                squad.member_names = [person.name for person in session.players if person.id in squad.player_ids]
                _mint_card(session, thread, squad, player)
        else:
            thread.done = thread.step >= thread.turn_limit
            player.score = averaged
            player.last_grade = grade_for_score(averaged)
            actor = player.name
            squad_id = None
            if thread.done:
                _mint_card(session, thread, None, player)
                _maybe_finish_compete(session)

        submission = Submission(
            id=_id("sub"),
            player_id=player.id,
            squad_id=squad_id,
            actor=actor,
            prompt=model_text,
            token_count=graded.prompt_tokens,
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
            turn_count=thread.turn_limit,
            reasonable=graded.reasonable,
            verdict_reason=graded.reviewer_reason,
            judged_by_model=graded.judged_by_model,
            server_side_tools=server_side_tools,
            effective_tokens=graded.effective_tokens,
            leaked=graded.leaked,
            receipt=graded.receipt(),
            flags=list(graded.flags),
            reviewer_verdict=graded.reviewer_verdict,
            better_prompt=graded.better_prompt,
            better_saves=graded.better_saves,
            saved_vs_vague=vague_saving,
            measured_tokens=graded.measured_tokens,
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
    if use_model and not simulated and graded.better_prompt and graded.measured_tokens and judge.allow_full():
        await _schedule(_measure_better(session.code, submission.id, graded, earlier))
    return session, submission


async def _schedule(coro) -> None:
    """Run slow follow-up work after the player already has their grade."""
    if RUN_BACKGROUND_INLINE:
        await coro
        return
    task = asyncio.create_task(coro)
    _background.add(task)
    task.add_done_callback(_background.discard)


async def _measure_better(code: str, submission_id: str, graded, history: list[dict]) -> None:
    """Layer 4, part 2: run the checked better prompt for real and put the saving on the receipt."""
    try:
        measured = await judge.measure_better(graded, history)
    except Exception:  # noqa: BLE001 - a failed extra run must never break the game
        return
    if not measured:
        return
    async with store.lock:
        session = store.get(code)
        if session is None:
            return
        submission = next((item for item in session.submissions if item.id == submission_id), None)
        if submission is None:
            return
        submission.better_measured_tokens = graded.better_measured_tokens
        submission.measured_saved = graded.measured_saved
        submission.receipt = graded.receipt()
        _persist(session)
    await _broadcast(session)


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
    """Send a sample prompt as the Rehearsal player, for the thread's current turn.

    efficient: the adequate sample for every remaining turn (should be A+).
    bloated: everything seen so far pasted in, for the current turn only (C or D).
    vague: the vague sample for the current turn only (F).
    """
    if kind not in REHEARSAL_KINDS:
        raise GameError(400, "Rehearse efficient, bloated, or vague.")
    async with store.lock:
        session = _must(code)
        _check_admin(session, admin_token)
        challenge = get_challenge(session.challenge_id)
        if challenge is None:
            raise GameError(500, "This game's challenge is missing.")
        if session.status == "lobby":
            connected = [p for p in _roster(session) if p.connected]
            if session.mode == "collaborate" and connected and not any(len(squad.player_ids) == 2 for squad in session.squads):
                _form_squads(session, connected)
            session.status = "playing"
        if session.status != "playing":
            raise GameError(409, "Start a new round before rehearsing.")
        player = next((p for p in session.players if p.id == REHEARSAL_PLAYER_ID), None)
        if player is None:
            player = Player(
                id=REHEARSAL_PLAYER_ID,
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
                    id=REHEARSAL_SQUAD_ID,
                    name="Rehearsal Reef",
                    player_ids=[player.id],
                    icebreaker="This squad exists so you can test the reef without a phone.",
                    shared="Rehearsal is checking the reef.",
                    distinct="No partner is at the table.",
                )
                player.squad_id = squad.id
                session.squads.append(squad)
        # Let the host press the rehearsal buttons as often as they like:
        # a finished rehearsal thread starts over instead of refusing.
        owner_id = player.squad_id if session.mode == "collaborate" and player.squad_id else player.id
        thread = next((item for item in session.threads if item.owner_id == owner_id), None)
        if thread is not None and thread.done:
            session.threads = [item for item in session.threads if item is not thread]
            thread = None
        step = thread.step if thread else 0
        if kind == "efficient":
            prompts = tuple(challenge.example_efficient[step:])
        elif kind == "bloated":
            prompts = (challenge.example_whole_file(step),)
        else:
            prompts = (challenge.example_vague[step],) if step < len(challenge.example_vague) else ()
        # Sample lines only cover the written beats. A small table may still
        # have turns left, so an empty script starts the rehearsal over.
        if not prompts:
            if thread is not None:
                session.threads = [item for item in session.threads if item is not thread]
            step = 0
            if kind == "efficient":
                prompts = tuple(challenge.example_efficient)
            elif kind == "bloated":
                prompts = (challenge.example_whole_file(0),)
            else:
                prompts = (challenge.example_vague[0],)
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
