"""The rules layer of the prompt judge (layers 1 and 2 in docs/PROMPT-JUDGE.md).

Every charge is priced in tokens, so the grade, the grams of CO2, and the reef
all come from one number:

    effective = the message's own tokens
              + 1,200 for each key detail the message left out (one web lookup each)
              + 250 if the message never says what it wants
              + 300 if it asks for far more output than it needs
              + one extra round if the model had to ask back (measured runs only)
    grade     = grade_for(effective, budget)      # see carbon.GRADE_BANDS

Pasting a credential is an automatic F, whatever else the message did.

Two modes:

- Game mode (a Beat is given): the beat's Facts are the answer key. In
  collaborate mode, beat_for adds each partner's piece (see Beat.parts).
- General mode (no Beat: the plugin, or any prompt): we can't know the right
  answer, so we count concrete details (files, functions, errors, numbers, IDs,
  quoted text). None counts as two missing details, one counts as one.

Grok can only add cost on top of these rules, never remove it (see judge.py).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace

from .carbon import (
    ASK_TOKENS,
    BUDGET_TOKENS,
    OUTPUT_TOKENS,
    WEB_LOOKUP_TOKENS,
    carbon_grams,
    count_tokens,
    excess_kg_at_scale,
    grade_for,
    score_for,
)
from .challenges import Beat, Fact

# Words that show the message says what it wants. Base-form verbs, modals, and
# question words. Deliberately broad: a false "no ask" would cost a real player
# 250 tokens, while a false "has an ask" only costs the rubric a little precision.
ASK_WORDS = (
    "fix", "change", "patch", "guard", "should", "instead", "rather", "need", "needs",
    "want", "why", "how", "what", "please", "swap", "reorder", "move", "replace",
    "remove", "stop", "drop", "return", "render", "store", "redact", "strip", "write",
    "add", "skip", "avoid", "never", "don'?t", r"do\s+not", "only", "must", "make",
    "keep", "handle", "check", "rename", "rewrite", "use", "set", "discount", "apply",
    "create", "wrap", "call", "compute", "show", "hide", "mask", "delete", "clear",
    "convert", "turn", "treat", "leave", "allow", "let", "give", "send", "filter",
    "confirm", "verify", "ensure", "double-check",
    "catch", "raise", "throw", "help", "can\\s+you", "could\\s+you",
)
_ASK = re.compile(r"\?|\b(?:" + "|".join(ASK_WORDS) + r")\b", re.IGNORECASE)

# ---------------------------------------------------------------------------
# General-mode signals. Starter patterns from docs/PROMPT-JUDGE.md, Appendix C.
# tests/test_judge.py pins their behavior; tune them there.
# ---------------------------------------------------------------------------

# Concrete details: the things that save the model from searching or guessing.
ANCHORS: dict[str, re.Pattern[str]] = {
    "file": re.compile(
        r"\b[\w./-]+\.(?:py|js|ts|tsx|jsx|sql|json|ya?ml|html|css|go|rs|java|rb|php|sh|md|log|csv|txt|toml)\b",
        re.IGNORECASE,
    ),
    "function": re.compile(r"\b[A-Za-z_]\w*\("),
    "error": re.compile(r"\b\w+(?:Error|Exception)\b"),
    "status": re.compile(r"\b(?:HTTP|status|code|error)\s*[45]\d\d\b", re.IGNORECASE),
    "line": re.compile(r"\bline\s+\d+\b", re.IGNORECASE),
    "number": re.compile(
        r"\d+(?:\.\d+)?\s?(?:%|(?:ms|secs?|seconds?|mins?|minutes?|hours?|hrs?|days?|kWh|kW|mm|MB|GB|°C|°F)\b)",
        re.IGNORECASE,
    ),
    "money": re.compile(r"\$\d[\d,]*(?:\.\d+)?"),
    "id": re.compile(r"\b[A-Z]{1,3}-?\d{1,4}\b"),  # case-sensitive: Z3, V3, R1, INV-104
    "quoted": re.compile(r"\"[^\"\n]{3,}\"|'[^'\n]{3,}'|`[^`\n]+`"),
}

VAGUE = re.compile(
    r"\b(?:do (?:this|it|that) for me|fix (?:it|this|that)|make it work|look into (?:it|this)|"
    r"figure (?:it|this) out|something(?:'s| is) (?:wrong|broken|off)|doesn'?t work|isn'?t working|asap)\b",
    re.IGNORECASE,
)
FILLER = re.compile(
    r"\b(?:hi|hello|hey|hope you(?:'re| are) (?:well|doing well)|thanks?(?: you)?(?: so much)?|"
    r"sorry|i was wondering|could you please kindly)\b",
    re.IGNORECASE,
)
TOO_MUCH_OUTPUT = re.compile(
    r"\b(?:explain (?:everything|in detail|in depth)|step[- ]by[- ]step|(?:full|whole|entire) (?:file|code|program)|"
    r"rewrite (?:the|this|my) (?:whole|entire)|every (?:line|function|case)|as detailed as possible)\b",
    re.IGNORECASE,
)
# Credentials in any form. Beat.forbidden adds round-specific ones on top.
SECRETS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bxai-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\b(?:sk|pk|ghp|gho)[-_][A-Za-z0-9_-]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"bearer\s+(?!(?:<|\[|\{|\(|\*|x{3}|redacted\b))[A-Za-z0-9._~+/=-]{16,}", re.IGNORECASE),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
BULK_LINES = 15

GENERAL_MISSING = (
    "The exact thing: a file, function, error message, or value",
    "Where or what you expected: a line, ID, number, or quoted output",
)


def _flat(text: str) -> str:
    """One line, single spaces, so patterns can span what the player typed on two lines."""
    return " ".join(text.split())


def fact_covered(fact: Fact, text: str) -> bool:
    flat = _flat(text)
    return all(any(re.search(pattern, flat, re.IGNORECASE) for pattern in group) for group in fact.needs)


def _anchor_pattern(anchor: str) -> str:
    """A part anchor as a regex: any case, and any space, hyphen, underscore, or # between words."""
    body = r"[\s#_-]*".join(re.escape(word) for word in anchor.split())
    if re.match(r"\w", anchor):
        body = r"(?<!\w)" + body
    if re.search(r"\d$", anchor):
        body += r"(?!\d)"
    return body


