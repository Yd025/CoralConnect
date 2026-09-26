"""The prompt judge: one entry point for the game, the phone's live verdict, and the plugin.

The four layers (docs/PROMPT-JUDGE.md):

1. Count tokens     carbon.count_tokens
2. Rules            grading.grade_prompt       (game mode or general mode)
3. Grok reviewer    grok.review_prompt         can only add cost
4. Measured run     grok.complete              real usage numbers from Grok

"fast" runs layers 1 and 2: instant, free, and deterministic.
"full" adds layers 3 and 4 when a Grok key is set.

The rules set the minimum cost. Grok can add cost (a real web search, a
reviewer that finds something missing, an answer that has to ask back), but it
can never make a prompt look cheaper than the rules say.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque

from . import grok
from .carbon import VERDICT_WORDS, count_tokens
from .challenges import Beat
from .config import settings
from .grading import (
    Line,
    TurnGrade,
    add_asked_back,
    add_live_call,
    check_rewrite,
    grade_prompt,
    redact,
)

MODES = ("fast", "full")
logger = logging.getLogger("coralconnect.judge")

# At most this many Grok judge calls in flight at once.
_CONCURRENCY = 4
_semaphore: asyncio.Semaphore | None = None


def _gate() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(_CONCURRENCY)
    return _semaphore


class _Window:
    """Counts calls in the last 60 seconds."""

    def __init__(self) -> None:
        self.calls: deque[float] = deque()

    def allow(self, limit: int) -> bool:
        now = time.monotonic()
        while self.calls and now - self.calls[0] > 60:
            self.calls.popleft()
        if limit <= 0 or len(self.calls) >= limit:
            return False
        self.calls.append(now)
        return True

    def reset(self) -> None:
        self.calls.clear()


_full_window = _Window()


def allow_full() -> bool:
    """Rate limit for anything that spends extra Grok calls (full mode, better-prompt runs)."""
    return _full_window.allow(settings.judge_full_per_minute)


def reset_limits() -> None:
    _full_window.reset()


def history_messages(history: list[dict] | None) -> list[dict]:
    """Clean chat history: only user/assistant turns with text."""
    cleaned: list[dict] = []
    for item in history or []:
        role = str(item.get("role") or "user")
        content = str(item.get("content") or "")
        if role in ("user", "assistant") and content.strip():
            cleaned.append({"role": role, "content": content})
    return cleaned


def user_texts(history: list[dict] | None) -> list[str]:
    return [item["content"] for item in history_messages(history) if item["role"] == "user"]


def review_packet(prompt: str, beat: Beat | None, result: TurnGrade) -> dict:
    """What the reviewer sees. The prompt must already be redacted."""
    return {
        "task": beat.ask if beat else "Not given. Judge the prompt on its own.",
        "key_details": list(beat.anchors) if beat else [],
        "rules": {
            "promptTokens": result.prompt_tokens,
            "missing": list(result.missing),
            "askMissing": result.ask_missing,
            "flags": list(result.flags),
        },
        "prompt": prompt,
    }


def _usage_total(trace: dict) -> tuple[int, dict]:
    detail = {
        "input": int(trace.get("inputTokens") or 0),
        "output": int(trace.get("outputTokens") or 0),
        "reasoning": int(trace.get("reasoningTokens") or 0),
        "searches": int(trace.get("serverSideTools") or 0),
    }
    return detail["input"] + detail["output"] + detail["reasoning"], detail


def apply_measured(result: TurnGrade, answer: str, trace: dict, *, history_tokens: int) -> None:
    """Layer 4, part 1: fold in the real solver run of this prompt."""
    total, detail = _usage_total(trace)
    if total > 0:
        result.measured_tokens = total
        result.measured_detail = detail
        reasoning = f", {detail['reasoning']:,} reasoning" if detail["reasoning"] else ""
        result.lines.append(
            Line("info", f"Real Grok run: {total:,} tokens ({detail['input']:,} in, {detail['output']:,} out{reasoning}).", total)
        )
    add_live_call(result, searches=detail["searches"], verdict=None)
    if grok.asks_back(answer):
        add_asked_back(result, history_tokens + result.prompt_tokens)


def apply_review(result: TurnGrade, review: dict | None, beat: Beat | None, history: list[str]) -> None:
    """Layer 3: the reviewer can add one lookup and suggest a better prompt. Our rules check the rewrite."""
    if review is None:
        return
    add_live_call(result, searches=result.searches, verdict=review)
    if review.get("better_prompt") and not result.leaked:
        check_rewrite(result, review["better_prompt"], beat, history)


async def measure_better(result: TurnGrade, history: list[dict] | None) -> bool:
    """Layer 4, part 2: run the checked better prompt through the same solver and compare real usage."""
    if not result.better_prompt or not result.measured_tokens or not grok.live():
        return False
    messages = [*history_messages(history), {"role": "user", "content": result.better_prompt}]
    async with _gate():
        _answer, simulated, _request, trace = await grok.complete(messages, "")
    if simulated:
        return False
    total, _detail = _usage_total(trace)
    if total <= 0:
        return False
    result.better_measured_tokens = total
    result.lines.append(
        Line(
            "good",
            f"Better prompt, real run: {total:,} tokens. That saves {result.measured_saved:,} real tokens.",
            total,
        )
    )
    return True


def saved_vs_vague(result: TurnGrade, beat: Beat | None) -> int:
    """Game mode: tokens this prompt saved compared with the round's vague sample."""
    if beat is None or result.leaked:
        return 0
    vague = grade_prompt(beat.samples.vague, beat)
    return max(0, vague.effective_tokens - result.effective_tokens)


