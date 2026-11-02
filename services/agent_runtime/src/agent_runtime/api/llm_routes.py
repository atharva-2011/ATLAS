"""LLM completion and structured generation API endpoints."""

from typing import Annotated

from agent_runtime.core.config import Settings, get_settings
from agent_runtime.llm.base import (
    LLMAuthenticationError,
    LLMError,
    LLMOutputParsingError,
    LLMTimeoutError,
)
from agent_runtime.llm.factory import ResilientLLMService, get_resilient_llm_service
from atlas_contracts.agent_schemas import (
    CriticOutput,
    LLMMessage,
    LLMResponse,
    PlannerOutput,
    ResearcherOutput,
    SynthesizerOutput,
    VerifierOutput,
)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/llm", tags=["LLM"])

_service_instance: ResilientLLMService | None = None


def get_llm_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ResilientLLMService:
    global _service_instance
    if _service_instance is None:
        _service_instance = get_resilient_llm_service(settings)
    return _service_instance


class TextCompletionRequest(BaseModel):
    messages: list[LLMMessage] = Field(..., min_length=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = None
    timeout: float | None = None


class StructuredCompletionRequest(BaseModel):
    schema_type: str = Field(
        ...,
        description="One of: 'planner', 'researcher', 'verifier', 'critic', 'synthesizer'",
    )
    messages: list[LLMMessage] = Field(..., min_length=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int | None = None
    timeout: float | None = None


SCHEMA_MAP: dict[str, type[BaseModel]] = {
    "planner": PlannerOutput,
    "researcher": ResearcherOutput,
    "verifier": VerifierOutput,
    "critic": CriticOutput,
    "synthesizer": SynthesizerOutput,
}


@router.post(
    "/complete",
    response_model=LLMResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate raw text completion from configured LLM service",
)
async def complete_text(
    payload: TextCompletionRequest,
    llm_service: Annotated[ResilientLLMService, Depends(get_llm_service)],
) -> LLMResponse:
    try:
        return await llm_service.complete(
            messages=payload.messages,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            timeout=payload.timeout,
        )
    except LLMTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
    except LLMAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.post(
    "/complete-structured",
    response_model=LLMResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate typed structured response conforming to agent schema",
)
async def complete_structured(
    payload: StructuredCompletionRequest,
    llm_service: Annotated[ResilientLLMService, Depends(get_llm_service)],
) -> LLMResponse:
    schema_cls = SCHEMA_MAP.get(payload.schema_type.lower())
    if not schema_cls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown schema_type '{payload.schema_type}'. Allowed: {list(SCHEMA_MAP.keys())}",
        )

    try:
        _, response = await llm_service.complete_structured(
            messages=payload.messages,
            response_model=schema_cls,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            timeout=payload.timeout,
        )
        return response
    except LLMOutputParsingError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Model output failed schema validation: {exc}",
        ) from exc
    except LLMTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
    except LLMAuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
