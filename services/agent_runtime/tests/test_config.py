"""Unit tests for Agent Runtime configuration."""

from agent_runtime.core.config import Settings


def test_default_config():
    settings = Settings()
    assert settings.service_name == "agent-runtime"
    assert settings.port == 8004
    assert settings.environment == "local"
    assert settings.host == "127.0.0.1"


def test_custom_config_override():
    settings = Settings(
        service_name="agent-runtime-custom",
        port=9004,
        environment="staging",
        log_level="DEBUG",
    )
    assert settings.service_name == "agent-runtime-custom"
    assert settings.port == 9004
    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"
