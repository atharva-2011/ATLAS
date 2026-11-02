"""Document format loaders for ATLAS Ingestion Service."""

from pathlib import Path

from ingestion_service.loaders.base import (
    DocumentLoaderError,
    DocumentLoaderProtocol,
    ExtractedBlock,
    ExtractedDocument,
)
from ingestion_service.loaders.docx_loader import DocxDocumentLoader
from ingestion_service.loaders.pdf_loader import PdfDocumentLoader
from ingestion_service.loaders.text_loader import TextDocumentLoader


def get_loader_for_file(file_path: Path) -> DocumentLoaderProtocol:
    """Return the appropriate format loader based on file extension."""
    suffix = file_path.suffix.lower()
    if suffix in (".txt", ".md"):
        return TextDocumentLoader()
    if suffix == ".pdf":
        return PdfDocumentLoader()
    if suffix == ".docx":
        return DocxDocumentLoader()

    raise DocumentLoaderError(f"Unsupported file format: '{suffix}'")


__all__ = [
    "DocxDocumentLoader",
    "DocumentLoaderError",
    "DocumentLoaderProtocol",
    "ExtractedBlock",
    "ExtractedDocument",
    "PdfDocumentLoader",
    "TextDocumentLoader",
    "get_loader_for_file",
]
