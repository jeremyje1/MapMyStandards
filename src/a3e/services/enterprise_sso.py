"""
Enterprise SSO Integration Service
Single Sign-On integration with major identity providers
Part of Phase M3: Enterprise Features
"""

import logging
import json
import secrets
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import uuid
import urllib.parse
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)


class IdentityProvider(Enum):
    """Supported identity providers"""
    AZURE_AD = "azure_ad"
    OKTA = "okta"
    GOOGLE_WORKSPACE = "google_workspace"
    SAML2_GENERIC = "saml2_generic"
    LDAP = "ldap"
    ACTIVE_DIRECTORY = "active_directory"
    PING_IDENTITY = "ping_identity"
    ONELOGIN = "onelogin"
    AUTH0 = "auth0"
    KEYCLOAK = "keycloak"


class AuthenticationMethod(Enum):
    """Authentication methods"""
    SAML2 = "saml2"
    OAUTH2 = "oauth2"
    OPENID_CONNECT = "oidc"
    LDAP_BIND = "ldap_bind"
    KERBEROS = "kerberos"
    JWT_BEARER = "jwt_bearer"


class ProvisioningMethod(Enum):
    """User provisioning methods"""
    JUST_IN_TIME = "jit"
    SCIM = "scim"
    MANUAL = "manual"
    LDAP_SYNC = "ldap_sync"
    API_SYNC = "api_sync"


