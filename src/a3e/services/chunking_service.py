"""Artifact chunking utilities for EvidenceMapper pipeline."""

from __future__ import annotations

import asyncio
import io
import logging
import re
from dataclasses import dataclass
from typing import List

from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    page: int
    chunk_index: int
    content: str


class ArtifactChunker:
    """Convert binary artifacts into text chunks with page provenance."""

    def __init__(self, max_chars: int = 1600, overlap: int = 200):
        self.max_chars = max_chars
        self.overlap = overlap

    async def chunk(self, blob: bytes, mime_type: str) -> List[Chunk]:
        return await asyncio.to_thread(self._chunk_sync, blob, mime_type)

    # ---------------------------------------------------------------------
    def _chunk_sync(self, blob: bytes, mime_type: str) -> List[Chunk]:
        mime = (mime_type or "").lower()
        if "pdf" in mime:
            return self._chunk_pdf(blob)
        if "word" in mime or "docx" in mime:
            return self._chunk_docx(blob)
        if mime.startswith("text/") or mime.endswith("markdown") or mime.endswith("plain"):
            return self._chunk_text(blob)
        # Fallback: treat as text
        logger.warning("Unsupported mime '%s', treating as plain text for chunking", mime_type)
        return self._chunk_text(blob)

    # ------------------------------------------------------------------
    def _chunk_pdf(self, blob: bytes) -> List[Chunk]:
        reader = PdfReader(io.BytesIO(blob))
        chunks: List[Chunk] = []
        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as exc:  # pragma: no cover - pypdf edge cases
                logger.warning("Failed to extract text from page %s: %s", page_idx, exc)
                text = ""
            chunks.extend(self._split_text(text, page_idx, 0))
        return chunks

    def _chunk_docx(self, blob: bytes) -> List[Chunk]:
        document = Document(io.BytesIO(blob))
        text = "\n".join(p.text for p in document.paragraphs if p.text)
        return self._split_text(text, page=1, starting_index=0)

    def _chunk_text(self, blob: bytes) -> List[Chunk]:
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError:
            text = blob.decode("utf-16", errors="ignore")
        return self._split_text(text, page=1, starting_index=0)

    # ------------------------------------------------------------------
    def _split_text(self, text: str, page: int, starting_index: int) -> List[Chunk]:
        cleaned = self._normalize(text)
        if not cleaned:
            return []

        segments: List[Chunk] = []
        start = 0
        chunk_index = starting_index
        length = len(cleaned)

        while start < length:
            end = min(length, start + self.max_chars)
            segment = cleaned[start:end].strip()
            if segment:
                segments.append(Chunk(page=page, chunk_index=chunk_index, content=segment))
                chunk_index += 1
            if end == length:
                break
            start = max(end - self.overlap, start + 1)

        return segments

    @staticmethod
    def _normalize(text: str) -> str:
        # Collapse whitespace and control characters while preserving paragraphs
        text = text.replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[\t\u00A0]+", " ", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()
