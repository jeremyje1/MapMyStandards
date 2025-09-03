#!/usr/bin/env python3
"""
Fix all get_db imports to use the new async database session pattern
"""

import os
import re

# Files that need to be updated
files_to_fix = [
    "src/a3e/api/routes/enterprise.py",
    "src/a3e/api/routes/enterprise_metrics.py",
    "src/a3e/api/routes/analytics.py", 
    "src/a3e/api/routes/powerbi.py",
    "src/a3e/services/analytics_service.py"
]

def fix_file(filepath):
    """Fix a single file's database imports and dependencies"""
    print(f"Fixing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace imports
    content = re.sub(
        r'from \.\.\.database import get_db',
        'from ...database.connection import db_manager',
        content
    )
    
    content = re.sub(
        r'from \.\.database import get_db',
        'from ..database.connection import db_manager',
        content
    )
    
    # Replace SQLAlchemy Session imports
    content = re.sub(
        r'from sqlalchemy.orm import Session',
        'from sqlalchemy.ext.asyncio import AsyncSession\nfrom typing import AsyncGenerator',
        content
    )
    
    # Add async session dependency if not present
    if 'async def get_db_session()' not in content:
        dependency_code = '''
# Dependency for async database session
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        yield session
'''
        # Find the router definition and add dependency before it
        router_match = re.search(r'router = APIRouter\(\)', content)
        if router_match:
            insert_pos = router_match.end()
            content = content[:insert_pos] + dependency_code + content[insert_pos:]
    
    # Replace database dependencies in function signatures
    content = re.sub(
        r'db: Session = Depends\(get_db\)',
        'db: AsyncSession = Depends(get_db_session)',
        content
    )
    
    # Fix TeamMember references to TeamInvitation 
    content = re.sub(
        r'TeamMember',
        'TeamInvitation',
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {filepath}")

def main():
    """Fix all files"""
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            fix_file(filepath)
        else:
            print(f"❌ File not found: {filepath}")
    
    print("✅ All files fixed!")

if __name__ == "__main__":
    main()
