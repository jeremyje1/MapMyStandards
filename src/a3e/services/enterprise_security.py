"""
Enterprise Security Service
Advanced security features including SSO, MFA, RBAC, and compliance
Part of Phase M3: Enterprise Features
"""

import logging
import secrets
import hashlib
import hmac
import base64
import jwt
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import re
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuthProvider(Enum):
    """Supported authentication providers"""
    LOCAL = "local"
    AZURE_AD = "azure_ad"
    OKTA = "okta"
    GOOGLE_WORKSPACE = "google_workspace"
    SAML2 = "saml2"
    LDAP = "ldap"
    ACTIVE_DIRECTORY = "active_directory"


class Permission(Enum):
    """System permissions"""
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_IMPERSONATE = "user:impersonate"
    
    # Organization management
    ORG_CREATE = "org:create"
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_DELETE = "org:delete"
    ORG_MANAGE_USERS = "org:manage_users"
    
    # Document operations
    DOC_CREATE = "doc:create"
    DOC_READ = "doc:read"
    DOC_UPDATE = "doc:update"
    DOC_DELETE = "doc:delete"
    DOC_SHARE = "doc:share"
    DOC_EXPORT = "doc:export"
    
    # Analytics and reporting
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    ANALYTICS_ADMIN = "analytics:admin"
    
    # PowerBI integration
    POWERBI_VIEW = "powerbi:view"
    POWERBI_CREATE = "powerbi:create"
    POWERBI_ADMIN = "powerbi:admin"
    
    # System administration
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_AUDIT = "system:audit"
    
    # API access
    API_READ = "api:read"
    API_WRITE = "api:write"
    API_ADMIN = "api:admin"


@dataclass
class Role:
    """Role-based access control role definition"""
    id: str
    name: str
    description: str
    permissions: Set[Permission]
    tenant_id: Optional[str] = None
    is_system_role: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    tenant_id: str
    
    # Password policy
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_symbols: bool = True
    password_history_count: int = 5
    password_expiry_days: int = 90
    
    # Account lockout policy
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30
    lockout_reset_time_minutes: int = 60
    
    # Session security
    session_timeout_minutes: int = 60
    session_absolute_timeout_hours: int = 8
    concurrent_sessions_limit: int = 3
    require_mfa: bool = False
    
    # IP restrictions
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    geo_restrictions: List[str] = field(default_factory=list)
    
    # Audit requirements
    audit_all_actions: bool = True
    audit_sensitive_data: bool = True
    audit_retention_days: int = 2555  # 7 years
    
    # Compliance settings
    require_data_encryption: bool = True
    require_secure_transport: bool = True
    data_residency_region: Optional[str] = None


@dataclass
class SecurityEvent:
    """Security event for audit logging"""
    event_id: str
    tenant_id: str
    user_id: Optional[str]
    event_type: str
    severity: SecurityLevel
    timestamp: datetime
    source_ip: str
    user_agent: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class MFADevice:
    """Multi-factor authentication device"""
    device_id: str
    user_id: str
    device_type: str  # "totp", "sms", "email", "hardware"
    device_name: str
    secret_key: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    is_primary: bool = False
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None


