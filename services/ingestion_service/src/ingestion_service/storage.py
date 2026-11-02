"""Local filesystem storage adapter for uploaded research documents."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from ingestion_service.core.config import get_settings


class FileStorageError(RuntimeError):
    """Raised when file storage operations fail."""

    pass


@dataclass
class StoredFile:
    """Descriptor for a validated, stored document."""

    document_id: UUID
    filename: str
    file_path: Path
    storage_key: str
    content_hash: str
    byte_size: int


class LocalDocumentStorage:
    """Manages raw document persistence, validation, and SHA-256 verification."""

    def __init__(self, base_directory: Path | str | None = None) -> None:
        settings = get_settings()
        self._base_dir = Path(base_directory or settings.storage_dir).resolve()
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._max_size = settings.max_upload_size_bytes
        self._allowed_exts = set(settings.allowed_extensions)

    @property
    def base_dir(self) -> Path:
        return self._base_dir

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize raw filenames to prevent path traversal and unsafe characters."""
        clean_name = Path(filename).name
        safe = re.sub(r"[^\w.\-]", "_", clean_name)
        return safe or "document.bin"

    def compute_sha256(self, content: bytes) -> str:
        """Compute hex digest SHA-256 for a byte stream."""
        return hashlib.sha256(content).hexdigest()

    async def save_file(
        self,
        tenant_id: str,
        filename: str,
        content: bytes,
        document_id: UUID | None = None,
    ) -> StoredFile:
        """Validate and persist byte content to disk."""
        safe_name = self.sanitize_filename(filename)
        ext = Path(safe_name).suffix.lower()

        if self._allowed_exts and ext not in self._allowed_exts:
            raise ValueError(
                f"File extension '{ext}' is not permitted. Allowed: {sorted(self._allowed_exts)}"
            )

        if len(content) > self._max_size:
            raise ValueError(
                f"File size {len(content)} bytes exceeds maximum {self._max_size} bytes limit"
            )

        doc_id = document_id or uuid4()
        tenant_dir = self._base_dir / tenant_id
        tenant_dir.mkdir(parents=True, exist_ok=True)

        dest_path = tenant_dir / f"{doc_id}_{safe_name}"
        try:
            dest_path.write_bytes(content)
        except Exception as err:
            raise FileStorageError(f"Failed to persist file '{filename}': {err}") from err

        content_hash = self.compute_sha256(content)
        storage_key = f"{tenant_id}/{doc_id}_{safe_name}"

        return StoredFile(
            document_id=doc_id,
            filename=safe_name,
            file_path=dest_path,
            storage_key=storage_key,
            content_hash=content_hash,
            byte_size=len(content),
        )

    def read_file(self, path: Path) -> bytes:
        """Read file bytes from path."""
        if not path.is_file():
            raise FileStorageError(f"File not found at '{path}'")
        return path.read_bytes()

    def delete_file(self, path: Path) -> None:
        """Remove file if it exists, ignoring missing files."""
        try:
            if path.exists():
                path.unlink()
        except Exception as e:
            raise FileStorageError(f"Failed to delete file '{path}': {e}") from e


# Backward compatibility alias
LocalStorageService = LocalDocumentStorage
