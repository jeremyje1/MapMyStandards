"""
Multi-Tenant Architecture Service
Enterprise-grade multi-tenancy with organization isolation
Part of Phase M3: Enterprise Features
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class TenantStatus(Enum):
    """Tenant status enumeration"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"
    PENDING_SETUP = "pending_setup"


class TenantTier(Enum):
    """Tenant subscription tiers"""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    ENTERPRISE_PLUS = "enterprise_plus"


@dataclass
class TenantConfiguration:
    """Tenant-specific configuration"""
    tenant_id: str
    organization_name: str
    domain: str
    status: TenantStatus
    tier: TenantTier
    created_at: datetime
    last_accessed: datetime
    
    # Subscription details
    subscription_id: Optional[str] = None
    subscription_expires: Optional[datetime] = None
    trial_expires: Optional[datetime] = None
    
    # Resource limits
    max_users: int = 10
    max_documents: int = 1000
    max_storage_gb: int = 5
    api_rate_limit: int = 1000  # requests per hour
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        "advanced_analytics": False,
        "custom_dashboards": False,
        "api_access": True,
        "sso_integration": False,
        "audit_logs": False,
        "white_labeling": False,
        "priority_support": False,
        "custom_integrations": False
    })
    
    # Database configuration
    database_schema: str = ""
    isolation_level: str = "schema"  # schema, database, or shared
    
    # Security settings
    security_config: Dict[str, Any] = field(default_factory=lambda: {
        "password_policy": {
            "min_length": 8,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_symbols": False,
            "expiry_days": 90
        },
        "session_timeout": 3600,  # seconds
        "mfa_required": False,
        "ip_whitelist": [],
        "allowed_domains": []
    })
    
    # Integration settings
    integrations: Dict[str, Any] = field(default_factory=dict)
    
    # Custom branding
    branding: Dict[str, str] = field(default_factory=lambda: {
        "logo_url": "",
        "primary_color": "#667eea",
        "secondary_color": "#764ba2",
        "organization_name": "",
        "support_email": "",
        "support_phone": ""
    })


@dataclass
class TenantUsage:
    """Tenant resource usage tracking"""
    tenant_id: str
    period_start: datetime
    period_end: datetime
    
    # Usage metrics
    active_users: int = 0
    total_users: int = 0
    documents_processed: int = 0
    storage_used_gb: float = 0.0
    api_requests: int = 0
    powerbi_reports_generated: int = 0
    
    # Cost tracking
    compute_hours: float = 0.0
    bandwidth_gb: float = 0.0
    
    # Performance metrics
    avg_response_time_ms: float = 0.0
    error_rate: float = 0.0
    uptime_percentage: float = 100.0


