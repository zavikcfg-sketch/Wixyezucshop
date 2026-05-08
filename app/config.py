from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Settings:
    bot_token: str
    web_app_url: str
    admin_id: Optional[int]
    site_url: str
    db_path: str


def _load_dotenv(dotenv_path: str = ".env") -> None:
    env_file = Path(dotenv_path)
    if not env_file.exists():
        return

    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_settings() -> Settings:
    _load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN не указан. Добавьте его в .env")

    admin_raw = os.getenv("ADMIN_ID", "").strip()
    admin_id = int(admin_raw) if admin_raw.isdigit() else None

    return Settings(
        bot_token=bot_token,
        web_app_url=os.getenv("WEB_APP_URL", "https://example.ngrok-free.app/index.html").strip(),
        admin_id=admin_id,
        site_url=os.getenv("SITE_URL", "https://google.com/search?q=WIXYEZ+UC+SHOP").strip(),
        db_path=os.getenv("DB_PATH", "shop.db").strip(),
    )
