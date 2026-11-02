"""Loader for PDF documents preserving page-level locators and detecting scanned pages."""

from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from ingestion_service.loaders.base import (
    DocumentLoaderError,
    DocumentLoaderProtocol,
    ExtractedBlock,
    ExtractedDocument,
)


class PdfDocumentLoader(DocumentLoaderProtocol):
    """Extracts text from PDF documents with exact page numbers and scanned detection."""

    def load(self, file_path: Path) -> ExtractedDocument:
        if not file_path.exists():
            raise DocumentLoaderError(f"File not found: {file_path}")

        try:
            reader = PdfReader(str(file_path))
        except (PyPdfError, Exception) as exc:
            raise DocumentLoaderError(f"Corrupted or invalid PDF file: {exc}") from exc

        page_count = len(reader.pages)
        if page_count == 0:
            return ExtractedDocument(page_count=0, total_characters=0, is_scanned=False)

        blocks: list[ExtractedBlock] = []
        total_chars = 0
        pages_with_text = 0

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            cleaned_text = page_text.strip()
            if cleaned_text:
                pages_with_text += 1
                total_chars += len(cleaned_text)

                # Segment page content into paragraphs
                paragraphs = [p.strip() for p in cleaned_text.split("\n\n") if p.strip()]
                for para_idx, para in enumerate(paragraphs, start=1):
                    blocks.append(
                        ExtractedBlock(
                            text=para,
                            locator={
                                "page": page_idx,
                                "paragraph": para_idx,
                            },
                        )
                    )

        # Scanned heuristic: If PDF has multiple pages but 0 or negligible text (<20 chars per page on average)
        is_scanned = (page_count > 0 and pages_with_text == 0) or (
            page_count > 0 and (total_chars / page_count) < 20
        )

        metadata = {}
        if reader.metadata:
            for k, v in reader.metadata.items():
                if isinstance(v, str):
                    clean_k = k.lstrip("/")
                    metadata[clean_k] = v

        return ExtractedDocument(
            blocks=blocks,
            page_count=page_count,
            is_scanned=is_scanned,
            total_characters=total_chars,
            metadata=metadata,
        )
