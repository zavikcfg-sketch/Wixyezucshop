from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = ""
    paycore_api_base_url: str = ""
    paycore_public_key: str = ""
    paycore_payment_service: str = ""
    paycore_currency: str = "RUB"
    web_public_url: str = "http://127.0.0.1:8080"
    channel_username: str = ""
    telegram_bot_username: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
