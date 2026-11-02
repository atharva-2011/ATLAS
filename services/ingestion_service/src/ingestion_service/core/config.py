"""Configuration management for Ingestion Service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ingestion Service settings loaded from environment variables and local .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "ingestion-service"
    service_version: str = "0.1.0"
    environment: str = "local"
    host: str = "127.0.0.1"
    port: int = 8002
    log_level: str = "INFO"
    log_format: str = "console"
    api_prefix: str = "/api/v1"

    # Ingestion & Storage Settings
    storage_dir: str = ".atlas_storage/documents"
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25 MB
    allowed_extensions: list[str] = [".pdf", ".docx", ".txt", ".md"]
    chunk_size_chars: int = 800
    chunk_overlap_chars: int = 150
    min_scanned_chars_per_page: int = 20


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
