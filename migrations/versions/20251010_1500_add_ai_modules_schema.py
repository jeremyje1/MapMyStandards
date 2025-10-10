"""Introduce AI module core tables and pgvector support

Revision ID: 20251010_1500_add_ai_modules_schema
Revises: 20250909_0310_merge_heads
Create Date: 2025-10-10 15:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20251010_1500_add_ai_modules_schema"
down_revision = "20250909_0310_merge_heads"
branch_labels = None
depends_on = None


VECTOR = getattr(postgresql, "VECTOR", None)
if VECTOR is None:
    try:
        from pgvector.sqlalchemy import Vector  # type: ignore
    except Exception:  # pragma: no cover - fallback for environments without pgvector package
        Vector = None
else:  # pragma: no cover - prefer native dialect when available
    Vector = VECTOR

def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "citext"')

    op.create_table(
        "orgs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "app_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", postgresql.CITEXT(), nullable=False, unique=True),
        sa.Column("display_name", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("sha256_hex", sa.Text(), nullable=False),
        sa.Column("author", sa.Text()),
        sa.Column("source_system", sa.Text()),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("app_users.id")),
        sa.Column("uploaded_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    chunk_embedding_type = Vector(1536) if Vector is not None else sa.LargeBinary()

    op.create_table(
        "artifact_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", chunk_embedding_type),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "standards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("standard_set", sa.Text(), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("body", sa.Text()),
        sa.Column("level", sa.Integer()),
        sa.Column("parent_code", sa.Text()),
        sa.Column("version", sa.Text()),
        sa.Column("source_url", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "standards_graph_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("standard_set", sa.Text(), nullable=False),
        sa.Column("from_code", sa.Text(), nullable=False),
        sa.Column("to_code", sa.Text(), nullable=False),
        sa.Column("rel_type", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "evidence_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("standard_set", sa.Text(), nullable=False),
        sa.Column("standard_code", sa.Text(), nullable=False),
        sa.Column("score", sa.Numeric(5, 4), nullable=False),
        sa.Column("evidence_spans", postgresql.JSONB()),
        sa.Column("rationale", sa.Text()),
        sa.Column("evidence_trust", sa.Numeric(5, 4)),
        sa.Column("citations", postgresql.JSONB()),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "crosswalk_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("from_set", sa.Text(), nullable=False),
        sa.Column("from_code", sa.Text(), nullable=False),
        sa.Column("to_set", sa.Text(), nullable=False),
        sa.Column("to_code", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("rationale", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "trust_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("freshness", sa.Numeric(5, 4), nullable=False),
        sa.Column("authenticity", sa.Numeric(5, 4), nullable=False),
        sa.Column("redundancy", sa.Numeric(5, 4), nullable=False),
        sa.Column("citation_density", sa.Numeric(5, 4), nullable=False),
        sa.Column("trust", sa.Numeric(5, 4), nullable=False),
        sa.Column("explanation", sa.Text()),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("style", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("issues", postgresql.JSONB()),
        sa.Column("checked_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "risk_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("standard_set", sa.Text(), nullable=False),
        sa.Column("coverage", sa.Numeric(5, 4), nullable=False),
        sa.Column("risk_index", sa.Numeric(5, 4), nullable=False),
        sa.Column("gaps", postgresql.JSONB()),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("artifacts_org_idx", "artifacts", ["org_id"])
    op.create_index("artifacts_org_sha_idx", "artifacts", ["org_id", "sha256_hex"], unique=True)
    op.create_index("chunks_unique_idx", "artifact_chunks", ["artifact_id", "page", "chunk_index"], unique=True)
    op.create_index("chunks_embedding_idx", "artifact_chunks", ["embedding"], postgresql_using="ivfflat", postgresql_with={"lists": 100})
    op.create_index("standards_unique_idx", "standards", ["standard_set", "code"], unique=True)
    op.create_index("standards_set_idx", "standards", ["standard_set"])
    op.create_index("sgraph_from_idx", "standards_graph_edges", ["standard_set", "from_code"])
    op.create_index("sgraph_to_idx", "standards_graph_edges", ["standard_set", "to_code"])
    op.create_index("evlinks_lookup_idx", "evidence_links", ["org_id", "standard_set", "standard_code"])
    op.create_index("evlinks_artifact_idx", "evidence_links", ["artifact_id"])
    op.create_index(
        "evlinks_unique_idx",
        "evidence_links",
        ["org_id", "standard_set", "standard_code", "artifact_id"],
        unique=True,
    )
    op.create_index("crosswalk_from_idx", "crosswalk_edges", ["from_set", "from_code"])
    op.create_index("crosswalk_to_idx", "crosswalk_edges", ["to_set", "to_code"])
    op.create_index(
        "crosswalk_unique_idx",
        "crosswalk_edges",
        ["from_set", "from_code", "to_set", "to_code"],
        unique=True,
    )
    op.create_index("trust_artifact_idx", "trust_signals", ["artifact_id"])
    op.create_index("citations_artifact_idx", "citations", ["artifact_id"])
    op.create_index("risk_lookup_idx", "risk_snapshots", ["org_id", "standard_set", "computed_at"])


def downgrade():  # pragma: no cover - irreversible in production
    op.drop_index("risk_lookup_idx", table_name="risk_snapshots")
    op.drop_table("risk_snapshots")
    op.drop_index("citations_artifact_idx", table_name="citations")
    op.drop_table("citations")
    op.drop_index("trust_artifact_idx", table_name="trust_signals")
    op.drop_table("trust_signals")
    op.drop_index("crosswalk_to_idx", table_name="crosswalk_edges")
    op.drop_index("crosswalk_from_idx", table_name="crosswalk_edges")
    op.drop_index("crosswalk_unique_idx", table_name="crosswalk_edges")
    op.drop_table("crosswalk_edges")
    op.drop_index("evlinks_artifact_idx", table_name="evidence_links")
    op.drop_index("evlinks_lookup_idx", table_name="evidence_links")
    op.drop_index("evlinks_unique_idx", table_name="evidence_links")
    op.drop_table("evidence_links")
    op.drop_index("sgraph_to_idx", table_name="standards_graph_edges")
    op.drop_index("sgraph_from_idx", table_name="standards_graph_edges")
    op.drop_table("standards_graph_edges")
    op.drop_index("standards_set_idx", table_name="standards")
    op.drop_index("standards_unique_idx", table_name="standards")
    op.drop_table("standards")
    op.drop_index("chunks_embedding_idx", table_name="artifact_chunks")
    op.drop_index("chunks_unique_idx", table_name="artifact_chunks")
    op.drop_table("artifact_chunks")
    op.drop_index("artifacts_org_sha_idx", table_name="artifacts")
    op.drop_index("artifacts_org_idx", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_table("app_users")
    op.drop_table("orgs")

    op.execute('DROP EXTENSION IF EXISTS "citext"')
    op.execute('DROP EXTENSION IF EXISTS "vector"')
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
