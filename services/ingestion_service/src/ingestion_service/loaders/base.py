"""Base models and protocols for document format loaders."""

from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, Field


class ExtractedBlock(BaseModel):
    """A logical extracted block of text carrying its provenance locator."""

    text: str = Field(min_length=1)
    locator: dict[str, Any] = Field(default_factory=dict)


class ExtractedDocument(BaseModel):
    """Normalized document representation containing extracted blocks and page metadata."""

    blocks: list[ExtractedBlock] = Field(default_factory=list)
    page_count: int = 1
    is_scanned: bool = False
    total_characters: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentLoaderError(RuntimeError):
    """Raised when document parsing or extraction fails."""

    pass


class DocumentLoaderProtocol(Protocol):
    """Interface implemented by format-specific document loaders."""

    def load(self, file_path: Path) -> ExtractedDocument: ...
