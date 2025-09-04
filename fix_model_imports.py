#!/usr/bin/env python3
"""
Fix all model imports to use the correct sources after removing database/models.py
"""

import os
import re
from pathlib import Path

# Define the fixes needed
fixes = [
    # For files importing from database.models (relative imports)
    {
        'pattern': r'from \.\.database\.models import (.*)',
        'files': ['src/a3e/services/*.py'],
        'replacement': lambda m: fix_import(m.group(1))
    },
    {
        'pattern': r'from \.\.\.database\.models import (.*)',
        'files': ['src/a3e/api/routes/*.py'],
        'replacement': lambda m: fix_import(m.group(1))
    },
    # For files importing with absolute imports  
    {
        'pattern': r'from src\.a3e\.database\.models import (.*)',
        'files': ['**/*.py'],
        'replacement': lambda m: fix_absolute_import(m.group(1))
    }
]

def fix_import(import_list):
    """Fix relative imports based on what's being imported"""
    imports = [i.strip() for i in import_list.split(',')]
    
    user_imports = []
    enterprise_imports = []
    other_imports = []
    
    for imp in imports:
        if 'User' in imp and 'UserTeam' not in imp:
            user_imports.append(imp)
        elif any(model in imp for model in ['OrgChart', 'Scenario', 'PowerBIConfig', 'Team', 'AuditLog']):
            enterprise_imports.append(imp)
        else:
            other_imports.append(imp)
    
    result = []
    if user_imports:
        result.append(f"from ..models.user import {', '.join(user_imports)}")
    if enterprise_imports:
        result.append(f"from ..database.enterprise_models import {', '.join(enterprise_imports)}")
    if other_imports:
        # For other models, use database_schema
        result.append(f"from ..models.database_schema import {', '.join(other_imports)}")
    
    return '\n'.join(result)

def fix_absolute_import(import_list):
    """Fix absolute imports"""
    imports = [i.strip() for i in import_list.split(',')]
    
    user_imports = []
    enterprise_imports = []
    other_imports = []
    
    for imp in imports:
        if 'User' in imp and 'UserTeam' not in imp:
            user_imports.append(imp)
        elif any(model in imp for model in ['OrgChart', 'Scenario', 'PowerBIConfig', 'Team', 'AuditLog']):
            enterprise_imports.append(imp)
        else:
            other_imports.append(imp)
    
    result = []
    if user_imports:
        result.append(f"from src.a3e.models.user import {', '.join(user_imports)}")
    if enterprise_imports:
        result.append(f"from src.a3e.database.enterprise_models import {', '.join(enterprise_imports)}")
    if other_imports:
        result.append(f"from src.a3e.models.database_schema import {', '.join(other_imports)}")
    
    return '\n'.join(result)

def process_file(filepath, pattern, replacement):
    """Process a single file"""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original = content
    content = re.sub(pattern, replacement, content)
    
    if content != original:
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    base_dir = Path.cwd()
    fixed_files = []
    
    for fix in fixes:
        pattern = fix['pattern']
        replacement = fix['replacement']
        
        for file_pattern in fix['files']:
            for filepath in base_dir.glob(file_pattern):
                if filepath.is_file() and filepath.suffix == '.py':
                    if process_file(filepath, pattern, replacement):
                        fixed_files.append(str(filepath))
                        print(f"Fixed: {filepath}")
    
    print(f"\nTotal files fixed: {len(fixed_files)}")
    
if __name__ == "__main__":
    main()
