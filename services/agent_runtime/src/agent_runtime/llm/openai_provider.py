"""Generic OpenAI-compatible LLM provider adapter using httpx."""

import time
from typing import Any, TypeVar

import httpx
from atlas_contracts.agent_schemas import LLMMessage, LLMResponse, LLMUsage
from pydantic import BaseModel

from agent_runtime.llm.base import (
    BaseLLMProvider,
    LLMAuthenticationError,
    LLMError,
    LLMTimeoutError,
)
from agent_runtime.llm.parser import parse_structured_output

T = TypeVar("T", bound=BaseModel)


class OpenAICompatibleProvider(BaseLLMProvider):
    """Adapter for any OpenAI-compatible API endpoint (OpenAI, Ollama, vLLM, DeepSeek, etc.)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        model_name: str = "gpt-4o-mini",
        default_timeout: float = 30.0,
        provider_identifier: str = "openai",
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._model_name = model_name
        self.default_timeout = default_timeout
        self._provider_identifier = provider_identifier

    @property
    def provider_name(self) -> str:
        return self._provider_identifier

    @property
    def model_name(self) -> str:
        return self._model_name

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        start_time = time.perf_counter()
        req_timeout = timeout or self.default_timeout

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, Any] = {
            "model": self._model_name,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=req_timeout) as client:
            try:
                res = await client.post(url, headers=headers, json=payload)
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(
                    f"{self.provider_name} request timed out after {req_timeout}s",
                    provider=self.provider_name,
                ) from exc
            except httpx.RequestError as exc:
                raise LLMError(
                    f"{self.provider_name} connection error: {exc}",
                    provider=self.provider_name,
                    recoverable=True,
                ) from exc

            if res.status_code == 401 or res.status_code == 403:
                raise LLMAuthenticationError(
                    f"Authentication failed with status {res.status_code}",
                    provider=self.provider_name,
                )
            if res.status_code >= 400:
                raise LLMError(
                    f"LLM API returned error status {res.status_code}: {res.text}",
                    provider=self.provider_name,
                    recoverable=(res.status_code >= 500),
                )

            data = res.json()
            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage_info = data.get("usage", {})

            prompt_tokens = usage_info.get("prompt_tokens", 0)
            comp_tokens = usage_info.get("completion_tokens", 0)
            total_tokens = usage_info.get("total_tokens", prompt_tokens + comp_tokens)

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            return LLMResponse(
                content=content,
                model=self._model_name,
                provider=self.provider_name,
                usage=LLMUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=comp_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=(prompt_tokens * 0.15 + comp_tokens * 0.60) / 1_000_000,
                ),
                latency_ms=latency_ms,
                finish_reason=choice.get("finish_reason", "stop"),
            )

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> tuple[T, LLMResponse]:
        """Request structured JSON completion and validate using the given response_model."""
        schema = response_model.model_json_schema()
        system_instruction = (
            f"You MUST respond ONLY with valid JSON conforming strictly to the following JSON Schema:\n"
            f"{schema}\n"
            "Do not include conversational filler, markdown explanations, or commentary outside the JSON."
        )

        # Prepend or append system prompt schema constraint
        augmented_messages = [
            LLMMessage(role="system", content=system_instruction),
            *messages,
        ]

        raw_response = await self.complete(
            messages=augmented_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )

        parsed = parse_structured_output(raw_response.content, response_model)
        raw_response.parsed = parsed.model_dump()
        return parsed, raw_response
