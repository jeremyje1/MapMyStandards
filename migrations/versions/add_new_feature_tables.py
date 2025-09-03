"""Add org charts, scenarios, and powerbi configs tables

Revision ID: add_new_tables
Revises: 
Create Date: 2025-01-03 14:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_new_tables'
down_revision = '93dac6dcdc1a'
branch_labels = None
depends_on = None


def upgrade():
    # Create org_charts table
    op.create_table('org_charts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('chart_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_org_charts_user_id'), 'org_charts', ['user_id'], unique=False)

    # Create scenarios table
    op.create_table('scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scenario_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scenarios_user_id'), 'scenarios', ['user_id'], unique=False)

    # Create powerbi_configs table
    op.create_table('powerbi_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('workspace_id', sa.String(length=255), nullable=False),
        sa.Column('report_id', sa.String(length=255), nullable=False),
        sa.Column('config_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_powerbi_configs_user_id'), 'powerbi_configs', ['user_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_powerbi_configs_user_id'), table_name='powerbi_configs')
    op.drop_table('powerbi_configs')
    
    op.drop_index(op.f('ix_scenarios_user_id'), table_name='scenarios')
    op.drop_table('scenarios')
    
    op.drop_index(op.f('ix_org_charts_user_id'), table_name='org_charts')
    op.drop_table('org_charts')
