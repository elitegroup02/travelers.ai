from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_name: str = "travelers.ai API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://travelers:travelers_dev@localhost:5432/travelers"
    )

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379")
    cache_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days for POI data

    # Auth
    secret_key: str = Field(default="dev-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # LLM
    llm_provider: Literal["llama", "openai", "anthropic"] = "llama"
    llama_model_path: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # External APIs
    google_places_api_key: str | None = None
    openroute_api_key: str | None = None

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
