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

    # Database - REQUIRED, no default
    database_url: PostgresDsn = Field(
        ...,  # Required field
        description="PostgreSQL connection string (e.g., postgresql+asyncpg://user:pass@host:5432/db)"
    )

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379")
    cache_ttl_seconds: int = 60 * 60 * 24 * 30  # 30 days for POI data

    # Auth - secret_key REQUIRED, no default
    secret_key: str = Field(
        ...,  # Required field
        min_length=32,
        description="Secret key for JWT signing (min 32 characters)"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS - stored as comma-separated string, converted to list via property
    allowed_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:8081,http://localhost:19006",
        alias="ALLOWED_ORIGINS",
        description="Allowed CORS origins (comma-separated)"
    )

    @property
    def allowed_origins(self) -> list[str]:
        """Parse comma-separated string into list of origins."""
        return [origin.strip() for origin in self.allowed_origins_str.split(",") if origin.strip()]

    # LLM
    llm_provider: Literal["llama", "openai", "anthropic", "none"] = "none"
    llama_model_path: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # External APIs
    google_places_api_key: str | None = None
    openroute_api_key: str | None = None

    # Omen AI Engine
    omen_enabled: bool = False
    omen_ws_url: str = "ws://localhost:8100/ws"
    omen_api_key: str | None = None

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    def validate_llm_config(self) -> None:
        """Validate that LLM provider has required configuration."""
        if self.llm_provider == "llama" and not self.llama_model_path:
            raise ValueError("LLAMA_MODEL_PATH required when llm_provider=llama")
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY required when llm_provider=openai")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required when llm_provider=anthropic")


@lru_cache
def get_settings() -> Settings:
    return Settings()
