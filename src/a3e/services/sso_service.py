"""
Single Sign-On (SSO) service for enterprise authentication
Supports SAML 2.0 and OAuth providers
"""

import uuid
import secrets
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlencode
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import base64

from ..models.user import User
from ..database.enterprise_models import Team, SessionSecurity
from ..services.team_service import TeamService
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class SSOProvider:
    """Base SSO provider interface"""
    
    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        """Get the authorization URL for the provider"""
        raise NotImplementedError
    
    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for user info"""
        raise NotImplementedError

class GoogleOAuthProvider(SSOProvider):
    """Google OAuth 2.0 provider"""
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_endpoint = "https://oauth2.googleapis.com/token"
        self.userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account"
        }
        return f"{self.auth_endpoint}?{urlencode(params)}"
    
    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                self.token_endpoint,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            token_data = token_response.json()
            
            if "error" in token_data:
                raise ValueError(f"OAuth error: {token_data.get('error_description', token_data['error'])}")
            
            # Get user info
            userinfo_response = await client.get(
                self.userinfo_endpoint,
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            userinfo = userinfo_response.json()
            
            return {
                "provider": "google",
                "email": userinfo["email"],
                "name": userinfo.get("name"),
                "picture": userinfo.get("picture"),
                "provider_id": userinfo["id"],
                "verified": userinfo.get("verified_email", False)
            }

class MicrosoftOAuthProvider(SSOProvider):
    """Microsoft/Azure AD OAuth 2.0 provider"""
    
    def __init__(self):
        self.client_id = settings.microsoft_client_id
        self.client_secret = settings.microsoft_client_secret
        self.tenant_id = settings.microsoft_tenant_id or "common"
        self.auth_endpoint = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
        self.token_endpoint = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.userinfo_endpoint = "https://graph.microsoft.com/v1.0/me"
    
    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile User.Read",
            "state": state,
            "response_mode": "query"
        }
        return f"{self.auth_endpoint}?{urlencode(params)}"
    
    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                self.token_endpoint,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            token_data = token_response.json()
            
            if "error" in token_data:
                raise ValueError(f"OAuth error: {token_data.get('error_description', token_data['error'])}")
            
            # Get user info
            userinfo_response = await client.get(
                self.userinfo_endpoint,
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            userinfo = userinfo_response.json()
            
            return {
                "provider": "microsoft",
                "email": userinfo.get("mail") or userinfo.get("userPrincipalName"),
                "name": userinfo.get("displayName"),
                "provider_id": userinfo["id"],
                "verified": True
            }

class OktaOAuthProvider(SSOProvider):
    """Okta OAuth 2.0 provider"""
    
    def __init__(self):
        self.client_id = settings.okta_client_id
        self.client_secret = settings.okta_client_secret
        self.domain = settings.okta_domain
        self.auth_endpoint = f"{self.domain}/oauth2/default/v1/authorize"
        self.token_endpoint = f"{self.domain}/oauth2/default/v1/token"
        self.userinfo_endpoint = f"{self.domain}/oauth2/default/v1/userinfo"
    
    async def get_auth_url(self, state: str, redirect_uri: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state
        }
        return f"{self.auth_endpoint}?{urlencode(params)}"
    
    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            auth_header = base64.b64encode(
                f"{self.client_id}:{self.client_secret}".encode()
            ).decode()
            
            token_response = await client.post(
                self.token_endpoint,
                headers={"Authorization": f"Basic {auth_header}"},
                data={
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            token_data = token_response.json()
            
            if "error" in token_data:
                raise ValueError(f"OAuth error: {token_data.get('error_description', token_data['error'])}")
            
            # Get user info
            userinfo_response = await client.get(
                self.userinfo_endpoint,
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            userinfo = userinfo_response.json()
            
            return {
                "provider": "okta",
                "email": userinfo["email"],
                "name": userinfo.get("name"),
                "provider_id": userinfo["sub"],
                "verified": userinfo.get("email_verified", False)
            }

class SSOService:
    """Main SSO service for handling authentication flows"""
    
    providers = {
        "google": GoogleOAuthProvider,
        "microsoft": MicrosoftOAuthProvider,
        "okta": OktaOAuthProvider
    }
    
    @staticmethod
    def get_provider(provider_name: str) -> Optional[SSOProvider]:
        """Get SSO provider instance"""
        provider_class = SSOService.providers.get(provider_name)
        if not provider_class:
            return None
        
        # Check if provider is configured
        if provider_name == "google" and not settings.google_client_id:
            return None
        elif provider_name == "microsoft" and not settings.microsoft_client_id:
            return None
        elif provider_name == "okta" and not settings.okta_client_id:
            return None
        
        return provider_class()
    
    @staticmethod
    async def initiate_sso(
        provider_name: str,
        redirect_uri: str
    ) -> Dict[str, str]:
        """Initiate SSO flow"""
        provider = SSOService.get_provider(provider_name)
        if not provider:
            raise ValueError(f"SSO provider {provider_name} not available")
        
        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store state in cache/session (implement based on your session management)
        # For now, we'll include it in the response
        
        auth_url = await provider.get_auth_url(state, redirect_uri)
        
        return {
            "auth_url": auth_url,
            "state": state
        }
    
    @staticmethod
    async def complete_sso(
        db: AsyncSession,
        provider_name: str,
        code: str,
        state: str,
        redirect_uri: str
    ) -> Tuple[User, str]:
        """Complete SSO flow and return user and session token"""
        provider = SSOService.get_provider(provider_name)
        if not provider:
            raise ValueError(f"SSO provider {provider_name} not available")
        
        # Verify state token (implement based on your session management)
        # For now, we'll skip this check
        
        # Exchange code for user info
        user_info = await provider.exchange_code(code, redirect_uri)
        
        # Find or create user
        user = await SSOService.find_or_create_user(db, user_info)
        
        # Create session
        from .auth_service import EnhancedAuthService
        session_token = await EnhancedAuthService.create_secure_session(
            db=db,
            user_id=user.id,
            ip_address="0.0.0.0",  # Should be passed from request
            user_agent=None,
            two_factor_verified=True  # SSO considered as 2FA
        )
        
        logger.info(f"SSO login successful for {user.email} via {provider_name}")
        
        return (user, session_token)
    
    @staticmethod
    async def find_or_create_user(
        db: AsyncSession,
        user_info: Dict[str, Any]
    ) -> User:
        """Find existing user or create new one from SSO info"""
        # Check if user exists
        query = select(User).where(User.email == user_info["email"])
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            # Update user info
            if user_info.get("name") and not user.name:
                user.name = user_info["name"]
            user.auth_provider = user_info["provider"]
            user.last_login = datetime.utcnow()
        else:
            # Create new user
            user = User(
                id=f"user_{uuid.uuid4().hex[:12]}",
                email=user_info["email"],
                name=user_info.get("name"),
                auth_provider=user_info["provider"],
                is_active=True,
                last_login=datetime.utcnow()
            )
            db.add(user)
            await db.flush()
            
            # Create personal team for new user
            await TeamService.create_team(
                db=db,
                name=f"{user.name or user.email.split('@')[0]}'s Team",
                owner_id=user.id,
                description="Personal workspace"
            )
        
        await db.commit()
        return user
    
    @staticmethod
    async def get_available_providers() -> Dict[str, Dict[str, Any]]:
        """Get list of available SSO providers"""
        available = {}
        
        for provider_name in SSOService.providers:
            provider = SSOService.get_provider(provider_name)
            if provider:
                available[provider_name] = {
                    "name": provider_name.title(),
                    "enabled": True,
                    "icon": f"fa-{provider_name}"
                }
        
        return available
    
    @staticmethod
    async def configure_provider(
        db: AsyncSession,
        provider_name: str,
        config: Dict[str, Any]
    ) -> bool:
        """Configure SSO provider settings"""
        # In a real implementation, this would store the config in database
        # For now, we'll validate and return success
        
        if provider_name not in ["google", "microsoft", "saml", "oauth"]:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        # Validate required fields based on provider type
        if provider_name == "google":
            required = ["client_id", "client_secret"]
        elif provider_name == "microsoft":
            required = ["tenant_id", "client_id", "client_secret"]
        elif provider_name == "saml":
            required = ["entity_id", "sso_url", "certificate"]
        elif provider_name == "oauth":
            required = ["auth_url", "token_url", "client_id", "client_secret"]
        else:
            required = []
        
        for field in required:
            if not config.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # TODO: Store in database
        # For now, return success
        return True
    
    @staticmethod
    async def get_configurations(db: AsyncSession) -> Dict[str, Dict[str, Any]]:
        """Get SSO provider configurations"""
        # In a real implementation, this would load from database
        # For now, return empty configurations
        return {
            "google": {},
            "microsoft": {},
            "saml": {},
            "oauth": {}
        }
    
    @staticmethod
    async def validate_session_token(db: AsyncSession, token: str) -> Optional[Any]:
        """Validate session token and return user"""
        # In a real implementation, this would validate against SessionSecurity table
        # For now, we'll do a basic check
        
        # Extract user ID from token (simplified)
        # Token format: "sess_<user_id>_<random>"
        if not token or not token.startswith("sess_"):
            return None
        
        try:
            parts = token.split("_")
            if len(parts) < 3:
                return None
            
            user_id = parts[1]
            
            # Get user from database
            from ..models.user import User
            stmt = select(User).where(User.id == user_id, User.is_active.is_(True))
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            return user
            
        except Exception:
            return None
