"""
Enterprise API Governance Service
Comprehensive API management, rate limiting, and governance
Part of Phase M3: Enterprise Features
"""

import logging
import json
import time
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import uuid
from collections import defaultdict, deque
import jwt
import secrets

logger = logging.getLogger(__name__)


class APIAccessLevel(Enum):
    """API access levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    PARTNER = "partner"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class RateLimitType(Enum):
    """Rate limit types"""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    CONCURRENT_REQUESTS = "concurrent_requests"
    BANDWIDTH_PER_SECOND = "bandwidth_per_second"


class APIMethod(Enum):
    """HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class APIKeyStatus(Enum):
    """API key status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


@dataclass
class RateLimit:
    """Rate limit configuration"""
    limit_type: RateLimitType
    value: int
    window_seconds: int
    burst_allowance: int = 0
    
    def __post_init__(self):
        """Set default window based on limit type"""
        if self.window_seconds == 0:
            if self.limit_type == RateLimitType.REQUESTS_PER_MINUTE:
                self.window_seconds = 60
            elif self.limit_type == RateLimitType.REQUESTS_PER_HOUR:
                self.window_seconds = 3600
            elif self.limit_type == RateLimitType.REQUESTS_PER_DAY:
                self.window_seconds = 86400


@dataclass
class APIEndpoint:
    """API endpoint configuration"""
    endpoint_id: str
    path: str
    method: APIMethod
    access_level: APIAccessLevel
    description: str
    
    # Rate limiting
    rate_limits: List[RateLimit] = field(default_factory=list)
    
    # Authentication requirements
    requires_authentication: bool = True
    requires_api_key: bool = False
    allowed_roles: List[str] = field(default_factory=list)
    allowed_scopes: List[str] = field(default_factory=list)
    
    # Caching
    cache_ttl: int = 0  # seconds, 0 = no cache
    cache_vary_headers: List[str] = field(default_factory=list)
    
    # Documentation
    summary: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    response_schemas: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Monitoring
    enabled: bool = True
    deprecated: bool = False
    deprecation_date: Optional[datetime] = None
    replacement_endpoint: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    version: str = "1.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class APIKey:
    """API key for authentication"""
    key_id: str
    key_hash: str  # Hashed API key
    tenant_id: str
    name: str
    description: str
    
    # Access control
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    access_level: APIAccessLevel = APIAccessLevel.INTERNAL
    allowed_endpoints: List[str] = field(default_factory=list)  # Empty = all allowed
    allowed_methods: List[APIMethod] = field(default_factory=list)  # Empty = all allowed
    allowed_ips: List[str] = field(default_factory=list)  # Empty = all IPs allowed
    
    # Rate limiting overrides
    custom_rate_limits: List[RateLimit] = field(default_factory=list)
    
    # Lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    
    # Usage tracking
    total_requests: int = 0
    total_bytes: int = 0
    
    # Security
    requires_ip_whitelist: bool = False
    requires_user_agent: Optional[str] = None
    
    def is_valid(self) -> bool:
        """Check if API key is valid"""
        if self.status != APIKeyStatus.ACTIVE:
            return False
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        return True
    
    def is_endpoint_allowed(self, endpoint_id: str) -> bool:
        """Check if endpoint is allowed for this key"""
        if not self.allowed_endpoints:
            return True  # All endpoints allowed
        
        return endpoint_id in self.allowed_endpoints
    
    def is_method_allowed(self, method: APIMethod) -> bool:
        """Check if HTTP method is allowed"""
        if not self.allowed_methods:
            return True  # All methods allowed
        
        return method in self.allowed_methods


@dataclass
class APIRequest:
    """API request record"""
    request_id: str
    tenant_id: str
    endpoint_id: str
    method: APIMethod
    path: str
    
    # Authentication
    api_key_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Request details
    source_ip: str = "unknown"
    user_agent: str = "unknown"
    request_size: int = 0
    
    # Response details
    status_code: Optional[int] = None
    response_size: int = 0
    response_time_ms: float = 0
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Headers
    request_headers: Dict[str, str] = field(default_factory=dict)
    response_headers: Dict[str, str] = field(default_factory=dict)
    
    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Rate limiting
    rate_limit_hit: bool = False
    rate_limit_type: Optional[RateLimitType] = None
    
    # Caching
    cache_hit: bool = False
    
    def mark_completed(self, status_code: int, response_size: int = 0):
        """Mark request as completed"""
        self.completed_at = datetime.utcnow()
        self.status_code = status_code
        self.response_size = response_size
        
        if self.completed_at:
            self.response_time_ms = (self.completed_at - self.timestamp).total_seconds() * 1000


@dataclass
class RateLimitBucket:
    """Rate limit bucket for tracking usage"""
    key: str
    limit: RateLimit
    requests: deque = field(default_factory=deque)
    current_count: int = 0
    reset_time: datetime = field(default_factory=datetime.utcnow)
    
    def is_allowed(self, current_time: datetime) -> bool:
        """Check if request is allowed under rate limit"""
        
        # Clean old requests outside window
        cutoff_time = current_time - timedelta(seconds=self.limit.window_seconds)
        while self.requests and self.requests[0] < cutoff_time:
            self.requests.popleft()
            self.current_count -= 1
        
        # Check if under limit
        return self.current_count < self.limit.value
    
    def add_request(self, current_time: datetime):
        """Add request to bucket"""
        self.requests.append(current_time)
        self.current_count += 1
    
    def get_reset_time(self, current_time: datetime) -> datetime:
        """Get time when bucket resets"""
        if not self.requests:
            return current_time
        
        return self.requests[0] + timedelta(seconds=self.limit.window_seconds)


class EnterpriseAPIGovernanceService:
    """Enterprise API governance service"""
    
    def __init__(self):
        self.endpoints: Dict[str, APIEndpoint] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.rate_limit_buckets: Dict[str, RateLimitBucket] = {}
        self.active_requests: Dict[str, APIRequest] = {}
        self.request_history: List[APIRequest] = []
        
        # Caching
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Security
        self.jwt_secret = secrets.token_urlsafe(32)
        self.blocked_ips: Set[str] = set()
        self.suspicious_activities: Dict[str, List[datetime]] = defaultdict(list)
        
        # Performance monitoring
        self.endpoint_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Initialize default endpoints
        self._initialize_default_endpoints()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _initialize_default_endpoints(self):
        """Initialize default API endpoints"""
        
        # Authentication endpoints
        auth_endpoints = [
            APIEndpoint(
                endpoint_id="auth_login",
                path="/api/v1/auth/login",
                method=APIMethod.POST,
                access_level=APIAccessLevel.PUBLIC,
                description="User authentication",
                requires_authentication=False,
                rate_limits=[RateLimit(RateLimitType.REQUESTS_PER_MINUTE, 10, 60)]
            ),
            APIEndpoint(
                endpoint_id="auth_refresh",
                path="/api/v1/auth/refresh",
                method=APIMethod.POST,
                access_level=APIAccessLevel.INTERNAL,
                description="Token refresh",
                rate_limits=[RateLimit(RateLimitType.REQUESTS_PER_MINUTE, 20, 60)]
            )
        ]
        
        # User management endpoints
        user_endpoints = [
            APIEndpoint(
                endpoint_id="users_list",
                path="/api/v1/users",
                method=APIMethod.GET,
                access_level=APIAccessLevel.INTERNAL,
                description="List users",
                allowed_roles=["admin", "user_manager"],
                rate_limits=[RateLimit(RateLimitType.REQUESTS_PER_MINUTE, 100, 60)],
                cache_ttl=300
            ),
            APIEndpoint(
                endpoint_id="users_create",
                path="/api/v1/users",
                method=APIMethod.POST,
                access_level=APIAccessLevel.INTERNAL,
                description="Create user",
                allowed_roles=["admin", "user_manager"],
                rate_limits=[RateLimit(RateLimitType.REQUESTS_PER_MINUTE, 20, 60)]
            )
        ]
        
        # Analytics endpoints
        analytics_endpoints = [
            APIEndpoint(
                endpoint_id="analytics_dashboard",
                path="/api/v1/analytics/dashboard",
                method=APIMethod.GET,
                access_level=APIAccessLevel.ENTERPRISE,
                description="Analytics dashboard data",
                allowed_roles=["admin", "analyst"],
                rate_limits=[RateLimit(RateLimitType.REQUESTS_PER_MINUTE, 50, 60)],
                cache_ttl=600
            )
        ]
        
        # Add all endpoints
        all_endpoints = auth_endpoints + user_endpoints + analytics_endpoints
        for endpoint in all_endpoints:
            self.endpoints[endpoint.endpoint_id] = endpoint
    
    def _start_background_tasks(self):
        """Start background API governance tasks"""
        
        async def cleanup_rate_limits():
            """Clean up expired rate limit buckets"""
            while True:
                try:
                    await self._cleanup_rate_limits()
                    await asyncio.sleep(300)  # Run every 5 minutes
                except Exception as e:
                    logger.error(f"Rate limit cleanup error: {e}")
                    await asyncio.sleep(600)
        
        async def cleanup_cache():
            """Clean up expired cache entries"""
            while True:
                try:
                    await self._cleanup_cache()
                    await asyncio.sleep(600)  # Run every 10 minutes
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
                    await asyncio.sleep(1200)
        
        async def monitor_security():
            """Monitor for security threats"""
            while True:
                try:
                    await self._monitor_security_threats()
                    await asyncio.sleep(60)  # Run every minute
                except Exception as e:
                    logger.error(f"Security monitoring error: {e}")
                    await asyncio.sleep(300)
        
        async def update_metrics():
            """Update API performance metrics"""
            while True:
                try:
                    await self._update_performance_metrics()
                    await asyncio.sleep(300)  # Run every 5 minutes
                except Exception as e:
                    logger.error(f"Metrics update error: {e}")
                    await asyncio.sleep(600)
        
        # Start background tasks
        asyncio.create_task(cleanup_rate_limits())
        asyncio.create_task(cleanup_cache())
        asyncio.create_task(monitor_security())
        asyncio.create_task(update_metrics())
    
    async def create_api_key(
        self,
        tenant_id: str,
        name: str,
        description: str,
        access_level: APIAccessLevel = APIAccessLevel.INTERNAL,
        expires_in_days: Optional[int] = None
    ) -> Tuple[str, str]:
        """Create new API key"""
        
        # Generate API key
        key_id = f"ak_{uuid.uuid4().hex}"
        api_key = f"a3e_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # Create API key object
        api_key_obj = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            tenant_id=tenant_id,
            name=name,
            description=description,
            access_level=access_level,
            expires_at=expires_at
        )
        
        # Store API key
        self.api_keys[key_id] = api_key_obj
        
        logger.info(f"API key created: {key_id} for tenant {tenant_id}")
        return key_id, api_key  # Return both ID and the actual key
    
    async def authenticate_api_key(self, api_key: str) -> Optional[APIKey]:
        """Authenticate API key"""
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Find matching key
        for key_obj in self.api_keys.values():
            if key_obj.key_hash == key_hash and key_obj.is_valid():
                # Update last used
                key_obj.last_used_at = datetime.utcnow()
                return key_obj
        
        return None
    
    async def validate_request(
        self,
        tenant_id: str,
        endpoint_id: str,
        method: APIMethod,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        source_ip: str = "unknown",
        user_agent: str = "unknown"
    ) -> Dict[str, Any]:
        """Validate API request"""
        
        # Get endpoint configuration
        endpoint = self.endpoints.get(endpoint_id)
        if not endpoint or not endpoint.enabled:
            return {"allowed": False, "error": "Endpoint not found or disabled"}
        
        # Check if endpoint is deprecated
        if endpoint.deprecated:
            logger.warning(f"Deprecated endpoint accessed: {endpoint_id}")
        
        # Authenticate API key if provided
        api_key_obj = None
        if api_key:
            api_key_obj = await self.authenticate_api_key(api_key)
            if not api_key_obj:
                return {"allowed": False, "error": "Invalid API key"}
            
            # Check tenant match
            if api_key_obj.tenant_id != tenant_id:
                return {"allowed": False, "error": "API key tenant mismatch"}
            
            # Check endpoint access
            if not api_key_obj.is_endpoint_allowed(endpoint_id):
                return {"allowed": False, "error": "Endpoint not allowed for this API key"}
            
            # Check method access
            if not api_key_obj.is_method_allowed(method):
                return {"allowed": False, "error": "HTTP method not allowed for this API key"}
        
        # Check authentication requirements
        if endpoint.requires_authentication and not api_key_obj and not user_id:
            return {"allowed": False, "error": "Authentication required"}
        
        if endpoint.requires_api_key and not api_key_obj:
            return {"allowed": False, "error": "API key required"}
        
        # Check IP restrictions
        if api_key_obj and api_key_obj.allowed_ips:
            if source_ip not in api_key_obj.allowed_ips:
                return {"allowed": False, "error": "IP address not allowed"}
        
        # Check if IP is blocked
        if source_ip in self.blocked_ips:
            return {"allowed": False, "error": "IP address blocked"}
        
        # Check rate limits
        rate_limit_check = await self._check_rate_limits(
            tenant_id, endpoint_id, api_key_obj, source_ip
        )
        
        if not rate_limit_check["allowed"]:
            return rate_limit_check
        
        # Check access level
        if api_key_obj and api_key_obj.access_level.value < endpoint.access_level.value:
            return {"allowed": False, "error": "Insufficient access level"}
        
        return {
            "allowed": True,
            "api_key_id": api_key_obj.key_id if api_key_obj else None,
            "endpoint": endpoint,
            "rate_limit_info": rate_limit_check.get("rate_limit_info", {})
        }
    
    async def _check_rate_limits(
        self,
        tenant_id: str,
        endpoint_id: str,
        api_key_obj: Optional[APIKey],
        source_ip: str
    ) -> Dict[str, Any]:
        """Check rate limits for request"""
        
        current_time = datetime.utcnow()
        endpoint = self.endpoints.get(endpoint_id)
        
        if not endpoint:
            return {"allowed": True}
        
        # Determine applicable rate limits
        rate_limits = endpoint.rate_limits.copy()
        
        # Add custom rate limits from API key
        if api_key_obj and api_key_obj.custom_rate_limits:
            rate_limits.extend(api_key_obj.custom_rate_limits)
        
        rate_limit_info = {}
        
        # Check each rate limit
        for rate_limit in rate_limits:
            # Create bucket key based on scope
            if api_key_obj:
                bucket_key = f"{api_key_obj.key_id}_{rate_limit.limit_type.value}"
            else:
                bucket_key = f"{tenant_id}_{source_ip}_{endpoint_id}_{rate_limit.limit_type.value}"
            
            # Get or create bucket
            if bucket_key not in self.rate_limit_buckets:
                self.rate_limit_buckets[bucket_key] = RateLimitBucket(
                    key=bucket_key,
                    limit=rate_limit
                )
            
            bucket = self.rate_limit_buckets[bucket_key]
            
            # Check if request is allowed
            if not bucket.is_allowed(current_time):
                reset_time = bucket.get_reset_time(current_time)
                return {
                    "allowed": False,
                    "error": f"Rate limit exceeded: {rate_limit.limit_type.value}",
                    "rate_limit_type": rate_limit.limit_type,
                    "reset_time": reset_time,
                    "retry_after": int((reset_time - current_time).total_seconds())
                }
            
            # Add to rate limit info
            rate_limit_info[rate_limit.limit_type.value] = {
                "limit": rate_limit.value,
                "remaining": rate_limit.value - bucket.current_count,
                "reset_time": bucket.get_reset_time(current_time)
            }
        
        return {
            "allowed": True,
            "rate_limit_info": rate_limit_info
        }
    
    async def record_request(
        self,
        tenant_id: str,
        endpoint_id: str,
        method: APIMethod,
        path: str,
        api_key_id: Optional[str] = None,
        user_id: Optional[str] = None,
        source_ip: str = "unknown",
        user_agent: str = "unknown",
        request_size: int = 0
    ) -> str:
        """Record API request"""
        
        request_id = f"req_{uuid.uuid4().hex}"
        
        request = APIRequest(
            request_id=request_id,
            tenant_id=tenant_id,
            endpoint_id=endpoint_id,
            method=method,
            path=path,
            api_key_id=api_key_id,
            user_id=user_id,
            source_ip=source_ip,
            user_agent=user_agent,
            request_size=request_size
        )
        
        # Store active request
        self.active_requests[request_id] = request
        
        # Update rate limit buckets
        await self._update_rate_limit_buckets(tenant_id, endpoint_id, api_key_id, source_ip)
        
        # Update API key usage
        if api_key_id and api_key_id in self.api_keys:
            api_key_obj = self.api_keys[api_key_id]
            api_key_obj.total_requests += 1
            api_key_obj.total_bytes += request_size
        
        return request_id
    
    async def _update_rate_limit_buckets(
        self,
        tenant_id: str,
        endpoint_id: str,
        api_key_id: Optional[str],
        source_ip: str
    ):
        """Update rate limit buckets for request"""
        
        current_time = datetime.utcnow()
        endpoint = self.endpoints.get(endpoint_id)
        
        if not endpoint:
            return
        
        # Get applicable rate limits
        rate_limits = endpoint.rate_limits.copy()
        
        if api_key_id and api_key_id in self.api_keys:
            api_key_obj = self.api_keys[api_key_id]
            if api_key_obj.custom_rate_limits:
                rate_limits.extend(api_key_obj.custom_rate_limits)
        
        # Update each bucket
        for rate_limit in rate_limits:
            if api_key_id:
                bucket_key = f"{api_key_id}_{rate_limit.limit_type.value}"
            else:
                bucket_key = f"{tenant_id}_{source_ip}_{endpoint_id}_{rate_limit.limit_type.value}"
            
            if bucket_key in self.rate_limit_buckets:
                bucket = self.rate_limit_buckets[bucket_key]
                bucket.add_request(current_time)
    
    async def complete_request(
        self,
        request_id: str,
        status_code: int,
        response_size: int = 0,
        cache_hit: bool = False
    ):
        """Complete API request"""
        
        if request_id not in self.active_requests:
            logger.warning(f"Request not found: {request_id}")
            return
        
        request = self.active_requests[request_id]
        request.mark_completed(status_code, response_size)
        request.cache_hit = cache_hit
        
        # Move to history
        self.request_history.append(request)
        del self.active_requests[request_id]
        
        # Update API key usage
        if request.api_key_id and request.api_key_id in self.api_keys:
            api_key_obj = self.api_keys[request.api_key_id]
            api_key_obj.total_bytes += response_size
        
        # Check for suspicious activity
        await self._check_suspicious_activity(request)
        
        logger.debug(f"Request completed: {request_id} - {status_code}")
    
    async def _check_suspicious_activity(self, request: APIRequest):
        """Check for suspicious activity patterns"""
        
        current_time = datetime.utcnow()
        
        # Track by IP
        ip_activities = self.suspicious_activities[f"ip_{request.source_ip}"]
        ip_activities.append(current_time)
        
        # Clean old activities (last hour)
        cutoff = current_time - timedelta(hours=1)
        self.suspicious_activities[f"ip_{request.source_ip}"] = [
            t for t in ip_activities if t > cutoff
        ]
        
        # Check for high-frequency requests
        if len(ip_activities) > 1000:  # More than 1000 requests per hour
            logger.warning(f"High-frequency requests detected from IP: {request.source_ip}")
            await self._add_to_blocked_ips(request.source_ip, "high_frequency_requests")
        
        # Check for error patterns
        if request.status_code and request.status_code >= 400:
            error_key = f"errors_{request.source_ip}"
            error_activities = self.suspicious_activities[error_key]
            error_activities.append(current_time)
            
            # Clean old errors
            self.suspicious_activities[error_key] = [
                t for t in error_activities if t > cutoff
            ]
            
            # Block if too many errors
            if len(error_activities) > 100:  # More than 100 errors per hour
                logger.warning(f"High error rate detected from IP: {request.source_ip}")
                await self._add_to_blocked_ips(request.source_ip, "high_error_rate")
    
    async def _add_to_blocked_ips(self, ip: str, reason: str):
        """Add IP to blocked list"""
        
        self.blocked_ips.add(ip)
        logger.warning(f"IP blocked: {ip} - Reason: {reason}")
        
        # In a real implementation, this would integrate with a threat intelligence system
    
    async def get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached response"""
        
        if cache_key not in self.response_cache:
            return None
        
        metadata = self.cache_metadata.get(cache_key, {})
        expires_at = metadata.get("expires_at")
        
        if expires_at and datetime.utcnow() > expires_at:
            # Cache expired
            del self.response_cache[cache_key]
            del self.cache_metadata[cache_key]
            return None
        
        return self.response_cache[cache_key]
    
    async def cache_response(
        self,
        cache_key: str,
        response_data: Dict[str, Any],
        ttl_seconds: int
    ):
        """Cache response"""
        
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        
        self.response_cache[cache_key] = response_data
        self.cache_metadata[cache_key] = {
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "ttl_seconds": ttl_seconds
        }
    
    def generate_cache_key(
        self,
        endpoint_id: str,
        tenant_id: str,
        query_params: Dict[str, Any],
        vary_headers: Dict[str, str]
    ) -> str:
        """Generate cache key for request"""
        
        key_parts = [
            endpoint_id,
            tenant_id,
            json.dumps(query_params, sort_keys=True),
            json.dumps(vary_headers, sort_keys=True)
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke API key"""
        
        if key_id not in self.api_keys:
            return False
        
        api_key = self.api_keys[key_id]
        api_key.status = APIKeyStatus.REVOKED
        
        logger.info(f"API key revoked: {key_id}")
        return True
    
    async def get_api_usage_statistics(
        self,
        tenant_id: str,
        days: int = 30,
        api_key_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get API usage statistics"""
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Filter requests
        filtered_requests = []
        for r in self.request_history:
            tenant_match = r.tenant_id == tenant_id
            time_match = r.timestamp >= start_time
            key_match = not api_key_id or r.api_key_id == api_key_id
            
            if tenant_match and time_match and key_match:
                filtered_requests.append(r)
        
        # Calculate statistics
        stats = {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_requests": len(filtered_requests),
            "successful_requests": len([r for r in filtered_requests if r.status_code and r.status_code < 400]),
            "error_requests": len([r for r in filtered_requests if r.status_code and r.status_code >= 400]),
            "total_bytes_sent": sum(r.request_size for r in filtered_requests),
            "total_bytes_received": sum(r.response_size for r in filtered_requests),
            "cache_hit_rate": 0,
            "average_response_time": 0,
            "requests_by_endpoint": {},
            "requests_by_day": {},
            "requests_by_status": {},
            "top_ips": {},
            "active_api_keys": 0
        }
        
        # Cache hit rate
        cache_hits = len([r for r in filtered_requests if r.cache_hit])
        if filtered_requests:
            stats["cache_hit_rate"] = cache_hits / len(filtered_requests) * 100
        
        # Average response time
        response_times = [r.response_time_ms for r in filtered_requests if r.response_time_ms > 0]
        if response_times:
            stats["average_response_time"] = sum(response_times) / len(response_times)
        
        # Requests by endpoint
        for request in filtered_requests:
            endpoint = request.endpoint_id
            stats["requests_by_endpoint"][endpoint] = stats["requests_by_endpoint"].get(endpoint, 0) + 1
        
        # Requests by day
        for request in filtered_requests:
            day = request.timestamp.date().isoformat()
            stats["requests_by_day"][day] = stats["requests_by_day"].get(day, 0) + 1
        
        # Requests by status
        for request in filtered_requests:
            if request.status_code:
                status = str(request.status_code)
                stats["requests_by_status"][status] = stats["requests_by_status"].get(status, 0) + 1
        
        # Top IPs
        for request in filtered_requests:
            ip = request.source_ip
            stats["top_ips"][ip] = stats["top_ips"].get(ip, 0) + 1
        
        # Sort top IPs
        stats["top_ips"] = dict(sorted(stats["top_ips"].items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Active API keys count
        stats["active_api_keys"] = len([
            key for key in self.api_keys.values()
            if key.tenant_id == tenant_id and key.status == APIKeyStatus.ACTIVE
        ])
        
        return stats
    
    async def _cleanup_rate_limits(self):
        """Clean up expired rate limit buckets"""
        
        current_time = datetime.utcnow()
        expired_buckets = []
        
        for bucket_key, bucket in self.rate_limit_buckets.items():
            # Clean old requests
            cutoff_time = current_time - timedelta(seconds=bucket.limit.window_seconds * 2)
            while bucket.requests and bucket.requests[0] < cutoff_time:
                bucket.requests.popleft()
                bucket.current_count -= 1
            
            # Remove empty buckets
            if not bucket.requests:
                expired_buckets.append(bucket_key)
        
        for bucket_key in expired_buckets:
            del self.rate_limit_buckets[bucket_key]
        
        if expired_buckets:
            logger.debug(f"Cleaned up {len(expired_buckets)} expired rate limit buckets")
    
    async def _cleanup_cache(self):
        """Clean up expired cache entries"""
        
        current_time = datetime.utcnow()
        expired_keys = []
        
        for cache_key, metadata in self.cache_metadata.items():
            expires_at = metadata.get("expires_at")
            if expires_at and current_time > expires_at:
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            if cache_key in self.response_cache:
                del self.response_cache[cache_key]
            del self.cache_metadata[cache_key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def _monitor_security_threats(self):
        """Monitor for security threats"""
        
        # This would integrate with threat intelligence feeds
        # and implement advanced security monitoring
        pass
    
    async def _update_performance_metrics(self):
        """Update API performance metrics"""
        
        current_time = datetime.utcnow()
        
        # Calculate metrics for each endpoint
        for endpoint_id, endpoint in self.endpoints.items():
            recent_requests = []
            for r in self.request_history:
                endpoint_match = r.endpoint_id == endpoint_id
                time_match = r.timestamp > current_time - timedelta(hours=1)
                if endpoint_match and time_match:
                    recent_requests.append(r)
            
            if recent_requests:
                # Calculate average response time
                response_times = [r.response_time_ms for r in recent_requests if r.response_time_ms > 0]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
                
                # Calculate error rate
                errors = len([r for r in recent_requests if r.status_code and r.status_code >= 400])
                error_rate = errors / len(recent_requests) * 100
                
                # Store metrics
                self.endpoint_metrics[endpoint_id] = {
                    "requests_per_hour": len(recent_requests),
                    "average_response_time_ms": avg_response_time,
                    "error_rate_percent": error_rate,
                    "last_updated": current_time
                }


# Global service instance
api_governance_service = EnterpriseAPIGovernanceService()