def beat_for(beat: Beat, mode: str) -> Beat:
    """The beat as it is graded in this mode.

    Collaborate mode deals each person in a pair a different piece of the turn
    (Beat.parts), and the shared message has to carry every piece. It is graded
    on the beat's facts plus each part anchor those facts don't already cover,
    so one detail is never charged twice. Compete mode, and beats without
    parts, are graded as written.
    """
    if mode != "collaborate" or len(beat.parts) < 2:
        return beat
    extra: list[Fact] = []
    for index, part in enumerate(beat.parts, start=1):
        anchor = " ".join(part.anchor.split())
        if not anchor or any(fact_covered(fact, anchor) for fact in beat.facts):
            continue
        extra.append(Fact(f"part-{index}", f'The piece titled "{part.title}": {anchor}', ((_anchor_pattern(anchor),),)))
    return replace(beat, facts=(*beat.facts, *extra)) if extra else beat


def has_ask(text: str) -> bool:
    return bool(_ASK.search(text))


def _forbidden(beat: Beat | None) -> list[re.Pattern[str]]:
    extra = [re.compile(pattern, re.IGNORECASE) for pattern in (beat.forbidden if beat else ())]
    return [*SECRETS, *extra]


def leaks(text: str, beat: Beat | None = None) -> bool:
    flat = _flat(text)
    return any(pattern.search(flat) or pattern.search(text) for pattern in _forbidden(beat))


def redact(text: str, beat: Beat | None = None) -> str:
    """Replace credentials with [redacted] before the text goes to Grok, a log, or other players."""
    cleaned = text
    for pattern in _forbidden(beat):
        cleaned = pattern.sub("[redacted]", cleaned)
    return cleaned