async def judge(
    prompt: str,
    *,
    beat: Beat | None = None,
    history: list[dict] | None = None,
    mode: str = "fast",
) -> TurnGrade:
    """Run the judge. fast = rules only. full = rules, a real run, the reviewer, and a better-prompt run."""
    texts = user_texts(history)
    result = grade_prompt(prompt, beat, texts)
    if mode != "full" or not grok.live():
        return result

    safe = redact(prompt, beat)
    earlier = history_messages(history)
    history_tokens = count_tokens("\n".join(item["content"] for item in earlier))
    async with _gate():
        answer, simulated, _request, trace = await grok.complete([*earlier, {"role": "user", "content": safe}], "")
    if not simulated:
        apply_measured(result, answer, trace, history_tokens=history_tokens)
    if not result.leaked:
        async with _gate():
            review = await grok.review_prompt(review_packet(safe, beat, result))
        apply_review(result, review, beat, texts)
    if not simulated:
        await measure_better(result, history)
    return result


def public_verdict(result: TurnGrade, *, reveal: bool = True, vague_saving: int = 0, note: str = "") -> dict:
    """The /api/judge response. reveal=False hides the answer key (game mode, before sending)."""
    flags = list(result.flags)
    if note:
        flags.insert(0, note)
    return {
        "mode": result.mode,
        "verdict": VERDICT_WORDS[result.grade],
        "grade": result.grade,
        "score": result.score,
        "measured": result.measured_tokens > 0,
        "tokens": {
            "prompt": result.prompt_tokens,
            "lookups": result.lookup_tokens,
            "ask": result.ask_tokens,
            "output": result.output_tokens,
            "extraRounds": result.extra_round_tokens,
            "effective": result.effective_tokens,
            "budget": result.target_tokens,
            "measured": result.measured_tokens or None,
            "betterMeasured": result.better_measured_tokens or None,
        },
        "missing": list(result.missing) if reveal else list(result.missing_hints),
        "flags": flags,
        "betterPrompt": result.better_prompt if reveal else "",
        "betterPromptSaves": result.better_saves if reveal else 0,
        "measuredSaved": result.measured_saved,
        "savedVsVague": vague_saving,
        "gramsCO2e": round(result.grams, 4),
        "reviewer": {
            "used": result.judged_by_model,
            "verdict": result.reviewer_verdict if reveal else "",
            "reason": result.reviewer_reason if reveal else "",
            "missing": list(result.reviewer_missing) if reveal else [],
        },
        "reasons": result.receipt(reveal),
    }


def log_judgment(
    source: str,
    prompt: str,
    result: TurnGrade,
    *,
    beat: Beat | None = None,
    challenge_id: str = "",
    turn: int = 0,
    mode: str = "fast",
) -> None:
    """Append one line to data/judge-log.jsonl when JUDGE_LOG=true. Credentials are redacted."""
    if not settings.judge_log:
        return
    record = {
        "time": round(time.time(), 3),
        "source": source,
        "mode": mode,
        "challengeId": challenge_id,
        "turn": turn,
        "prompt": redact(prompt, beat),
        "grade": result.grade,
        "effective": result.effective_tokens,
        "missing": result.missing_hints,
        "flags": result.flags,
        "reviewer": result.reviewer_verdict,
        "measured": result.measured_tokens,
        "betterMeasured": result.better_measured_tokens,
        "label": "",
    }
    path = settings.data_path.parent / "judge-log.jsonl"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.warning("Could not write the judge log: %s", exc)
