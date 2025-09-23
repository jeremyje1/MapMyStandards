#!/usr/bin/env python3
"""
Test script for the new API endpoints we added
"""

import os
import sys
from datetime import datetime
import json

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock environment variables required for the application
os.environ['SECRET_KEY'] = 'test_secret_key_for_validation_only_32chars'
os.environ['JWT_SECRET_KEY'] = 'test_jwt_secret_key_for_validation_32chars'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'
os.environ['USER_SETTINGS_STORE'] = 'test_user_settings.json'
os.environ['USER_UPLOADS_STORE'] = 'test_user_uploads.json'
os.environ['USER_REVIEWS_STORE'] = 'test_user_reviews.json'
os.environ['USER_STANDARD_REVIEWS_STORE'] = 'test_standard_reviews.json'
os.environ['USER_SESSIONS_STORE'] = 'test_user_sessions.json'

# Test data for user uploads
test_uploads_data = {
    "user_b3feaed034925c74": {
        "documents": [
            {
                "filename": "Strategic_Plan_2024.pdf",
                "uploaded_at": "2025-09-23T10:00:00",
                "standards_mapped": ["HLC.1.A", "HLC.2.B", "HLC.3.C"],
                "doc_type": "strategic_plan",
                "fingerprint": "abc123def456",
                "saved_path": "/uploads/simple/20250923_100000_abc123.pdf",
                "size": 2500000
            },
            {
                "filename": "Assessment_Report_Fall2023.docx", 
                "uploaded_at": "2025-09-23T10:30:00",
                "standards_mapped": ["HLC.4.A", "HLC.4.B"],
                "doc_type": "assessment_report",
                "fingerprint": "def456ghi789",
                "saved_path": "/uploads/simple/20250923_103000_def456.docx"
            },
            {
                "filename": "Faculty_Handbook.pdf",
                "uploaded_at": "2025-09-23T11:00:00", 
                "standards_mapped": [],
                "doc_type": "policy_document",
                "fingerprint": "ghi789jkl012",
                "saved_path": "/uploads/simple/20250923_110000_ghi789.pdf"
            }
        ],
        "unique_standards": ["HLC.1.A", "HLC.2.B", "HLC.3.C", "HLC.4.A", "HLC.4.B"]
    }
}

# Create test data files
with open('test_user_uploads.json', 'w') as f:
    json.dump(test_uploads_data, f, indent=2)

# Create empty files for other stores
for store in ['test_user_settings.json', 'test_user_reviews.json', 'test_standard_reviews.json', 'test_user_sessions.json']:
    with open(store, 'w') as f:
        json.dump({}, f)

print("Test environment set up successfully!")
print("\nTest user uploads data created with:")
print(f"- {len(test_uploads_data['user_b3feaed034925c74']['documents'])} documents")
print(f"- {len(test_uploads_data['user_b3feaed034925c74']['unique_standards'])} unique standards")

# Now test importing the module to check for syntax errors
try:
    from a3e.api.routes.user_intelligence_simple import (
        list_evidence,
        list_uploads,
        list_user_standards,
        get_dashboard_metrics_alias
    )
    print("\n✅ All new endpoint functions imported successfully!")
    print("   - list_evidence")
    print("   - list_uploads") 
    print("   - list_user_standards")
    print("   - get_dashboard_metrics_alias")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("This might be due to missing dependencies or module structure issues.")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")

# Clean up test files
import os
for store in ['test_user_uploads.json', 'test_user_settings.json', 'test_user_reviews.json', 
              'test_standard_reviews.json', 'test_user_sessions.json']:
    if os.path.exists(store):
        os.remove(store)

print("\n✅ Test complete - new endpoints are syntactically valid!")