def anchors_in(text: str) -> list[str]:
    """Distinct concrete details in the message, in the order they appear."""
    found: dict[str, int] = {}
    for pattern in ANCHORS.values():
        for match in pattern.finditer(text):
            value = match.group(0).strip()
            key = value.lower()
            if key and key not in found:
                found[key] = match.start()
    ordered = sorted(found.items(), key=lambda item: item[1])
    return [text[start : start + len(key)] for key, start in ordered]


def short_label(label: str) -> str:
    """'Where it breaks: total() calls apply_coupon' -> 'where it breaks'."""
    head = label.split(":", 1)[0].strip()
    return head[:1].lower() + head[1:]


def _history_lines(history: list[str]) -> set[str]:
    lines: set[str] = set()
    for message in history:
        for line in message.splitlines():
            cleaned = line.strip()
            if len(cleaned) >= 20:
                lines.add(cleaned)
    return lines


def general_flags(text: str, history: list[str] | None = None) -> list[str]:
    """Things worth telling the player that don't change the grade on their own."""
    flags: list[str] = []
    vague = VAGUE.search(text)
    if vague:
        flags.append(f'Vague phrase: "{vague.group(0)}". Say exactly what is wrong and where.')
    if FILLER.search(text):
        flags.append("Greetings and thanks cost tokens too. Skip them.")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) > BULK_LINES:
        flags.append(f"Pasted {len(lines)} lines. Quote only the lines that matter.")
    repeats = len(lines) - len(set(lines))
    if repeats >= 3:
        flags.append("The same lines appear more than once.")
    if history:
        resent = [line for line in lines if len(line) >= 20 and line in _history_lines(history)]
        if len(resent) >= 3:
            flags.append("Re-sent text from an earlier turn. The model already has it.")
    return flags


@dataclass
class Line:
    """One row of the receipt: what the message carried, and what it cost."""

    tone: str  # "info" | "good" | "cost" | "bad"
    text: str
    tokens: int = 0
    # A version without the answer key, for players who haven't sent yet.
    hint: str = ""

    def public(self, reveal: bool = True) -> dict:
        text = self.text if reveal or not self.hint else self.hint
        return {"tone": self.tone, "text": text, "tokens": self.tokens}


@dataclass
class TurnGrade:
    prompt_tokens: int
    target_tokens: int
    covered: list[str]
    missing: list[str]
    ask_missing: bool
    leaked: bool
    mode: str = "game"
    missing_hints: list[str] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)
    lookup_tokens: int = 0
    ask_tokens: int = 0
    output_tokens: int = 0
    extra_round_tokens: int = 0
    searches: int = 0
    judged_by_model: bool = False
    reviewer_verdict: str = ""
    reviewer_reason: str = ""
    reviewer_missing: list[str] = field(default_factory=list)
    better_prompt: str = ""
    better_effective: int = 0
    measured_tokens: int = 0
    measured_detail: dict = field(default_factory=dict)
    better_measured_tokens: int = 0

    @property
    def effective_tokens(self) -> int:
        return self.prompt_tokens + self.lookup_tokens + self.ask_tokens + self.output_tokens + self.extra_round_tokens

    @property
    def grade(self) -> str:
        if self.leaked:
            return "F"
        return grade_for(self.effective_tokens, self.target_tokens)

    @property
    def score(self) -> int:
        if self.leaked:
            return 0
        return score_for(self.effective_tokens, self.target_tokens)

    @property
    def reasonable(self) -> bool:
        """B or better: the model could answer from the message without much extra work."""
        return self.grade in ("A+", "A", "B")

    @property
    def grams(self) -> float:
        return carbon_grams(self.effective_tokens)

    @property
    def excess_kg(self) -> float:
        return excess_kg_at_scale(self.effective_tokens, self.target_tokens)

    @property
    def better_saves(self) -> int:
        """Estimated tokens the checked better prompt saves over this one."""
        if not self.better_prompt:
            return 0
        return max(0, self.effective_tokens - self.better_effective)

    @property
    def measured_saved(self) -> int:
        """Real tokens saved, when both prompts were run through Grok."""
        if not self.measured_tokens or not self.better_measured_tokens:
            return 0
        return max(0, self.measured_tokens - self.better_measured_tokens)

    def receipt(self, reveal: bool = True) -> list[dict]:
        return [line.public(reveal) for line in self.lines]


