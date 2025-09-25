#!/usr/bin/env python3
"""
Fix for user ID mismatch between JWT tokens (email) and database (UUID)
This script adds a helper function to properly resolve user IDs
"""

import os

# The fix to add to user_intelligence_simple.py
FIX_CODE = '''
# Helper function to get user UUID from email
async def get_user_uuid_from_email(email: str) -> str:
    """Get the actual UUID for a user from their email address"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email}
            )
            user = result.first()
            if user:
                return user.id
            # If no user found, check if the provided value is already a UUID
            # This handles cases where the JWT already contains the UUID
            import uuid
            try:
                uuid.UUID(email)
                return email  # It's already a UUID
            except:
                # Return the email as fallback (for backward compatibility)
                logger.warning(f"No user found for email: {email}, using email as ID")
                return email
    except Exception as e:
        logger.error(f"Error getting user UUID: {e}")
        return email
'''

print("User ID Mismatch Fix")
print("=" * 60)
print("\nThe issue:")
print("- JWT tokens contain email addresses (e.g., 'jeremy.estrella@gmail.com')")
print("- Database stores user IDs as UUIDs (e.g., 'e144cf90-d8ed-4277-bf12-3d86443e2099')")
print("- API queries fail because they're comparing email to UUID")
print("\nThe fix:")
print("1. Add a helper function to resolve email to UUID")
print("2. Update all endpoints to use this function")
print("\nHere's the code to add after the get_current_user_simple function:")
print("\n" + FIX_CODE)
print("\nThen update each endpoint to use:")
print("""
# Instead of:
user_id = current_user.get("sub", current_user.get("user_id", "unknown"))

# Use:
email = current_user.get("sub", current_user.get("email", current_user.get("user_id", "unknown")))
user_id = await get_user_uuid_from_email(email)
""")
print("\nEndpoints to update:")
print("- /documents/list")
print("- /documents/{document_id}/analyze") 
print("- /uploads/{document_id}")
print("- /evidence/list")
print("- /evidence/upload")
print("- And all other endpoints that query by user_id")
print("\n" + "=" * 60)