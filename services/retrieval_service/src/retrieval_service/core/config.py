"""Configuration management for Retrieval Service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Retrieval Service settings loaded from environment variables and local .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "retrieval-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    host: str = "127.0.0.1"
    port: int = 8003
    log_level: str = "INFO"
    log_format: str = "console"
    api_prefix: str = "/api/v1"

    # Vector Storage and Embeddings
    qdrant_location: str = ":memory:"
    qdrant_path: str | None = None
    collection_name: str = "atlas_evidence_chunks"
    embedding_provider: str = "deterministic"
    embedding_model: str = "deterministic-local-384"
    vector_dimension: int = 384


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
