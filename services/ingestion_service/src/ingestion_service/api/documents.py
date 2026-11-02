"""Document ingestion and upload API endpoints for Ingestion Service."""

from atlas_contracts import DocumentIngestionResult, ErrorResponse
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from ingestion_service.pipeline import IngestionPipeline

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])
pipeline = IngestionPipeline()


@router.post(
    "/upload",
    response_model=DocumentIngestionResult,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Form(default="default_tenant"),
) -> DocumentIngestionResult:
    """Upload and process a research document (PDF, DOCX, TXT, MD)."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    try:
        result, _ = await pipeline.process_file(
            tenant_id=tenant_id,
            filename=file.filename,
            content=content,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        ) from val_err