class MultiTenantService:
    """Service for managing multi-tenant architecture and organization isolation"""
    
    def __init__(self):
        self.tenants: Dict[str, TenantConfiguration] = {}
        self.tenant_usage: Dict[str, List[TenantUsage]] = {}
        self.tenant_cache: Dict[str, Dict[str, Any]] = {}
        self._initialize_default_configurations()
    
    def _initialize_default_configurations(self):
        """Initialize default tenant configurations for different tiers"""
        
        self.tier_defaults = {
            TenantTier.BASIC: {
                "max_users": 5,
                "max_documents": 100,
                "max_storage_gb": 1,
                "api_rate_limit": 100,
                "features": {
                    "advanced_analytics": False,
                    "custom_dashboards": False,
                    "api_access": True,
                    "sso_integration": False,
                    "audit_logs": False,
                    "white_labeling": False,
                    "priority_support": False,
                    "custom_integrations": False
                }
            },
            TenantTier.PROFESSIONAL: {
                "max_users": 25,
                "max_documents": 1000,
                "max_storage_gb": 10,
                "api_rate_limit": 1000,
                "features": {
                    "advanced_analytics": True,
                    "custom_dashboards": True,
                    "api_access": True,
                    "sso_integration": False,
                    "audit_logs": True,
                    "white_labeling": False,
                    "priority_support": False,
                    "custom_integrations": False
                }
            },
            TenantTier.ENTERPRISE: {
                "max_users": 100,
                "max_documents": 10000,
                "max_storage_gb": 100,
                "api_rate_limit": 5000,
                "features": {
                    "advanced_analytics": True,
                    "custom_dashboards": True,
                    "api_access": True,
                    "sso_integration": True,
                    "audit_logs": True,
                    "white_labeling": True,
                    "priority_support": True,
                    "custom_integrations": True
                }
            },
            TenantTier.ENTERPRISE_PLUS: {
                "max_users": 500,
                "max_documents": 50000,
                "max_storage_gb": 500,
                "api_rate_limit": 25000,
                "features": {
                    "advanced_analytics": True,
                    "custom_dashboards": True,
                    "api_access": True,
                    "sso_integration": True,
                    "audit_logs": True,
                    "white_labeling": True,
                    "priority_support": True,
                    "custom_integrations": True
                }
            }
        }
    
    async def create_tenant(
        self,
        organization_name: str,
        domain: str,
        tier: TenantTier = TenantTier.TRIAL,
        admin_email: str = None,
        custom_config: Dict[str, Any] = None
    ) -> str:
        """Create a new tenant with organization isolation"""
        
        tenant_id = f"tenant_{uuid.uuid4().hex[:12]}"
        
        # Get default configuration for tier
        tier_config = self.tier_defaults.get(tier, self.tier_defaults[TenantTier.BASIC])
        
        # Create tenant configuration
        tenant_config = TenantConfiguration(
            tenant_id=tenant_id,
            organization_name=organization_name,
            domain=domain,
            status=TenantStatus.TRIAL if tier == TenantTier.BASIC else TenantStatus.PENDING_SETUP,
            tier=tier,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            database_schema=f"tenant_{tenant_id}",
            **tier_config
        )
        
        # Apply custom configuration overrides
        if custom_config:
            self._apply_custom_config(tenant_config, custom_config)
        
        # Set trial expiration for trial tenants
        if tier == TenantTier.BASIC:
            tenant_config.trial_expires = datetime.utcnow() + timedelta(days=14)
        
        # Store tenant configuration
        self.tenants[tenant_id] = tenant_config
        
        # Initialize tenant database schema
        await self._initialize_tenant_database(tenant_config)
        
        # Initialize usage tracking
        self.tenant_usage[tenant_id] = []
        
        # Create initial admin user if provided
        if admin_email:
            await self._create_tenant_admin(tenant_config, admin_email)
        
        logger.info(f"Created new tenant: {tenant_id} for organization: {organization_name}")
        
        return tenant_id
    
    def _apply_custom_config(self, tenant_config: TenantConfiguration, custom_config: Dict[str, Any]):
        """Apply custom configuration to tenant"""
        
        if "max_users" in custom_config:
            tenant_config.max_users = custom_config["max_users"]
        
        if "max_documents" in custom_config:
            tenant_config.max_documents = custom_config["max_documents"]
        
        if "max_storage_gb" in custom_config:
            tenant_config.max_storage_gb = custom_config["max_storage_gb"]
        
        if "features" in custom_config:
            tenant_config.features.update(custom_config["features"])
        
        if "branding" in custom_config:
            tenant_config.branding.update(custom_config["branding"])
        
        if "security_config" in custom_config:
            tenant_config.security_config.update(custom_config["security_config"])
    
    async def _initialize_tenant_database(self, tenant_config: TenantConfiguration):
        """Initialize isolated database schema for tenant"""
        
        schema_name = tenant_config.database_schema
        
        try:
            # Create schema (this would be done with actual database connection)
            logger.info(f"Creating database schema: {schema_name}")
            
            # In a real implementation, this would:
            # 1. Create dedicated database schema
            # 2. Create tenant-specific tables
            # 3. Set up proper indexes and constraints
            # 4. Configure backup and monitoring
            
            # Simulated database initialization
            tenant_config.status = TenantStatus.ACTIVE
            
        except Exception as e:
            logger.error(f"Failed to initialize tenant database: {e}")
            tenant_config.status = TenantStatus.SUSPENDED
            raise
    
    async def _create_tenant_admin(self, tenant_config: TenantConfiguration, admin_email: str):
        """Create initial admin user for tenant"""
        
        try:
            # This would integrate with the user management system
            logger.info(f"Creating admin user {admin_email} for tenant {tenant_config.tenant_id}")
            
            # In a real implementation, this would:
            # 1. Create user account in tenant schema
            # 2. Assign admin role
            # 3. Send welcome email
            # 4. Set up initial workspace
            
        except Exception as e:
            logger.error(f"Failed to create tenant admin: {e}")
            raise
    
    async def get_tenant(self, tenant_id: str) -> Optional[TenantConfiguration]:
        """Get tenant configuration by ID"""
        return self.tenants.get(tenant_id)
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[TenantConfiguration]:
        """Get tenant configuration by domain"""
        for tenant in self.tenants.values():
            if tenant.domain == domain:
                return tenant
        return None
    
    async def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> bool:
        """Update tenant configuration"""
        
        if tenant_id not in self.tenants:
            return False
        
        tenant = self.tenants[tenant_id]
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        
        # Update last accessed time
        tenant.last_accessed = datetime.utcnow()
        
        logger.info(f"Updated tenant configuration: {tenant_id}")
        return True
    
    async def suspend_tenant(self, tenant_id: str, reason: str = "Administrative action") -> bool:
        """Suspend tenant access"""
        
        if tenant_id not in self.tenants:
            return False
        
        tenant = self.tenants[tenant_id]
        tenant.status = TenantStatus.SUSPENDED
        
        # Log suspension
        await self._log_tenant_action(tenant_id, "tenant_suspended", {"reason": reason})
        
        logger.warning(f"Suspended tenant: {tenant_id}, reason: {reason}")
        return True
    
    async def reactivate_tenant(self, tenant_id: str) -> bool:
        """Reactivate suspended tenant"""
        
        if tenant_id not in self.tenants:
            return False
        
        tenant = self.tenants[tenant_id]
        tenant.status = TenantStatus.ACTIVE
        
        # Log reactivation
        await self._log_tenant_action(tenant_id, "tenant_reactivated", {})
        
        logger.info(f"Reactivated tenant: {tenant_id}")
        return True
    
    async def delete_tenant(self, tenant_id: str, confirm_deletion: bool = False) -> bool:
        """Delete tenant and all associated data"""
        
        if not confirm_deletion:
            raise ValueError("Deletion must be explicitly confirmed")
        
        if tenant_id not in self.tenants:
            return False
        
        tenant = self.tenants[tenant_id]
        
        try:
            # Delete tenant database schema
            await self._delete_tenant_database(tenant)
            
            # Remove from memory
            del self.tenants[tenant_id]
            if tenant_id in self.tenant_usage:
                del self.tenant_usage[tenant_id]
            if tenant_id in self.tenant_cache:
                del self.tenant_cache[tenant_id]
            
            logger.warning(f"Deleted tenant: {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete tenant: {e}")
            return False
    
    async def _delete_tenant_database(self, tenant: TenantConfiguration):
        """Delete tenant database schema and all data"""
        
        schema_name = tenant.database_schema
        
        try:
            # In a real implementation, this would:
            # 1. Backup tenant data
            # 2. Drop database schema
            # 3. Clean up associated resources
            # 4. Update monitoring and backups
            
            logger.info(f"Deleted database schema: {schema_name}")
            
        except Exception as e:
            logger.error(f"Failed to delete tenant database: {e}")
            raise
    
    async def check_tenant_limits(self, tenant_id: str, resource_type: str, requested_amount: int = 1) -> bool:
        """Check if tenant can use additional resources"""
        
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return False
        
        # Get current usage
        current_usage = await self.get_tenant_current_usage(tenant_id)
        
        if resource_type == "users":
            return current_usage.total_users + requested_amount <= tenant.max_users
        elif resource_type == "documents":
            return current_usage.documents_processed + requested_amount <= tenant.max_documents
        elif resource_type == "storage":
            return current_usage.storage_used_gb + requested_amount <= tenant.max_storage_gb
        elif resource_type == "api_requests":
            return current_usage.api_requests + requested_amount <= tenant.api_rate_limit
        
        return True
    
    async def record_tenant_usage(
        self,
        tenant_id: str,
        usage_type: str,
        amount: float = 1.0,
        metadata: Dict[str, Any] = None
    ):
        """Record tenant resource usage"""
        
        # Get or create current usage period
        current_usage = await self.get_tenant_current_usage(tenant_id)
        
        # Update usage metrics
        if usage_type == "api_request":
            current_usage.api_requests += int(amount)
        elif usage_type == "document_processed":
            current_usage.documents_processed += int(amount)
        elif usage_type == "storage_used":
            current_usage.storage_used_gb += amount
        elif usage_type == "compute_time":
            current_usage.compute_hours += amount
        elif usage_type == "bandwidth":
            current_usage.bandwidth_gb += amount
        
        # Update tenant last accessed time
        if tenant_id in self.tenants:
            self.tenants[tenant_id].last_accessed = datetime.utcnow()
    
    async def get_tenant_current_usage(self, tenant_id: str) -> TenantUsage:
        """Get current usage period for tenant"""
        
        if tenant_id not in self.tenant_usage:
            self.tenant_usage[tenant_id] = []
        
        usage_list = self.tenant_usage[tenant_id]
        
        # Check if current period exists
        now = datetime.utcnow()
        current_period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        for usage in usage_list:
            if usage.period_start == current_period_start:
                return usage
        
        # Create new usage period
        new_usage = TenantUsage(
            tenant_id=tenant_id,
            period_start=current_period_start,
            period_end=current_period_start + timedelta(days=32)  # Next month
        )
        
        usage_list.append(new_usage)
        return new_usage
    
    async def get_tenant_analytics(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get tenant analytics and usage insights"""
        
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            return {}
        
        current_usage = await self.get_tenant_current_usage(tenant_id)
        
        # Calculate utilization percentages
        user_utilization = (current_usage.total_users / tenant.max_users) * 100
        storage_utilization = (current_usage.storage_used_gb / tenant.max_storage_gb) * 100
        document_utilization = (current_usage.documents_processed / tenant.max_documents) * 100
        
        return {
            "tenant_info": {
                "tenant_id": tenant_id,
                "organization_name": tenant.organization_name,
                "tier": tenant.tier.value,
                "status": tenant.status.value,
                "created_at": tenant.created_at.isoformat(),
                "last_accessed": tenant.last_accessed.isoformat()
            },
            "current_usage": {
                "users": {
                    "current": current_usage.total_users,
                    "limit": tenant.max_users,
                    "utilization_percent": user_utilization
                },
                "storage": {
                    "current_gb": current_usage.storage_used_gb,
                    "limit_gb": tenant.max_storage_gb,
                    "utilization_percent": storage_utilization
                },
                "documents": {
                    "current": current_usage.documents_processed,
                    "limit": tenant.max_documents,
                    "utilization_percent": document_utilization
                },
                "api_requests": {
                    "current": current_usage.api_requests,
                    "limit": tenant.api_rate_limit
                }
            },
            "performance": {
                "avg_response_time_ms": current_usage.avg_response_time_ms,
                "error_rate": current_usage.error_rate,
                "uptime_percentage": current_usage.uptime_percentage
            },
            "features_enabled": tenant.features,
            "subscription": {
                "expires": tenant.subscription_expires.isoformat() if tenant.subscription_expires else None,
                "trial_expires": tenant.trial_expires.isoformat() if tenant.trial_expires else None
            }
        }
    
    async def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        tier: Optional[TenantTier] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List tenants with optional filtering"""
        
        tenants = list(self.tenants.values())
        
        # Apply filters
        if status:
            tenants = [t for t in tenants if t.status == status]
        
        if tier:
            tenants = [t for t in tenants if t.tier == tier]
        
        # Sort by creation date (newest first)
        tenants.sort(key=lambda t: t.created_at, reverse=True)
        
        # Apply pagination
        tenants = tenants[offset:offset + limit]
        
        # Return summary information
        return [
            {
                "tenant_id": tenant.tenant_id,
                "organization_name": tenant.organization_name,
                "domain": tenant.domain,
                "status": tenant.status.value,
                "tier": tenant.tier.value,
                "created_at": tenant.created_at.isoformat(),
                "last_accessed": tenant.last_accessed.isoformat(),
                "user_count": await self._get_tenant_user_count(tenant.tenant_id)
            }
            for tenant in tenants
        ]
    
    async def _get_tenant_user_count(self, tenant_id: str) -> int:
        """Get current user count for tenant"""
        # This would query the actual user database
        current_usage = await self.get_tenant_current_usage(tenant_id)
        return current_usage.total_users
    
    async def _log_tenant_action(self, tenant_id: str, action: str, metadata: Dict[str, Any]):
        """Log tenant-related actions for audit trail"""
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "action": action,
            "metadata": metadata
        }
        
        # This would integrate with the audit logging system
        logger.info(f"Tenant action logged: {action} for {tenant_id}")
    
    async def get_platform_analytics(self) -> Dict[str, Any]:
        """Get platform-wide tenant analytics"""
        
        total_tenants = len(self.tenants)
        active_tenants = len([t for t in self.tenants.values() if t.status == TenantStatus.ACTIVE])
        trial_tenants = len([t for t in self.tenants.values() if t.status == TenantStatus.TRIAL])
        
        # Calculate tier distribution
        tier_distribution = {}
        for tier in TenantTier:
            count = len([t for t in self.tenants.values() if t.tier == tier])
            tier_distribution[tier.value] = count
        
        # Calculate total usage across all tenants
        total_users = 0
        total_documents = 0
        total_storage = 0.0
        total_api_requests = 0
        
        for tenant_id in self.tenants.keys():
            usage = await self.get_tenant_current_usage(tenant_id)
            total_users += usage.total_users
            total_documents += usage.documents_processed
            total_storage += usage.storage_used_gb
            total_api_requests += usage.api_requests
        
        return {
            "platform_summary": {
                "total_tenants": total_tenants,
                "active_tenants": active_tenants,
                "trial_tenants": trial_tenants,
                "suspended_tenants": total_tenants - active_tenants - trial_tenants
            },
            "tier_distribution": tier_distribution,
            "resource_usage": {
                "total_users": total_users,
                "total_documents_processed": total_documents,
                "total_storage_gb": total_storage,
                "total_api_requests": total_api_requests
            },
            "generated_at": datetime.utcnow().isoformat()
        }


# Global service instance
multi_tenant_service = MultiTenantService()
