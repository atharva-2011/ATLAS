"""Environment and production readiness configuration validator for ATLAS."""

import os
from typing import Any

from atlas_common.constants import (
    ENV_LOCAL,
    ENV_PRODUCTION,
    ENV_STAGING,
    SUPPORTED_ENVIRONMENTS,
)


class EnvironmentValidationError(Exception):
    """Raised when environment configuration violates production constraints."""

    pass


class EnvironmentValidator:
    """Validates configuration against environment constraints."""

    INSECURE_SECRETS = {
        "change_this_to_a_cryptographically_secure_random_key_in_production",
        "secret",
        "password",
        "admin",
        "",
    }

    @classmethod
    def validate_environment(cls, env_vars: dict[str, Any] | None = None) -> list[str]:
        """Validates configuration settings, returning a list of warnings or raising on strict errors."""
        env = (env_vars or os.environ).get("ENVIRONMENT", ENV_LOCAL)
        warnings: list[str] = []

        if env not in SUPPORTED_ENVIRONMENTS:
            raise EnvironmentValidationError(
                f"Unknown ENVIRONMENT '{env}'. Supported: {SUPPORTED_ENVIRONMENTS}"
            )

        # Production / Staging Strict Quality Constraints
        if env in (ENV_PRODUCTION, ENV_STAGING):
            secret_key = (env_vars or os.environ).get("SECRET_KEY", "")
            if secret_key in cls.INSECURE_SECRETS or len(secret_key) < 32:
                raise EnvironmentValidationError(
                    "SECRET_KEY must be a cryptographically strong random string (>= 32 chars) in production/staging."
                )

            db_url = (env_vars or os.environ).get("DATABASE_URL", "")
            if "sqlite" in db_url.lower():
                raise EnvironmentValidationError(
                    "SQLite DATABASE_URL is not permitted in production/staging environments. Use PostgreSQL."
                )

            qdrant_loc = (env_vars or os.environ).get("QDRANT_LOCATION", "")
            if qdrant_loc == ":memory:":
                raise EnvironmentValidationError(
                    "In-memory Qdrant (:memory:) is not permitted in production/staging. Use a distributed Qdrant cluster."
                )

            log_fmt = (env_vars or os.environ).get("LOG_FORMAT", "console")
            if log_fmt != "json":
                warnings.append(
                    f"LOG_FORMAT is '{log_fmt}'; 'json' is strongly recommended for production structured logging."
                )

        return warnings
