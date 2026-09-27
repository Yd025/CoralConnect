from __future__ import annotations

from .carbon import VERDICT_WORDS, reef_band
from .challenges import get_challenge, public_challenge
from .models import Player, ReefEvent, Session, Squad, Submission, Thread, player_bounds, turns_for_table


def _piece(session: Session, player: Player, challenge) -> dict | None:
    if session.mode != "collaborate" or not player.squad_id or challenge is None:
        return None
    squad = next((item for item in session.squads if item.id == player.squad_id), None)
    if squad is None or player.id not in squad.player_ids:
        return None
    thread = next((item for item in session.threads if item.owner_id == squad.id), None)
    if thread and thread.done:
        return None
    step = thread.step if thread else 0
    beat = challenge.beats[min(step, len(challenge.beats) - 1)]
    if len(beat.parts) < 2:
        return None
    seat = squad.player_ids.index(player.id)
    part = beat.parts[seat % len(beat.parts)]
    return {"role": part.role, "title": part.title, "body": part.body}


def public_player(player: Player, session: Session, challenge) -> dict:
    return {
        "id": player.id,
        "name": player.name,
        "language": player.language,
        "builds": player.builds,
        "cares": player.cares,
        "piece": _piece(session, player, challenge),
        "squadId": player.squad_id,
        "score": player.score,
        "lastGrade": player.last_grade,
        "connected": player.connected,
        "joinedAt": player.joined_at,
    }


def public_squad(squad: Squad, players: list[Player]) -> dict:
    names = {p.id: p.name for p in players}
    return {
        "id": squad.id,
        "name": squad.name,
        "playerIds": squad.player_ids,
        "memberNames": [names.get(pid, "Someone") for pid in squad.player_ids],
        "shared": squad.shared,
        "distinct": squad.distinct,
        "creature": squad.creature,
        "closing": squad.closing,
        "readyIds": list(squad.ready_ids),
        "startedAt": squad.started_at,
        "scored": squad.scored,
        "icebreaker": squad.icebreaker,
        "prompt": squad.prompt,
        "promptAuthorId": squad.prompt_author_id,
        "promptUpdatedAt": squad.prompt_updated_at,
        "score": squad.score,
        "lastGrade": squad.last_grade,
    }


def public_submission(submission: Submission) -> dict:
    return {
        "id": submission.id,
        "playerId": submission.player_id,
        "squadId": submission.squad_id,
        "actor": submission.actor,
        "prompt": submission.prompt,
        "tokenCount": submission.token_count,
        "targetTokens": submission.target_tokens,
        "lookupTokens": submission.lookup_tokens,
        "carbonGrams": round(submission.carbon_grams, 4),
        "excessKgAtScale": round(submission.excess_kg_at_scale, 2),
        "grade": submission.grade,
        "score": submission.score,
        "reefDelta": submission.reef_delta,
        "reefHealth": submission.reef_health,
        "aiResponse": submission.ai_response,
        "simulated": submission.simulated,
        "summary": submission.summary,
        "eventType": submission.event_type,
        "createdAt": submission.created_at,
        "turnIndex": submission.turn_index,
        "turnCount": submission.turn_count,
        "followUp": submission.turn_index + 1 < submission.turn_count,
        "reasonable": submission.reasonable,
        "verdictReason": submission.verdict_reason,
        "judgedByModel": submission.judged_by_model,
        "serverSideTools": submission.server_side_tools,
        "effectiveTokens": submission.effective_tokens,
        "leaked": submission.leaked,
        "receipt": submission.receipt,
        "verdict": VERDICT_WORDS.get(submission.grade, ""),
        "flags": submission.flags,
        "reviewerVerdict": submission.reviewer_verdict,
        "betterPrompt": submission.better_prompt,
        "betterSaves": submission.better_saves,
        "savedVsVague": submission.saved_vs_vague,
        "measuredTokens": submission.measured_tokens,
        "betterMeasuredTokens": submission.better_measured_tokens,
        "measuredSaved": submission.measured_saved,
    }


def public_thread(thread: Thread) -> dict:
    return {
        "ownerId": thread.owner_id,
        "step": thread.step,
        "done": thread.done,
        "turnLimit": thread.turn_limit,
        "cardId": thread.card_id,
        "files": [{"name": name, "body": body} for name, body in thread.files.items()],
        "messages": [{"role": message.role, "content": message.content} for message in thread.messages],
    }


def public_event(event: ReefEvent) -> dict:
    return {
        "id": event.id,
        "type": event.type,
        "title": event.title,
        "subtitle": event.subtitle,
        "grade": event.grade,
        "actor": event.actor,
        "imageUrl": event.image_url,
        "createdAt": event.created_at,
    }


def public_session(session: Session) -> dict:
    challenge = get_challenge(session.challenge_id)
    return {
        "code": session.code,
        "mode": session.mode,
        "status": session.status,
        "playerMin": player_bounds(session.mode)[0],
        "playerMax": player_bounds(session.mode)[1],
        "challenge": public_challenge(challenge) if challenge else None,
        "reefHealth": session.reef_health,
        "reefBand": reef_band(session.reef_health),
        "players": [public_player(p, session, challenge) for p in session.players],
        "squads": [public_squad(s, session.players) for s in session.squads],
        "submissions": [public_submission(s) for s in session.submissions],
        "events": [public_event(e) for e in session.events],
        "threads": [public_thread(thread) for thread in session.threads],
        "createdAt": session.created_at,
        "revision": session.revision,
        "turnsAllowed": turns_for_table(len([player for player in session.players if player.id != "p_rehearsal"])),
    }
