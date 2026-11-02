"""Configuration management for API Gateway."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """API Gateway settings loaded from environment variables and local .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "api-gateway"
    service_version: str = "0.1.0"
    environment: str = "local"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    log_format: str = "console"
    api_prefix: str = "/api/v1"
    research_orchestrator_url: str = "http://127.0.0.1:8001"
    ingestion_service_url: str = "http://127.0.0.1:8002"
    retrieval_service_url: str = "http://127.0.0.1:8003"
    agent_runtime_url: str = "http://127.0.0.1:8004"
    evaluation_service_url: str = "http://127.0.0.1:8005"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
