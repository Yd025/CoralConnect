from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from typing import Any


def _take(cls, data: dict[str, Any]):
    allowed = {f.name for f in fields(cls)}
    return cls(**{key: value for key, value in data.items() if key in allowed})


@dataclass
class Player:
    id: str
    token: str
    name: str
    language: str
    squad_id: str | None = None
    score: int = 0
    last_grade: str | None = None
    connected: bool = True
    joined_at: float = 0


@dataclass
class Squad:
    id: str
    name: str
    player_ids: list[str]
    icebreaker: str
    prompt: str = ""
    prompt_author_id: str | None = None
    prompt_updated_at: float = 0
    score: int = 0
    last_grade: str | None = None


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class Thread:
    owner_id: str
    messages: list[ChatMessage]
    step: int = 0
    done: bool = False
    score_sum: int = 0
    turns_graded: int = 0


@dataclass
class Submission:
    id: str
    player_id: str
    squad_id: str | None
    actor: str
    prompt: str
    token_count: int
    target_tokens: int
    carbon_grams: float
    excess_kg_at_scale: float
    grade: str
    score: int
    reef_delta: int
    reef_health: int
    ai_response: str
    simulated: bool
    summary: str
    event_type: str
    created_at: float
    turn_index: int = 0
    turn_count: int = 1
    lookup_tokens: int = 0
    reasonable: bool = True
    verdict_reason: str = ""
    judged_by_model: bool = False
    server_side_tools: int = 0


@dataclass
class ReefEvent:
    id: str
    type: str
    title: str
    subtitle: str
    grade: str
    actor: str
    image_url: str | None
    created_at: float


@dataclass
class Session:
    code: str
    admin_token: str
    mode: str
    status: str
    challenge_id: str
    reef_health: int
    players: list[Player]
    squads: list[Squad]
    submissions: list[Submission]
    events: list[ReefEvent]
    created_at: float
    threads: list[Thread] = field(default_factory=list)
    revision: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> Session:
        payload = dict(data)
        payload["players"] = [_take(Player, p) for p in data.get("players", [])]
        payload["squads"] = [_take(Squad, s) for s in data.get("squads", [])]
        payload["submissions"] = [_take(Submission, s) for s in data.get("submissions", [])]
        payload["events"] = [_take(ReefEvent, e) for e in data.get("events", [])]
        threads = []
        for item in data.get("threads") or []:
            raw = dict(item)
            raw["messages"] = [_take(ChatMessage, message) for message in raw.get("messages") or []]
            threads.append(_take(Thread, raw))
        payload["threads"] = threads
        return _take(Session, payload)
