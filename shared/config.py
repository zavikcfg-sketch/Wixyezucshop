import warnings
from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CWD_DOTENV = Path.cwd() / ".env"
_dotenv_candidates = [_PROJECT_ROOT / ".env"]
if _CWD_DOTENV.resolve() != (_PROJECT_ROOT / ".env").resolve():
    _dotenv_candidates.append(_CWD_DOTENV)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=tuple(str(p) for p in _dotenv_candidates),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = ""
    telegram_bot_token_file: str = ""
    paycore_api_base_url: str = ""
    paycore_public_key: str = ""
    paycore_payment_service: str = ""
    paycore_currency: str = "RUB"
    web_public_url: str = "http://127.0.0.1:8080"
    channel_username: str = ""
    telegram_bot_username: str = ""

    @model_validator(mode="after")
    def _token_from_file(self) -> "Settings":
        t = self.telegram_bot_token.strip()
        if t:
            self.telegram_bot_token = t
            return self
        path = self.telegram_bot_token_file.strip()
        if not path:
            return self
        fp = Path(path)
        if not fp.is_file():
            warnings.warn(
                f"TELEGRAM_BOT_TOKEN_FILE указан, но файл не найден: {path}",
                stacklevel=1,
            )
            return self
        self.telegram_bot_token = fp.read_text(encoding="utf-8").strip()
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
