#!/usr/bin/env python3
"""Fix database connection issues"""

import os
import asyncio
import asyncpg
from urllib.parse import urlparse, parse_qs

print("🔧 Diagnosing Database Connection")
print("=" * 50)

# Common Railway PostgreSQL URL format
sample_urls = [
    "postgresql://postgres:password@containers-us-west-123.railway.app:5432/railway",
    "postgres://postgres:password@containers-us-west-123.railway.app:5432/railway"
]

print("\n1. Railway PostgreSQL URL formats:")
for url in sample_urls:
    print(f"   {url}")

print("\n2. Common issues and fixes:")
print("   - Ensure DATABASE_URL is properly set in Railway")
print("   - Railway URLs often use 'postgres://' instead of 'postgresql://'")
print("   - Special characters in password must be URL-encoded")
print("   - The app already converts to asyncpg format automatically")

# Test connection function
async def test_connection(database_url: str):
    """Test database connection"""
    try:
        # Parse the URL
        if database_url.startswith("postgres://"):
            # asyncpg expects postgresql://
            test_url = database_url.replace("postgres://", "postgresql://", 1)
        else:
            test_url = database_url
            
        print(f"\n3. Testing connection...")
        print(f"   Original URL: {database_url[:50]}...")
        print(f"   Test URL: {test_url[:50]}...")
        
        # Try to connect
        conn = await asyncpg.connect(test_url, timeout=10)
        version = await conn.fetchval('SELECT version()')
        await conn.close()
        
        print(f"\n✅ Connection successful!")
        print(f"   PostgreSQL version: {version[:50]}...")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed!")
        print(f"   Error: {str(e)}")
        
        # Provide specific guidance based on error
        if "Name or service not known" in str(e):
            print("\n   🔍 This error means the hostname cannot be resolved.")
            print("   Check that:")
            print("   1. DATABASE_URL is correctly set in Railway")
            print("   2. The database service is running")
            print("   3. The URL format matches Railway's PostgreSQL format")
        elif "password authentication failed" in str(e):
            print("\n   🔍 Authentication failed.")
            print("   Check that the password in DATABASE_URL is correct")
        elif "timeout" in str(e).lower():
            print("\n   🔍 Connection timed out.")
            print("   The database might still be provisioning")
            
        return False

# Check if DATABASE_URL is set
database_url = os.getenv("DATABASE_URL")

if database_url:
    print(f"\n4. Found DATABASE_URL in environment")
    # Run the test
    asyncio.run(test_connection(database_url))
else:
    print("\n❌ DATABASE_URL not found in environment")
    print("\nTo test locally, run:")
    print("export DATABASE_URL='your-railway-database-url'")
    print("python3 fix_database_connection.py")

print("\n" + "=" * 50)
print("Next steps:")
print("1. Ensure DATABASE_URL is set correctly in Railway Variables")
print("2. Wait a moment for the database to fully provision")
print("3. Check that the URL format matches the examples above")
print("4. If using special characters in password, ensure they're URL-encoded")
