#!/usr/bin/env python3
"""Clear all local JSON stores and SQLite databases"""

import os
import json
import glob
import shutil
import sys

print("=" * 60)
print("⚠️  WARNING: This will DELETE ALL LOCAL DATA!")
print("=" * 60)
print("\nThis script will delete:")
print("- All local JSON store files")
print("- All SQLite databases")
print("- All upload directories")
print("- All session data")

confirmation = input("\nType 'DELETE LOCAL' to confirm: ")
if confirmation != "DELETE LOCAL":
    print("Cancelled.")
    sys.exit(0)

print("\n" + "=" * 60)
print("Clearing local data...")

# JSON stores to clear
json_stores = [
    "user_settings_store.json",
    "user_reviews_store.json",
    "user_standard_reviews_store.json",
    "user_uploads_store.json",
    "user_sessions_store.json",
    "user_org_charts.json",
    "user_reviews_audit.jsonl",
    "user_tasks_store.json",
    "user_tasks_audit.jsonl",
    "session_store.json",
    "secure_sessions.json",
    "local_user_store.json",
    "local_session_store.json",
]

print("\n1. Clearing JSON stores...")
for store in json_stores:
    if os.path.exists(store):
        try:
            # Try to show count before deletion
            if store.endswith('.json'):
                with open(store, 'r') as f:
                    try:
                        data = json.load(f)
                        if isinstance(data, dict):
                            count = len(data)
                        elif isinstance(data, list):
                            count = len(data)
                        else:
                            count = 1
                        print(f"   ✓ Deleted {store} ({count} entries)")
                    except:
                        print(f"   ✓ Deleted {store}")
            else:
                print(f"   ✓ Deleted {store}")
            os.remove(store)
        except Exception as e:
            print(f"   ⚠️  Error deleting {store}: {e}")
    else:
        print(f"   - {store} not found")

# SQLite databases
print("\n2. Clearing SQLite databases...")
db_patterns = ["*.db", "*.sqlite", "*.sqlite3"]
for pattern in db_patterns:
    for db_file in glob.glob(pattern):
        try:
            size = os.path.getsize(db_file) / 1024  # KB
            os.remove(db_file)
            print(f"   ✓ Deleted {db_file} ({size:.1f} KB)")
        except Exception as e:
            print(f"   ⚠️  Error deleting {db_file}: {e}")

# Upload directories
print("\n3. Clearing upload directories...")
upload_dirs = [
    "uploads",
    "uploads/simple",
    "data/uploads",
    "temp",
    "tmp",
]

for upload_dir in upload_dirs:
    if os.path.exists(upload_dir) and os.path.isdir(upload_dir):
        try:
            # Count files first
            file_count = sum(len(files) for _, _, files in os.walk(upload_dir))
            shutil.rmtree(upload_dir)
            os.makedirs(upload_dir, exist_ok=True)  # Recreate empty
            print(f"   ✓ Cleared {upload_dir} ({file_count} files)")
        except Exception as e:
            print(f"   ⚠️  Error clearing {upload_dir}: {e}")
    else:
        print(f"   - {upload_dir} not found")

# Other data files
print("\n4. Clearing other data files...")
other_patterns = [
    "*.log",
    "*.tmp",
    "*.cache",
    "BUILD_STATE.json",
]

for pattern in other_patterns:
    for file in glob.glob(pattern):
        try:
            os.remove(file)
            print(f"   ✓ Deleted {file}")
        except Exception as e:
            print(f"   ⚠️  Error deleting {file}: {e}")

print("\n✅ Local data cleared successfully!")
print("\n" + "=" * 60)