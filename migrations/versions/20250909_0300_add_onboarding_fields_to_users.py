"""add onboarding fields to users

Revision ID: 20250909_0300_add_onboarding
Revises: 20250904_1715_add_agent_workflows
Create Date: 2025-09-09 03:00:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250909_0300_add_onboarding'
down_revision = '20250909_0310_merge_heads'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('onboarding_completed', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('onboarding_data', sa.JSON(), nullable=True))

    # Backfill default False where NULL
    op.execute("UPDATE users SET onboarding_completed = FALSE WHERE onboarding_completed IS NULL")


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('onboarding_data')
        batch_op.drop_column('onboarding_completed')
