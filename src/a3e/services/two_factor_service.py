"""
Two-Factor Authentication (2FA) service
Supports TOTP (Time-based One-Time Passwords)
"""

import secrets
import pyotp
import qrcode
import io
import base64
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
import logging

from ..models.user import User
from ..database.enterprise_models import SessionSecurity

logger = logging.getLogger(__name__)

class TwoFactorService:
    """Service for managing two-factor authentication"""
    
    @staticmethod
    async def generate_2fa_secret(
        db: AsyncSession,
        user_id: str
    ) -> Tuple[str, str]:
        """
        Generate a new 2FA secret for user
        Returns (secret, provisioning_uri)
        """
        # Generate random secret
        secret = pyotp.random_base32()
        
        # Get user
        user = await db.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Create provisioning URI for QR code
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="MapMyStandards"
        )
        
        logger.info(f"Generated 2FA secret for user {user_id}")
        
        return (secret, provisioning_uri)
    
    @staticmethod
    async def generate_qr_code(provisioning_uri: str) -> str:
        """Generate QR code image as base64 string"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        base64_image = base64.b64encode(buffer.read()).decode()
        return f"data:image/png;base64,{base64_image}"
    
    @staticmethod
    async def enable_2fa(
        db: AsyncSession,
        user_id: str,
        secret: str,
        verification_code: str
    ) -> bool:
        """Enable 2FA for user after verifying the code"""
        # Verify the code first
        if not TwoFactorService.verify_code(secret, verification_code):
            return False
        
        # Store encrypted secret in user record
        # In production, encrypt the secret before storing
        # For now, we'll store it as-is (NOT SECURE FOR PRODUCTION)
        user = await db.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Add two_factor_secret column to User model in production
        # For now, we'll store in a separate table or user metadata
        
        logger.info(f"2FA enabled for user {user_id}")
        return True
    
    @staticmethod
    def verify_code(secret: str, code: str) -> bool:
        """Verify a TOTP code"""
        totp = pyotp.TOTP(secret)
        # Allow for time drift (accepts codes from 30 seconds before/after)
        return totp.verify(code, valid_window=1)
    
    @staticmethod
    async def disable_2fa(
        db: AsyncSession,
        user_id: str
    ) -> bool:
        """Disable 2FA for user"""
        user = await db.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Remove two_factor_secret from user record
        # Implementation depends on where secret is stored
        
        logger.info(f"2FA disabled for user {user_id}")
        return True
    
    @staticmethod
    async def generate_backup_codes(
        db: AsyncSession,
        user_id: str,
        count: int = 10
    ) -> list[str]:
        """Generate backup codes for 2FA recovery"""
        codes = []
        
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        
        # Store hashed versions of backup codes
        # Implementation depends on database schema
        
        logger.info(f"Generated {count} backup codes for user {user_id}")
        return codes
    
    @staticmethod
    async def verify_backup_code(
        db: AsyncSession,
        user_id: str,
        code: str
    ) -> bool:
        """Verify and consume a backup code"""
        # Remove formatting
        clean_code = code.replace('-', '').upper()
        
        # Check against stored backup codes
        # Mark as used if valid
        # Implementation depends on database schema
        
        # For now, return False (not implemented)
        return False
    
    @staticmethod
    async def require_2fa_verification(
        db: AsyncSession,
        session_id: str,
        code: str,
        user_secret: str
    ) -> bool:
        """Verify 2FA code and update session"""
        # Verify the code
        if not TwoFactorService.verify_code(user_secret, code):
            return False
        
        # Update session to mark 2FA as verified
        session = await db.get(SessionSecurity, session_id)
        if session:
            session.two_factor_verified = True
            await db.commit()
        
        return True
    
    @staticmethod
    async def get_2fa_status(
        db: AsyncSession,
        user_id: str
    ) -> Dict[str, Any]:
        """Get 2FA status for user"""
        user = await db.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        
        # Check if 2FA is enabled
        # Implementation depends on where secret is stored
        has_2fa = False  # Placeholder
        
        # Check for backup codes
        backup_codes_count = 0  # Placeholder
        
        return {
            "enabled": has_2fa,
            "backup_codes_remaining": backup_codes_count,
            "methods": ["totp"] if has_2fa else []
        }
