"""LLM provider abstraction interface and base types."""

from abc import ABC, abstractmethod
from typing import TypeVar

from atlas_contracts.agent_schemas import LLMMessage, LLMResponse
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Base exception for LLM operations."""

    def __init__(
        self, message: str, provider: str | None = None, recoverable: bool = False
    ) -> None:
        super().__init__(message)
        self.message = message
        self.provider = provider
        self.recoverable = recoverable


class LLMTimeoutError(LLMError):
    """Raised when an LLM provider request times out."""

    def __init__(self, message: str = "LLM request timed out", provider: str | None = None) -> None:
        super().__init__(message, provider=provider, recoverable=True)


class LLMOutputParsingError(LLMError):
    """Raised when structured JSON output from LLM fails validation."""

    def __init__(self, message: str, raw_content: str, provider: str | None = None) -> None:
        super().__init__(message, provider=provider, recoverable=False)
        self.raw_content = raw_content


class LLMAuthenticationError(LLMError):
    """Raised when LLM API keys or credentials are rejected."""

    def __init__(
        self, message: str = "LLM authentication failed", provider: str | None = None
    ) -> None:
        super().__init__(message, provider=provider, recoverable=False)


class BaseLLMProvider(ABC):
    """Abstract interface for all language model providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'mock', 'openai', 'gemini')."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier."""
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        """Execute text completion over messages."""
        ...

    @abstractmethod
    async def complete_structured(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> tuple[T, LLMResponse]:
        """Execute completion and parse result into typed Pydantic schema."""
        ...
