"""Runtime configuration loaded from environment variables.

The defaults match the values in `.env.example` so the app can boot for a
quick smoke test without a real `.env`, but every secret-bearing setting
must be overridden in production.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    groq_api_key: str = Field(default="", description="Groq API key")
    groq_model: str = Field(default="llama-3.1-8b-instant")

    # Telegram
    telegram_bot_token: str = Field(default="")
    telegram_webhook_secret: str = Field(default="dev-secret")
    admin_chat_id: str = Field(default="")

    # Public URL (used for webhook registration)
    public_base_url: str = Field(default="")

    # Admin endpoint
    admin_api_token: str = Field(default="dev-admin-token")

    # CORS
    allowed_origins: str = Field(default="*")

    # Optional SMTP
    smtp_host: str = Field(default="")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    smtp_from: str = Field(default="")
    smtp_to: str = Field(default="")

    # SQLite
    db_path: str = Field(default="leads.db")

    @property
    def cors_origins(self) -> List[str]:
        raw = (self.allowed_origins or "").strip()
        if not raw or raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token)

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.smtp_host and self.smtp_from and self.smtp_to)


@lru_cache
def get_settings() -> Settings:
    return Settings()
