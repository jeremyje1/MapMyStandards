"""Add org charts, scenarios, and powerbi configs tables

Revision ID: 20250103_1500_add_feature_tables
Revises: 93dac6dcdc1a
Create Date: 2025-01-03 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250103_1500_add_feature_tables'
down_revision = '93dac6dcdc1a'
branch_labels = None
depends_on = None


def upgrade():
    # Tables already created manually, this migration just records the change
    pass


def downgrade():
    # Drop the tables
    op.drop_table('powerbi_configs')
    op.drop_table('scenarios')
    op.drop_table('org_charts')
