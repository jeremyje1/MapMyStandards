"""
Audit-Ready Traceability System for A³E
Complete traceability from LLM output to evidentiary source with immutable audit trails
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import uuid
import json
import hashlib
import logging
from pathlib import Path
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class AuditEventType(Enum):
    """Types of auditable events in the system."""
    # Pipeline events
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_ERROR = "pipeline_error"
    
    # Agent events
    AGENT_PROCESSING_START = "agent_processing_start"
    AGENT_PROCESSING_COMPLETE = "agent_processing_complete"
    AGENT_ERROR = "agent_error"
    
    # Evidence events
    EVIDENCE_INGESTED = "evidence_ingested"
    EVIDENCE_MAPPED = "evidence_mapped"
    EVIDENCE_VERIFIED = "evidence_verified"
    
    # LLM events
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    LLM_ERROR = "llm_error"
    
    # Standards events
    STANDARD_MATCHED = "standard_matched"
    STANDARD_VERIFIED = "standard_verified"
    GAP_IDENTIFIED = "gap_identified"
    
    # Output events
    NARRATIVE_GENERATED = "narrative_generated"
    CITATION_CREATED = "citation_created"
    REPORT_GENERATED = "report_generated"
    
    # System events
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    USER_ACTION = "user_action"
    DATA_EXPORT = "data_export"

class TraceabilityLevel(Enum):
    """Levels of traceability detail."""
    MINIMAL = "minimal"         # Basic event logging
    STANDARD = "standard"       # Standard audit requirements
    COMPREHENSIVE = "comprehensive"  # Full forensic traceability
    FORENSIC = "forensic"       # Maximum detail for legal review

@dataclass
class AuditEvent:
    """Immutable audit event record."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Context information
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    institution_id: Optional[str] = None
    accreditor_id: Optional[str] = None
    
    # Agent/component information
    agent_role: Optional[str] = None
    agent_id: Optional[str] = None
    component: Optional[str] = None
    
    # Event data
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Traceability links
    parent_event_id: Optional[str] = None
    related_event_ids: List[str] = field(default_factory=list)
    
    # Evidence and source tracking
    evidence_ids: List[str] = field(default_factory=list)
    source_documents: List[str] = field(default_factory=list)
    
    # LLM tracking
    llm_model: Optional[str] = None
    llm_prompt_hash: Optional[str] = None
    llm_response_hash: Optional[str] = None
    token_usage: Dict[str, int] = field(default_factory=dict)
    
    # Integrity and verification
    data_hash: Optional[str] = None
    signature: Optional[str] = None
    verification_status: str = "pending"
    
    def __post_init__(self):
        """Compute data hash for integrity verification."""
        if not self.data_hash:
            self.data_hash = self._compute_data_hash()
    
    def _compute_data_hash(self) -> str:
        """Compute SHA-256 hash of event data for integrity checking."""
        # Create deterministic representation
        hash_data = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_role": self.agent_role,
            "data": self.data
        }
        
        # Sort keys for deterministic hashing
        json_str = json.dumps(hash_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify the integrity of this audit event."""
        current_hash = self._compute_data_hash()
        return current_hash == self.data_hash

@dataclass
class TraceabilityLink:
    """Link between outputs and their evidentiary sources."""
    link_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Output information
    output_type: str = ""  # "narrative", "citation", "gap_analysis", etc.
    output_id: str = ""
    output_content_hash: str = ""
    
    # Source information
    source_type: str = ""  # "evidence_document", "llm_response", "agent_output"
    source_id: str = ""
    source_content_hash: str = ""
    
    # Relationship details
    relationship_type: str = ""  # "derived_from", "cites", "supports", "contradicts"
    confidence_score: float = 0.0
    semantic_similarity: float = 0.0
    
    # Agent and processing context
    agent_role: Optional[str] = None
    processing_step: Optional[str] = None
    
    # LLM interaction details
    llm_model: Optional[str] = None
    llm_prompt_context: Optional[str] = None
    
    # Verification status
    verified: bool = False
    verification_method: Optional[str] = None
    verification_timestamp: Optional[datetime] = None

@dataclass
class EvidenceChain:
    """Complete chain of evidence from source to final output."""
    chain_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Chain metadata
    start_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_timestamp: Optional[datetime] = None
    
    # Chain components
    source_document_id: str = ""
    intermediate_steps: List[TraceabilityLink] = field(default_factory=list)
    final_output_id: str = ""
    
    # Chain validation
    chain_integrity_score: float = 0.0
    broken_links: List[str] = field(default_factory=list)
    validation_timestamp: Optional[datetime] = None

class AuditDatabase:
    """SQLite-based audit database for immutable event storage."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the audit database schema."""
        with self._get_connection() as conn:
            # Audit events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    user_id TEXT,
                    institution_id TEXT,
                    accreditor_id TEXT,
                    agent_role TEXT,
                    agent_id TEXT,
                    component TEXT,
                    data TEXT,
                    parent_event_id TEXT,
                    related_event_ids TEXT,
                    evidence_ids TEXT,
                    source_documents TEXT,
                    llm_model TEXT,
                    llm_prompt_hash TEXT,
                    llm_response_hash TEXT,
                    token_usage TEXT,
                    data_hash TEXT NOT NULL,
                    signature TEXT,
                    verification_status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Traceability links table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS traceability_links (
                    link_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    output_type TEXT NOT NULL,
                    output_id TEXT NOT NULL,
                    output_content_hash TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    source_content_hash TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    confidence_score REAL DEFAULT 0.0,
                    semantic_similarity REAL DEFAULT 0.0,
                    agent_role TEXT,
                    processing_step TEXT,
                    llm_model TEXT,
                    llm_prompt_context TEXT,
                    verified INTEGER DEFAULT 0,
                    verification_method TEXT,
                    verification_timestamp TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Evidence chains table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS evidence_chains (
                    chain_id TEXT PRIMARY KEY,
                    start_timestamp TEXT NOT NULL,
                    end_timestamp TEXT,
                    source_document_id TEXT NOT NULL,
                    final_output_id TEXT NOT NULL,
                    chain_integrity_score REAL DEFAULT 0.0,
                    broken_links TEXT,
                    validation_timestamp TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indices for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON audit_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON audit_events(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON audit_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_links_output ON traceability_links(output_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_links_source ON traceability_links(source_id)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def store_event(self, event: AuditEvent) -> bool:
        """Store an audit event immutably."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO audit_events (
                        event_id, event_type, timestamp, session_id, user_id,
                        institution_id, accreditor_id, agent_role, agent_id, component,
                        data, parent_event_id, related_event_ids, evidence_ids,
                        source_documents, llm_model, llm_prompt_hash, llm_response_hash,
                        token_usage, data_hash, signature, verification_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id, event.event_type, event.timestamp.isoformat(),
                    event.session_id, event.user_id, event.institution_id, event.accreditor_id,
                    event.agent_role, event.agent_id, event.component,
                    json.dumps(event.data), event.parent_event_id,
                    json.dumps(event.related_event_ids), json.dumps(event.evidence_ids),
                    json.dumps(event.source_documents), event.llm_model,
                    event.llm_prompt_hash, event.llm_response_hash,
                    json.dumps(event.token_usage), event.data_hash,
                    event.signature, event.verification_status
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to store audit event: {e}")
            return False
    
    def store_traceability_link(self, link: TraceabilityLink) -> bool:
        """Store a traceability link."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO traceability_links (
                        link_id, timestamp, output_type, output_id, output_content_hash,
                        source_type, source_id, source_content_hash, relationship_type,
                        confidence_score, semantic_similarity, agent_role, processing_step,
                        llm_model, llm_prompt_context, verified, verification_method,
                        verification_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    link.link_id, link.timestamp.isoformat(), link.output_type,
                    link.output_id, link.output_content_hash, link.source_type,
                    link.source_id, link.source_content_hash, link.relationship_type,
                    link.confidence_score, link.semantic_similarity, link.agent_role,
                    link.processing_step, link.llm_model, link.llm_prompt_context,
                    1 if link.verified else 0, link.verification_method,
                    link.verification_timestamp.isoformat() if link.verification_timestamp else None
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to store traceability link: {e}")
            return False
    
    def get_events_by_session(self, session_id: str) -> List[AuditEvent]:
        """Retrieve all events for a session."""
        events = []
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM audit_events 
                    WHERE session_id = ? 
                    ORDER BY timestamp ASC
                """, (session_id,))
                
                for row in cursor.fetchall():
                    events.append(self._row_to_event(row))
        except Exception as e:
            logger.error(f"Failed to retrieve events: {e}")
        
        return events
    
    def get_traceability_chain(self, output_id: str) -> List[TraceabilityLink]:
        """Get complete traceability chain for an output."""
        links = []
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM traceability_links 
                    WHERE output_id = ? 
                    ORDER BY timestamp ASC
                """, (output_id,))
                
                for row in cursor.fetchall():
                    links.append(self._row_to_link(row))
        except Exception as e:
            logger.error(f"Failed to retrieve traceability chain: {e}")
        
        return links
    
    def _row_to_event(self, row: sqlite3.Row) -> AuditEvent:
        """Convert database row to AuditEvent."""
        return AuditEvent(
            event_id=row["event_id"],
            event_type=row["event_type"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            session_id=row["session_id"],
            user_id=row["user_id"],
            institution_id=row["institution_id"],
            accreditor_id=row["accreditor_id"],
            agent_role=row["agent_role"],
            agent_id=row["agent_id"],
            component=row["component"],
            data=json.loads(row["data"]) if row["data"] else {},
            parent_event_id=row["parent_event_id"],
            related_event_ids=json.loads(row["related_event_ids"]) if row["related_event_ids"] else [],
            evidence_ids=json.loads(row["evidence_ids"]) if row["evidence_ids"] else [],
            source_documents=json.loads(row["source_documents"]) if row["source_documents"] else [],
            llm_model=row["llm_model"],
            llm_prompt_hash=row["llm_prompt_hash"],
            llm_response_hash=row["llm_response_hash"],
            token_usage=json.loads(row["token_usage"]) if row["token_usage"] else {},
            data_hash=row["data_hash"],
            signature=row["signature"],
            verification_status=row["verification_status"]
        )
    
    def _row_to_link(self, row: sqlite3.Row) -> TraceabilityLink:
        """Convert database row to TraceabilityLink."""
        return TraceabilityLink(
            link_id=row["link_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            output_type=row["output_type"],
            output_id=row["output_id"],
            output_content_hash=row["output_content_hash"],
            source_type=row["source_type"],
            source_id=row["source_id"],
            source_content_hash=row["source_content_hash"],
            relationship_type=row["relationship_type"],
            confidence_score=row["confidence_score"],
            semantic_similarity=row["semantic_similarity"],
            agent_role=row["agent_role"],
            processing_step=row["processing_step"],
            llm_model=row["llm_model"],
            llm_prompt_context=row["llm_prompt_context"],
            verified=bool(row["verified"]),
            verification_method=row["verification_method"],
            verification_timestamp=datetime.fromisoformat(row["verification_timestamp"]) if row["verification_timestamp"] else None
        )

class AuditTrailSystem:
    """Main audit trail system for A³E."""
    
    def __init__(self, db_path: str, traceability_level: TraceabilityLevel = TraceabilityLevel.STANDARD):
        self.db = AuditDatabase(db_path)
        self.traceability_level = traceability_level
        self.current_session_id: Optional[str] = None
        
        # Performance tracking
        self.events_logged = 0
        self.links_created = 0
        
    def start_session(self, session_id: str, user_id: Optional[str] = None, 
                     institution_id: Optional[str] = None, accreditor_id: Optional[str] = None) -> str:
        """Start a new audit session."""
        self.current_session_id = session_id
        
        # Log session start
        self.log_event(AuditEvent(
            event_type=AuditEventType.PIPELINE_STARTED.value,
            session_id=session_id,
            user_id=user_id,
            institution_id=institution_id,
            accreditor_id=accreditor_id,
            data={
                "traceability_level": self.traceability_level.value,
                "session_start": datetime.now(timezone.utc).isoformat()
            }
        ))
        
        return session_id
    
    def log_event(self, event: AuditEvent) -> bool:
        """Log an audit event."""
        # Set session ID if not provided
        if not event.session_id and self.current_session_id:
            event.session_id = self.current_session_id
        
        # Store event
        success = self.db.store_event(event)
        if success:
            self.events_logged += 1
        
        return success
    
    def create_traceability_link(self, output_type: str, output_id: str, output_content: str,
                               source_type: str, source_id: str, source_content: str,
                               relationship_type: str, confidence_score: float = 0.0,
                               semantic_similarity: float = 0.0, agent_role: Optional[str] = None,
                               processing_step: Optional[str] = None, llm_model: Optional[str] = None) -> TraceabilityLink:
        """Create a traceability link between output and source."""
        
        # Compute content hashes
        output_hash = hashlib.sha256(output_content.encode()).hexdigest()
        source_hash = hashlib.sha256(source_content.encode()).hexdigest()
        
        link = TraceabilityLink(
            output_type=output_type,
            output_id=output_id,
            output_content_hash=output_hash,
            source_type=source_type,
            source_id=source_id,
            source_content_hash=source_hash,
            relationship_type=relationship_type,
            confidence_score=confidence_score,
            semantic_similarity=semantic_similarity,
            agent_role=agent_role,
            processing_step=processing_step,
            llm_model=llm_model
        )
        
        # Store link
        if self.db.store_traceability_link(link):
            self.links_created += 1
        
        return link
    
    def log_llm_interaction(self, prompt: str, response: str, model: str, 
                           session_id: Optional[str] = None, agent_role: Optional[str] = None,
                           token_usage: Optional[Dict[str, int]] = None) -> AuditEvent:
        """Log an LLM interaction with full traceability."""
        
        # Compute hashes for prompt and response
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        response_hash = hashlib.sha256(response.encode()).hexdigest()
        
        event = AuditEvent(
            event_type=AuditEventType.LLM_REQUEST.value,
            session_id=session_id or self.current_session_id,
            agent_role=agent_role,
            llm_model=model,
            llm_prompt_hash=prompt_hash,
            llm_response_hash=response_hash,
            token_usage=token_usage or {},
            data={
                "prompt_length": len(prompt),
                "response_length": len(response),
                "model": model,
                "interaction_timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Store full prompt/response based on traceability level
        if self.traceability_level in [TraceabilityLevel.COMPREHENSIVE, TraceabilityLevel.FORENSIC]:
            event.data.update({
                "full_prompt": prompt,
                "full_response": response
            })
        
        self.log_event(event)
        return event
    
    def trace_output_to_sources(self, output_id: str) -> Dict[str, Any]:
        """Trace an output back to all its evidentiary sources."""
        
        # Get direct traceability links
        links = self.db.get_traceability_chain(output_id)
        
        # Build complete evidence chain
        evidence_chain = self._build_evidence_chain(output_id, links)
        
        # Validate chain integrity
        integrity_score = self._validate_chain_integrity(evidence_chain)
        
        return {
            "output_id": output_id,
            "evidence_chain": evidence_chain,
            "integrity_score": integrity_score,
            "total_links": len(links),
            "verification_status": "verified" if integrity_score >= 0.8 else "questionable",
            "trace_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _build_evidence_chain(self, output_id: str, links: List[TraceabilityLink]) -> List[Dict[str, Any]]:
        """Build complete evidence chain from traceability links."""
        
        chain = []
        
        for link in links:
            chain_item = {
                "link_id": link.link_id,
                "source_type": link.source_type,
                "source_id": link.source_id,
                "relationship_type": link.relationship_type,
                "confidence_score": link.confidence_score,
                "semantic_similarity": link.semantic_similarity,
                "agent_role": link.agent_role,
                "processing_step": link.processing_step,
                "verified": link.verified,
                "timestamp": link.timestamp.isoformat()
            }
            chain.append(chain_item)
        
        return chain
    
    def _validate_chain_integrity(self, evidence_chain: List[Dict[str, Any]]) -> float:
        """Validate the integrity of an evidence chain."""
        
        if not evidence_chain:
            return 0.0
        
        # Scoring factors
        total_score = 0.0
        max_score = 0.0
        
        for item in evidence_chain:
            # Base score from confidence and similarity
            base_score = (item.get("confidence_score", 0.0) + item.get("semantic_similarity", 0.0)) / 2
            
            # Verification bonus
            if item.get("verified", False):
                base_score *= 1.2
            
            # Agent processing bonus
            if item.get("agent_role"):
                base_score *= 1.1
            
            total_score += min(1.0, base_score)
            max_score += 1.0
        
        return total_score / max_score if max_score > 0 else 0.0
    
    def generate_audit_report(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive audit report for a session."""
        
        events = self.db.get_events_by_session(session_id)
        
        # Categorize events
        event_categories = {}
        for event in events:
            category = event.event_type
            if category not in event_categories:
                event_categories[category] = []
            event_categories[category].append(event)
        
        # Calculate session metrics
        session_start = min(event.timestamp for event in events) if events else datetime.now()
        session_end = max(event.timestamp for event in events) if events else datetime.now()
        session_duration = (session_end - session_start).total_seconds()
        
        # LLM usage summary
        llm_events = [e for e in events if e.event_type == AuditEventType.LLM_REQUEST.value]
        total_tokens = sum(
            sum(event.token_usage.values()) for event in llm_events 
            if event.token_usage
        )
        
        # Evidence processing summary
        evidence_events = [e for e in events if "evidence" in e.event_type]
        
        return {
            "session_id": session_id,
            "audit_report_generated": datetime.now(timezone.utc).isoformat(),
            "session_summary": {
                "start_time": session_start.isoformat(),
                "end_time": session_end.isoformat(),
                "duration_seconds": session_duration,
                "total_events": len(events),
                "event_categories": {cat: len(evts) for cat, evts in event_categories.items()}
            },
            "llm_usage": {
                "total_requests": len(llm_events),
                "total_tokens": total_tokens,
                "models_used": list(set(e.llm_model for e in llm_events if e.llm_model))
            },
            "evidence_processing": {
                "evidence_events": len(evidence_events),
                "unique_evidence_ids": len(set(
                    eid for event in events 
                    for eid in event.evidence_ids
                ))
            },
            "integrity_checks": {
                "events_verified": len([e for e in events if e.verification_status == "verified"]),
                "events_pending": len([e for e in events if e.verification_status == "pending"]),
                "hash_mismatches": len([e for e in events if not e.verify_integrity()])
            },
            "traceability_level": self.traceability_level.value,
            "system_metrics": {
                "events_logged": self.events_logged,
                "links_created": self.links_created
            }
        }
    
    def export_audit_data(self, session_id: str, format: str = "json") -> str:
        """Export audit data for external review."""
        
        # Log data export event
        self.log_event(AuditEvent(
            event_type=AuditEventType.DATA_EXPORT.value,
            session_id=session_id,
            data={
                "export_format": format,
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "exported_by": "system"
            }
        ))
        
        events = self.db.get_events_by_session(session_id)
        
        if format == "json":
            export_data = {
                "session_id": session_id,
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "events": [
                    {
                        "event_id": e.event_id,
                        "event_type": e.event_type,
                        "timestamp": e.timestamp.isoformat(),
                        "agent_role": e.agent_role,
                        "data": e.data,
                        "data_hash": e.data_hash,
                        "verification_status": e.verification_status
                    }
                    for e in events
                ]
            }
            return json.dumps(export_data, indent=2)
        
        # Additional formats can be added here
        return ""

# Global audit system instance
audit_system = None

def initialize_audit_system(db_path: str, traceability_level: TraceabilityLevel = TraceabilityLevel.STANDARD) -> AuditTrailSystem:
    """Initialize the global audit system."""
    global audit_system
    audit_system = AuditTrailSystem(db_path, traceability_level)
    return audit_system

def get_audit_system() -> Optional[AuditTrailSystem]:
    """Get the global audit system instance."""
    return audit_system
