#!/usr/bin/env python3
"""Create a test user for authentication testing"""
import sqlite3
import hashlib
import uuid
from datetime import datetime
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False
    print("⚠️  bcrypt not available, using SHA256 fallback")

def create_test_user():
    """Create a test user in the database"""
    conn = sqlite3.connect('a3e.db')
    cursor = conn.cursor()
    
    # Test user details
    user_id = str(uuid.uuid4())
    email = "test@example.com"
    password = "password123"
    name = "Test User"
    
    # Try different password hashing methods based on what the system uses
    if HAS_BCRYPT:
        # Try bcrypt first (most secure)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"Using bcrypt hash: {password_hash[:20]}...")
    else:
        # Fallback to SHA256
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        print(f"Using SHA256 hash: {password_hash[:20]}...")
    
    # Delete existing test user if any
    cursor.execute("DELETE FROM users WHERE email = ?", (email,))
    
    # Insert test user with all fields
    try:
        cursor.execute('''
            INSERT INTO users (
                id, email, password_hash, name, 
                is_active, is_verified, created_at,
                institution_name, role, subscription_tier
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, email, password_hash, name,
            1, 1, datetime.now(),
            "Test Institution", "admin", "premium"
        ))
        conn.commit()
        print("✅ Test user created with extended fields")
    except sqlite3.Error as e:
        print(f"❌ Error creating user: {e}")
        # Try simpler insert
        cursor.execute('''
            INSERT INTO users (id, email, password_hash, name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, email, password_hash, name))
        conn.commit()
        print("✅ Test user created with basic fields")
    
    # Verify user was created
    cursor.execute("SELECT email, name, password_hash FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    
    if result:
        print(f"✅ Test user verified in database:")
        print(f"   Email: {result[0]}")
        print(f"   Name: {result[1]}")
        print(f"   Password: {password}")
        print(f"   Hash type: {'bcrypt' if result[2].startswith('$2') else 'SHA256'}")
    else:
        print("❌ Failed to create test user")
    
    # Also create a simpler hash version for auth-simple
    simple_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("UPDATE users SET password_hash = ? WHERE email = ? AND password_hash != ?", 
                   (simple_hash, email, simple_hash))
    conn.commit()
    print(f"✅ Also created SHA256 version for auth-simple")
    
    conn.close()

if __name__ == "__main__":
    create_test_user()
