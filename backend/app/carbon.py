from __future__ import annotations

import math

# Educational booth model, not a full lifecycle assessment.
# The bill that hits the reef is extra model work: a web lookup the model
# runs when the prompt never included the fact it needed.
# ~0.3 Wh per 1,000 of those lookup tokens, times 390 g CO2 per kWh.
ENERGY_KWH_PER_1K_TOKENS = 0.0003
CARBON_G_PER_KWH = 390
MILLION_QUERIES = 1_000_000
WEB_LOOKUP_TOKENS = 1200

FORMULA = {
    "energyKwhPer1kTokens": ENERGY_KWH_PER_1K_TOKENS,
    "carbonGramsPerKwh": CARBON_G_PER_KWH,
    "scaleQueries": MILLION_QUERIES,
    "webLookupTokens": WEB_LOOKUP_TOKENS,
    "tokenizer": "cl100k_base (tiktoken), with a 4-characters-per-token fallback",
    "note": (
        "The grade is the lookup the model has to do when the prompt leaves out "
        "the source. Giving the model that source costs no lookup."
    ),
}

GRADES = ("A+", "A", "B", "C", "D", "F")

# Keep these thresholds in sync with frontend/lib/reef.ts
REEF_DELTAS = {"A+": 4, "A": 2, "B": 0, "C": -8, "D": -16, "F": -28}
EVENT_TYPES = {
    "A+": "turtle",
    "A": "bloom",
    "B": "fish",
    "C": "murk",
    "D": "murk",
    "F": "sludge",
}

_encoder = None


def count_tokens(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    global _encoder
    try:
        if _encoder is None:
            import tiktoken

            _encoder = tiktoken.get_encoding("cl100k_base")
        return len(_encoder.encode(stripped))
    except Exception:
        return max(1, math.ceil(len(stripped) / 4))


def grade_for(tokens: int, target: int) -> str:
    if tokens <= 0:
        return "A+"
    ratio = tokens / max(target, 1)
    if ratio <= 0.6:
        return "A+"
    if ratio <= 1.0:
        return "A"
    if ratio <= 1.6:
        return "B"
    if ratio <= 2.5:
        return "C"
    if ratio <= 4.0:
        return "D"
    return "F"


def score_for(tokens: int, target: int) -> int:
    if tokens <= 0:
        return 150
    return max(0, min(150, round(100 * target / tokens)))


def reef_delta(grade: str) -> int:
    return REEF_DELTAS[grade]


def event_type(grade: str) -> str:
    return EVENT_TYPES[grade]


def reef_band(health: int) -> str:
    if health >= 75:
        return "thriving"
    if health >= 50:
        return "stressed"
    if health >= 25:
        return "bleaching"
    return "dead"


def carbon_grams(tokens: int) -> float:
    kwh = (tokens / 1000) * ENERGY_KWH_PER_1K_TOKENS
    return kwh * CARBON_G_PER_KWH


def excess_kg_at_scale(tokens: int, target: int) -> float:
    excess = max(0, tokens - target)
    grams = carbon_grams(excess)
    return grams * MILLION_QUERIES / 1000


def lookup_cost(prompt: str, anchors: tuple[str, ...]) -> int:
    folded = prompt.lower()
    if any(anchor.lower() in folded for anchor in anchors):
        return 0
    return WEB_LOOKUP_TOKENS


def explain(lookup_tokens: int, grams: float, excess_kg: float, *, turn: int, turn_count: int) -> str:
    where = f"Turn {turn} of {turn_count}. "
    if lookup_tokens <= 0:
        return where + "The prompt had the source, so the model did no web lookup. The reef gets a little life back."
    return (
        where
        + f"The prompt left the source out, so the model spent about {lookup_tokens} tokens looking it up on the web. "
        + f"About {grams:.3f} g CO2e. "
        + f"Sent a million times, that search is about {excess_kg:.1f} kg CO2e."
    )


def clamp_health(health: int) -> int:
    return max(0, min(100, health))
