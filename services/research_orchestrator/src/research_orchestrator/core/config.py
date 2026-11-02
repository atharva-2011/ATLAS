"""Configuration management for Research Orchestrator."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Research Orchestrator settings loaded from environment variables and local .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "research-orchestrator"
    service_version: str = "0.1.0"
    environment: str = "local"
    host: str = "127.0.0.1"
    port: int = 8001
    log_level: str = "INFO"
    log_format: str = "console"
    api_prefix: str = "/api/v1"

    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./atlas_orchestrator.db"
    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
