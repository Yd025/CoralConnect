from __future__ import annotations

import json
import logging
import re

import httpx

from .config import settings

logger = logging.getLogger("coralconnect.grok")

SYSTEM = (
    "You are a coding assistant in a live debugging thread. "
    "Answer only the latest user message. Be concise and specific. "
    "Do not ask them to resend files from earlier turns. "
    "Do not lecture about tokens or carbon. "
    "If the latest message already contains the code or error you need, answer from it and do not search the web. "
    "Search only when that source is missing."
)

JUDGE_SYSTEM = (
    "You review one coding-model API call from a live game. "
    "A reasonable prompt includes the source the model needs, so the call does no web search. "
    "A prompt that leaves that source out makes the model do extra work, including looking it up. "
    "Prompt length is not the verdict. "
    "If the solver call used a server-side tool such as web search, the prompt took too much work. "
    'Return only JSON: {"reasonable": true or false, "reason": "one sentence for the player"}'
)

TOOL_TYPES = {
    "web_search_call",
    "x_search_call",
    "code_interpreter_call",
    "file_search_call",
    "mcp_call",
}

IMAGE_PROMPTS = {
    "turtle": (
        "A single sea turtle swimming toward the viewer, soft watercolor, "
        "science-museum illustration, clear turquoise water, no text, no letters, "
        "centered animal, simple background"
    ),
    "bloom": (
        "A vibrant branching coral bloom in turquoise, coral, and gold, "
        "soft watercolor, science-museum illustration, no text, no letters, "
        "centered, simple ocean background"
    ),
}


def _output_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str) and payload["output_text"].strip():
        return payload["output_text"].strip()
    chunks: list[str] = []
    for item in payload.get("output") or []:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if isinstance(content, str) and content.strip():
            chunks.append(content.strip())
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("text"):
                    chunks.append(str(part["text"]))
                elif isinstance(part, str):
                    chunks.append(part)
    return "\n".join(chunk.strip() for chunk in chunks if chunk and chunk.strip()).strip()


def empty_trace() -> dict:
    return {
        "toolCalls": [],
        "serverSideTools": 0,
        "inputTokens": None,
        "outputTokens": None,
        "reasoningTokens": None,
    }


def call_trace(payload: dict) -> dict:
    """Read a Responses API payload for tool use and token usage."""
    tool_calls: list[str] = []
    for item in payload.get("output") or []:
        if isinstance(item, dict) and item.get("type") in TOOL_TYPES:
            tool_calls.append(str(item["type"]))
    usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
    server_tools = usage.get("num_server_side_tools_used")
    if not isinstance(server_tools, int):
        server_tools = len(tool_calls)
    return {
        "toolCalls": tool_calls,
        "serverSideTools": server_tools,
        "inputTokens": _int_or_none(usage.get("input_tokens") or usage.get("prompt_tokens")),
        "outputTokens": _int_or_none(usage.get("output_tokens") or usage.get("completion_tokens")),
        "reasoningTokens": _int_or_none(usage.get("reasoning_tokens")),
    }


def parse_verdict(text: str) -> dict | None:
    data = _json_object(text)
    if not data or "reasonable" not in data:
        return None
    reasonable = data["reasonable"]
    if isinstance(reasonable, str):
        reasonable = reasonable.strip().lower() == "true"
    if not isinstance(reasonable, bool):
        return None
    reason = " ".join(str(data.get("reason", "")).split())
    if not reason:
        return None
    return {"reasonable": reasonable, "reason": reason[:400]}


def finalize_verdict(
    model_verdict: dict | None,
    trace: dict,
    *,
    local_reasonable: bool,
    local_reason: str,
) -> tuple[bool, str, bool]:
    """Combine the judge's sentence with what the solver call actually did.

    Returns (reasonable, reason, judged_by_model). A live web search overrides a
    generous judge, because that API call is the extra work.
    """
    tools = int(trace.get("serverSideTools") or 0)
    if model_verdict is None:
        if tools > 0:
            return False, "The solver call searched the web. That extra work is what hits the reef.", False
        return local_reasonable, local_reason, False
    reasonable = bool(model_verdict["reasonable"])
    reason = str(model_verdict["reason"])
    if tools > 0 and reasonable:
        reasonable = False
        reason = "The solver call searched the web. " + reason
    return reasonable, reason, True


async def complete(messages: list[dict], fallback: str) -> tuple[str, bool, dict, dict]:
    """Return (answer, simulated, request_body, trace).

    The request body is the solver API call, without the auth header.
    Search is enabled so a prompt that omits the source can actually look it up.
    """
    request = {
        "model": settings.grok_model,
        "input": [{"role": "system", "content": SYSTEM}, *messages],
        "tools": [{"type": "web_search"}],
    }
    if not settings.xai_api_key:
        return fallback, True, request, empty_trace()
    payload = await _post_responses(request, timeout=40)
    if payload is None:
        plain = {key: value for key, value in request.items() if key != "tools"}
        payload = await _post_responses(plain, timeout=22)
        request = plain
    if payload is None:
        return fallback, True, request, empty_trace()
    text = _output_text(payload)
    if not text:
        logger.warning("Grok text response had no output_text")
        return fallback, True, request, empty_trace()
    return text, False, request, call_trace(payload)


