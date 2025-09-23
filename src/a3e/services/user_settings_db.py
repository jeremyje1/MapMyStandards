"""
Database-backed user settings service to replace JSON file storage
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from ..models.user import User
from ..core.config import get_settings

logger = logging.getLogger(__name__)

class UserSettingsDB:
    """Service for managing user settings in database instead of JSON files"""
    
    def __init__(self):
        self.settings = get_settings()
        # Create database engine
        self.engine = create_engine(self.settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _get_user_by_id(self, user_id: str, db: Session) -> Optional[User]:
        """Get user by ID from database"""
        return db.query(User).filter(User.id == user_id).first()
    
    def _get_user_by_email(self, email: str, db: Session) -> Optional[User]:
        """Get user by email from database"""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_settings(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """Get user settings from database"""
        db = self.SessionLocal()
        try:
            # Try to find user by ID or email
            user_id = user_info.get("sub", user_info.get("user_id"))
            email = user_info.get("email")
            
            user = None
            if user_id:
                user = self._get_user_by_id(user_id, db)
            if not user and email:
                user = self._get_user_by_email(email, db)
                
            if not user:
                logger.warning(f"User not found: {user_id or email}")
                return {}
                
            # Build settings from user model
            settings = {
                "organization": user.institution_name,
                "institution_name": user.institution_name,
                "institution_type": user.institution_type,
                "department": user.department,
                "role": user.role,
                "primary_accreditor": user.primary_accreditor,
                "onboarding_completed": user.onboarding_completed,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
            
            # Merge with onboarding_data if exists
            if user.onboarding_data:
                if isinstance(user.onboarding_data, str):
                    try:
                        onboarding_data = json.loads(user.onboarding_data)
                        settings.update(onboarding_data)
                    except:
                        pass
                elif isinstance(user.onboarding_data, dict):
                    settings.update(user.onboarding_data)
                    
            return settings
            
        except Exception as e:
            logger.error(f"Error getting user settings: {e}")
            return {}
        finally:
            db.close()
    
    def save_user_settings(self, user_info: Dict[str, Any], settings: Dict[str, Any]) -> bool:
        """Save user settings to database"""
        db = self.SessionLocal()
        try:
            # Try to find user
            user_id = user_info.get("sub", user_info.get("user_id"))
            email = user_info.get("email")
            
            user = None
            if user_id:
                user = self._get_user_by_id(user_id, db)
            if not user and email:
                user = self._get_user_by_email(email, db)
                
            if not user:
                # Create new user if doesn't exist
                user = User(
                    id=user_id or email,
                    email=email,
                    username=email.split("@")[0] if email else "user"
                )
                db.add(user)
                
            # Update user fields from settings
            if "organization" in settings:
                user.institution_name = settings["organization"]
            if "institution_name" in settings:
                user.institution_name = settings["institution_name"] 
            if "institution_type" in settings:
                user.institution_type = settings["institution_type"]
            if "department" in settings:
                user.department = settings["department"]
            if "role" in settings:
                user.role = settings["role"]
            if "primary_accreditor" in settings:
                user.primary_accreditor = settings["primary_accreditor"]
                
            # Mark onboarding as completed if we have key fields
            if user.institution_name or user.primary_accreditor:
                user.onboarding_completed = True
                
            # Store full settings in onboarding_data
            user.onboarding_data = settings
            
            db.commit()
            logger.info(f"Saved settings for user: {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving user settings: {e}")
            db.rollback()
            return False
        finally:
            db.close()

# Singleton instance
user_settings_db = UserSettingsDB()

def get_user_settings_db() -> UserSettingsDB:
    """Get user settings database service instance"""
    return user_settings_db