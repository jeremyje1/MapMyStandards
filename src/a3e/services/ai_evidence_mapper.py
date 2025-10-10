"""Evidence mapping orchestration for the new AI pipeline."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Sequence
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.models import EvidenceMapRequest, EvidenceMatch, EvidenceMapResponse, EvidenceSpan
from ..core.config import Settings
from ..database.ai_models import Artifact, ArtifactChunk, EvidenceLink, StandardClause
from ..database.ai_repositories import (
    ArtifactRepository,
    EvidenceLinkRepository,
    StandardsRepository,
)
from .chunking_service import ArtifactChunker, Chunk
from .embedding_service import EmbeddingService
from .storage_service import StorageService

logger = logging.getLogger(__name__)


@dataclass
class CandidateMatch:
    standard: StandardClause
    score: float
    chunk: dict
    embedding: Sequence[float]


class EvidenceMapperService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.chunker = ArtifactChunker()
        self.embedder = EmbeddingService(settings)
        self.storage = StorageService(settings)

    async def map(self, session: AsyncSession, payload: EvidenceMapRequest) -> EvidenceMapResponse:
        artifact_repo = ArtifactRepository(session)
        standards_repo = StandardsRepository(session)
        evidence_repo = EvidenceLinkRepository(session)

        artifact = await self._get_artifact(artifact_repo, payload.artifact_id)
        if artifact is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")

        await self._ensure_chunks(artifact_repo, artifact)
        standards = await standards_repo.list_clauses(payload.standard_set)
        if not standards:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Standards not found for set")

        standard_texts = [self._standard_text(clause) for clause in standards]
        try:
            standard_embeddings = await self.embedder.embed(standard_texts)
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Embedding provider failure")

        candidates = await self._score_candidates(
            artifact_repo=artifact_repo,
            artifact=artifact,
            standards=standards,
            embeddings=standard_embeddings,
            top_k=payload.top_k,
            threshold=payload.threshold,
        )

        candidates.sort(key=lambda c: c.score, reverse=True)
        selected = candidates[: payload.top_k]

        matches = [self._to_evidence_match(candidate, payload.explain) for candidate in selected]
        computed_at = datetime.utcnow()
        if selected:
            await evidence_repo.upsert_links(
                self._to_evidence_links(artifact, selected, computed_at)
            )

        return EvidenceMapResponse(
            artifact_id=str(artifact.id),
            matches=matches,
            computed_at=computed_at,
        )

    # ------------------------------------------------------------------
    async def _get_artifact(self, repo: ArtifactRepository, artifact_id: str) -> Artifact | None:
        try:
            return await repo.get(UUID(artifact_id))
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid artifact_id")

    async def _ensure_chunks(self, repo: ArtifactRepository, artifact: Artifact) -> None:
        needs_embedding = not artifact.chunks or any(chunk.embedding is None for chunk in artifact.chunks)
        if not needs_embedding:
            return

        if not artifact.storage_key:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact storage key missing")

        binary = await self.storage.get_file(artifact.storage_key)
        if not binary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact binary missing from storage")

        chunk_structs: List[Chunk] = await self.chunker.chunk(binary, artifact.mime_type or "text/plain")
        if not chunk_structs:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unable to extract text from artifact")

        chunk_texts = [chunk.content for chunk in chunk_structs]
        try:
            embeddings = await self.embedder.embed(chunk_texts)
        except Exception as exc:
            logger.error("Chunk embedding failed: %s", exc)
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Embedding provider failure")

        chunk_models = [
            ArtifactChunk(
                id=uuid4(),
                artifact_id=artifact.id,
                page=chunk.page,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                embedding=vector,
            )
            for chunk, vector in zip(chunk_structs, embeddings)
        ]
        await repo.replace_chunks(artifact.id, chunk_models)

    async def _score_candidates(
        self,
        artifact_repo: ArtifactRepository,
        artifact: Artifact,
        standards: List[StandardClause],
        embeddings: Sequence[Sequence[float]],
        top_k: int,
        threshold: float,
    ) -> List[CandidateMatch]:
        tasks = []
        for clause, embedding in zip(standards, embeddings):
            tasks.append(
                artifact_repo.vector_search(
                    artifact_id=artifact.id,
                    embedding=embedding,
                    top_k=max(1, top_k),
                )
            )
        results = await asyncio.gather(*tasks)

        candidates: List[CandidateMatch] = []
        for clause, embedding, result in zip(standards, embeddings, results):
            if not result:
                continue
            best = max(result, key=lambda row: row.get("score", 0.0))
            score = float(best.get("score") or 0.0)
            if score < threshold:
                continue
            candidates.append(CandidateMatch(standard=clause, score=score, chunk=best, embedding=embedding))
        return candidates

    @staticmethod
    def _standard_text(clause: StandardClause) -> str:
        parts = [clause.title or "", clause.body or ""]
        return "\n".join(part.strip() for part in parts if part)

    def _to_evidence_match(self, candidate: CandidateMatch, explain: bool) -> EvidenceMatch:
        chunk_text: str = candidate.chunk.get("content", "")
        rationale = None
        if explain and chunk_text:
            rationale = f"Top matching excerpt: {chunk_text[:240]}" + ("..." if len(chunk_text) > 240 else "")
        span = EvidenceSpan(
            page=int(candidate.chunk.get("page", 1)),
            start=0,
            end=min(len(chunk_text), 5000) if chunk_text else None,
        )
        return EvidenceMatch(
            standard_id=f"{candidate.standard.standard_set}.{candidate.standard.code}",
            score=round(candidate.score, 4),
            evidence_spans=[span],
            rationale=rationale,
            evidence_trust=0.75,
            citations=[{"type": "page", "value": span.page}],
        )

    def _to_evidence_links(
        self,
        artifact: Artifact,
        candidates: Sequence[CandidateMatch],
        computed_at: datetime,
    ) -> List[EvidenceLink]:
        links: List[EvidenceLink] = []
        for candidate in candidates:
            span = {
                "page": int(candidate.chunk.get("page", 1)),
                "start": 0,
                "end": len(candidate.chunk.get("content", "")),
            }
            links.append(
                EvidenceLink(
                    id=uuid4(),
                    org_id=artifact.org_id,
                    artifact_id=artifact.id,
                    standard_set=candidate.standard.standard_set,
                    standard_code=candidate.standard.code,
                    score=Decimal(str(round(candidate.score, 4))),
                    evidence_spans=[span],
                    rationale=(candidate.chunk.get("content") or "")[:240],
                    evidence_trust=Decimal("0.75"),
                    citations_payload=[{"type": "page", "value": span["page"]}],
                    computed_at=computed_at,
                )
            )
        return links
