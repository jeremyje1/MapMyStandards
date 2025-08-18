"""
Database Models for A3E System

SQLAlchemy models for institutions, evidence, standards, and agent workflows.
Supports all US accrediting bodies with contextual mapping.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey, Enum as SQLEnum, Table, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from enum import Enum
import uuid
from typing import Optional, List, Dict, Any

from ..core.accreditation_registry import InstitutionType, AccreditorType

Base = declarative_base()

# Association tables for many-to-many relationships
institution_accreditor_association = Table(
    'institution_accreditor',
    Base.metadata,
    Column('institution_id', UUID(as_uuid=True), ForeignKey('institutions.id')),
    Column('accreditor_id', String, ForeignKey('accreditors.id'))
)

evidence_standard_association = Table(
    'evidence_standard',
    Base.metadata,
    Column('evidence_id', UUID(as_uuid=True), ForeignKey('evidence.id')),
    Column('standard_id', String, ForeignKey('standards.id')),
    Column('confidence_score', Float, default=0.0),
    Column('mapped_by_agent', Boolean, default=True),
    Column('verified_by_human', Boolean, default=False),
    Column('mapping_timestamp', DateTime, default=datetime.utcnow)
)


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class EvidenceType(str, Enum):
    DOCUMENT = "document"
    DATA_EXTRACT = "data_extract"
    POLICY = "policy"
    REPORT = "report"
    ASSESSMENT = "assessment"
    CURRICULUM = "curriculum"
    FINANCIAL = "financial"
    SURVEY = "survey"
    TRANSCRIPT = "transcript"
    OTHER = "other"


class Institution(Base):
    """Higher education institution model"""
    __tablename__ = "institutions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    ipeds_id = Column(String(10), unique=True, nullable=True)  # IPEDS Unit ID
    ope_id = Column(String(10), unique=True, nullable=True)    # OPE ID
    ein = Column(String(10), unique=True, nullable=True)       # Employer Identification Number
    
    # Institution characteristics
    institution_types = Column(JSONB, nullable=False)  # List of InstitutionType enums
    state = Column(String(2), nullable=False)
    city = Column(String(100), nullable=False)
    zip_code = Column(String(10), nullable=True)
    
    # Control and sector
    control = Column(String(20), nullable=True)  # Public, Private non-profit, Private for-profit
    sector = Column(String(50), nullable=True)   # Detailed sector classification
    
    # Enrollment data
    total_enrollment = Column(Integer, nullable=True)
    undergraduate_enrollment = Column(Integer, nullable=True)
    graduate_enrollment = Column(Integer, nullable=True)
    
    # Contact information
    website = Column(String(255), nullable=True)
    primary_contact_email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # System metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    accreditors = relationship("Accreditor", secondary=institution_accreditor_association, back_populates="institutions")
    evidence_items = relationship("Evidence", back_populates="institution")
    agent_workflows = relationship("AgentWorkflow", back_populates="institution")
    gap_analyses = relationship("GapAnalysis", back_populates="institution")


class Accreditor(Base):
    """Accrediting body model"""
    __tablename__ = "accreditors"
    
    id = Column(String(20), primary_key=True)  # e.g., 'msche', 'hlc', 'aacsb'
    name = Column(String(255), nullable=False)
    acronym = Column(String(20), nullable=False)
    type = Column(SQLEnum(AccreditorType), nullable=False)
    recognition_authority = Column(String(20), nullable=False)  # USDE, CHEA, Both
    
    geographic_scope = Column(JSONB, nullable=False)  # List of states or ["National"]
    applicable_institution_types = Column(JSONB, nullable=False)  # List of InstitutionType enums
    
    website = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    
    # Metadata
    last_standards_update = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    institutions = relationship("Institution", secondary=institution_accreditor_association, back_populates="accreditors")
    standards = relationship("Standard", back_populates="accreditor")


class Standard(Base):
    """Accreditation standard model"""
    __tablename__ = "standards"
    
    id = Column(String(50), primary_key=True)  # e.g., 'msche_1', 'hlc_criterion_1'
    accreditor_id = Column(String(20), ForeignKey('accreditors.id'), nullable=False)
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    full_text = Column(Text, nullable=True)  # Complete standard text
    
    # Hierarchical structure
    parent_standard_id = Column(String(50), ForeignKey('standards.id'), nullable=True)
    order_sequence = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=1)  # 1=main, 2=sub, 3=sub-sub
    
    # Applicability
    applicable_institution_types = Column(JSONB, nullable=False)
    weight = Column(Float, default=1.0)  # Relative importance
    
    # Evidence requirements
    evidence_requirements = Column(JSONB, nullable=False)  # List of required evidence types
    sample_evidence_descriptions = Column(JSONB, nullable=True)
    
    # Processing metadata
    embedding_vector = Column(Text, nullable=True)  # Serialized embedding
    keywords = Column(JSONB, nullable=True)  # Extracted keywords for matching
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accreditor = relationship("Accreditor", back_populates="standards")
    parent_standard = relationship("Standard", remote_side=[id])
    sub_standards = relationship("Standard")
    evidence_items = relationship("Evidence", secondary=evidence_standard_association, back_populates="standards")


class Evidence(Base):
    """Evidence artifact model"""
    __tablename__ = "evidence"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey('institutions.id'), nullable=False)
    
    # Content identification
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    evidence_type = Column(SQLEnum(EvidenceType), nullable=False)
    
    # Source information
    source_system = Column(String(100), nullable=True)  # Canvas, Banner, SharePoint, etc.
    source_url = Column(String(1000), nullable=True)
    file_path = Column(String(1000), nullable=True)
    file_name = Column(String(255), nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Content and processing
    extracted_text = Column(Text, nullable=True)
    structured_data = Column(JSONB, nullable=True)  # For data extracts, surveys, etc.
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    processing_error = Column(Text, nullable=True)
    
    # Vector embeddings and search
    embedding_vector = Column(Text, nullable=True)  # Serialized embedding
    keywords = Column(JSONB, nullable=True)
    entities = Column(JSONB, nullable=True)  # Named entities extracted
    
    # Temporal information
    evidence_date = Column(DateTime, nullable=True)  # When the evidence was created
    academic_year = Column(String(10), nullable=True)  # e.g., "2024-25"
    
    # Quality metrics
    confidence_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    completeness_score = Column(Float, default=0.0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    institution = relationship("Institution", back_populates="evidence_items")
    standards = relationship("Standard", secondary=evidence_standard_association, back_populates="evidence_items")


class AgentWorkflow(Base):
    """Agent workflow execution tracking"""
    __tablename__ = "agent_workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey('institutions.id'), nullable=False)
    
    # Workflow identification
    workflow_type = Column(String(50), nullable=False)  # mapping, gap_analysis, narrative_generation
    accreditor_id = Column(String(20), ForeignKey('accreditors.id'), nullable=True)
    
    # Execution details
    status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    current_agent = Column(String(50), nullable=True)  # mapper, gap_finder, narrator, verifier
    round_number = Column(Integer, default=1)
    max_rounds = Column(Integer, default=3)
    
    # Configuration
    agent_config = Column(JSONB, nullable=True)  # Agent-specific configuration
    llm_model = Column(String(100), nullable=True)
    temperature = Column(Float, default=0.1)
    
    # Results
    output_data = Column(JSONB, nullable=True)  # Final agent output
    intermediate_results = Column(JSONB, nullable=True)  # Round-by-round results
    error_message = Column(Text, nullable=True)
    
    # Performance metrics
    execution_time_seconds = Column(Float, nullable=True)
    token_usage = Column(JSONB, nullable=True)
    cost_estimate = Column(Float, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    institution = relationship("Institution", back_populates="agent_workflows")


class GapAnalysis(Base):
    """Standards gap analysis results"""
    __tablename__ = "gap_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey('institutions.id'), nullable=False)
    accreditor_id = Column(String(20), ForeignKey('accreditors.id'), nullable=False)
    
    # Analysis metadata
    analysis_date = Column(DateTime, default=datetime.utcnow)
    academic_year = Column(String(10), nullable=False)
    analyst_type = Column(String(20), default="agent")  # agent, human, hybrid
    
    # Gap results
    total_standards = Column(Integer, nullable=False)
    standards_with_evidence = Column(Integer, nullable=False)
    standards_without_evidence = Column(Integer, nullable=False)
    standards_insufficient_evidence = Column(Integer, nullable=False)
    
    # Detailed gap data
    gap_details = Column(JSONB, nullable=False)  # Standard-by-standard gap analysis
    risk_assessment = Column(JSONB, nullable=True)  # Risk levels per standard
    recommendations = Column(JSONB, nullable=True)  # AI-generated recommendations
    
    # Quality metrics
    confidence_score = Column(Float, default=0.0)
    completeness_score = Column(Float, default=0.0)
    
    # Status tracking
    is_current = Column(Boolean, default=True)
    reviewed_by_human = Column(Boolean, default=False)
    approved_by = Column(String(255), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    institution = relationship("Institution", back_populates="gap_analyses")
    
    __table_args__ = (
        UniqueConstraint('institution_id', 'accreditor_id', 'academic_year', name='uq_gap_analysis_per_year'),
    )


class Narrative(Base):
    """Generated narrative text for standards"""
    __tablename__ = "narratives"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id = Column(UUID(as_uuid=True), ForeignKey('institutions.id'), nullable=False)
    standard_id = Column(String(50), ForeignKey('standards.id'), nullable=False)
    
    # Content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSONB, nullable=True)  # Evidence citations with page numbers
    
    # Generation metadata
    generated_by = Column(String(50), default="agent")  # agent, human, hybrid
    llm_model = Column(String(100), nullable=True)
    generation_config = Column(JSONB, nullable=True)
    
    # Quality and review
    quality_score = Column(Float, default=0.0)
    citation_accuracy = Column(Float, default=0.0)
    human_reviewed = Column(Boolean, default=False)
    human_edited = Column(Boolean, default=False)
    
    # Version control
    version = Column(Integer, default=1)
    is_current = Column(Boolean, default=True)
    previous_version_id = Column(UUID(as_uuid=True), ForeignKey('narratives.id'), nullable=True)
    
    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Self-referencing relationship for version history
    previous_version = relationship("Narrative", remote_side=[id])


class AuditLog(Base):
    """System audit log for compliance and tracking"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # create, update, delete, process, review
    entity_type = Column(String(50), nullable=False)  # institution, evidence, standard, etc.
    entity_id = Column(String(100), nullable=False)
    
    # Actor information
    user_id = Column(String(100), nullable=True)
    user_email = Column(String(255), nullable=True)
    user_role = Column(String(50), nullable=True)
    
    # Change details
    old_values = Column(JSONB, nullable=True)
    new_values = Column(JSONB, nullable=True)
    change_summary = Column(String(500), nullable=True)
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for common queries
    __table_args__ = (
        UniqueConstraint('entity_type', 'entity_id', 'timestamp', name='uq_audit_entity_time'),
    )


# Export all models for easy importing
__all__ = [
    'Base',
    'Institution',
    'Evidence', 
    'Standard',
    'Accreditor',
    'AgentWorkflow',
    'GapAnalysis',
    'Narrative',
    'AuditLog',
    'ProcessingStatus',
    'EvidenceType',
    'InstitutionType',
    'AccreditorType'
]
