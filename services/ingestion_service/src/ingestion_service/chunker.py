"""Structure-aware text chunker preserving page and section provenance."""

import hashlib
from typing import Any
from uuid import UUID

from atlas_contracts import DocumentChunkDTO

from ingestion_service.loaders.base import ExtractedBlock


class StructureAwareChunker:
    """Chunks structured text blocks enforcing size and overlap bounds while preserving locators."""

    def __init__(self, target_chunk_size: int = 800, chunk_overlap: int = 150) -> None:
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_blocks(
        self,
        document_id: UUID,
        blocks: list[ExtractedBlock],
    ) -> list[DocumentChunkDTO]:
        if not blocks:
            return []

        chunks: list[DocumentChunkDTO] = []
        current_text_parts: list[str] = []
        current_locators: list[dict[str, Any]] = []
        current_char_count = 0
        chunk_index = 0

        for block in blocks:
            block_text = block.text.strip()
            if not block_text:
                continue

            # If adding this block exceeds target size and we have accumulated content, flush chunk
            if current_char_count + len(block_text) > self.target_chunk_size and current_text_parts:
                chunk = self._build_chunk(
                    document_id, chunk_index, current_text_parts, current_locators
                )
                chunks.append(chunk)
                chunk_index += 1

                # Calculate overlap: retain trailing blocks that fit within overlap limit
                retained_parts: list[str] = []
                retained_locators: list[dict[str, Any]] = []
                retained_count = 0

                for part, loc in zip(
                    reversed(current_text_parts), reversed(current_locators), strict=False
                ):
                    if retained_count + len(part) <= self.chunk_overlap:
                        retained_parts.insert(0, part)
                        retained_locators.insert(0, loc)
                        retained_count += len(part)
                    else:
                        break

                current_text_parts = retained_parts
                current_locators = retained_locators
                current_char_count = retained_count

            current_text_parts.append(block_text)
            current_locators.append(block.locator)
            current_char_count += len(block_text)

        # Flush final remaining chunk
        if current_text_parts:
            chunk = self._build_chunk(
                document_id, chunk_index, current_text_parts, current_locators
            )
            chunks.append(chunk)

        return chunks

    def _build_chunk(
        self,
        document_id: UUID,
        chunk_index: int,
        parts: list[str],
        locators: list[dict[str, Any]],
    ) -> DocumentChunkDTO:
        combined_text = "\n\n".join(parts)
        content_hash = hashlib.sha256(combined_text.encode("utf-8")).hexdigest()

        # Merge locators (e.g. pages spanned, sections referenced)
        pages = sorted({loc["page"] for loc in locators if "page" in loc})
        sections = list(dict.fromkeys(loc["section"] for loc in locators if "section" in loc))

        merged_locator: dict[str, Any] = {}
        if pages:
            merged_locator["page"] = pages[0]
            if len(pages) > 1:
                merged_locator["page_end"] = pages[-1]
        if sections:
            merged_locator["section"] = sections[0]
            if len(sections) > 1:
                merged_locator["sections"] = sections

        return DocumentChunkDTO(
            document_id=document_id,
            chunk_index=chunk_index,
            text=combined_text,
            locator=merged_locator,
            content_hash=content_hash,
            character_count=len(combined_text),
        )
