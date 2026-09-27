from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_dotenv(BACKEND_ROOT / ".env")


def _flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    try:
        return max(0, int(raw)) if raw else default
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    try:
        return max(0.0, float(raw)) if raw else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    xai_api_key: str
    grok_model: str
    grok_image_model: str
    grok_images: bool
    data_path: Path
    xai_base: str = "https://api.x.ai/v1"
    # Model for the prompt reviewer (layer 3 of the judge). A fast, non-reasoning
    # model is best. Defaults to GROK_MODEL.
    grok_judge_model: str = ""
    # Shared secret for full-mode calls to POST /api/judge (the plugin sends it in
    # the X-Judge-Key header). Blank turns full mode off for outside callers, so
    # nobody on the internet can spend the Grok key. Fast mode is always open.
    judge_api_key: str = ""
    # Most full-mode judge calls (reviewer + measured runs) allowed per minute.
    judge_full_per_minute: int = 20
    # Append every judged prompt (credentials redacted) to data/judge-log.jsonl,
    # for labeling real prompts into the test set. Off unless JUDGE_LOG=true.
    judge_log: bool = False
    tech_domain: str = ""
    # Seconds to wait for Grok's answer before trying once more (the retry gets
    # the same reply cap, without web search). A booth turn should stay under ~25 s.
    grok_timeout: float = 15.0
    # Grok calls allowed in flight at once, across every phone.
    grok_concurrency: int = 8
    # Spending cap: Grok calls per minute across the whole server. Past it, turns
    # are still graded by the rules and the reply is the round's written answer.
    # 0 turns the cap off.
    grok_calls_per_minute: int = 120
    # Grok Imagine rewards per hour across the server. 0 turns the cap off.
    grok_images_per_hour: int = 40
    # Games anyone can create from one address in 10 minutes. 0 turns the cap off.
    sessions_per_ip: int = 30
    # Games with no activity for this many hours are dropped from the save file.
    # Their result cards and the pair board stay. 0 keeps every game forever.
    idle_session_hours: float = 6.0


def get_settings() -> Settings:
    data = os.environ.get("DATA_PATH", "data/sessions.json")
    path = Path(data)
    if not path.is_absolute():
        path = BACKEND_ROOT / path
    return Settings(
        xai_api_key=os.environ.get("XAI_API_KEY", "").strip(),
        grok_model=os.environ.get("GROK_MODEL", "grok-4.6").strip() or "grok-4.6",
        grok_image_model=os.environ.get("GROK_IMAGE_MODEL", "grok-imagine-image-2.0").strip()
        or "grok-imagine-image-2.0",
        grok_images=_flag("GROK_IMAGES", True),
        data_path=path,
        grok_judge_model=os.environ.get("GROK_JUDGE_MODEL", "").strip()
        or os.environ.get("GROK_MODEL", "grok-4.6").strip()
        or "grok-4.6",
        judge_api_key=os.environ.get("JUDGE_API_KEY", "").strip(),
        judge_full_per_minute=_int("JUDGE_FULL_PER_MINUTE", 20),
        judge_log=_flag("JUDGE_LOG", False),
        tech_domain=os.environ.get("TECH_DOMAIN", "").strip().removeprefix("https://").removeprefix("http://").strip("/"),
        grok_timeout=_float("GROK_TIMEOUT", 15.0) or 15.0,
        grok_concurrency=_int("GROK_CONCURRENCY", 8) or 8,
        grok_calls_per_minute=_int("GROK_CALLS_PER_MINUTE", 120),
        grok_images_per_hour=_int("GROK_IMAGES_PER_HOUR", 40),
        sessions_per_ip=_int("SESSIONS_PER_IP", 30),
        idle_session_hours=_float("IDLE_SESSION_HOURS", 6.0),
    )


settings = get_settings()
