"""Unit tests for Ingestion Service configuration."""

from ingestion_service.core.config import Settings


def test_default_config():
    settings = Settings()
    assert settings.service_name == "ingestion-service"
    assert settings.port == 8002
    assert settings.environment == "local"
    assert settings.host == "127.0.0.1"


def test_custom_config_override():
    settings = Settings(
        service_name="ingestion-service-custom",
        port=9002,
        environment="staging",
        log_level="DEBUG",
    )
    assert settings.service_name == "ingestion-service-custom"
    assert settings.port == 9002
    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"
