"""Merge multiple heads into single lineage

Revision ID: 20250909_0310_merge_heads
Revises: add_agent_workflows, add_enterprise_features, add_new_tables
Create Date: 2025-09-09 03:10:00
"""
from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

revision = '20250909_0310_merge_heads'
down_revision = ('add_agent_workflows', 'add_enterprise_features', 'add_new_tables')
branch_labels = None
depends_on = None


def upgrade():
    # No-op merge
    pass


def downgrade():
    # Can't unmerge easily; no-op
    pass