async def review_call(task: str, anchors: tuple[str, ...], request: dict, trace: dict) -> dict | None:
    """Second Grok call. Reads the solver request and its trace, then judges the prompt."""
    if not settings.xai_api_key:
        return None
    packet = {
        "task": task,
        "factsTheLatestUserMessageNeeded": list(anchors),
        "solverRequest": request,
        "solverTrace": trace,
    }
    body = {
        "model": settings.grok_model,
        "input": [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": json.dumps(packet, ensure_ascii=False)},
        ],
    }
    payload = await _post_responses(body, timeout=20)
    if payload is None:
        return None
    return parse_verdict(_output_text(payload))


async def _post_responses(body: dict, *, timeout: float) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{settings.xai_base}/responses",
                headers={
                    "Authorization": f"Bearer {settings.xai_api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
        if response.status_code >= 400:
            logger.warning("Grok call failed: %s %s", response.status_code, response.text[:300])
            return None
        return response.json()
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        logger.warning("Grok call error: %s", exc)
        return None


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _people_lines(people: list[dict]) -> str:
    lines = []
    for person in people:
        builds = str(person.get("builds") or "").strip() or "unspecified"
        cares = str(person.get("cares") or "").strip() or "unspecified"
        lines.append(
            f"- id: {person.get('id')}; name: {person.get('name')}; builds: {builds}; wants the work to care about: {cares}"
        )
    return "\n".join(lines)


async def _ask_json(prompt: str, label: str) -> dict | None:
    if not settings.xai_api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                f"{settings.xai_base}/responses",
                headers={
                    "Authorization": f"Bearer {settings.xai_api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": settings.grok_model, "input": prompt},
            )
        if response.status_code >= 400:
            logger.warning("Grok %s failed: %s", label, response.status_code)
            return None
        return _json_object(_output_text(response.json()))
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        logger.warning("Grok %s error: %s", label, exc)
        return None


def _connection_fields(data: dict) -> dict | None:
    shared = str(data.get("shared", "")).strip()
    distinct = str(data.get("distinct", "")).strip()
    if not shared or not distinct:
        return None
    result = {"shared": shared[:240], "distinct": distinct[:240]}
    name = str(data.get("name", "")).strip()
    closing = str(data.get("closing", "")).strip()
    if name:
        result["name"] = name[:48]
    if closing:
        result["closing"] = closing[:280]
    return result


async def match_table(people: list[dict]) -> list[dict] | None:
    if not settings.xai_api_key or len(people) < 2:
        return None
    prompt = (
        "Pair these people for a short collaboration. Use every id exactly once. "
        "Make groups of 2. If one person is left, add them to a group so it has 3. "
        "Put people together when their answers overlap and each still knows something the other does not. "
        "For each group write a name of at most 4 words, one sentence on what they share, "
        "and one sentence on what only one of them brings. Use their words. "
        "Do not sort them into opposing camps. Do not mention reefs, carbon, tokens, or prompts.\n"
        f"People:\n{_people_lines(people)}\n"
        'Return only JSON: {"squads": [{"playerIds": ["id"], "name": "...", "shared": "...", "distinct": "..."}]}'
    )
    data = await _ask_json(prompt, "match")
    if not data:
        return None
    raw = data.get("squads")
    if not isinstance(raw, list):
        return None
    squads = []
    for item in raw:
        if not isinstance(item, dict):
            return None
        ids = item.get("playerIds")
        fields = _connection_fields(item)
        if not isinstance(ids, list) or not fields:
            return None
        clean_ids = [str(player_id).strip() for player_id in ids if str(player_id).strip()]
        if not clean_ids:
            return None
        squads.append({"playerIds": clean_ids, **fields})
    return squads or None


async def describe_pair(people: list[dict]) -> dict | None:
    if not settings.xai_api_key or not people:
        return None
    prompt = (
        "These two people have to find each other in a room, then work together. "
        "Write one sentence on what they share, one sentence on what only one of them brings, "
        "and one question they should ask each other out loud about the environment after the task. "
        "Use what they build and what they care about. "
        "Do not mention reefs, carbon, tokens, or prompts.\n"
        f"People:\n{_people_lines(people)}\n"
        'Return only JSON: {"shared": "...", "distinct": "...", "closing": "..."}'
    )
    data = await _ask_json(prompt, "connection")
    if not data:
        return None
    return _connection_fields(data)


def _json_object(text: str) -> dict | None:
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


async def imagine(kind: str, actor: str) -> str | None:
    if not settings.xai_api_key or not settings.grok_images:
        return None
    prompt = IMAGE_PROMPTS.get(kind)
    if not prompt:
        return None
    # Names are overlaid in HTML. Image models render text badly.
    del actor
    try:
        async with httpx.AsyncClient(timeout=28) as client:
            response = await client.post(
                f"{settings.xai_base}/images/generations",
                headers={
                    "Authorization": f"Bearer {settings.xai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.grok_image_model,
                    "prompt": prompt,
                    "aspect_ratio": "1:1",
                    "quality": "low",
                    "response_format": "url",
                },
            )
        if response.status_code >= 400:
            logger.warning("Grok Imagine failed: %s %s", response.status_code, response.text[:300])
            return None
        data = response.json().get("data") or []
        if not data:
            return None
        url = data[0].get("url")
        return url if isinstance(url, str) and url else None
    except (httpx.HTTPError, json.JSONDecodeError, IndexError, AttributeError) as exc:
        logger.warning("Grok Imagine error: %s", exc)
        return None
