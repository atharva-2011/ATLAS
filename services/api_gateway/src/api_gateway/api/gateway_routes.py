"""Gateway proxy routing endpoints delegating to research, ingestion, and retrieval services."""

from typing import Annotated, Any
from uuid import UUID

import httpx
from api_gateway.core.config import Settings, get_settings
from atlas_contracts import DocumentIngestionResult
from atlas_contracts.domain import ResearchCreate
from atlas_security import SecurityContext, get_security_context
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

router = APIRouter(prefix="/api/v1", tags=["Gateway Proxy"])


@router.post(
    "/research/jobs",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit async research job through gateway",
)
async def gateway_create_research_job(
    payload: ResearchCreate,
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """Validate client context and forward research job submission to Research Orchestrator."""
    url = f"{settings.research_orchestrator_url}/api/v1/research/jobs"
    headers = {
        "X-Tenant-ID": ctx.tenant_id,
        "X-User-ID": ctx.user_id,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload.model_dump(mode="json"), headers=headers)
            if resp.status_code != status.HTTP_202_ACCEPTED:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Downstream research orchestrator unavailable: {exc}",
        ) from exc


@router.get(
    "/research/jobs/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Query research job status through gateway",
)
async def gateway_get_research_job_status(
    job_id: UUID,
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """Retrieve job execution status with tenant boundary verification."""
    url = f"{settings.research_orchestrator_url}/api/v1/research/jobs/{job_id}"
    headers = {
        "X-Tenant-ID": ctx.tenant_id,
        "X-User-ID": ctx.user_id,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != status.HTTP_200_OK:
                raise HTTPException(status_code=resp.status_code, detail=resp.json())
            return resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Downstream research orchestrator unavailable: {exc}",
        ) from exc


@router.post(
    "/research/jobs/{job_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel active research job through gateway",
)
async def gateway_cancel_research_job(
    job_id: UUID,
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """Dispatch cancellation request to Research Orchestrator."""
    url = f"{settings.research_orchestrator_url}/api/v1/research/jobs/{job_id}/cancel"
    headers = {
        "X-Tenant-ID": ctx.tenant_id,
        "X-User-ID": ctx.user_id,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers)
            if resp.status_code != status.HTTP_200_OK:
                raise HTTPException(status_code=resp.status_code, detail=resp.json())
            return resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Downstream research orchestrator unavailable: {exc}",
        ) from exc


@router.get(
    "/research/jobs/{job_id}/report",
    status_code=status.HTTP_200_OK,
    summary="Retrieve completed research report through gateway",
)
async def gateway_get_research_report(
    job_id: UUID,
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """Retrieve publication markdown report and structured findings."""
    url = f"{settings.research_orchestrator_url}/api/v1/research/jobs/{job_id}/report"
    headers = {
        "X-Tenant-ID": ctx.tenant_id,
        "X-User-ID": ctx.user_id,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != status.HTTP_200_OK:
                raise HTTPException(status_code=resp.status_code, detail=resp.json())
            return resp.json()
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Downstream research orchestrator unavailable: {exc}",
        ) from exc


@router.post(
    "/documents/upload",
    response_model=DocumentIngestionResult,
    status_code=status.HTTP_201_CREATED,
    summary="Upload document through gateway to Ingestion Service",
)
async def gateway_upload_document(
    ctx: Annotated[SecurityContext, Depends(get_security_context)],
    settings: Annotated[Settings, Depends(get_settings)],
    file: UploadFile = File(...),
    tenant_id: str | None = Form(default=None),
) -> DocumentIngestionResult:
    """Stream document upload directly to the downstream Ingestion Service."""
    url = f"{settings.ingestion_service_url}/api/v1/documents/upload"
    active_tenant = tenant_id or ctx.tenant_id
    file_bytes = await file.read()

    files = {"file": (file.filename, file_bytes, file.content_type)}
    data = {"tenant_id": active_tenant}
    headers = {
        "X-Tenant-ID": active_tenant,
        "X-User-ID": ctx.user_id,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, files=files, data=data, headers=headers)
            if resp.status_code != status.HTTP_201_CREATED:
                raise HTTPException(status_code=resp.status_code, detail=resp.text)
            return DocumentIngestionResult.model_validate(resp.json())
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Downstream ingestion service unavailable: {exc}",
        ) from exc
