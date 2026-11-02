"""Ingestion pipeline coordinator managing file validation, storage, parsing, and chunking."""

import logging

from atlas_contracts import DocumentChunkDTO, DocumentIngestionResult, DocumentStatus

from ingestion_service.chunker import StructureAwareChunker
from ingestion_service.core.config import get_settings
from ingestion_service.loaders import DocumentLoaderError, get_loader_for_file
from ingestion_service.storage import LocalDocumentStorage

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Coordinates end-to-end processing of research documents."""

    def __init__(
        self,
        storage: LocalDocumentStorage | None = None,
        chunker: StructureAwareChunker | None = None,
    ) -> None:
        self.storage = storage or LocalDocumentStorage()
        self.chunker = chunker or StructureAwareChunker()
        self.settings = get_settings()

    async def process_file(
        self,
        tenant_id: str,
        filename: str,
        content: bytes,
    ) -> tuple[DocumentIngestionResult, list[DocumentChunkDTO]]:
        """Validate, store, extract, and chunk a document."""
        # 1. Store and validate file
        stored_file = await self.storage.save_file(
            tenant_id=tenant_id,
            filename=filename,
            content=content,
        )

        doc_id = stored_file.document_id
        path = stored_file.file_path

        try:
            # 2. Select format loader and extract blocks
            loader = get_loader_for_file(path)
            extracted = loader.load(path)

            if extracted.is_scanned:
                logger.warning(
                    "Document %s is detected as a scanned or image-only document with minimal text.",
                    doc_id,
                )
                result = DocumentIngestionResult(
                    document_id=doc_id,
                    filename=filename,
                    storage_key=stored_file.storage_key,
                    content_hash=stored_file.content_hash,
                    byte_size=stored_file.byte_size,
                    page_count=extracted.page_count,
                    chunk_count=0,
                    status=DocumentStatus.SCANNED_OCR_REQUIRED,
                    error_message="Document appears to be scanned or contains non-extractable text. OCR is required.",
                )
                return result, []

            # 3. Structure-aware chunking
            chunks = self.chunker.chunk_blocks(document_id=doc_id, blocks=extracted.blocks)

            result = DocumentIngestionResult(
                document_id=doc_id,
                filename=filename,
                storage_key=stored_file.storage_key,
                content_hash=stored_file.content_hash,
                byte_size=stored_file.byte_size,
                page_count=extracted.page_count,
                chunk_count=len(chunks),
                status=DocumentStatus.COMPLETED,
            )
            return result, chunks

        except DocumentLoaderError as err:
            logger.error("Failed to parse document %s: %s", doc_id, err, exc_info=True)
            result = DocumentIngestionResult(
                document_id=doc_id,
                filename=filename,
                storage_key=stored_file.storage_key,
                content_hash=stored_file.content_hash,
                byte_size=stored_file.byte_size,
                page_count=0,
                chunk_count=0,
                status=DocumentStatus.FAILED,
                error_message=str(err),
            )
            return result, []
