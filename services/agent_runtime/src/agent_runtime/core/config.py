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


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
