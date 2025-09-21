#!/usr/bin/env python3
"""Test Railway database connection with different approaches"""

import os
import asyncio
import asyncpg
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

# Get the database URL from environment or use the one we know
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:jOSLpQcnUAahNTkVPIAraoepMQxbqXGc@shinkansen.proxy.rlwy.net:28831/railway")

async def test_asyncpg():
    """Test with asyncpg directly"""
    try:
        print("\n1. Testing with asyncpg...")
        # Parse the URL for asyncpg
        if DATABASE_URL.startswith("postgresql://"):
            conn_url = DATABASE_URL.replace("postgresql://", "")
        else:
            conn_url = DATABASE_URL.replace("postgres://", "")
        
        # Split into components
        user_pass, host_db = conn_url.split("@")
        user, password = user_pass.split(":")
        host_port, database = host_db.split("/")
        host, port = host_port.split(":")
        
        conn = await asyncpg.connect(
            user=user,
            password=password,
            database=database,
            host=host,
            port=int(port)
        )
        
        result = await conn.fetchval('SELECT 1')
        print(f"✅ asyncpg connection successful! Result: {result}")
        await conn.close()
        return True
    except Exception as e:
        print(f"❌ asyncpg failed: {type(e).__name__}: {e}")
        return False

def test_psycopg2():
    """Test with psycopg2 (sync)"""
    try:
        print("\n2. Testing with psycopg2...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1")
        result = cur.fetchone()
        print(f"✅ psycopg2 connection successful! Result: {result}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ psycopg2 failed: {type(e).__name__}: {e}")
        return False

def test_sqlalchemy_sync():
    """Test with SQLAlchemy sync engine"""
    try:
        print("\n3. Testing with SQLAlchemy sync...")
        from sqlalchemy import text
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            print(f"✅ SQLAlchemy sync successful! Result: {result}")
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy sync failed: {type(e).__name__}: {e}")
        return False

async def test_sqlalchemy_async():
    """Test with SQLAlchemy async engine"""
    try:
        print("\n4. Testing with SQLAlchemy async...")
        from sqlalchemy import text
        # Convert URL for async
        async_url = DATABASE_URL
        if async_url.startswith("postgresql://"):
            async_url = async_url.replace("postgresql://", "postgresql+asyncpg://")
        elif async_url.startswith("postgres://"):
            async_url = async_url.replace("postgres://", "postgresql+asyncpg://")
        
        engine = create_async_engine(async_url)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"✅ SQLAlchemy async successful! Result: {result.scalar()}")
        await engine.dispose()
        return True
    except Exception as e:
        print(f"❌ SQLAlchemy async failed: {type(e).__name__}: {e}")
        return False

async def main():
    print(f"Testing connection to: {DATABASE_URL[:50]}...")
    
    # Test all methods
    results = {
        "asyncpg": await test_asyncpg(),
        "psycopg2": test_psycopg2(),
        "sqlalchemy_sync": test_sqlalchemy_sync(),
        "sqlalchemy_async": await test_sqlalchemy_async()
    }
    
    print("\n=== Summary ===")
    for method, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {method}")
    
    if not results["sqlalchemy_async"]:
        print("\n💡 SQLAlchemy async failed - this is likely the issue!")
        print("   Consider using sync database connections instead")

if __name__ == "__main__":
    asyncio.run(main())