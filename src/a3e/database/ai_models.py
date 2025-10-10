"""SQLAlchemy models for the AI module schema (orgs, artifacts, standards, etc.)."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID, CITEXT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

try:  # pragma: no cover - optional dependency
    from pgvector.sqlalchemy import Vector as PGVector  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    PGVector = None


class AIModuleBase(DeclarativeBase):
    pass


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


VectorColumn = PGVector if PGVector is not None else Text  # Fallback for local dev without pgvector


class Org(AIModuleBase):
    __tablename__ = "orgs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    users: Mapped[List["AppUser"]] = relationship(back_populates="org", cascade="all, delete-orphan")
    artifacts: Mapped[List["Artifact"]] = relationship(back_populates="org", cascade="all, delete-orphan")
    evidence_links: Mapped[List["EvidenceLink"]] = relationship(back_populates="org", cascade="all, delete-orphan")
    risk_snapshots: Mapped[List["RiskSnapshot"]] = relationship(back_populates="org", cascade="all, delete-orphan")


class AppUser(AIModuleBase):
    __tablename__ = "app_users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    email: Mapped[str] = mapped_column(CITEXT(), unique=True, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org: Mapped[Org] = relationship(back_populates="users")
    uploaded_artifacts: Mapped[List["Artifact"]] = relationship(back_populates="uploader")


class Artifact(AIModuleBase):
    __tablename__ = "artifacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    sha256_hex: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[Optional[str]] = mapped_column(Text)
    source_system: Mapped[Optional[str]] = mapped_column(Text)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("app_users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org: Mapped[Org] = relationship(back_populates="artifacts")
    uploader: Mapped[Optional[AppUser]] = relationship(back_populates="uploaded_artifacts")
    chunks: Mapped[List["ArtifactChunk"]] = relationship(back_populates="artifact", cascade="all, delete-orphan")
    evidence_links: Mapped[List["EvidenceLink"]] = relationship(back_populates="artifact", cascade="all, delete-orphan")
    trust_signals: Mapped[List["TrustSignal"]] = relationship(back_populates="artifact", cascade="all, delete-orphan")
    citations: Mapped[List["Citation"]] = relationship(back_populates="artifact", cascade="all, delete-orphan")


class ArtifactChunk(AIModuleBase):
    __tablename__ = "artifact_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    artifact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False)
    page: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[object]] = mapped_column(VectorColumn, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    artifact: Mapped[Artifact] = relationship(back_populates="chunks")


class StandardClause(AIModuleBase):
    __tablename__ = "standards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    standard_set: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(Text)
    body: Mapped[Optional[str]] = mapped_column(Text)
    level: Mapped[Optional[int]] = mapped_column(Integer)
    parent_code: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class StandardsGraphEdge(AIModuleBase):
    __tablename__ = "standards_graph_edges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    standard_set: Mapped[str] = mapped_column(Text, nullable=False)
    from_code: Mapped[str] = mapped_column(Text, nullable=False)
    to_code: Mapped[str] = mapped_column(Text, nullable=False)
    rel_type: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EvidenceLink(AIModuleBase):
    __tablename__ = "evidence_links"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    artifact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False)
    standard_set: Mapped[str] = mapped_column(Text, nullable=False)
    standard_code: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    evidence_spans: Mapped[Optional[dict]] = mapped_column(JSONB)
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    evidence_trust: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    citations_payload: Mapped[Optional[dict]] = mapped_column("citations", JSONB)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org: Mapped[Org] = relationship(back_populates="evidence_links")
    artifact: Mapped[Artifact] = relationship(back_populates="evidence_links")


class CrosswalkEdge(AIModuleBase):
    __tablename__ = "crosswalk_edges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    from_set: Mapped[str] = mapped_column(Text, nullable=False)
    from_code: Mapped[str] = mapped_column(Text, nullable=False)
    to_set: Mapped[str] = mapped_column(Text, nullable=False)
    to_code: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TrustSignal(AIModuleBase):
    __tablename__ = "trust_signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    artifact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False)
    freshness: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    authenticity: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    redundancy: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    citation_density: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    trust: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    artifact: Mapped[Artifact] = relationship(back_populates="trust_signals")


class Citation(AIModuleBase):
    __tablename__ = "citations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    artifact_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False)
    style: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    issues: Mapped[Optional[dict]] = mapped_column(JSONB)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    artifact: Mapped[Artifact] = relationship(back_populates="citations")


class RiskSnapshot(AIModuleBase):
    __tablename__ = "risk_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False)
    standard_set: Mapped[str] = mapped_column(Text, nullable=False)
    coverage: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    risk_index: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    gaps: Mapped[Optional[dict]] = mapped_column(JSONB)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    org: Mapped[Org] = relationship(back_populates="risk_snapshots")
