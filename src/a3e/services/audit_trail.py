"""
Enterprise Audit Trail Service
Comprehensive audit logging and compliance monitoring
Part of Phase M3: Enterprise Features
"""

import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """Audit log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(Enum):
    """Audit event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_EXPORT = "data_export"
    USER_MANAGEMENT = "user_management"
    SYSTEM_ADMINISTRATION = "system_administration"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    API_ACCESS = "api_access"
    INTEGRATION = "integration"
    REPORTING = "reporting"
    CONFIGURATION = "configuration"


class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    SOX = "sarbanes_oxley"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    ISO27001 = "iso_27001"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    FERPA = "ferpa"
    CCPA = "ccpa"
    NIST = "nist_cybersecurity"


@dataclass
class AuditEvent:
    """Comprehensive audit event record"""
    
    # Core identifiers
    event_id: str
    tenant_id: str
    timestamp: datetime
    
    # Event details
    category: AuditCategory
    action: str
    description: str
    level: AuditLevel
    
    # User context
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    impersonated_by: Optional[str] = None
    
    # Session context
    session_id: Optional[str] = None
    source_ip: str = "unknown"
    user_agent: str = "unknown"
    geographic_location: Optional[str] = None
    
    # Resource context
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    
    # Data context
    data_classification: Optional[str] = None  # public, internal, confidential, restricted
    data_sensitivity: Optional[str] = None     # low, medium, high, critical
    affected_records: int = 0
    
    # Change tracking
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)
    changes_summary: Optional[str] = None
    
    # Compliance context
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    policy_violations: List[str] = field(default_factory=list)
    
    # Request context
    request_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    request_size_bytes: int = 0
    response_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # Integrity verification
    checksum: Optional[str] = None
    
    def __post_init__(self):
        """Generate checksum for integrity verification"""
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate SHA-256 checksum for event integrity"""
        
        # Create deterministic string representation
        data_to_hash = {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "timestamp": self.timestamp.isoformat(),
            "category": self.category.value,
            "action": self.action,
            "description": self.description,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id
        }
        
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data_to_hash, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify event integrity using checksum"""
        return self.checksum == self._calculate_checksum()


@dataclass
class AuditQuery:
    """Audit log query parameters"""
    tenant_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    categories: List[AuditCategory] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    resource_types: List[str] = field(default_factory=list)
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    search_text: Optional[str] = None
    limit: int = 1000
    offset: int = 0


@dataclass
class ComplianceReport:
    """Compliance report structure"""
    tenant_id: str
    framework: ComplianceFramework
    report_period: Tuple[datetime, datetime]
    generated_at: datetime
    
    # Report summary
    total_events: int
    compliance_events: int
    violations: int
    coverage_percentage: float
    
    # Event breakdowns
    events_by_category: Dict[str, int]
    events_by_user: Dict[str, int]
    violations_by_type: Dict[str, int]
    
    # Timeline analysis
    events_timeline: List[Dict[str, Any]]
    
    # Risk assessment
    risk_score: float
    risk_factors: List[str]
    recommendations: List[str]
    
    # Detailed findings
    findings: List[Dict[str, Any]]
    
    # Supporting evidence
    evidence_files: List[str] = field(default_factory=list)