class EnterpriseSecurityService:
    """Enterprise-grade security service with advanced features"""
    
    def __init__(self):
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.roles: Dict[str, Role] = {}
        self.security_events: List[SecurityEvent] = []
        self.mfa_devices: Dict[str, List[MFADevice]] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.failed_attempts: Dict[str, Dict[str, Any]] = {}
        self.encryption_key = self._generate_encryption_key()
        
        # Initialize default system roles
        self._initialize_system_roles()
        
        # Initialize security monitoring
        self._start_security_monitoring()
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for sensitive data"""
        # In production, this would be loaded from secure key management
        password = b"mapmystandards_enterprise_key_2024"
        salt = b"security_salt_unique"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def _initialize_system_roles(self):
        """Initialize default system roles"""
        
        # Super Admin - Full system access
        super_admin = Role(
            id="super_admin",
            name="Super Administrator", 
            description="Full system administration access",
            permissions=set(Permission),
            is_system_role=True
        )
        
        # Organization Admin - Full org access
        org_admin = Role(
            id="org_admin",
            name="Organization Administrator",
            description="Full organizational administration access",
            permissions={
                Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
                Permission.ORG_READ, Permission.ORG_UPDATE, Permission.ORG_MANAGE_USERS,
                Permission.DOC_CREATE, Permission.DOC_READ, Permission.DOC_UPDATE, Permission.DOC_DELETE,
                Permission.DOC_SHARE, Permission.DOC_EXPORT,
                Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT,
                Permission.POWERBI_VIEW, Permission.POWERBI_CREATE,
                Permission.API_READ, Permission.API_WRITE
            },
            is_system_role=True
        )
        
        # Compliance Manager - Compliance focused access
        compliance_manager = Role(
            id="compliance_manager",
            name="Compliance Manager",
            description="Compliance management and reporting access",
            permissions={
                Permission.USER_READ,
                Permission.ORG_READ,
                Permission.DOC_CREATE, Permission.DOC_READ, Permission.DOC_UPDATE, Permission.DOC_EXPORT,
                Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT,
                Permission.POWERBI_VIEW, Permission.POWERBI_CREATE,
                Permission.API_READ
            },
            is_system_role=True
        )
        
        # Analyst - Read and analyze access
        analyst = Role(
            id="analyst",
            name="Analyst",
            description="Analysis and reporting access",
            permissions={
                Permission.USER_READ,
                Permission.ORG_READ,
                Permission.DOC_READ,
                Permission.ANALYTICS_VIEW,
                Permission.POWERBI_VIEW,
                Permission.API_READ
            },
            is_system_role=True
        )
        
        # End User - Basic access
        end_user = Role(
            id="end_user",
            name="End User",
            description="Basic user access",
            permissions={
                Permission.DOC_CREATE, Permission.DOC_READ, Permission.DOC_UPDATE,
                Permission.ANALYTICS_VIEW,
                Permission.POWERBI_VIEW
            },
            is_system_role=True
        )
        
        # Store system roles
        for role in [super_admin, org_admin, compliance_manager, analyst, end_user]:
            self.roles[role.id] = role
    
    def _start_security_monitoring(self):
        """Start background security monitoring tasks"""
        
        async def monitor_security_events():
            while True:
                try:
                    await self._check_security_threats()
                    await asyncio.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Security monitoring error: {e}")
                    await asyncio.sleep(300)  # Wait 5 minutes on error
        
        async def cleanup_expired_sessions():
            while True:
                try:
                    await self._cleanup_expired_sessions()
                    await asyncio.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Session cleanup error: {e}")
                    await asyncio.sleep(600)  # Wait 10 minutes on error
        
        # Start background tasks
        asyncio.create_task(monitor_security_events())
        asyncio.create_task(cleanup_expired_sessions())
    
    async def create_security_policy(self, tenant_id: str, policy_config: Dict[str, Any]) -> SecurityPolicy:
        """Create security policy for tenant"""
        
        policy = SecurityPolicy(tenant_id=tenant_id)
        
        # Apply configuration overrides
        for key, value in policy_config.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        self.security_policies[tenant_id] = policy
        
        await self._log_security_event(
            tenant_id=tenant_id,
            event_type="security_policy_created",
            severity=SecurityLevel.MEDIUM,
            description=f"Security policy created for tenant {tenant_id}"
        )
        
        return policy
    
    async def update_security_policy(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """Update security policy for tenant"""
        
        if tenant_id not in self.security_policies:
            return False
        
        policy = self.security_policies[tenant_id]
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        await self._log_security_event(
            tenant_id=tenant_id,
            event_type="security_policy_updated",
            severity=SecurityLevel.MEDIUM,
            description=f"Security policy updated for tenant {tenant_id}",
            metadata=updates
        )
        
        return True
    
    async def create_role(
        self,
        tenant_id: str,
        name: str,
        description: str,
        permissions: List[str]
    ) -> str:
        """Create custom role for tenant"""
        
        role_id = f"{tenant_id}_{name.lower().replace(' ', '_')}"
        
        # Convert permission strings to enum
        permission_set = set()
        for perm_str in permissions:
            try:
                permission_set.add(Permission(perm_str))
            except ValueError:
                logger.warning(f"Invalid permission: {perm_str}")
        
        role = Role(
            id=role_id,
            name=name,
            description=description,
            permissions=permission_set,
            tenant_id=tenant_id
        )
        
        self.roles[role_id] = role
        
        await self._log_security_event(
            tenant_id=tenant_id,
            event_type="role_created",
            severity=SecurityLevel.LOW,
            description=f"Custom role '{name}' created",
            metadata={"role_id": role_id, "permissions": permissions}
        )
        
        return role_id
    
    async def assign_role_to_user(self, tenant_id: str, user_id: str, role_id: str) -> bool:
        """Assign role to user"""
        
        if role_id not in self.roles:
            return False
        
        # This would integrate with user management system
        # For now, we'll just log the assignment
        
        await self._log_security_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="role_assigned",
            severity=SecurityLevel.LOW,
            description=f"Role {role_id} assigned to user {user_id}",
            metadata={"role_id": role_id}
        )
        
        return True
    
    async def check_permission(self, tenant_id: str, user_id: str, permission: Permission) -> bool:
        """Check if user has specific permission"""
        
        # This would integrate with user management system to get user roles
        # For now, we'll simulate permission checking
        
        # Log permission check for audit
        await self._log_security_event(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type="permission_checked",
            severity=SecurityLevel.LOW,
            description=f"Permission check: {permission.value}",
            metadata={"permission": permission.value, "granted": True}
        )
        
        return True  # Simplified for demo
    
    async def authenticate_user(
        self,
        tenant_id: str,
        username: str,
        password: str,
        source_ip: str,
        user_agent: str,
        provider: AuthProvider = AuthProvider.LOCAL
    ) -> Optional[Dict[str, Any]]:
        """Authenticate user with security checks"""
        
        # Check if account is locked
        if await self._is_account_locked(tenant_id, username):
            await self._log_security_event(
                tenant_id=tenant_id,
                event_type="auth_attempt_locked_account",
                severity=SecurityLevel.HIGH,
                description=f"Authentication attempt on locked account: {username}",
                source_ip=source_ip,
                user_agent=user_agent
            )
            return None
        
        # Check IP restrictions
        if not await self._check_ip_restrictions(tenant_id, source_ip):
            await self._log_security_event(
                tenant_id=tenant_id,
                event_type="auth_attempt_restricted_ip",
                severity=SecurityLevel.HIGH,
                description=f"Authentication attempt from restricted IP: {source_ip}",
                source_ip=source_ip,
                user_agent=user_agent,
                metadata={"username": username}
            )
            return None
        
        # Simulate authentication (would integrate with actual auth system)
        auth_success = await self._verify_credentials(username, password, provider)
        
        if auth_success:
            # Reset failed attempts
            await self._reset_failed_attempts(tenant_id, username)
            
            # Create session
            session_token = await self._create_session(tenant_id, username, source_ip, user_agent)
            
            await self._log_security_event(
                tenant_id=tenant_id,
                user_id=username,
                event_type="auth_success",
                severity=SecurityLevel.LOW,
                description=f"Successful authentication for user: {username}",
                source_ip=source_ip,
                user_agent=user_agent
            )
            
            return {
                "session_token": session_token,
                "user_id": username,
                "requires_mfa": await self._requires_mfa(tenant_id, username),
                "expires_at": (datetime.utcnow() + timedelta(hours=8)).isoformat()
            }
        else:
            # Record failed attempt
            await self._record_failed_attempt(tenant_id, username, source_ip)
            
            await self._log_security_event(
                tenant_id=tenant_id,
                event_type="auth_failure",
                severity=SecurityLevel.MEDIUM,
                description=f"Failed authentication attempt for user: {username}",
                source_ip=source_ip,
                user_agent=user_agent,
                metadata={"username": username}
            )
            
            return None
    
    async def setup_mfa_device(
        self,
        user_id: str,
        device_type: str,
        device_name: str,
        contact_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """Setup MFA device for user"""
        
        device_id = f"mfa_{secrets.token_hex(8)}"
        
        device = MFADevice(
            device_id=device_id,
            user_id=user_id,
            device_type=device_type,
            device_name=device_name
        )
        
        if device_type == "totp":
            # Generate TOTP secret
            device.secret_key = base64.b32encode(secrets.token_bytes(32)).decode()
        elif device_type == "sms":
            device.phone_number = contact_info
        elif device_type == "email":
            device.email = contact_info
        
        # Store device
        if user_id not in self.mfa_devices:
            self.mfa_devices[user_id] = []
        
        self.mfa_devices[user_id].append(device)
        
        # Return setup information
        result = {
            "device_id": device_id,
            "device_type": device_type,
            "device_name": device_name
        }
        
        if device_type == "totp":
            # Generate QR code URL for TOTP setup
            result["qr_code_url"] = f"otpauth://totp/MapMyStandards:{user_id}?secret={device.secret_key}&issuer=MapMyStandards"
            result["manual_entry_key"] = device.secret_key
        
        return result
    
    async def verify_mfa_code(self, user_id: str, device_id: str, code: str) -> bool:
        """Verify MFA code"""
        
        if user_id not in self.mfa_devices:
            return False
        
        device = None
        for d in self.mfa_devices[user_id]:
            if d.device_id == device_id:
                device = d
                break
        
        if not device:
            return False
        
        # Simulate MFA verification (would use actual TOTP/SMS verification)
        if device.device_type == "totp":
            # In real implementation, would verify TOTP code
            verified = len(code) == 6 and code.isdigit()
        else:
            # For SMS/email, would verify against sent code
            verified = len(code) == 6 and code.isdigit()
        
        if verified:
            device.last_used = datetime.utcnow()
            if not device.is_verified:
                device.is_verified = True
        
        return verified
    
    async def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for storage"""
        
        fernet = Fernet(self.encryption_key)
        encrypted_data = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    async def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        
        try:
            fernet = Fernet(self.encryption_key)
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise
    
    async def validate_password_policy(self, tenant_id: str, password: str, username: str = None) -> Dict[str, Any]:
        """Validate password against security policy"""
        
        policy = self.security_policies.get(tenant_id)
        if not policy:
            # Use default policy
            policy = SecurityPolicy(tenant_id=tenant_id)
        
        errors = []
        
        # Length check
        if len(password) < policy.password_min_length:
            errors.append(f"Password must be at least {policy.password_min_length} characters long")
        
        # Character requirements
        if policy.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if policy.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if policy.password_require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if policy.password_require_symbols and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Common password checks
        common_passwords = ["password", "123456", "admin", "user"]
        if password.lower() in common_passwords:
            errors.append("Password is too common")
        
        # Username similarity check
        if username and username.lower() in password.lower():
            errors.append("Password cannot contain username")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength_score": self._calculate_password_strength(password)
        }
    
    def _calculate_password_strength(self, password: str) -> int:
        """Calculate password strength score (0-100)"""
        
        score = 0
        
        # Length scoring
        if len(password) >= 8:
            score += 20
        if len(password) >= 12:
            score += 20
        if len(password) >= 16:
            score += 10
        
        # Character variety
        if re.search(r'[a-z]', password):
            score += 10
        if re.search(r'[A-Z]', password):
            score += 10
        if re.search(r'\d', password):
            score += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 20
        
        return min(score, 100)
    
    async def get_security_report(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Generate security report for tenant"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Filter events for tenant and date range
        tenant_events = [
            event for event in self.security_events
            if event.tenant_id == tenant_id and start_date <= event.timestamp <= end_date
        ]
        
        # Categorize events
        auth_events = [e for e in tenant_events if e.event_type.startswith('auth_')]
        security_violations = [e for e in tenant_events if e.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]]
        
        # Calculate metrics
        total_auth_attempts = len([e for e in auth_events if e.event_type in ['auth_success', 'auth_failure']])
        failed_auth_attempts = len([e for e in auth_events if e.event_type == 'auth_failure'])
        
        auth_success_rate = ((total_auth_attempts - failed_auth_attempts) / total_auth_attempts * 100) if total_auth_attempts > 0 else 0
        
        return {
            "tenant_id": tenant_id,
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "security_summary": {
                "total_security_events": len(tenant_events),
                "security_violations": len(security_violations),
                "auth_success_rate": round(auth_success_rate, 2)
            },
            "authentication_metrics": {
                "total_attempts": total_auth_attempts,
                "successful_attempts": total_auth_attempts - failed_auth_attempts,
                "failed_attempts": failed_auth_attempts,
                "locked_accounts": len(self._get_locked_accounts(tenant_id))
            },
            "security_events_by_type": self._group_events_by_type(tenant_events),
            "security_events_by_severity": self._group_events_by_severity(tenant_events),
            "top_security_risks": self._identify_top_risks(tenant_events),
            "recommendations": self._generate_security_recommendations(tenant_id, tenant_events)
        }
    
    # Private helper methods
    
    async def _is_account_locked(self, tenant_id: str, username: str) -> bool:
        """Check if account is locked due to failed attempts"""
        
        key = f"{tenant_id}_{username}"
        if key not in self.failed_attempts:
            return False
        
        attempt_data = self.failed_attempts[key]
        
        # Check if lockout period has expired
        if datetime.utcnow() > attempt_data.get('lockout_until', datetime.min):
            del self.failed_attempts[key]
            return False
        
        return attempt_data.get('locked', False)
    
    async def _check_ip_restrictions(self, tenant_id: str, source_ip: str) -> bool:
        """Check IP whitelist/blacklist restrictions"""
        
        policy = self.security_policies.get(tenant_id)
        if not policy:
            return True
        
        # Check blacklist
        if source_ip in policy.ip_blacklist:
            return False
        
        # Check whitelist (if configured)
        if policy.ip_whitelist and source_ip not in policy.ip_whitelist:
            return False
        
        return True
    
    async def _verify_credentials(self, username: str, password: str, provider: AuthProvider) -> bool:
        """Verify user credentials"""
        
        # Simulate credential verification
        # In real implementation, would integrate with actual auth systems
        
        if provider == AuthProvider.LOCAL:
            # Local database verification
            return len(username) > 0 and len(password) >= 8
        elif provider == AuthProvider.AZURE_AD:
            # Azure AD verification
            return True  # Simplified
        elif provider == AuthProvider.LDAP:
            # LDAP verification
            return True  # Simplified
        
        return False
    
    async def _record_failed_attempt(self, tenant_id: str, username: str, source_ip: str):
        """Record failed authentication attempt"""
        
        key = f"{tenant_id}_{username}"
        now = datetime.utcnow()
        
        if key not in self.failed_attempts:
            self.failed_attempts[key] = {
                'count': 0,
                'first_attempt': now,
                'last_attempt': now,
                'locked': False
            }
        
        attempt_data = self.failed_attempts[key]
        attempt_data['count'] += 1
        attempt_data['last_attempt'] = now
        
        # Check if should lock account
        policy = self.security_policies.get(tenant_id, SecurityPolicy(tenant_id=tenant_id))
        
        if attempt_data['count'] >= policy.max_failed_attempts:
            attempt_data['locked'] = True
            attempt_data['lockout_until'] = now + timedelta(minutes=policy.lockout_duration_minutes)
    
    async def _reset_failed_attempts(self, tenant_id: str, username: str):
        """Reset failed attempt counter"""
        
        key = f"{tenant_id}_{username}"
        if key in self.failed_attempts:
            del self.failed_attempts[key]
    
    async def _create_session(self, tenant_id: str, user_id: str, source_ip: str, user_agent: str) -> str:
        """Create authenticated session"""
        
        session_token = secrets.token_urlsafe(32)
        
        self.active_sessions[session_token] = {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'source_ip': source_ip,
            'user_agent': user_agent,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=8)
        }
        
        return session_token
    
    async def _requires_mfa(self, tenant_id: str, user_id: str) -> bool:
        """Check if user requires MFA"""
        
        policy = self.security_policies.get(tenant_id)
        if policy and policy.require_mfa:
            return True
        
        # Check if user has MFA devices configured
        return user_id in self.mfa_devices and len(self.mfa_devices[user_id]) > 0
    
    async def _log_security_event(
        self,
        tenant_id: str,
        event_type: str,
        severity: SecurityLevel,
        description: str,
        user_id: Optional[str] = None,
        source_ip: str = "unknown",
        user_agent: str = "unknown",
        metadata: Dict[str, Any] = None
    ):
        """Log security event"""
        
        event = SecurityEvent(
            event_id=f"sec_{secrets.token_hex(8)}",
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            source_ip=source_ip,
            user_agent=user_agent,
            description=description,
            metadata=metadata or {}
        )
        
        self.security_events.append(event)
        
        # Keep only last 10000 events
        if len(self.security_events) > 10000:
            self.security_events = self.security_events[-10000:]
    
    async def _check_security_threats(self):
        """Monitor for security threats"""
        
        # Check for suspicious patterns in recent events
        recent_events = [
            e for e in self.security_events 
            if e.timestamp > datetime.utcnow() - timedelta(minutes=10)
        ]
        
        # Check for brute force attacks
        failed_attempts_by_ip = {}
        for event in recent_events:
            if event.event_type == 'auth_failure':
                ip = event.source_ip
                failed_attempts_by_ip[ip] = failed_attempts_by_ip.get(ip, 0) + 1
        
        for ip, count in failed_attempts_by_ip.items():
            if count >= 10:  # 10 failed attempts in 10 minutes
                await self._log_security_event(
                    tenant_id="system",
                    event_type="potential_brute_force_attack",
                    severity=SecurityLevel.CRITICAL,
                    description=f"Potential brute force attack from IP: {ip}",
                    source_ip=ip,
                    metadata={"failed_attempts": count}
                )
    
    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_token, session_data in self.active_sessions.items():
            if now > session_data['expires_at']:
                expired_sessions.append(session_token)
        
        for session_token in expired_sessions:
            del self.active_sessions[session_token]
    
    def _get_locked_accounts(self, tenant_id: str) -> List[str]:
        """Get list of currently locked accounts"""
        
        locked_accounts = []
        for key, attempt_data in self.failed_attempts.items():
            if key.startswith(f"{tenant_id}_") and attempt_data.get('locked', False):
                username = key.replace(f"{tenant_id}_", "")
                locked_accounts.append(username)
        
        return locked_accounts
    
    def _group_events_by_type(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Group security events by type"""
        
        event_counts = {}
        for event in events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        return event_counts
    
    def _group_events_by_severity(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Group security events by severity"""
        
        severity_counts = {}
        for event in events:
            severity = event.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return severity_counts
    
    def _identify_top_risks(self, events: List[SecurityEvent]) -> List[Dict[str, Any]]:
        """Identify top security risks"""
        
        risks = []
        
        # Analyze patterns in security events
        high_severity_events = [e for e in events if e.severity == SecurityLevel.HIGH]
        critical_events = [e for e in events if e.severity == SecurityLevel.CRITICAL]
        
        if len(critical_events) > 0:
            risks.append({
                "risk": "Critical security events detected",
                "count": len(critical_events),
                "severity": "critical",
                "description": "Multiple critical security events require immediate attention"
            })
        
        if len(high_severity_events) > 5:
            risks.append({
                "risk": "High number of security violations",
                "count": len(high_severity_events),
                "severity": "high",
                "description": "Unusual number of security violations detected"
            })
        
        return risks
    
    def _generate_security_recommendations(self, tenant_id: str, events: List[SecurityEvent]) -> List[str]:
        """Generate security recommendations"""
        
        recommendations = []
        
        # Check if MFA is enabled
        policy = self.security_policies.get(tenant_id)
        if not policy or not policy.require_mfa:
            recommendations.append("Enable multi-factor authentication for enhanced security")
        
        # Check for failed authentication attempts
        failed_auth_count = len([e for e in events if e.event_type == 'auth_failure'])
        if failed_auth_count > 10:
            recommendations.append("Review failed authentication attempts and consider implementing IP restrictions")
        
        # Check password policy
        if not policy or policy.password_min_length < 12:
            recommendations.append("Strengthen password policy with longer minimum length")
        
        # Check for security violations
        violations = len([e for e in events if e.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]])
        if violations > 0:
            recommendations.append("Investigate and resolve security violations immediately")
        
        return recommendations


# Global service instance
enterprise_security = EnterpriseSecurityService()
