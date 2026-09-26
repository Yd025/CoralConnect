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
    "Do not lecture about tokens or carbon."
)

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


async def complete(messages: list[dict], fallback: str) -> tuple[str, bool]:
    """Return (answer, simulated). Messages are the thread, oldest first, including the new user turn."""
    if not settings.xai_api_key:
        return fallback, True
    try:
        async with httpx.AsyncClient(timeout=22) as client:
            response = await client.post(
                f"{settings.xai_base}/responses",
                headers={
                    "Authorization": f"Bearer {settings.xai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.grok_model,
                    "input": [{"role": "system", "content": SYSTEM}, *messages],
                },
            )
        if response.status_code >= 400:
            logger.warning("Grok text failed: %s %s", response.status_code, response.text[:300])
            return fallback, True
        text = _output_text(response.json())
        if not text:
            logger.warning("Grok text response had no output_text")
            return fallback, True
        return text, False
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        logger.warning("Grok text error: %s", exc)
        return fallback, True


async def icebreaker(names: list[str], languages: list[str]) -> dict | None:
    if not settings.xai_api_key:
        return None
    prompt = (
        "Write a reef-squad name of at most 4 words and a one-sentence icebreaker. "
        "These strangers must collaborate on a prompt that includes the source, so the model does not search the web. "
        f"Names: {', '.join(names)}. Languages: {', '.join(languages)}. "
        'Return only JSON: {"name": "...", "icebreaker": "..."}'
    )
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(
                f"{settings.xai_base}/responses",
                headers={
                    "Authorization": f"Bearer {settings.xai_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.grok_model,
                    "input": prompt,
                },
            )
        if response.status_code >= 400:
            logger.warning("Grok icebreaker failed: %s", response.status_code)
            return None
        return _parse_json_object(_output_text(response.json()))
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        logger.warning("Grok icebreaker error: %s", exc)
        return None


def _parse_json_object(text: str) -> dict | None:
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    name = str(data.get("name", "")).strip()
    line = str(data.get("icebreaker", "")).strip()
    if not name or not line:
        return None
    return {"name": name[:48], "icebreaker": line[:240]}


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
