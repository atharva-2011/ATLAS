"""Gemini LLM Provider adapter using Google GenAI SDK or direct HTTP REST API."""

import json
import time
from typing import Any, TypeVar

import httpx
from atlas_contracts.agent_schemas import LLMMessage, LLMMessageRole, LLMResponse, LLMUsage
from pydantic import BaseModel

from agent_runtime.llm.base import (
    BaseLLMProvider,
    LLMAuthenticationError,
    LLMError,
    LLMTimeoutError,
)
from agent_runtime.llm.parser import parse_structured_output

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(BaseLLMProvider):
    """Native Google Gemini provider adapter using the v1beta generateContent API."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        default_timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self._model_name = model_name
        self.default_timeout = default_timeout

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _format_contents(
        self, messages: list[LLMMessage]
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        """Convert standard LLM messages to Gemini systemInstruction and contents list."""
        system_instruction = None
        contents: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == LLMMessageRole.SYSTEM:
                system_instruction = {"parts": [{"text": msg.content}]}
            elif msg.role in (LLMMessageRole.USER, LLMMessageRole.TOOL):
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == LLMMessageRole.ASSISTANT:
                contents.append({"role": "model", "parts": [{"text": msg.content}]})

        return system_instruction, contents

    async def complete(
        self,
        messages: list[LLMMessage],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> LLMResponse:
        start_time = time.perf_counter()
        req_timeout = timeout or self.default_timeout

        system_instruction, contents = self._format_contents(messages)

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if max_tokens is not None:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self._model_name}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=req_timeout) as client:
            try:
                res = await client.post(url, json=payload)
            except httpx.TimeoutException as exc:
                raise LLMTimeoutError(
                    f"Gemini request timed out after {req_timeout}s",
                    provider=self.provider_name,
                ) from exc
            except httpx.RequestError as exc:
                raise LLMError(
                    f"Gemini connection error: {exc}",
                    provider=self.provider_name,
                    recoverable=True,
                ) from exc

            if res.status_code in (401, 403):
                raise LLMAuthenticationError(
                    f"Gemini authentication failed (status {res.status_code}): {res.text}",
                    provider=self.provider_name,
                )
            if res.status_code >= 400:
                raise LLMError(
                    f"Gemini API returned error status {res.status_code}: {res.text}",
                    provider=self.provider_name,
                    recoverable=(res.status_code >= 500 or res.status_code == 429),
                )

            data = res.json()
            candidates = data.get("candidates", [])
            if not candidates:
                content = ""
            else:
                parts = candidates[0].get("content", {}).get("parts", [])
                content = "".join(part.get("text", "") for part in parts)

            usage_metadata = data.get("usageMetadata", {})
            prompt_tokens = usage_metadata.get("promptTokenCount", 0)
            comp_tokens = usage_metadata.get("candidatesTokenCount", 0)
            total_tokens = usage_metadata.get("totalTokenCount", prompt_tokens + comp_tokens)

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            return LLMResponse(
                content=content,
                model=self._model_name,
                provider=self.provider_name,
                usage=LLMUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=comp_tokens,
                    total_tokens=total_tokens,
                    estimated_cost_usd=(prompt_tokens * 0.10 + comp_tokens * 0.40) / 1_000_000,
                ),
                latency_ms=latency_ms,
            )

    async def complete_structured(
        self,
        messages: list[LLMMessage],
        response_model: type[T],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        timeout: float | None = None,
    ) -> tuple[T, LLMResponse]:
        """Request JSON schema constrained completion and parse into typed Pydantic model."""
        schema = response_model.model_json_schema()
        instruction = (
            f"You MUST respond ONLY with valid JSON conforming strictly to this JSON Schema:\n"
            f"{json.dumps(schema)}\n"
            "Do NOT include markdown backticks or commentary outside the JSON object."
        )

        augmented_messages = [
            LLMMessage(role=LLMMessageRole.SYSTEM, content=instruction),
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
