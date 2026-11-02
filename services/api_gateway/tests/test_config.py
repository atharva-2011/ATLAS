"""Unit tests for API Gateway configuration."""

from api_gateway.core.config import Settings


def test_default_config():
    settings = Settings()
    assert settings.service_name == "api-gateway"
    assert settings.port == 8000
    assert settings.environment == "local"
    assert settings.host == "127.0.0.1"


def test_custom_config_override():
    settings = Settings(
        service_name="api-gateway-custom",
        port=9000,
        environment="staging",
        log_level="DEBUG",
    )
    assert settings.service_name == "api-gateway-custom"
    assert settings.port == 9000
    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"
