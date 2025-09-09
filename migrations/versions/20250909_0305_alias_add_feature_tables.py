"""Alias missing add_feature_tables revision

This creates a no-op revision with id 'add_feature_tables' so that
subsequent migrations referencing it (e.g., add_enterprise_features)
resolve correctly. Original changes already applied manually.

Revision ID: add_feature_tables
Revises: 20250103_1500_add_feature_tables
Create Date: 2025-09-09 03:05:00
"""
from alembic import op
import sqlalchemy as sa  # noqa: F401

revision = 'add_feature_tables'
down_revision = '20250103_1500_add_feature_tables'
branch_labels = None
depends_on = None


def upgrade():
    # No-op (acts as alias placeholder)
    pass


def downgrade():
    # No-op
    pass
