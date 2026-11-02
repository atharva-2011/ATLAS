"""Unit tests for Research Orchestrator configuration."""

from research_orchestrator.core.config import Settings


def test_default_config():
    settings = Settings()
    assert settings.service_name == "research-orchestrator"
    assert settings.port == 8001
    assert settings.environment == "local"
    assert settings.host == "127.0.0.1"


def test_custom_config_override():
    settings = Settings(
        service_name="research-orchestrator-custom",
        port=9001,
        environment="staging",
        log_level="DEBUG",
    )
    assert settings.service_name == "research-orchestrator-custom"
    assert settings.port == 9001
    assert settings.environment == "staging"
    assert settings.log_level == "DEBUG"
