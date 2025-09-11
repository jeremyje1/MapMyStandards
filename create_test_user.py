#!/usr/bin/env python3
"""
Create a test user for authentication testing
"""
import sqlite3
import bcrypt
import uuid
from datetime import datetime

# Connect to the database
conn = sqlite3.connect('a3e.db')
cursor = conn.cursor()

# Test user details
email = "test@example.com"
password = "test123"
name = "Test User"

# Hash the password
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

# Check if user exists
cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
existing = cursor.fetchone()

if existing:
    print(f"User {email} already exists")
    # Update password
    cursor.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (hashed_password.decode('utf-8'), email)
    )
else:
    # Create new user
    user_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO users (id, email, password_hash, name, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, 1, ?, ?)
    """, (
        user_id,
        email,
        hashed_password.decode('utf-8'),
        name,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    print(f"Created user {email}")

conn.commit()
conn.close()

print(f"""
✅ Test user ready!
Email: {email}
Password: {password}

You can now login with these credentials.
""")
