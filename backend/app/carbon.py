from __future__ import annotations

import math

# Educational booth model, not a full lifecycle assessment.
# The bill is every token the model has to handle for one turn: the message
# itself, plus a web lookup for each fact the message left out.
# ~0.3 Wh per 1,000 tokens, times 390 g CO2 per kWh.
ENERGY_KWH_PER_1K_TOKENS = 0.0003
CARBON_G_PER_KWH = 390
MILLION_QUERIES = 1_000_000
# One web lookup: the search call plus the pages the model reads back.
WEB_LOOKUP_TOKENS = 1200
# A message with no ask makes the model guess what you want, or ask back.
ASK_TOKENS = 250
# A message that asks for far more output than it needs ("rewrite the whole file",
# "explain everything") makes the model write more. Output tokens cost the most.
OUTPUT_TOKENS = 300
# Every turn is graded against this many tokens.
BUDGET_TOKENS = 200

FORMULA = {
    "energyKwhPer1kTokens": ENERGY_KWH_PER_1K_TOKENS,
    "carbonGramsPerKwh": CARBON_G_PER_KWH,
    "scaleQueries": MILLION_QUERIES,
    "webLookupTokens": WEB_LOOKUP_TOKENS,
    "tokenizer": "cl100k_base (tiktoken), with a 4-characters-per-token fallback",
    "budgetTokens": BUDGET_TOKENS,
    "askTokens": ASK_TOKENS,
    "outputTokens": OUTPUT_TOKENS,
    "note": (
        "Each fact the message leaves out is charged as one web lookup (about 1,200 tokens). "
        "The message's own tokens count too, so pasting a whole file is not free. "
        "The grade compares that total with the budget."
    ),
}

GRADES = ("A+", "A", "B", "C", "D", "F")
# The word the judge shows next to each grade.
VERDICT_WORDS = {"A+": "efficient", "A": "efficient", "B": "okay", "C": "okay", "D": "wasteful", "F": "horrible"}

# A thin prompt is a web lookup (about 1,200 tokens) and wilts the reef by a step.
# It does not skip a whole health band. A prompt that includes the source heals a little.
REEF_DELTAS = {"A+": 4, "A": 2, "B": 0, "C": -3, "D": -5, "F": -8}
EVENT_TYPES = {
    "A+": "turtle",
    "A": "bloom",
    "B": "fish",
    "C": "murk",
    "D": "murk",
    "F": "sludge",
}

_encoder = None
# tiktoken downloads its table on first use. If that fails (no internet at the
# booth), remember it, so every prompt doesn't wait on another download attempt.
_encoder_failed = False


def count_tokens(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    global _encoder, _encoder_failed
    if _encoder is None and not _encoder_failed:
        try:
            import tiktoken

            _encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _encoder_failed = True
    if _encoder is not None:
        try:
            return len(_encoder.encode(stripped))
        except Exception:
            pass
    return max(1, math.ceil(len(stripped) / 4))


# Grade bands, as multiples of the budget. With the 200-token budget:
# A+ up to 200, A up to 400, B up to 800, C up to 1,400, D up to 2,200, F above.
# One missing fact (a 1,200-token lookup) lands in C. Two missing facts land in F.
GRADE_BANDS = (("A+", 1.0), ("A", 2.0), ("B", 4.0), ("C", 7.0), ("D", 11.0))


def grade_for(tokens: int, target: int) -> str:
    """Grade the tokens the model handled for one turn against the budget."""
    if tokens <= 0:
        return "A+"
    ratio = tokens / max(target, 1)
    for grade, limit in GRADE_BANDS:
        if ratio <= limit:
            return grade
    return "F"


def score_for(tokens: int, target: int) -> int:
    """0 to 100. 100 means the turn stayed inside the budget."""
    if tokens <= 0:
        return 100
    return max(0, min(100, round(100 * min(1.0, target / tokens) ** 0.75)))


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


def clamp_health(health: int) -> int:
    return max(0, min(100, health))
