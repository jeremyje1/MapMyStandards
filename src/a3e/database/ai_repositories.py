"""Async SQLAlchemy data-access helpers for the AI module tables."""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .ai_models import (
    AppUser,
    Artifact,
    ArtifactChunk,
    Citation,
    CrosswalkEdge,
    EvidenceLink,
    Org,
    RiskSnapshot,
    StandardClause,
    StandardsGraphEdge,
    TrustSignal,
)


class OrgRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, org_id: UUID) -> Optional[Org]:
        result = await self.session.execute(
            select(Org).options(joinedload(Org.artifacts)).where(Org.id == org_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, *, org_id: Optional[UUID], name: str) -> Org:
        values = {"name": name}
        if org_id is not None:
            values["id"] = org_id

        stmt = pg_insert(Org).values(values)
        stmt = stmt.on_conflict_do_update(index_elements=[Org.id], set_={"name": name})

        await self.session.execute(stmt)
        await self.session.commit()

        identifier = org_id
        if identifier is None:
            result = await self.session.execute(select(Org).where(Org.name == name).limit(1))
            return result.scalar_one()
        return await self.get(identifier)


class AppUserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> Optional[AppUser]:
        result = await self.session.execute(select(AppUser).where(AppUser.email == email))
        return result.scalar_one_or_none()

    async def create(self, *, org_id: UUID, email: str, display_name: Optional[str] = None) -> AppUser:
        user = AppUser(org_id=org_id, email=email, display_name=display_name)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user


class ArtifactRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, artifact_id: UUID) -> Optional[Artifact]:
        result = await self.session.execute(
            select(Artifact)
            .options(joinedload(Artifact.chunks))
            .where(Artifact.id == artifact_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, artifact: Artifact) -> Artifact:
        merged = await self.session.merge(artifact)
        await self.session.commit()
        return merged

    async def replace_chunks(self, artifact_id: UUID, chunks: Sequence[ArtifactChunk]) -> None:
        await self.session.execute(delete(ArtifactChunk).where(ArtifactChunk.artifact_id == artifact_id))
        for chunk in chunks:
            chunk.artifact_id = artifact_id
            self.session.add(chunk)
        await self.session.commit()

    async def vector_search(self, *, artifact_id: Optional[UUID], embedding: Sequence[float], top_k: int) -> List[dict]:
        if artifact_id:
            filter_clause = "artifact_id = :artifact_id"
        else:
            filter_clause = "TRUE"

        query = text(
            """
            SELECT
                artifact_id,
                page,
                chunk_index,
                content,
                1 - (embedding <=> :query_embedding::vector) AS score
            FROM artifact_chunks
            WHERE {filter_clause}
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :top_k
            """.format(filter_clause=filter_clause)
        )

        params = {
            "query_embedding": self._vector_literal(embedding),
            "top_k": top_k,
        }
        if artifact_id:
            params["artifact_id"] = artifact_id

        result = await self.session.execute(query, params)
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]

    @staticmethod
    def _vector_literal(values: Sequence[float]) -> str:
        formatted = ",".join(f"{float(v):.8f}" for v in values)
        return f"[{formatted}]"


class EvidenceLinkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_links(self, links: Iterable[EvidenceLink]) -> None:
        for link in links:
            stmt = pg_insert(EvidenceLink).values(
                id=link.id,
                org_id=link.org_id,
                artifact_id=link.artifact_id,
                standard_set=link.standard_set,
                standard_code=link.standard_code,
                score=link.score,
                evidence_spans=link.evidence_spans,
                rationale=link.rationale,
                evidence_trust=link.evidence_trust,
                citations=link.citations_payload,
            ).on_conflict_do_update(
                index_elements=[EvidenceLink.org_id, EvidenceLink.standard_set, EvidenceLink.standard_code, EvidenceLink.artifact_id],
                set_={
                    "score": link.score,
                    "evidence_spans": link.evidence_spans,
                    "rationale": link.rationale,
                    "evidence_trust": link.evidence_trust,
                    "citations": link.citations_payload,
                    "computed_at": func.now(),
                },
            )
            await self.session.execute(stmt)
        await self.session.commit()

    async def get_latest(self, *, org_id: UUID, standard_set: str) -> List[EvidenceLink]:
        result = await self.session.execute(
            select(EvidenceLink)
            .where(EvidenceLink.org_id == org_id, EvidenceLink.standard_set == standard_set)
            .order_by(EvidenceLink.score.desc())
        )
        return list(result.scalars())


class TrustSignalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def record(self, signal: TrustSignal) -> TrustSignal:
        merged = await self.session.merge(signal)
        await self.session.commit()
        return merged

    async def latest_for_artifact(self, artifact_id: UUID) -> Optional[TrustSignal]:
        result = await self.session.execute(
            select(TrustSignal)
            .where(TrustSignal.artifact_id == artifact_id)
            .order_by(TrustSignal.computed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class CitationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, citation: Citation) -> Citation:
        merged = await self.session.merge(citation)
        await self.session.commit()
        return merged

    async def latest_for_artifact(self, artifact_id: UUID) -> Optional[Citation]:
        result = await self.session.execute(
            select(Citation)
            .where(Citation.artifact_id == artifact_id)
            .order_by(Citation.checked_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class CrosswalkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_pairs(self, *, from_set: str, to_set: str) -> List[CrosswalkEdge]:
        result = await self.session.execute(
            select(CrosswalkEdge)
            .where(CrosswalkEdge.from_set == from_set, CrosswalkEdge.to_set == to_set)
            .order_by(CrosswalkEdge.confidence.desc())
        )
        return list(result.scalars())

    async def bulk_upsert(self, rows: Iterable[CrosswalkEdge]) -> None:
        for row in rows:
            stmt = pg_insert(CrosswalkEdge).values(
                id=row.id,
                from_set=row.from_set,
                from_code=row.from_code,
                to_set=row.to_set,
                to_code=row.to_code,
                confidence=row.confidence,
                rationale=row.rationale,
            ).on_conflict_do_update(
                index_elements=[CrosswalkEdge.from_set, CrosswalkEdge.from_code, CrosswalkEdge.to_set, CrosswalkEdge.to_code],
                set_={"confidence": row.confidence, "rationale": row.rationale, "created_at": func.now()},
            )
            await self.session.execute(stmt)
        await self.session.commit()


class StandardsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_clauses(self, clauses: Iterable[StandardClause]) -> None:
        for clause in clauses:
            stmt = pg_insert(StandardClause).values(
                id=clause.id,
                standard_set=clause.standard_set,
                code=clause.code,
                title=clause.title,
                body=clause.body,
                level=clause.level,
                parent_code=clause.parent_code,
                version=clause.version,
                source_url=clause.source_url,
            ).on_conflict_do_update(
                index_elements=[StandardClause.standard_set, StandardClause.code],
                set_={
                    "title": clause.title,
                    "body": clause.body,
                    "level": clause.level,
                    "parent_code": clause.parent_code,
                    "version": clause.version,
                    "source_url": clause.source_url,
                    "created_at": func.now(),
                },
            )
            await self.session.execute(stmt)
        await self.session.commit()

    async def fetch_graph(self, standard_set: str) -> dict:
        nodes_result = await self.session.execute(
            select(StandardClause).where(StandardClause.standard_set == standard_set)
        )
        edges_result = await self.session.execute(
            select(StandardsGraphEdge).where(StandardsGraphEdge.standard_set == standard_set)
        )
        return {
            "nodes": [node for node in nodes_result.scalars()],
            "edges": [edge for edge in edges_result.scalars()],
        }

    async def list_clauses(self, standard_set: str) -> List[StandardClause]:
        result = await self.session.execute(
            select(StandardClause).where(StandardClause.standard_set == standard_set)
        )
        return list(result.scalars())


class RiskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_snapshot(self, snapshot: RiskSnapshot) -> RiskSnapshot:
        merged = await self.session.merge(snapshot)
        await self.session.commit()
        return merged

    async def latest(self, *, org_id: UUID, standard_set: str) -> Optional[RiskSnapshot]:
        result = await self.session.execute(
            select(RiskSnapshot)
            .where(RiskSnapshot.org_id == org_id, RiskSnapshot.standard_set == standard_set)
            .order_by(RiskSnapshot.computed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
