"""Unit tests for Retrieval Service configuration."""

from retrieval_service.core.config import Settings


def test_default_config():
    settings = Settings()
    assert settings.service_name == "retrieval-service"
    assert settings.port == 8003
    assert settings.environment == "local"
    assert settings.host == "127.0.0.1"


def test_custom_config_override():
    settings = Settings(
        service_name="retrieval-service-custom",
        port=9003,
        environment="staging",
        log_level="DEBUG",
    )
    assert settings.service_name == "retrieval-service-custom"
    assert settings.port == 9003
    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"
