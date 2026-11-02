"""Unit tests for Evaluation Service configuration."""

from evaluation_service.core.config import Settings


def test_default_config():
    settings = Settings()
    assert settings.service_name == "evaluation-service"
    assert settings.port == 8005
    assert settings.environment == "local"
    assert settings.host == "127.0.0.1"


def test_custom_config_override():
    settings = Settings(
        service_name="evaluation-service-custom",
        port=9005,
        environment="staging",
        log_level="DEBUG",
    )
    assert settings.service_name == "evaluation-service-custom"
    assert settings.port == 9005
    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"
