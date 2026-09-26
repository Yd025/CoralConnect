from __future__ import annotations

from .carbon import reef_band
from .challenges import get_challenge, public_challenge
from .models import Player, ReefEvent, Session, Squad, Submission, Thread, player_bounds


def public_player(player: Player) -> dict:
    return {
        "id": player.id,
        "name": player.name,
        "language": player.language,
        "lane": player.lane,
        "focus": player.focus,
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
        "kind": squad.kind,
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
    }


def public_thread(thread: Thread) -> dict:
    return {
        "ownerId": thread.owner_id,
        "step": thread.step,
        "done": thread.done,
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
        "players": [public_player(p) for p in session.players],
        "squads": [public_squad(s, session.players) for s in session.squads],
        "submissions": [public_submission(s) for s in session.submissions],
        "events": [public_event(e) for e in session.events],
        "threads": [public_thread(thread) for thread in session.threads],
        "createdAt": session.created_at,
        "revision": session.revision,
    }
