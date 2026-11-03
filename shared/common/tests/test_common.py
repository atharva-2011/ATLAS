"""Tests for atlas_common package."""

import pytest
from atlas_common import (
    APP_NAME,
    ENV_LOCAL,
    ENV_PRODUCTION,
    SUPPORTED_ENVIRONMENTS,
    EnvironmentValidationError,
    EnvironmentValidator,
)


def test_constants():
    assert APP_NAME == "ATLAS"
    assert ENV_LOCAL in SUPPORTED_ENVIRONMENTS
    assert len(SUPPORTED_ENVIRONMENTS) == 4


def test_environment_validator_local_allows_defaults():
    warnings = EnvironmentValidator.validate_environment({"ENVIRONMENT": ENV_LOCAL})
    assert isinstance(warnings, list)
    assert len(warnings) == 0


def test_environment_validator_production_rejects_insecure_secrets():
    with pytest.raises(EnvironmentValidationError, match="SECRET_KEY"):
        EnvironmentValidator.validate_environment({
            "ENVIRONMENT": ENV_PRODUCTION,
            "SECRET_KEY": "password",
            "DATABASE_URL": "postgresql+asyncpg://user:pass@host/db",
            "QDRANT_LOCATION": "http://qdrant:6333",
        })


def test_environment_validator_production_rejects_sqlite():
    with pytest.raises(EnvironmentValidationError, match="SQLite"):
        EnvironmentValidator.validate_environment({
            "ENVIRONMENT": ENV_PRODUCTION,
            "SECRET_KEY": "a" * 32,
            "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
            "QDRANT_LOCATION": "http://qdrant:6333",
        })


def test_environment_validator_production_rejects_in_memory_qdrant():
    with pytest.raises(EnvironmentValidationError, match=":memory:"):
        EnvironmentValidator.validate_environment({
            "ENVIRONMENT": ENV_PRODUCTION,
            "SECRET_KEY": "a" * 32,
            "DATABASE_URL": "postgresql+asyncpg://user:pass@host/db",
            "QDRANT_LOCATION": ":memory:",
        })


def test_environment_validator_production_valid():
    warnings = EnvironmentValidator.validate_environment({
        "ENVIRONMENT": ENV_PRODUCTION,
        "SECRET_KEY": "c0mpl3x_cr1pt0_str0ng_s3cr3t_k3y_f0r_pr0duct10n!",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@host/db",
        "QDRANT_LOCATION": "http://qdrant:6333",
        "LOG_FORMAT": "json",
    })
    assert len(warnings) == 0


def test_environment_validator_invalid_environment_name():
    with pytest.raises(EnvironmentValidationError, match="Unknown ENVIRONMENT"):
        EnvironmentValidator.validate_environment({"ENVIRONMENT": "invalid_env_name"})
