"""Correlation ID context management using contextvars."""

from contextvars import ContextVar, Token

_CORRELATION_ID_CTX: ContextVar[str | None] = ContextVar("correlation_id", default=None)
CORRELATION_ID_HEADER = "X-Correlation-ID"


def get_correlation_id() -> str | None:
    """Retrieve the correlation ID for the current async task context."""
    return _CORRELATION_ID_CTX.get()


def set_correlation_id(correlation_id: str | None) -> Token:
    """Set the correlation ID for the current context and return the reset token."""
    return _CORRELATION_ID_CTX.set(correlation_id)


def reset_correlation_id(token: Token) -> None:
    """Reset the correlation ID to its previous state using the given token."""
    _CORRELATION_ID_CTX.reset(token)