def grade_prompt(text: str, beat: Beat | None = None, history: list[str] | None = None) -> TurnGrade:
    """Layers 1 and 2. Runs with or without a Grok key, and always gives the same answer."""
    tokens = count_tokens(text)
    ask_missing = not has_ask(text)
    leaked = leaks(text, beat)
    target = beat.target_tokens if beat else BUDGET_TOKENS

    if beat is not None:
        covered_facts = [fact for fact in beat.facts if fact_covered(fact, text)]
        missing_facts = [fact for fact in beat.facts if fact not in covered_facts]
        result = TurnGrade(
            prompt_tokens=tokens,
            target_tokens=target,
            covered=[fact.label for fact in covered_facts],
            missing=[fact.label for fact in missing_facts],
            missing_hints=[short_label(fact.label) for fact in missing_facts],
            ask_missing=ask_missing,
            leaked=leaked,
            mode="game",
        )
    else:
        found = anchors_in(text)
        count = min(len(found), len(GENERAL_MISSING))
        missing = list(GENERAL_MISSING[count:]) if count < 2 else []
        result = TurnGrade(
            prompt_tokens=tokens,
            target_tokens=target,
            covered=found,
            missing=missing,
            missing_hints=list(missing),
            ask_missing=ask_missing,
            leaked=leaked,
            mode="general",
        )

    over = " That is over budget, so the model reads a lot it does not need." if tokens > 2 * target else ""
    result.lines.append(Line("info", f"Your message: {tokens:,} tokens (budget {target}).{over}", tokens))
    if result.mode == "game":
        for label in result.covered:
            result.lines.append(Line("good", f"Included. {label}", hint=f"Included: {short_label(label)}"))
    elif result.covered:
        shown = ", ".join(result.covered[:5]) + (" ..." if len(result.covered) > 5 else "")
        result.lines.append(Line("good", f"Specific details: {shown}"))
    for label, hint in zip(result.missing, result.missing_hints):
        result.lookup_tokens += WEB_LOOKUP_TOKENS
        result.lines.append(
            Line(
                "cost",
                f"Left out, so the model looks it up. {label}",
                WEB_LOOKUP_TOKENS,
                hint=f"Missing, so the model would look it up: {hint}",
            )
        )
    if ask_missing:
        result.ask_tokens = ASK_TOKENS
        result.lines.append(Line("cost", "No ask. The model has to guess what you want, or ask back.", ASK_TOKENS))
    if TOO_MUCH_OUTPUT.search(text):
        result.output_tokens = OUTPUT_TOKENS
        result.lines.append(
            Line("cost", "Asks for more output than it needs. Ask for only the changed lines.", OUTPUT_TOKENS)
        )
    if leaked:
        result.lines.append(
            Line("bad", "You pasted a credential. That is an automatic F. Describe the header and leave the value out.")
        )
    result.flags = general_flags(text, history)
    for flag in result.flags[:3]:
        result.lines.append(Line("info", f"Tip: {flag}"))
    return result


