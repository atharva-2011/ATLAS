"""Configuration management for Agent Runtime."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Agent Runtime settings loaded from environment variables and local .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "agent-runtime"
    service_version: str = "0.1.0"
    environment: str = "local"
    host: str = "127.0.0.1"
    port: int = 8004
    log_level: str = "INFO"
    log_format: str = "console"
    api_prefix: str = "/api/v1"

    # LLM Provider Configuration
    default_provider: str = "mock"
    default_model: str = "atlas-mock-v1"
    fallback_provider: str = "mock"
    fallback_model: str = "atlas-mock-fallback"
    request_timeout_seconds: float = 30.0
    max_retries: int = 2
    temperature: float = 0.0

    # API Keys & Endpoints (Optional/Secrets)
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
