"""Unit and integration tests for document loaders and chunker."""

from pathlib import Path

import docx
import pytest
from atlas_contracts import DocumentStatus
from ingestion_service.chunker import StructureAwareChunker
from ingestion_service.loaders import (
    DocxDocumentLoader,
    PdfDocumentLoader,
    TextDocumentLoader,
)
from ingestion_service.loaders.base import ExtractedBlock
from ingestion_service.pipeline import IngestionPipeline
from ingestion_service.storage import LocalDocumentStorage
from pypdf import PdfWriter


def test_text_loader(tmp_path: Path):
    sample_text = "# Overview\nThis is the first paragraph.\n\n## Section 2\nThis is paragraph two."
    file_path = tmp_path / "sample.txt"
    file_path.write_text(sample_text, encoding="utf-8")

    loader = TextDocumentLoader()
    doc = loader.load(file_path)

    assert doc.page_count == 1
    assert doc.is_scanned is False
    assert len(doc.blocks) >= 2
    assert doc.blocks[0].locator.get("section") == "Overview"


def test_pdf_loader(tmp_path: Path):
    # Generate in-memory PDF using pypdf
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    # Add text annotation or text if writer supports, otherwise test basic load
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, "wb") as f:
        writer.write(f)

    loader = PdfDocumentLoader()
    doc = loader.load(pdf_path)
    assert doc.page_count == 1
    # Blank page detected as scanned or no text
    assert doc.is_scanned is True


def test_docx_loader(tmp_path: Path):
    doc = docx.Document()
    doc.add_heading("Architecture", level=1)
    doc.add_paragraph("ATLAS is a research intelligence system.")
    docx_path = tmp_path / "test.docx"
    doc.save(str(docx_path))

    loader = DocxDocumentLoader()
    extracted = loader.load(docx_path)
    assert extracted.is_scanned is False
    assert len(extracted.blocks) >= 1
    assert extracted.blocks[0].locator.get("section") == "Architecture"


def test_chunker():
    from uuid import uuid4

    chunker = StructureAwareChunker(target_chunk_size=100, chunk_overlap=20)
    blocks = [
        ExtractedBlock(
            text="Block 1 text that is relatively long for testing chunk size.", locator={"page": 1}
        ),
        ExtractedBlock(text="Block 2 text that should spill into next chunk.", locator={"page": 2}),
    ]
    doc_id = uuid4()
    chunks = chunker.chunk_blocks(document_id=doc_id, blocks=blocks)
    assert len(chunks) >= 1
    assert all(c.document_id == doc_id for c in chunks)
    assert all(c.content_hash is not None for c in chunks)


@pytest.mark.anyio
async def test_ingestion_pipeline(tmp_path: Path):
    storage = LocalDocumentStorage(base_directory=tmp_path / "storage")
    pipeline = IngestionPipeline(storage=storage)

    content = b"# Document Title\n\nParagraph text for research testing."
    result, chunks = await pipeline.process_file(
        tenant_id="test_tenant",
        filename="research.md",
        content=content,
    )

    assert result.status == DocumentStatus.COMPLETED
    assert result.chunk_count == len(chunks)
    assert result.byte_size == len(content)
