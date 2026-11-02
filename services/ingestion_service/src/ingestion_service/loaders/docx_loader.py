"""Loader for DOCX (Word) documents preserving heading and paragraph structure."""

from pathlib import Path

import docx
from docx.opc.exceptions import PackageNotFoundError

from ingestion_service.loaders.base import (
    DocumentLoaderError,
    DocumentLoaderProtocol,
    ExtractedBlock,
    ExtractedDocument,
)


class DocxDocumentLoader(DocumentLoaderProtocol):
    """Extracts text from DOCX files preserving heading and section hierarchy."""

    def load(self, file_path: Path) -> ExtractedDocument:
        if not file_path.exists():
            raise DocumentLoaderError(f"File not found: {file_path}")

        try:
            doc = docx.Document(str(file_path))
        except (PackageNotFoundError, Exception) as exc:
            raise DocumentLoaderError(f"Corrupted or invalid DOCX document: {exc}") from exc

        blocks: list[ExtractedBlock] = []
        current_heading = "Introduction"
        total_chars = 0

        for p_idx, paragraph in enumerate(doc.paragraphs, start=1):
            text = paragraph.text.strip()
            if not text:
                continue

            style_name = paragraph.style.name.lower() if paragraph.style else ""
            if "heading" in style_name:
                current_heading = text

            blocks.append(
                ExtractedBlock(
                    text=text,
                    locator={
                        "section": current_heading,
                        "paragraph": p_idx,
                    },
                )
            )
            total_chars += len(text)

        # Process tables if present
        for t_idx, table in enumerate(doc.tables, start=1):
            for r_idx, row in enumerate(table.rows, start=1):
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    row_text = " | ".join(row_cells)
                    blocks.append(
                        ExtractedBlock(
                            text=row_text,
                            locator={
                                "section": current_heading,
                                "table": t_idx,
                                "row": r_idx,
                            },
                        )
                    )
                    total_chars += len(row_text)

        return ExtractedDocument(
            blocks=blocks,
            page_count=1,
            is_scanned=False,
            total_characters=total_chars,
            metadata={"core_properties": doc.core_properties.title or ""},
        )