def add_live_call(result: TurnGrade, *, searches: int, verdict: dict | None) -> TurnGrade:
    """Fold in what the real Grok calls saw. This can only add cost.

    verdict is the reviewer's normalized answer: {"reasonable", "reason"} plus,
    from the structured reviewer, "verdict", "missing", and "better_prompt".
    """
    result.searches = max(0, int(searches or 0))
    measured = result.searches * WEB_LOOKUP_TOKENS
    if measured > result.lookup_tokens:
        extra = measured - result.lookup_tokens
        plural = "" if result.searches == 1 else "s"
        result.lookup_tokens = measured
        result.lines.append(Line("cost", f"Grok's solver call searched the web {result.searches} time{plural}.", extra))
    if verdict is None:
        return result
    result.judged_by_model = True
    result.reviewer_reason = str(verdict.get("reason") or "")
    result.reviewer_verdict = str(verdict.get("verdict") or "")
    result.reviewer_missing = [str(item) for item in verdict.get("missing") or [] if str(item).strip()][:5]
    thinks_reasonable = bool(verdict.get("reasonable"))
    if not thinks_reasonable and result.lookup_tokens == 0 and not result.leaked:
        result.lookup_tokens = WEB_LOOKUP_TOKENS
        result.lines.append(
            Line("cost", f"Grok's reviewer says something is still missing. {result.reviewer_reason}".strip(), WEB_LOOKUP_TOKENS)
        )
    elif result.reviewer_reason:
        result.lines.append(Line("info", f"Grok's reviewer: {result.reviewer_reason}"))
    return result


def waive_unused_lookups(result: TurnGrade) -> TurnGrade:
    """A follow-up the model answered without searching is not billed for lookups it did not do."""
    if result.searches or result.leaked or result.lookup_tokens <= 0:
        return result
    result.lookup_tokens = 0
    result.lines = [line for line in result.lines if not (line.tone == "cost" and "look" in line.text.lower())]
    if result.missing:
        result.lines.append(Line("info", "This message left some details out, and the model still answered without searching."))
    return result


def add_asked_back(result: TurnGrade, tokens: int) -> TurnGrade:
    """Grok answered with a question, so the conversation needs one more round."""
    if tokens <= 0 or result.extra_round_tokens:
        return result
    result.extra_round_tokens = tokens
    result.lines.append(
        Line("cost", "Grok had to ask for more before it could help, so the chat runs one more round.", tokens)
    )
    return result


def check_rewrite(
    result: TurnGrade,
    better: str,
    beat: Beat | None = None,
    history: list[str] | None = None,
) -> bool:
    """Keep the reviewer's better prompt only if our own rules agree it is better.

    It must name every key detail, leak nothing, and cost less than the original
    (so a copy of the original never passes).
    """
    candidate = (better or "").strip()
    if not candidate:
        return False
    graded = grade_prompt(candidate, beat, history)
    if graded.leaked or graded.missing or graded.effective_tokens >= result.effective_tokens:
        return False
    result.better_prompt = candidate
    result.better_effective = graded.effective_tokens
    return True


def summary(result: TurnGrade, *, turn: int, turn_count: int) -> str:
    """One or two sentences for the phone, the stage, and the event feed."""
    lead = f"Turn {turn} of {turn_count}. {result.grade}."
    if result.leaked:
        return (
            f"{lead} The message pasted a credential. Anything you send a model can end up in logs, "
            "so name the header and leave the value out."
        )
    parts: list[str] = []
    if result.missing:
        names = " and ".join(short_label(label) for label in result.missing)
        pronoun = "it" if len(result.missing) == 1 else "them"
        parts.append(f"The message left out {names}, so the model looks {pronoun} up on the web.")
    elif result.lookup_tokens > 0:
        parts.append("The model still went looking, even though the message named the facts.")
    else:
        parts.append("The model had what it needed, so it did no web lookup.")
    if result.ask_missing:
        parts.append("It never said what you want, so the model has to guess.")
    if result.output_tokens:
        parts.append("It asked for more output than it needed.")
    if result.prompt_tokens > 2 * result.target_tokens:
        parts.append(f"The message itself was {result.prompt_tokens:,} tokens. Quote the lines that matter, not the whole file.")
    parts.append(f"About {result.effective_tokens:,} tokens, {result.grams:.3f} g CO2e.")
    if result.excess_kg >= 0.1:
        parts.append(f"Sent a million times, the part over budget is about {result.excess_kg:,.0f} kg CO2e.")
    return " ".join([lead, *parts])
