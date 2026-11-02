"""Factory and resilient wrapper with retry, fallback, and timeout support."""

import asyncio
from typing import TypeVar

from atlas_contracts.agent_schemas import LLMMessage, LLMResponse
from pydantic import BaseModel

from agent_runtime.core.config import Settings
from agent_runtime.llm.base import BaseLLMProvider, LLMError, LLMTimeoutError
from agent_runtime.llm.mock_provider import MockLLMProvider
from agent_runtime.llm.openai_provider import OpenAICompatibleProvider

T = TypeVar("T", bound=BaseModel)


class ResilientLLMService:
    """Orchestrates LLM calls with automatic retry, exponential backoff, and fallback provider failover."""

    def __init__(
        self,
        primary_provider: BaseLLMProvider,
        fallback_provider: BaseLLMProvider | None = None,
        max_retries: int = 2,
        initial_backoff_seconds: float = 0.5,
    ) -> None:
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.max_retries = max_retries
        self.initial_backoff_seconds = initial_backoff_seconds

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        """Execute text completion trying primary provider with retries, then fallback."""
        attempt = 0
        backoff = self.initial_backoff_seconds

        while attempt <= self.max_retries:
            try:
                return await self.primary_provider.complete(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )
            except (LLMTimeoutError, LLMError) as exc:
                if not getattr(exc, "recoverable", True) or attempt == self.max_retries:
                    # Try fallback provider if available
                    if self.fallback_provider and self.fallback_provider != self.primary_provider:
                        return await self.fallback_provider.complete(
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            timeout=timeout,
                        )
                    raise
                attempt += 1
                await asyncio.sleep(backoff)
                backoff *= 2.0

        raise LLMError("Failed after maximum retries", provider=self.primary_provider.provider_name)

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> tuple[T, LLMResponse]:
        """Execute structured output completion with retry and fallback handling."""
        attempt = 0
        backoff = self.initial_backoff_seconds

        while attempt <= self.max_retries:
            try:
                return await self.primary_provider.complete_structured(
                    messages=messages,
                    response_model=response_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )
            except (LLMTimeoutError, LLMError) as exc:
                if not getattr(exc, "recoverable", True) or attempt == self.max_retries:
                    if self.fallback_provider and self.fallback_provider != self.primary_provider:
                        return await self.fallback_provider.complete_structured(
                            messages=messages,
                            response_model=response_model,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            timeout=timeout,
                        )
                    raise
                attempt += 1
                await asyncio.sleep(backoff)
                backoff *= 2.0

        raise LLMError(
            "Failed structured completion after maximum retries",
            provider=self.primary_provider.provider_name,
        )


def create_llm_provider(
    provider_name: str,
    model_name: str,
    settings: Settings,
) -> BaseLLMProvider:
    """Instantiate a concrete LLM provider instance from name and settings."""
    name = provider_name.lower().strip()
    if name == "mock":
        return MockLLMProvider(model_name=model_name)
    if name in {"openai", "ollama", "vllm"}:
        base_url = settings.openai_base_url or "https://api.openai.com/v1"
        return OpenAICompatibleProvider(
            api_key=settings.openai_api_key,
            base_url=base_url,
            model_name=model_name,
            default_timeout=settings.request_timeout_seconds,
            provider_identifier=name,
        )

    # Default fallback to mock provider
    return MockLLMProvider(model_name=model_name)


def get_resilient_llm_service(settings: Settings) -> ResilientLLMService:
    """Build configured ResilientLLMService with primary and fallback providers."""
    primary = create_llm_provider(
        provider_name=settings.default_provider,
        model_name=settings.default_model,
        settings=settings,
    )

    fallback = None
    if settings.fallback_provider:
        fallback = create_llm_provider(
            provider_name=settings.fallback_provider,
            model_name=settings.fallback_model,
            settings=settings,
        )

    return ResilientLLMService(
        primary_provider=primary,
        fallback_provider=fallback,
        max_retries=settings.max_retries,
    )
