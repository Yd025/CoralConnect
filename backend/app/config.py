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


@dataclass(frozen=True)
class Settings:
    xai_api_key: str
    grok_model: str
    grok_image_model: str
    grok_images: bool
    data_path: Path
    xai_base: str = "https://api.x.ai/v1"


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
    )


settings = get_settings()
