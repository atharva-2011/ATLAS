"""Loader for plain text (.txt) and markdown (.md) documents."""

import re
from pathlib import Path

from ingestion_service.loaders.base import (
    DocumentLoaderError,
    DocumentLoaderProtocol,
    ExtractedBlock,
    ExtractedDocument,
)


class TextDocumentLoader(DocumentLoaderProtocol):
    """Extracts structured blocks from plain text and Markdown files, preserving headings."""

    def load(self, file_path: Path) -> ExtractedDocument:
        if not file_path.is_file():
            raise DocumentLoaderError(f"Text file not found: {file_path}")

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = file_path.read_text(encoding="latin-1")
            except Exception as e:
                raise DocumentLoaderError(f"Unable to decode text file '{file_path}': {e}") from e

        # Normalize carriage returns
        normalized = content.replace("\r\n", "\n").replace("\r", "\n")
        raw_paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]

        blocks: list[ExtractedBlock] = []
        current_section = "Document Header"
        total_chars = 0

        for idx, para in enumerate(raw_paragraphs):
            # Check for Markdown heading (e.g. # Heading, ## Section)
            heading_match = re.match(r"^#{1,6}\s+(.*)", para)
            if heading_match:
                current_section = heading_match.group(1).strip()

            locator = {
                "page": 1,
                "section": current_section,
                "paragraph": idx + 1,
            }
            blocks.append(ExtractedBlock(text=para, locator=locator))
            total_chars += len(para)

        return ExtractedDocument(
            blocks=blocks,
            page_count=1,
            is_scanned=False,
            total_characters=total_chars,
            metadata={"format": file_path.suffix.lower()},
        )
