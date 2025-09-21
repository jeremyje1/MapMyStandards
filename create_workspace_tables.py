"""Create workspace tables for team collaboration."""
import os
from sqlalchemy import create_engine, text

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://railway:Ja8eQoJqY0Ul5aZcbN7r@shinkansen.proxy.rlwy.net:28831/railway")

# Create engine
engine = create_engine(DATABASE_URL)

# SQL for creating tables
create_tables_sql = """
-- Create workspaces table
CREATE TABLE IF NOT EXISTS workspaces (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    institution_id VARCHAR(36),
    is_active BOOLEAN DEFAULT TRUE,
    allow_guest_access BOOLEAN DEFAULT FALSE,
    require_approval BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ
);

-- Create workspace_members association table
CREATE TABLE IF NOT EXISTS workspace_members (
    workspace_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'editor', 'viewer')),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    invited_by VARCHAR(36),
    invitation_accepted BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (workspace_id, user_id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (invited_by) REFERENCES users(id)
);

-- Create standard_workspaces table
CREATE TABLE IF NOT EXISTS standard_workspaces (
    id VARCHAR(36) PRIMARY KEY,
    standard_id VARCHAR(36) NOT NULL,
    workspace_id VARCHAR(36) NOT NULL,
    added_by VARCHAR(36),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    priority VARCHAR(20) DEFAULT 'medium',
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (added_by) REFERENCES users(id)
);

-- Create evidence_workspaces table
CREATE TABLE IF NOT EXISTS evidence_workspaces (
    id VARCHAR(36) PRIMARY KEY,
    evidence_id VARCHAR(36) NOT NULL,
    workspace_id VARCHAR(36) NOT NULL,
    added_by VARCHAR(36),
    added_at TIMESTAMPTZ DEFAULT NOW(),
    review_status VARCHAR(20) DEFAULT 'pending',
    reviewed_by VARCHAR(36),
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (added_by) REFERENCES users(id),
    FOREIGN KEY (reviewed_by) REFERENCES users(id)
);

-- Create workspace_invitations table
CREATE TABLE IF NOT EXISTS workspace_invitations (
    id VARCHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(36) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'editor', 'viewer')),
    invited_by VARCHAR(36),
    invitation_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending',
    accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (invited_by) REFERENCES users(id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_workspace_members_user ON workspace_members(user_id);
CREATE INDEX IF NOT EXISTS idx_workspace_members_workspace ON workspace_members(workspace_id);
CREATE INDEX IF NOT EXISTS idx_standard_workspaces_standard ON standard_workspaces(standard_id);
CREATE INDEX IF NOT EXISTS idx_standard_workspaces_workspace ON standard_workspaces(workspace_id);
CREATE INDEX IF NOT EXISTS idx_evidence_workspaces_evidence ON evidence_workspaces(evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_workspaces_workspace ON evidence_workspaces(workspace_id);
CREATE INDEX IF NOT EXISTS idx_workspace_invitations_token ON workspace_invitations(invitation_token);
CREATE INDEX IF NOT EXISTS idx_workspace_invitations_email ON workspace_invitations(email);
"""

def create_workspace_tables():
    """Create all workspace-related tables."""
    try:
        with engine.begin() as conn:
            # Execute the SQL
            conn.execute(text(create_tables_sql))
            print("✅ Workspace tables created successfully!")
            
            # Verify tables were created
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('workspaces', 'workspace_members', 'standard_workspaces', 
                                   'evidence_workspaces', 'workspace_invitations')
                ORDER BY table_name
            """))
            
            print("\nCreated tables:")
            for row in result:
                print(f"  - {row[0]}")
            
            # Check if we need to add relationship to institutions table
            inst_check = conn.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'institutions'
            """)).scalar()
            
            if inst_check > 0:
                # Add foreign key to institutions if table exists
                conn.execute(text("""
                    ALTER TABLE workspaces 
                    ADD CONSTRAINT fk_workspace_institution 
                    FOREIGN KEY (institution_id) 
                    REFERENCES institutions(id)
                    ON DELETE SET NULL
                """))
                print("  ✅ Added institution relationship")
            
    except Exception as e:
        print(f"❌ Error creating workspace tables: {e}")
        raise

if __name__ == "__main__":
    create_workspace_tables()