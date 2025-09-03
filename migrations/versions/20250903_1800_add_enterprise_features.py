"""add enterprise features

Revision ID: add_enterprise_features
Revises: add_feature_tables
Create Date: 2025-09-03 18:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
import json

# revision identifiers, used by Alembic.
revision = 'add_enterprise_features'
down_revision = 'add_feature_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create teams table
    op.create_table('teams',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('max_users', sa.Integer(), nullable=True, default=10),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('subscription_tier', sa.String(), nullable=True, default='starter'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )
    
    # Create user_teams association table
    op.create_table('user_teams',
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, default='viewer'),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'team_id')
    )
    
    # Create team_invitations table
    op.create_table('team_invitations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('OWNER', 'ADMIN', 'MANAGER', 'VIEWER', name='userrole'), nullable=True),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('accepted', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('invited_by_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('changes', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_team_created', 'audit_logs', ['team_id', 'created_at'])
    op.create_index('ix_audit_logs_user_created', 'audit_logs', ['user_id', 'created_at'])
    
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('prefix', sa.String(), nullable=False),
        sa.Column('scopes', sa.JSON(), nullable=True),
        sa.Column('rate_limit', sa.Integer(), nullable=True, default=1000),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('created_by_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['team_id'], ['teams.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index('ix_api_keys_prefix', 'api_keys', ['prefix'])
    
    # Create session_security table
    op.create_table('session_security',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('session_token_hash', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('two_factor_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('trusted_device', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token_hash')
    )
    
    # Add team_id to existing tables
    op.add_column('org_charts', sa.Column('team_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_org_charts_team', 'org_charts', 'teams', ['team_id'], ['id'])
    
    op.add_column('scenarios', sa.Column('team_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_scenarios_team', 'scenarios', 'teams', ['team_id'], ['id'])
    
    op.add_column('powerbi_configs', sa.Column('team_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_powerbi_configs_team', 'powerbi_configs', 'teams', ['team_id'], ['id'])
    
    # Add team role to users for default team behavior
    op.add_column('users', sa.Column('default_team_id', sa.String(), nullable=True))
    op.create_foreign_key('fk_users_default_team', 'users', 'teams', ['default_team_id'], ['id'])


def downgrade():
    # Remove foreign keys and columns from existing tables
    op.drop_constraint('fk_users_default_team', 'users', type_='foreignkey')
    op.drop_column('users', 'default_team_id')
    
    op.drop_constraint('fk_powerbi_configs_team', 'powerbi_configs', type_='foreignkey')
    op.drop_column('powerbi_configs', 'team_id')
    
    op.drop_constraint('fk_scenarios_team', 'scenarios', type_='foreignkey')
    op.drop_column('scenarios', 'team_id')
    
    op.drop_constraint('fk_org_charts_team', 'org_charts', type_='foreignkey')
    op.drop_column('org_charts', 'team_id')
    
    # Drop new tables
    op.drop_table('session_security')
    op.drop_index('ix_api_keys_prefix', table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index('ix_audit_logs_user_created', table_name='audit_logs')
    op.drop_index('ix_audit_logs_team_created', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_table('team_invitations')
    op.drop_table('user_teams')
    op.drop_table('teams')
    
    # Drop enum type
    sa.Enum('OWNER', 'ADMIN', 'MANAGER', 'VIEWER', name='userrole').drop(op.get_bind(), checkfirst=True)
