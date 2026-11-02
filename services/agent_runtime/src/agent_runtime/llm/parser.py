"""JSON parsing and markdown cleanup utilities for structured LLM outputs."""

import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from agent_runtime.llm.base import LLMOutputParsingError

T = TypeVar("T", bound=BaseModel)


def extract_json_from_text(text: str) -> str:
    """Extract raw JSON string from LLM responses containing markdown code fences."""
    cleaned = text.strip()

    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if match:
        return match.group(1).strip()

    # Or match outermost { ... } or [ ... ]
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace : last_brace + 1].strip()

    return cleaned


def parse_structured_output[T: BaseModel](raw_content: str, response_model: type[T]) -> T:
    """Parse raw LLM response text into the specified Pydantic model with strict validation."""
    json_str = extract_json_from_text(raw_content)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise LLMOutputParsingError(
            message=f"Invalid JSON returned by model: {exc}",
            raw_content=raw_content,
        ) from exc

    try:
        return response_model.model_validate(data)
    except ValidationError as exc:
        raise LLMOutputParsingError(
            message=f"Schema validation failed for {response_model.__name__}: {exc}",
            raw_content=raw_content,
        ) from exc


def redact_secrets(text: str) -> str:
    """Redact potential API keys or sensitive authorization tokens from text and logs."""
    # Matches patterns like sk-..., Bearer ..., api_key=...
    patterns = [
        (r"(?i)(api[_-]?key\s*[:=]\s*)['\"]?([a-zA-Z0-9_\-]{8,})['\"]?", r"\1[REDACTED]"),
        (r"(?i)(bearer\s+)([a-zA-Z0-9_\-\.]{8,})", r"\1[REDACTED]"),
        (r"\b(sk-[a-zA-Z0-9]{20,})\b", "[REDACTED_API_KEY]"),
    ]
    result = text
    for pat, repl in patterns:
        result = re.sub(pat, repl, result)
    return result