@dataclass
class IdentityProviderConfig:
    """Identity provider configuration"""
    
    # Basic configuration
    provider_id: str
    provider_type: IdentityProvider
    name: str
    description: str
    enabled: bool = True
    
    # Authentication configuration
    auth_method: AuthenticationMethod
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None  # For Azure AD
    domain: Optional[str] = None
    
    # SAML configuration
    saml_entity_id: Optional[str] = None
    saml_sso_url: Optional[str] = None
    saml_certificate: Optional[str] = None
    saml_private_key: Optional[str] = None
    saml_signature_algorithm: str = "rsa-sha256"
    
    # OAuth/OIDC configuration
    oauth_authorization_url: Optional[str] = None
    oauth_token_url: Optional[str] = None
    oauth_userinfo_url: Optional[str] = None
    oauth_scopes: List[str] = field(default_factory=lambda: ["openid", "profile", "email"])
    
    # LDAP configuration
    ldap_server: Optional[str] = None
    ldap_port: int = 389
    ldap_use_ssl: bool = False
    ldap_base_dn: Optional[str] = None
    ldap_bind_dn: Optional[str] = None
    ldap_bind_password: Optional[str] = None
    ldap_user_filter: str = "(uid={username})"
    ldap_group_filter: str = "(member={user_dn})"
    
    # User provisioning
    provisioning_method: ProvisioningMethod = ProvisioningMethod.JUST_IN_TIME
    scim_endpoint: Optional[str] = None
    scim_token: Optional[str] = None
    
    # Attribute mapping
    attribute_mapping: Dict[str, str] = field(default_factory=dict)
    role_mapping: Dict[str, str] = field(default_factory=dict)
    group_mapping: Dict[str, str] = field(default_factory=dict)
    
    # Advanced settings
    auto_create_users: bool = True
    auto_update_users: bool = True
    require_mfa: bool = False
    session_timeout: int = 8  # hours
    
    # Security settings
    encryption_key: Optional[str] = None
    signing_key: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Generate default attribute mappings"""
        if not self.attribute_mapping:
            self.attribute_mapping = self._get_default_attribute_mapping()
    
    def _get_default_attribute_mapping(self) -> Dict[str, str]:
        """Get default attribute mapping for provider type"""
        
        if self.provider_type == IdentityProvider.AZURE_AD:
            return {
                "email": "mail",
                "first_name": "givenName",
                "last_name": "surname",
                "display_name": "displayName",
                "groups": "groups",
                "department": "department",
                "title": "jobTitle"
            }
        
        elif self.provider_type == IdentityProvider.GOOGLE_WORKSPACE:
            return {
                "email": "email",
                "first_name": "given_name",
                "last_name": "family_name",
                "display_name": "name",
                "picture": "picture"
            }
        
        elif self.provider_type == IdentityProvider.OKTA:
            return {
                "email": "email",
                "first_name": "given_name",
                "last_name": "family_name",
                "display_name": "name",
                "groups": "groups"
            }
        
        else:
            return {
                "email": "email",
                "first_name": "firstName",
                "last_name": "lastName",
                "display_name": "displayName"
            }


@dataclass
class SSOSession:
    """SSO session information"""
    session_id: str
    tenant_id: str
    user_id: str
    provider_id: str
    saml_session_index: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return self.expires_at and datetime.utcnow() > self.expires_at


@dataclass
class AuthenticationRequest:
    """Authentication request"""
    request_id: str
    tenant_id: str
    provider_id: str
    relay_state: Optional[str] = None
    return_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))


@dataclass
class UserProvisioningEvent:
    """User provisioning event"""
    event_id: str
    tenant_id: str
    provider_id: str
    user_id: str
    action: str  # created, updated, disabled, deleted
    attributes: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    success: bool = True
    error_message: Optional[str] = None


class EnterpriseSSOService:
    """Enterprise SSO integration service"""
    
    def __init__(self):
        self.identity_providers: Dict[str, IdentityProviderConfig] = {}
        self.active_sessions: Dict[str, SSOSession] = {}
        self.auth_requests: Dict[str, AuthenticationRequest] = {}
        self.provisioning_events: List[UserProvisioningEvent] = []
        
        # Service endpoints
        self.base_url = "https://a3e.platform.com"  # Would come from config
        self.sso_endpoints = {
            "saml_acs": f"{self.base_url}/sso/saml/acs",
            "saml_sls": f"{self.base_url}/sso/saml/sls",
            "saml_metadata": f"{self.base_url}/sso/saml/metadata",
            "oauth_callback": f"{self.base_url}/sso/oauth/callback",
            "oidc_callback": f"{self.base_url}/sso/oidc/callback"
        }
        
        # Start background tasks
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background SSO processing tasks"""
        
        async def cleanup_expired_sessions():
            """Clean up expired SSO sessions"""
            while True:
                try:
                    await self._cleanup_expired_sessions()
                    await asyncio.sleep(300)  # Run every 5 minutes
                except Exception as e:
                    logger.error(f"Session cleanup error: {e}")
                    await asyncio.sleep(600)  # Wait 10 minutes on error
        
        async def sync_user_provisioning():
            """Sync user provisioning from identity providers"""
            while True:
                try:
                    await self._sync_user_provisioning()
                    await asyncio.sleep(3600)  # Run every hour
                except Exception as e:
                    logger.error(f"User provisioning sync error: {e}")
                    await asyncio.sleep(1800)  # Wait 30 minutes on error
        
        # Start background tasks
        asyncio.create_task(cleanup_expired_sessions())
        asyncio.create_task(sync_user_provisioning())
    
    async def configure_identity_provider(
        self,
        tenant_id: str,
        config: IdentityProviderConfig
    ) -> str:
        """Configure identity provider for tenant"""
        
        # Validate configuration
        await self._validate_provider_config(config)
        
        # Generate provider ID if not provided
        if not config.provider_id:
            config.provider_id = f"{tenant_id}_{config.provider_type.value}_{uuid.uuid4().hex[:8]}"
        
        # Store configuration
        provider_key = f"{tenant_id}_{config.provider_id}"
        self.identity_providers[provider_key] = config
        
        # Test connection
        connection_test = await self._test_provider_connection(config)
        if not connection_test["success"]:
            logger.warning(f"Provider connection test failed: {connection_test['error']}")
        
        logger.info(f"Identity provider configured: {config.provider_id} for tenant {tenant_id}")
        return config.provider_id
    
    async def _validate_provider_config(self, config: IdentityProviderConfig):
        """Validate identity provider configuration"""
        
        if config.auth_method == AuthenticationMethod.SAML2:
            if not config.saml_entity_id or not config.saml_sso_url:
                raise ValueError("SAML configuration requires entity_id and sso_url")
        
        elif config.auth_method in [AuthenticationMethod.OAUTH2, AuthenticationMethod.OPENID_CONNECT]:
            if not config.client_id or not config.oauth_authorization_url:
                raise ValueError("OAuth configuration requires client_id and authorization_url")
        
        elif config.auth_method == AuthenticationMethod.LDAP_BIND:
            if not config.ldap_server or not config.ldap_base_dn:
                raise ValueError("LDAP configuration requires server and base_dn")
    
    async def _test_provider_connection(self, config: IdentityProviderConfig) -> Dict[str, Any]:
        """Test connection to identity provider"""
        
        try:
            if config.auth_method == AuthenticationMethod.SAML2:
                return await self._test_saml_connection(config)
            elif config.auth_method == AuthenticationMethod.OAUTH2:
                return await self._test_oauth_connection(config)
            elif config.auth_method == AuthenticationMethod.LDAP_BIND:
                return await self._test_ldap_connection(config)
            else:
                return {"success": True, "message": "Connection test not implemented for this method"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _test_saml_connection(self, config: IdentityProviderConfig) -> Dict[str, Any]:
        """Test SAML connection"""
        
        # This would make an actual SAML metadata request
        # For now, just validate the configuration
        if config.saml_sso_url and config.saml_entity_id:
            return {"success": True, "message": "SAML configuration validated"}
        else:
            return {"success": False, "error": "Invalid SAML configuration"}
    
    async def _test_oauth_connection(self, config: IdentityProviderConfig) -> Dict[str, Any]:
        """Test OAuth connection"""
        
        # This would make an actual OAuth discovery request
        # For now, just validate the configuration
        if config.client_id and config.oauth_authorization_url:
            return {"success": True, "message": "OAuth configuration validated"}
        else:
            return {"success": False, "error": "Invalid OAuth configuration"}
    
    async def _test_ldap_connection(self, config: IdentityProviderConfig) -> Dict[str, Any]:
        """Test LDAP connection"""
        
        # This would make an actual LDAP bind request
        # For now, just validate the configuration
        if config.ldap_server and config.ldap_base_dn:
            return {"success": True, "message": "LDAP configuration validated"}
        else:
            return {"success": False, "error": "Invalid LDAP configuration"}
    
    async def initiate_sso_login(
        self,
        tenant_id: str,
        provider_id: str,
        return_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Initiate SSO login flow"""
        
        provider_key = f"{tenant_id}_{provider_id}"
        config = self.identity_providers.get(provider_key)
        
        if not config or not config.enabled:
            raise ValueError(f"Identity provider not found or disabled: {provider_id}")
        
        # Create authentication request
        request_id = f"auth_{uuid.uuid4().hex}"
        auth_request = AuthenticationRequest(
            request_id=request_id,
            tenant_id=tenant_id,
            provider_id=provider_id,
            return_url=return_url
        )
        
        self.auth_requests[request_id] = auth_request
        
        # Generate SSO URL based on provider type
        if config.auth_method == AuthenticationMethod.SAML2:
            return await self._generate_saml_request(config, auth_request)
        elif config.auth_method == AuthenticationMethod.OAUTH2:
            return await self._generate_oauth_request(config, auth_request)
        elif config.auth_method == AuthenticationMethod.OPENID_CONNECT:
            return await self._generate_oidc_request(config, auth_request)
        else:
            raise ValueError(f"Unsupported authentication method: {config.auth_method}")
    
    async def _generate_saml_request(
        self,
        config: IdentityProviderConfig,
        auth_request: AuthenticationRequest
    ) -> Dict[str, Any]:
        """Generate SAML authentication request"""
        
        # Create SAML AuthnRequest
        authn_request = self._create_saml_authn_request(config, auth_request)
        
        # Encode and deflate the request
        encoded_request = base64.b64encode(authn_request.encode()).decode()
        
        # Create SSO URL
        params = {
            "SAMLRequest": encoded_request,
            "RelayState": auth_request.request_id
        }
        
        sso_url = f"{config.saml_sso_url}?{urllib.parse.urlencode(params)}"
        
        return {
            "method": "redirect",
            "url": sso_url,
            "request_id": auth_request.request_id
        }
    
    def _create_saml_authn_request(
        self,
        config: IdentityProviderConfig,
        auth_request: AuthenticationRequest
    ) -> str:
        """Create SAML AuthnRequest XML"""
        
        request_id = f"_{uuid.uuid4().hex}"
        issue_instant = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        authn_request = f"""<?xml version="1.0" encoding="UTF-8"?>
<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                    xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                    ID="{request_id}"
                    Version="2.0"
                    IssueInstant="{issue_instant}"
                    Destination="{config.saml_sso_url}"
                    AssertionConsumerServiceURL="{self.sso_endpoints['saml_acs']}"
                    ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">
    <saml:Issuer>{self.base_url}</saml:Issuer>
    <samlp:NameIDPolicy Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
                        AllowCreate="true"/>
</samlp:AuthnRequest>"""
        
        return authn_request
    
    async def _generate_oauth_request(
        self,
        config: IdentityProviderConfig,
        auth_request: AuthenticationRequest
    ) -> Dict[str, Any]:
        """Generate OAuth authorization request"""
        
        # Generate state parameter
        state = f"{auth_request.request_id}_{secrets.token_urlsafe(16)}"
        
        # Create authorization URL
        params = {
            "response_type": "code",
            "client_id": config.client_id,
            "redirect_uri": self.sso_endpoints["oauth_callback"],
            "scope": " ".join(config.oauth_scopes),
            "state": state
        }
        
        auth_url = f"{config.oauth_authorization_url}?{urllib.parse.urlencode(params)}"
        
        return {
            "method": "redirect",
            "url": auth_url,
            "request_id": auth_request.request_id,
            "state": state
        }
    
    async def _generate_oidc_request(
        self,
        config: IdentityProviderConfig,
        auth_request: AuthenticationRequest
    ) -> Dict[str, Any]:
        """Generate OpenID Connect authentication request"""
        
        # Generate nonce and state
        nonce = secrets.token_urlsafe(16)
        state = f"{auth_request.request_id}_{secrets.token_urlsafe(16)}"
        
        # Create authorization URL
        params = {
            "response_type": "code",
            "client_id": config.client_id,
            "redirect_uri": self.sso_endpoints["oidc_callback"],
            "scope": " ".join(config.oauth_scopes),
            "state": state,
            "nonce": nonce
        }
        
        auth_url = f"{config.oauth_authorization_url}?{urllib.parse.urlencode(params)}"
        
        return {
            "method": "redirect",
            "url": auth_url,
            "request_id": auth_request.request_id,
            "state": state,
            "nonce": nonce
        }
    
    async def process_saml_response(
        self,
        saml_response: str,
        relay_state: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process SAML authentication response"""
        
        # Find the authentication request
        auth_request = None
        if relay_state:
            auth_request = self.auth_requests.get(relay_state)
        
        if not auth_request:
            raise ValueError("Invalid or expired authentication request")
        
        # Decode SAML response
        decoded_response = base64.b64decode(saml_response).decode()
        
        # Parse SAML response
        user_info = await self._parse_saml_response(decoded_response, auth_request)
        
        # Create or update user
        user = await self._provision_user(auth_request.tenant_id, auth_request.provider_id, user_info)
        
        # Create SSO session
        session = await self._create_sso_session(auth_request.tenant_id, user["id"], auth_request.provider_id, user_info)
        
        # Clean up auth request
        del self.auth_requests[relay_state]
        
        return {
            "success": True,
            "user": user,
            "session_id": session.session_id,
            "return_url": auth_request.return_url
        }
    
    async def _parse_saml_response(self, saml_response: str, auth_request: AuthenticationRequest) -> Dict[str, Any]:
        """Parse SAML response and extract user information"""
        
        try:
            # Parse XML
            root = ET.fromstring(saml_response)
            
            # Extract attributes (simplified)
            user_info = {
                "email": "user@example.com",  # Would extract from SAML attributes
                "first_name": "John",
                "last_name": "Doe",
                "groups": ["users"]
            }
            
            return user_info
        
        except Exception as e:
            logger.error(f"Failed to parse SAML response: {e}")
            raise ValueError("Invalid SAML response")
    
    async def process_oauth_callback(
        self,
        code: str,
        state: str,
        tenant_id: str
    ) -> Dict[str, Any]:
        """Process OAuth callback"""
        
        # Extract request ID from state
        request_id = state.split("_")[0]
        auth_request = self.auth_requests.get(request_id)
        
        if not auth_request:
            raise ValueError("Invalid or expired authentication request")
        
        # Get provider config
        provider_key = f"{tenant_id}_{auth_request.provider_id}"
        config = self.identity_providers.get(provider_key)
        
        if not config:
            raise ValueError("Identity provider not found")
        
        # Exchange code for token
        token_response = await self._exchange_oauth_code(config, code)
        
        # Get user info
        user_info = await self._get_oauth_user_info(config, token_response["access_token"])
        
        # Create or update user
        user = await self._provision_user(tenant_id, auth_request.provider_id, user_info)
        
        # Create SSO session
        session = await self._create_sso_session(tenant_id, user["id"], auth_request.provider_id, user_info)
        
        # Clean up auth request
        del self.auth_requests[request_id]
        
        return {
            "success": True,
            "user": user,
            "session_id": session.session_id,
            "return_url": auth_request.return_url
        }
    
    async def _exchange_oauth_code(self, config: IdentityProviderConfig, code: str) -> Dict[str, Any]:
        """Exchange OAuth code for access token"""
        
        # This would make an actual HTTP request to the token endpoint
        # For now, return a mock response
        return {
            "access_token": "mock_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
    
    async def _get_oauth_user_info(self, config: IdentityProviderConfig, access_token: str) -> Dict[str, Any]:
        """Get user information from OAuth provider"""
        
        # This would make an actual HTTP request to the userinfo endpoint
        # For now, return mock user info
        return {
            "email": "user@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "picture": "https://example.com/avatar.jpg"
        }
    
    async def _provision_user(
        self,
        tenant_id: str,
        provider_id: str,
        user_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Provision user based on SSO information"""
        
        # Get provider config
        provider_key = f"{tenant_id}_{provider_id}"
        config = self.identity_providers.get(provider_key)
        
        if not config:
            raise ValueError("Identity provider not found")
        
        # Map attributes
        mapped_attributes = self._map_user_attributes(user_info, config.attribute_mapping)
        
        # Create provisioning event
        event = UserProvisioningEvent(
            event_id=f"provision_{uuid.uuid4().hex}",
            tenant_id=tenant_id,
            provider_id=provider_id,
            user_id=mapped_attributes.get("email", "unknown"),
            action="created",
            attributes=mapped_attributes
        )
        
        self.provisioning_events.append(event)
        
        # This would integrate with the user management service
        # For now, return a mock user
        return {
            "id": f"user_{uuid.uuid4().hex}",
            "email": mapped_attributes.get("email"),
            "first_name": mapped_attributes.get("first_name"),
            "last_name": mapped_attributes.get("last_name"),
            "display_name": mapped_attributes.get("display_name"),
            "tenant_id": tenant_id,
            "sso_provider": provider_id
        }
    
    def _map_user_attributes(self, user_info: Dict[str, Any], attribute_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Map user attributes based on provider configuration"""
        
        mapped = {}
        
        for internal_attr, external_attr in attribute_mapping.items():
            if external_attr in user_info:
                mapped[internal_attr] = user_info[external_attr]
        
        return mapped
    
    async def _create_sso_session(
        self,
        tenant_id: str,
        user_id: str,
        provider_id: str,
        user_info: Dict[str, Any]
    ) -> SSOSession:
        """Create SSO session"""
        
        session_id = f"sso_{uuid.uuid4().hex}"
        expires_at = datetime.utcnow() + timedelta(hours=8)  # Default 8 hours
        
        session = SSOSession(
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
            provider_id=provider_id,
            expires_at=expires_at,
            attributes=user_info
        )
        
        self.active_sessions[session_id] = session
        
        logger.info(f"SSO session created: {session_id} for user {user_id}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[SSOSession]:
        """Get SSO session"""
        
        session = self.active_sessions.get(session_id)
        
        if session and session.is_expired():
            # Remove expired session
            del self.active_sessions[session_id]
            return None
        
        return session
    
    async def logout_session(self, session_id: str) -> bool:
        """Logout SSO session"""
        
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Remove session
            del self.active_sessions[session_id]
            
            # Initiate SLO if supported
            await self._initiate_single_logout(session)
            
            logger.info(f"SSO session logged out: {session_id}")
            return True
        
        return False
    
    async def _initiate_single_logout(self, session: SSOSession):
        """Initiate single logout with identity provider"""
        
        # Get provider config
        provider_key = f"{session.tenant_id}_{session.provider_id}"
        config = self.identity_providers.get(provider_key)
        
        if not config:
            return
        
        # This would initiate SLO based on provider type
        logger.debug(f"Single logout initiated for session {session.session_id}")
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired SSO sessions"""
        
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired SSO sessions")
    
    async def _sync_user_provisioning(self):
        """Sync user provisioning from identity providers"""
        
        for provider_key, config in self.identity_providers.items():
            if config.provisioning_method == ProvisioningMethod.SCIM:
                await self._sync_scim_users(config)
            elif config.provisioning_method == ProvisioningMethod.LDAP_SYNC:
                await self._sync_ldap_users(config)
    
    async def _sync_scim_users(self, config: IdentityProviderConfig):
        """Sync users via SCIM"""
        
        # This would make SCIM API calls to sync users
        logger.debug(f"SCIM user sync for provider {config.provider_id}")
    
    async def _sync_ldap_users(self, config: IdentityProviderConfig):
        """Sync users via LDAP"""
        
        # This would make LDAP queries to sync users
        logger.debug(f"LDAP user sync for provider {config.provider_id}")
    
    async def get_provider_metadata(self, tenant_id: str, provider_id: str) -> Dict[str, Any]:
        """Get SAML metadata for provider"""
        
        provider_key = f"{tenant_id}_{provider_id}"
        config = self.identity_providers.get(provider_key)
        
        if not config:
            raise ValueError("Identity provider not found")
        
        if config.auth_method != AuthenticationMethod.SAML2:
            raise ValueError("Metadata only available for SAML providers")
        
        # Generate SAML metadata
        metadata = self._generate_saml_metadata(config)
        
        return {
            "metadata": metadata,
            "content_type": "application/samlmetadata+xml"
        }
    
    def _generate_saml_metadata(self, config: IdentityProviderConfig) -> str:
        """Generate SAML metadata XML"""
        
        entity_id = self.base_url
        
        metadata = f"""<?xml version="1.0" encoding="UTF-8"?>
<md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata"
                     entityID="{entity_id}">
    <md:SPSSODescriptor AuthnRequestsSigned="false"
                        WantAssertionsSigned="true"
                        protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
        <md:AssertionConsumerService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                     Location="{self.sso_endpoints['saml_acs']}"
                                     index="1"/>
        <md:SingleLogoutService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
                                Location="{self.sso_endpoints['saml_sls']}"/>
    </md:SPSSODescriptor>
</md:EntityDescriptor>"""
        
        return metadata
    
    async def get_sso_statistics(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get SSO usage statistics"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Filter provisioning events
        events = [
            e for e in self.provisioning_events
            if e.tenant_id == tenant_id and e.timestamp >= start_date
        ]
        
        # Calculate statistics
        stats = {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_logins": len([e for e in events if e.action == "login"]),
            "total_provisioning": len([e for e in events if e.action in ["created", "updated"]]),
            "active_sessions": len([s for s in self.active_sessions.values() if s.tenant_id == tenant_id]),
            "providers": {},
            "daily_logins": [],
            "provisioning_by_action": {}
        }
        
        # Provider breakdown
        for event in events:
            provider = event.provider_id
            if provider not in stats["providers"]:
                stats["providers"][provider] = 0
            stats["providers"][provider] += 1
        
        # Provisioning by action
        for event in events:
            action = event.action
            if action not in stats["provisioning_by_action"]:
                stats["provisioning_by_action"][action] = 0
            stats["provisioning_by_action"][action] += 1
        
        return stats


# Global service instance
sso_service = EnterpriseSSOService()