class EnterpriseAuditService:
    """Enterprise audit trail service with comprehensive logging and compliance"""
    
    def __init__(self):
        self.audit_events: List[AuditEvent] = []
        self.event_index: Dict[str, AuditEvent] = {}
        self.tenant_events: Dict[str, List[AuditEvent]] = defaultdict(list)
        self.user_events: Dict[str, List[AuditEvent]] = defaultdict(list)
        self.category_events: Dict[AuditCategory, List[AuditEvent]] = defaultdict(list)
        
        # Compliance configurations
        self.compliance_rules: Dict[ComplianceFramework, Dict[str, Any]] = {}
        self.retention_policies: Dict[str, int] = {}  # tenant_id -> retention_days
        
        # Performance optimization
        self.event_cache: Dict[str, List[AuditEvent]] = {}
        self.cache_ttl: int = 300  # 5 minutes
        
        # Initialize compliance frameworks
        self._initialize_compliance_frameworks()
        
        # Start background tasks
        self._start_background_tasks()
    
    def _initialize_compliance_frameworks(self):
        """Initialize compliance framework rules and requirements"""
        
        # SOX (Sarbanes-Oxley)
        self.compliance_rules[ComplianceFramework.SOX] = {
            "required_categories": [
                AuditCategory.DATA_MODIFICATION,
                AuditCategory.USER_MANAGEMENT,
                AuditCategory.SYSTEM_ADMINISTRATION,
                AuditCategory.REPORTING
            ],
            "retention_years": 7,
            "critical_events": [
                "financial_data_access",
                "report_generation",
                "user_privilege_change",
                "system_configuration_change"
            ],
            "monitoring_requirements": {
                "real_time_alerting": True,
                "quarterly_reviews": True,
                "annual_assessment": True
            }
        }
        
        # GDPR (General Data Protection Regulation)
        self.compliance_rules[ComplianceFramework.GDPR] = {
            "required_categories": [
                AuditCategory.DATA_ACCESS,
                AuditCategory.DATA_MODIFICATION,
                AuditCategory.DATA_EXPORT,
                AuditCategory.USER_MANAGEMENT
            ],
            "retention_years": 3,
            "critical_events": [
                "personal_data_access",
                "personal_data_modification",
                "personal_data_export",
                "consent_management",
                "data_subject_request"
            ],
            "data_subject_rights": [
                "right_to_access",
                "right_to_rectification", 
                "right_to_erasure",
                "right_to_portability",
                "right_to_object"
            ]
        }
        
        # HIPAA (Health Insurance Portability and Accountability Act)
        self.compliance_rules[ComplianceFramework.HIPAA] = {
            "required_categories": [
                AuditCategory.DATA_ACCESS,
                AuditCategory.DATA_MODIFICATION,
                AuditCategory.DATA_EXPORT,
                AuditCategory.AUTHENTICATION,
                AuditCategory.AUTHORIZATION
            ],
            "retention_years": 6,
            "critical_events": [
                "phi_access",
                "phi_modification",
                "phi_export",
                "access_control_change",
                "breach_detection"
            ],
            "minimum_necessary_standard": True,
            "encryption_required": True
        }
        
        # ISO 27001
        self.compliance_rules[ComplianceFramework.ISO27001] = {
            "required_categories": [
                AuditCategory.SECURITY,
                AuditCategory.AUTHENTICATION,
                AuditCategory.AUTHORIZATION,
                AuditCategory.SYSTEM_ADMINISTRATION,
                AuditCategory.CONFIGURATION
            ],
            "retention_years": 3,
            "critical_events": [
                "security_incident",
                "access_control_change",
                "security_configuration_change",
                "vulnerability_detected",
                "security_policy_violation"
            ],
            "risk_management": True,
            "continuous_monitoring": True
        }
        
        # SOC 2
        self.compliance_rules[ComplianceFramework.SOC2] = {
            "required_categories": [
                AuditCategory.SECURITY,
                AuditCategory.AUTHENTICATION,
                AuditCategory.DATA_ACCESS,
                AuditCategory.SYSTEM_ADMINISTRATION,
                AuditCategory.CONFIGURATION
            ],
            "retention_years": 1,
            "trust_service_criteria": [
                "security",
                "availability", 
                "processing_integrity",
                "confidentiality",
                "privacy"
            ],
            "continuous_monitoring": True
        }
    
    def _start_background_tasks(self):
        """Start background audit processing tasks"""
        
        async def cleanup_expired_events():
            """Clean up events based on retention policies"""
            while True:
                try:
                    await self._cleanup_expired_events()
                    await asyncio.sleep(3600)  # Run every hour
                except Exception as e:
                    logger.error(f"Audit cleanup error: {e}")
                    await asyncio.sleep(1800)  # Wait 30 minutes on error
        
        async def process_compliance_monitoring():
            """Monitor for compliance violations"""
            while True:
                try:
                    await self._monitor_compliance_violations()
                    await asyncio.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Compliance monitoring error: {e}")
                    await asyncio.sleep(600)  # Wait 10 minutes on error
        
        async def generate_audit_statistics():
            """Generate periodic audit statistics"""
            while True:
                try:
                    await self._generate_audit_statistics()
                    await asyncio.sleep(1800)  # Run every 30 minutes
                except Exception as e:
                    logger.error(f"Audit statistics error: {e}")
                    await asyncio.sleep(3600)  # Wait 1 hour on error
        
        # Start background tasks
        asyncio.create_task(cleanup_expired_events())
        asyncio.create_task(process_compliance_monitoring())
        asyncio.create_task(generate_audit_statistics())
    
    async def log_event(
        self,
        tenant_id: str,
        category: AuditCategory,
        action: str,
        description: str,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Log an audit event"""
        
        event_id = f"audit_{uuid.uuid4().hex}"
        
        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            tenant_id=tenant_id,
            timestamp=datetime.utcnow(),
            category=category,
            action=action,
            description=description,
            level=level,
            user_id=user_id,
            **kwargs
        )
        
        # Determine compliance frameworks for this event
        event.compliance_frameworks = await self._determine_compliance_frameworks(event)
        
        # Check for policy violations
        event.policy_violations = await self._check_policy_violations(event)
        
        # Store event
        await self._store_event(event)
        
        # Process real-time compliance checks
        await self._process_compliance_checks(event)
        
        # Send alerts if necessary
        await self._send_compliance_alerts(event)
        
        logger.debug(f"Audit event logged: {event_id}")
        return event_id
    
    async def _store_event(self, event: AuditEvent):
        """Store audit event with indexing"""
        
        # Add to main storage
        self.audit_events.append(event)
        self.event_index[event.event_id] = event
        
        # Add to indexes
        self.tenant_events[event.tenant_id].append(event)
        if event.user_id:
            self.user_events[event.user_id].append(event)
        self.category_events[event.category].append(event)
        
        # Clear relevant caches
        cache_keys_to_clear = [
            f"tenant_{event.tenant_id}",
            f"user_{event.user_id}" if event.user_id else None,
            f"category_{event.category.value}"
        ]
        
        for key in cache_keys_to_clear:
            if key and key in self.event_cache:
                del self.event_cache[key]
    
    async def _determine_compliance_frameworks(self, event: AuditEvent) -> List[ComplianceFramework]:
        """Determine which compliance frameworks apply to this event"""
        
        applicable_frameworks = []
        
        for framework, rules in self.compliance_rules.items():
            if event.category in rules.get("required_categories", []):
                applicable_frameworks.append(framework)
            
            if event.action in rules.get("critical_events", []):
                applicable_frameworks.append(framework)
        
        return list(set(applicable_frameworks))  # Remove duplicates
    
    async def _check_policy_violations(self, event: AuditEvent) -> List[str]:
        """Check for policy violations in the audit event"""
        
        violations = []
        
        # Check data access patterns
        if event.category == AuditCategory.DATA_ACCESS:
            if event.data_sensitivity == "critical" and event.user_role not in ["admin", "compliance_officer"]:
                violations.append("unauthorized_critical_data_access")
        
        # Check administrative actions
        if event.category == AuditCategory.SYSTEM_ADMINISTRATION:
            if event.user_role != "admin":
                violations.append("unauthorized_admin_action")
        
        # Check after-hours access
        if event.timestamp.hour < 6 or event.timestamp.hour > 22:
            if event.category in [AuditCategory.DATA_ACCESS, AuditCategory.DATA_MODIFICATION]:
                violations.append("after_hours_sensitive_access")
        
        # Check bulk operations
        if event.affected_records > 1000:
            violations.append("bulk_operation_detected")
        
        return violations
    
    async def _process_compliance_checks(self, event: AuditEvent):
        """Process real-time compliance checks"""
        
        for framework in event.compliance_frameworks:
            framework_rules = self.compliance_rules.get(framework, {})
            
            # Check for critical events
            if event.action in framework_rules.get("critical_events", []):
                await self._trigger_compliance_alert(event, framework, "critical_event_detected")
            
            # Check for policy violations
            if event.policy_violations:
                await self._trigger_compliance_alert(event, framework, "policy_violation_detected")
    
    async def _trigger_compliance_alert(self, event: AuditEvent, framework: ComplianceFramework, alert_type: str):
        """Trigger compliance alert"""
        
        alert_data = {
            "alert_type": alert_type,
            "framework": framework.value,
            "event_id": event.event_id,
            "tenant_id": event.tenant_id,
            "timestamp": event.timestamp.isoformat(),
            "severity": event.level.value,
            "description": event.description
        }
        
        # Log the compliance alert
        await self.log_event(
            tenant_id=event.tenant_id,
            category=AuditCategory.COMPLIANCE,
            action="compliance_alert_triggered",
            description=f"Compliance alert: {alert_type} for {framework.value}",
            level=AuditLevel.WARNING,
            metadata=alert_data
        )
        
        logger.warning(f"Compliance alert triggered: {alert_type} for {framework.value}")
    
    async def query_events(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit events with filtering"""
        
        # Check cache first
        cache_key = self._generate_cache_key(query)
        if cache_key in self.event_cache:
            cached_result = self.event_cache[cache_key]
            # Check if cache is still valid
            if cached_result and len(cached_result) > 0:
                return cached_result[query.offset:query.offset + query.limit]
        
        # Get base events for tenant
        events = self.tenant_events.get(query.tenant_id, [])
        
        # Apply filters
        filtered_events = events
        
        # Date range filter
        if query.start_date:
            filtered_events = [e for e in filtered_events if e.timestamp >= query.start_date]
        if query.end_date:
            filtered_events = [e for e in filtered_events if e.timestamp <= query.end_date]
        
        # User filter
        if query.user_id:
            filtered_events = [e for e in filtered_events if e.user_id == query.user_id]
        
        # Category filter
        if query.categories:
            filtered_events = [e for e in filtered_events if e.category in query.categories]
        
        # Action filter
        if query.actions:
            filtered_events = [e for e in filtered_events if e.action in query.actions]
        
        # Resource type filter
        if query.resource_types:
            filtered_events = [e for e in filtered_events if e.resource_type in query.resource_types]
        
        # Compliance framework filter
        if query.compliance_frameworks:
            filtered_events = [
                e for e in filtered_events 
                if any(framework in e.compliance_frameworks for framework in query.compliance_frameworks)
            ]
        
        # Text search
        if query.search_text:
            search_lower = query.search_text.lower()
            search_filtered = []
            for e in filtered_events:
                if (search_lower in e.description.lower() or 
                    search_lower in e.action.lower() or 
                    (e.user_email and search_lower in e.user_email.lower())):
                    search_filtered.append(e)
            filtered_events = search_filtered
        
        # Sort by timestamp (newest first)
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # Cache results
        self.event_cache[cache_key] = filtered_events
        
        # Apply pagination
        return filtered_events[query.offset:query.offset + query.limit]
    
    def _generate_cache_key(self, query: AuditQuery) -> str:
        """Generate cache key for query"""
        
        key_parts = [
            f"tenant_{query.tenant_id}",
            f"start_{query.start_date.isoformat() if query.start_date else 'none'}",
            f"end_{query.end_date.isoformat() if query.end_date else 'none'}",
            f"user_{query.user_id or 'none'}",
            f"categories_{','.join([c.value for c in query.categories])}",
            f"actions_{','.join(query.actions)}",
            f"resources_{','.join(query.resource_types)}",
            f"frameworks_{','.join([f.value for f in query.compliance_frameworks])}",
            f"search_{query.search_text or 'none'}"
        ]
        
        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()
    
    async def generate_compliance_report(
        self,
        tenant_id: str,
        framework: ComplianceFramework,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceReport:
        """Generate comprehensive compliance report"""
        
        # Query relevant events
        query = AuditQuery(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            compliance_frameworks=[framework],
            limit=10000
        )
        
        events = await self.query_events(query)
        framework_rules = self.compliance_rules.get(framework, {})
        
        # Calculate compliance metrics
        total_events = len(events)
        compliance_events = len([e for e in events if framework in e.compliance_frameworks])
        violations = len([e for e in events if e.policy_violations])
        
        # Calculate coverage
        required_categories = set(framework_rules.get("required_categories", []))
        covered_categories = set(e.category for e in events)
        coverage_percentage = (len(covered_categories & required_categories) / len(required_categories) * 100) if required_categories else 100
        
        # Event breakdowns
        events_by_category = defaultdict(int)
        events_by_user = defaultdict(int)
        violations_by_type = defaultdict(int)
        
        for event in events:
            events_by_category[event.category.value] += 1
            if event.user_id:
                events_by_user[event.user_id] += 1
            for violation in event.policy_violations:
                violations_by_type[violation] += 1
        
        # Timeline analysis
        events_timeline = await self._generate_events_timeline(events, start_date, end_date)
        
        # Risk assessment
        risk_score, risk_factors = await self._calculate_risk_score(events, framework)
        recommendations = await self._generate_recommendations(events, framework, risk_factors)
        
        # Detailed findings
        findings = await self._generate_compliance_findings(events, framework)
        
        return ComplianceReport(
            tenant_id=tenant_id,
            framework=framework,
            report_period=(start_date, end_date),
            generated_at=datetime.utcnow(),
            total_events=total_events,
            compliance_events=compliance_events,
            violations=violations,
            coverage_percentage=coverage_percentage,
            events_by_category=dict(events_by_category),
            events_by_user=dict(events_by_user),
            violations_by_type=dict(violations_by_type),
            events_timeline=events_timeline,
            risk_score=risk_score,
            risk_factors=risk_factors,
            recommendations=recommendations,
            findings=findings
        )
    
    async def _generate_events_timeline(self, events: List[AuditEvent], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate timeline of events for visualization"""
        
        timeline = []
        
        # Group events by day
        events_by_day = defaultdict(list)
        for event in events:
            day_key = event.timestamp.date().isoformat()
            events_by_day[day_key].append(event)
        
        # Generate timeline entries
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            day_key = current_date.isoformat()
            day_events = events_by_day.get(day_key, [])
            
            timeline.append({
                "date": day_key,
                "total_events": len(day_events),
                "violations": len([e for e in day_events if e.policy_violations]),
                "critical_events": len([e for e in day_events if e.level == AuditLevel.CRITICAL]),
                "categories": list(set(e.category.value for e in day_events))
            })
            
            current_date += timedelta(days=1)
        
        return timeline
    
    async def _calculate_risk_score(self, events: List[AuditEvent], framework: ComplianceFramework) -> Tuple[float, List[str]]:
        """Calculate compliance risk score and identify risk factors"""
        
        risk_score = 0.0
        risk_factors = []
        
        # Base score calculation
        if not events:
            return 100.0, ["No audit events found"]
        
        # Violation risk
        violations = [e for e in events if e.policy_violations]
        violation_rate = len(violations) / len(events)
        
        if violation_rate > 0.1:  # >10% violation rate
            risk_score += 30
            risk_factors.append(f"High violation rate: {violation_rate:.1%}")
        elif violation_rate > 0.05:  # >5% violation rate
            risk_score += 15
            risk_factors.append(f"Elevated violation rate: {violation_rate:.1%}")
        
        # Critical event risk
        critical_events = [e for e in events if e.level == AuditLevel.CRITICAL]
        if critical_events:
            risk_score += len(critical_events) * 5
            risk_factors.append(f"{len(critical_events)} critical events detected")
        
        # After-hours activity risk
        after_hours = [e for e in events if e.timestamp.hour < 6 or e.timestamp.hour > 22]
        if len(after_hours) > len(events) * 0.2:  # >20% after hours
            risk_score += 20
            risk_factors.append("High after-hours activity")
        
        # Administrative activity risk
        admin_events = [e for e in events if e.category == AuditCategory.SYSTEM_ADMINISTRATION]
        if len(admin_events) > len(events) * 0.3:  # >30% admin events
            risk_score += 15
            risk_factors.append("High administrative activity")
        
        # Data export risk
        export_events = [e for e in events if e.category == AuditCategory.DATA_EXPORT]
        if export_events:
            risk_score += len(export_events) * 2
            risk_factors.append(f"{len(export_events)} data export events")
        
        # Ensure score is between 0 and 100
        risk_score = min(max(risk_score, 0), 100)
        
        return risk_score, risk_factors
    
    async def _generate_recommendations(self, events: List[AuditEvent], framework: ComplianceFramework, risk_factors: List[str]) -> List[str]:
        """Generate compliance recommendations based on analysis"""
        
        recommendations = []
        
        # General recommendations based on risk factors
        if "High violation rate" in str(risk_factors):
            recommendations.append("Review and strengthen security policies to reduce violation rate")
        
        if "critical events detected" in str(risk_factors):
            recommendations.append("Investigate critical events and implement preventive measures")
        
        if "High after-hours activity" in str(risk_factors):
            recommendations.append("Implement additional monitoring for after-hours activities")
        
        if "High administrative activity" in str(risk_factors):
            recommendations.append("Review administrative privileges and implement least privilege principle")
        
        # Framework-specific recommendations
        if framework == ComplianceFramework.SOX:
            recommendations.extend([
                "Ensure quarterly review of financial data access logs",
                "Implement segregation of duties for financial processes",
                "Maintain documentation of all system changes affecting financial reporting"
            ])
        
        elif framework == ComplianceFramework.GDPR:
            recommendations.extend([
                "Implement data subject request tracking system",
                "Ensure consent management audit trail is complete",
                "Review data retention policies and implement automated deletion"
            ])
        
        elif framework == ComplianceFramework.HIPAA:
            recommendations.extend([
                "Implement minimum necessary standard for PHI access",
                "Ensure all PHI access is logged and monitored",
                "Conduct regular access reviews for healthcare data"
            ])
        
        return recommendations
    
    async def _generate_compliance_findings(self, events: List[AuditEvent], framework: ComplianceFramework) -> List[Dict[str, Any]]:
        """Generate detailed compliance findings"""
        
        findings = []
        
        # Finding 1: Policy violations
        violations = [e for e in events if e.policy_violations]
        if violations:
            findings.append({
                "finding_id": f"finding_violations_{framework.value}",
                "title": "Policy Violations Detected",
                "severity": "high" if len(violations) > 10 else "medium",
                "description": f"Found {len(violations)} events with policy violations",
                "impact": "Potential compliance breach and increased risk exposure",
                "recommendation": "Review violations and implement corrective measures",
                "affected_events": len(violations),
                "evidence": [e.event_id for e in violations[:10]]  # First 10 as evidence
            })
        
        # Finding 2: Missing audit coverage
        framework_rules = self.compliance_rules.get(framework, {})
        required_categories = set(framework_rules.get("required_categories", []))
        covered_categories = set(e.category for e in events)
        missing_categories = required_categories - covered_categories
        
        if missing_categories:
            findings.append({
                "finding_id": f"finding_coverage_{framework.value}",
                "title": "Incomplete Audit Coverage",
                "severity": "medium",
                "description": f"Missing audit coverage for {len(missing_categories)} required categories",
                "impact": "Reduced visibility into compliance-relevant activities",
                "recommendation": "Implement logging for missing categories",
                "missing_categories": [cat.value for cat in missing_categories]
            })
        
        # Finding 3: Unusual access patterns
        unusual_access = await self._detect_unusual_access_patterns(events)
        if unusual_access:
            findings.append({
                "finding_id": f"finding_access_{framework.value}",
                "title": "Unusual Access Patterns",
                "severity": "medium",
                "description": "Detected unusual access patterns that may require review",
                "impact": "Potential unauthorized access or insider threat",
                "recommendation": "Review unusual access patterns and validate legitimacy",
                "patterns": unusual_access
            })
        
        return findings
    
    async def _detect_unusual_access_patterns(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """Detect unusual access patterns in audit events"""
        
        patterns = []
        
        # Pattern 1: High-frequency access by single user
        user_access_counts = defaultdict(int)
        for event in events:
            if event.category == AuditCategory.DATA_ACCESS and event.user_id:
                user_access_counts[event.user_id] += 1
        
        avg_access = sum(user_access_counts.values()) / len(user_access_counts) if user_access_counts else 0
        threshold = avg_access * 3  # 3x average
        
        for user_id, count in user_access_counts.items():
            if count > threshold and count > 50:  # Minimum threshold
                patterns.append({
                    "pattern_type": "high_frequency_access",
                    "user_id": user_id,
                    "access_count": count,
                    "threshold": threshold,
                    "description": f"User {user_id} accessed data {count} times (threshold: {threshold:.0f})"
                })
        
        # Pattern 2: Off-hours administrative activity
        admin_events = [e for e in events if e.category == AuditCategory.SYSTEM_ADMINISTRATION]
        off_hours_admin = [e for e in admin_events if e.timestamp.hour < 6 or e.timestamp.hour > 22]
        
        if len(off_hours_admin) > 5:  # More than 5 off-hours admin events
            patterns.append({
                "pattern_type": "off_hours_admin",
                "event_count": len(off_hours_admin),
                "description": f"{len(off_hours_admin)} administrative events occurred outside business hours"
            })
        
        return patterns
    
    async def get_audit_statistics(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get audit statistics for tenant"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = AuditQuery(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        events = await self.query_events(query)
        
        # Calculate statistics
        stats = {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_events": len(events),
            "events_by_category": {},
            "events_by_level": {},
            "events_by_user": {},
            "violation_summary": {
                "total_violations": 0,
                "violation_types": {}
            },
            "compliance_frameworks": {},
            "daily_event_counts": [],
            "top_actions": {},
            "risk_indicators": []
        }
        
        # Events by category
        for event in events:
            cat = event.category.value
            stats["events_by_category"][cat] = stats["events_by_category"].get(cat, 0) + 1
            
            # Events by level
            level = event.level.value
            stats["events_by_level"][level] = stats["events_by_level"].get(level, 0) + 1
            
            # Events by user
            if event.user_id:
                stats["events_by_user"][event.user_id] = stats["events_by_user"].get(event.user_id, 0) + 1
            
            # Violations
            for violation in event.policy_violations:
                stats["violation_summary"]["total_violations"] += 1
                stats["violation_summary"]["violation_types"][violation] = \
                    stats["violation_summary"]["violation_types"].get(violation, 0) + 1
            
            # Compliance frameworks
            for framework in event.compliance_frameworks:
                fw_name = framework.value
                stats["compliance_frameworks"][fw_name] = stats["compliance_frameworks"].get(fw_name, 0) + 1
            
            # Top actions
            stats["top_actions"][event.action] = stats["top_actions"].get(event.action, 0) + 1
        
        # Sort top actions
        stats["top_actions"] = dict(sorted(stats["top_actions"].items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Daily event counts
        events_by_day = defaultdict(int)
        for event in events:
            day = event.timestamp.date().isoformat()
            events_by_day[day] += 1
        
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            day_key = current_date.isoformat()
            stats["daily_event_counts"].append({
                "date": day_key,
                "count": events_by_day.get(day_key, 0)
            })
            current_date += timedelta(days=1)
        
        return stats
    
    async def _cleanup_expired_events(self):
        """Clean up expired audit events based on retention policies"""
        
        # Group events by tenant for retention policy lookup
        events_to_remove = []
        
        for event in self.audit_events:
            tenant_id = event.tenant_id
            retention_days = self.retention_policies.get(tenant_id, 2555)  # Default 7 years
            
            if (datetime.utcnow() - event.timestamp).days > retention_days:
                events_to_remove.append(event)
        
        # Remove expired events
        for event in events_to_remove:
            await self._remove_event(event)
        
        if events_to_remove:
            logger.info(f"Cleaned up {len(events_to_remove)} expired audit events")
    
    async def _remove_event(self, event: AuditEvent):
        """Remove event from all indexes"""
        
        # Remove from main storage
        if event in self.audit_events:
            self.audit_events.remove(event)
        
        if event.event_id in self.event_index:
            del self.event_index[event.event_id]
        
        # Remove from indexes
        if event in self.tenant_events[event.tenant_id]:
            self.tenant_events[event.tenant_id].remove(event)
        
        if event.user_id and event in self.user_events[event.user_id]:
            self.user_events[event.user_id].remove(event)
        
        if event in self.category_events[event.category]:
            self.category_events[event.category].remove(event)
    
    async def _monitor_compliance_violations(self):
        """Monitor for new compliance violations"""
        
        # Check recent events for violations
        recent_cutoff = datetime.utcnow() - timedelta(minutes=5)
        recent_events = [e for e in self.audit_events if e.timestamp > recent_cutoff]
        
        for event in recent_events:
            if event.policy_violations:
                logger.warning(f"Compliance violation detected: {event.event_id} - {event.policy_violations}")
    
    async def _generate_audit_statistics(self):
        """Generate periodic audit statistics"""
        
        # This would generate summary statistics for monitoring dashboards
        logger.debug("Generated audit statistics")
    
    async def _send_compliance_alerts(self, event: AuditEvent):
        """Send compliance alerts for critical events"""
        
        if event.level == AuditLevel.CRITICAL or event.policy_violations:
            # This would integrate with alerting system
            logger.warning(f"Compliance alert: {event.description}")


# Global service instance
audit_service = EnterpriseAuditService()
