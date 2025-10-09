"""
Complete Database Schema for MapMyStandards Platform

This module defines all database tables for tracking:
- Institutions and users
- Documents and evidence
- Standards mappings
- Compliance metrics
- Processing history
- Reports
"""

from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())


class Institution(Base):
    """Institution/Organization using the platform"""
    __tablename__ = "institutions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    ipeds_id = Column(String(20), unique=True, nullable=True)
    state = Column(String(2))
    institution_type = Column(String(50))  # college, university, community_college
    enrollment_size = Column(String(20))  # under_1000, 1k_5k, 5k_15k, 15k_plus
    primary_accreditor = Column(String(20))  # SACSCOC, HLC, WASC, etc.
    
    # Subscription info
    subscription_status = Column(String(20), default="trial")  # trial, active, expired
    subscription_plan = Column(String(50))
    trial_end_date = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    onboarding_completed = Column(Boolean, default=False)
    onboarding_data = Column(JSON)  # Store onboarding wizard responses
    
    # Relationships
    users = relationship("User", back_populates="institution")
    documents = relationship("Document", back_populates="institution")
    compliance_snapshots = relationship("ComplianceSnapshot", back_populates="institution")
    reports = relationship("Report", back_populates="institution")


class User(Base):
    """Platform users"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    role = Column(String(50))  # admin, editor, viewer
    institution_id = Column(String(36), ForeignKey("institutions.id"))
    
    # Auth
    auth_provider = Column(String(20))  # email, google, microsoft
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    institution = relationship("Institution", back_populates="users")
    uploaded_documents = relationship("Document", back_populates="uploaded_by")


class Document(Base):
    """Uploaded documents/evidence"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    uploaded_by_id = Column(String(36), ForeignKey("users.id"))
    
    # File info
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    file_path = Column(String(500))  # Storage location
    file_size = Column(Integer)  # bytes
    mime_type = Column(String(100))
    file_hash = Column(String(64))  # SHA256 hash for deduplication
    
    # Document metadata
    title = Column(String(255))
    description = Column(Text)
    document_type = Column(String(50))  # policy, procedure, report, evidence, etc.
    document_date = Column(DateTime)  # Date of the document content
    academic_year = Column(String(20))  # 2023-2024
    
    # Processing status
    processing_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    processed_at = Column(DateTime)
    processing_time_seconds = Column(Float)
    error_message = Column(Text)
    
    # Extracted content
    extracted_text = Column(Text)
    page_count = Column(Integer)
    word_count = Column(Integer)
    
    # AI Analysis results
    ai_summary = Column(Text)
    ai_insights = Column(JSON)  # Structured insights from AI
    confidence_score = Column(Float)  # 0-100
    
    # Metadata
    uploaded_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    tags = Column(JSON)  # Array of tags
    
    # Relationships
    institution = relationship("Institution", back_populates="documents")
    uploaded_by = relationship("User", back_populates="uploaded_documents")
    standard_mappings = relationship("StandardMapping", back_populates="document")
    
    # Indexes
    __table_args__ = (
        Index("idx_institution_documents", "institution_id"),
        Index("idx_document_status", "processing_status"),
        Index("idx_document_type", "document_type"),
    )


class AccreditationStandard(Base):
    """Accreditation standards from various bodies"""
    __tablename__ = "accreditation_standards"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    accreditor = Column(String(20), nullable=False)  # SACSCOC, HLC, WASC, etc.
    standard_id = Column(String(20), nullable=False)  # CR 1, CS 5.4, etc.
    standard_title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))  # Core Requirements, Comprehensive Standards, etc.
    
    # Requirements
    evidence_requirements = Column(JSON)  # List of required evidence types
    is_required = Column(Boolean, default=True)
    applies_to_types = Column(JSON)  # Institution types this applies to
    
    # Metadata
    version = Column(String(20))  # 2024 Principles
    effective_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    mappings = relationship("StandardMapping", back_populates="standard")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint("accreditor", "standard_id", "version"),
        Index("idx_accreditor_standards", "accreditor"),
    )


class StandardMapping(Base):
    """Mapping between documents and standards"""
    __tablename__ = "standard_mappings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    standard_id = Column(String(36), ForeignKey("accreditation_standards.id"), nullable=False)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    
    # Mapping details
    evidence_text = Column(Text)  # Specific text that maps to standard
    page_numbers = Column(JSON)  # Array of page numbers
    confidence = Column(String(10))  # High, Medium, Low
    confidence_score = Column(Float)  # 0-100
    mapping_method = Column(String(20))  # ai_auto, manual, verified
    
    # Quality indicators
    evidence_strength = Column(String(20))  # Strong, Adequate, Weak, Missing
    gap_identified = Column(Boolean, default=False)
    gap_description = Column(Text)
    recommendations = Column(JSON)  # Array of recommendations
    
    # Review status
    reviewed_by_id = Column(String(36), ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    is_verified = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="standard_mappings")
    standard = relationship("AccreditationStandard", back_populates="mappings")
    institution = relationship("Institution")
    reviewed_by = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_document_mappings", "document_id"),
        Index("idx_standard_mappings", "standard_id"),
        Index("idx_institution_mappings", "institution_id"),
        UniqueConstraint("document_id", "standard_id"),  # One mapping per document-standard pair
    )


class ComplianceSnapshot(Base):
    """Point-in-time compliance status for an institution"""
    __tablename__ = "compliance_snapshots"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    accreditor = Column(String(20), nullable=False)
    
    # Metrics
    overall_compliance_score = Column(Float)  # 0-100
    standards_addressed = Column(Integer)
    total_standards = Column(Integer)
    documents_processed = Column(Integer)
    evidence_items = Column(Integer)
    
    # Breakdown by category
    category_scores = Column(JSON)  # {category: score} mapping
    
    # Gap analysis
    critical_gaps = Column(Integer, default=0)
    major_gaps = Column(Integer, default=0)
    minor_gaps = Column(Integer, default=0)
    gap_details = Column(JSON)  # Detailed gap information
    
    # Trends
    score_change_from_previous = Column(Float)  # Percentage change
    trend_direction = Column(String(10))  # up, down, stable
    
    # Metadata
    snapshot_date = Column(DateTime, default=func.now())
    generated_by_id = Column(String(36), ForeignKey("users.id"))
    notes = Column(Text)
    
    # Relationships
    institution = relationship("Institution", back_populates="compliance_snapshots")
    generated_by = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_institution_snapshots", "institution_id"),
        Index("idx_snapshot_date", "snapshot_date"),
    )


class Report(Base):
    """Generated reports"""
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    requested_by_id = Column(String(36), ForeignKey("users.id"))
    
    # Report details
    report_type = Column(String(50), nullable=False)  # comprehensive, gap_analysis, qep, evidence_mapping
    title = Column(String(255))
    description = Column(Text)
    accreditor = Column(String(20))
    
    # Generation status
    status = Column(String(20), default="pending")  # pending, generating, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    
    # Report content
    executive_summary = Column(Text)
    report_data = Column(JSON)  # Structured report data
    file_path = Column(String(500))  # Generated file location
    file_format = Column(String(10))  # pdf, docx, xlsx
    file_size = Column(Integer)
    
    # Parameters used
    parameters = Column(JSON)  # Report generation parameters
    filters_applied = Column(JSON)  # Any filters used
    date_range_start = Column(DateTime)
    date_range_end = Column(DateTime)
    
    # Metadata
    requested_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    generation_time_seconds = Column(Float)
    error_message = Column(Text)
    
    # Access tracking
    download_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)
    shared_with = Column(JSON)  # List of user IDs
    
    # Relationships
    institution = relationship("Institution", back_populates="reports")
    requested_by = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_institution_reports", "institution_id"),
        Index("idx_report_status", "status"),
        Index("idx_report_type", "report_type"),
    )


class ProcessingJob(Base):
    """Background processing jobs"""
    __tablename__ = "processing_jobs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_type = Column(String(50), nullable=False)  # document_processing, report_generation, bulk_analysis
    status = Column(String(20), default="queued")  # queued, running, completed, failed
    
    # Job details
    entity_id = Column(String(36))  # ID of document, report, etc.
    entity_type = Column(String(50))  # document, report, analysis
    parameters = Column(JSON)
    
    # Progress tracking
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(255))
    steps_completed = Column(Integer, default=0)
    total_steps = Column(Integer)
    
    # Results
    result = Column(JSON)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timing
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    processing_time_seconds = Column(Float)
    
    # Indexes
    __table_args__ = (
        Index("idx_job_status", "status"),
        Index("idx_job_type", "job_type"),
        Index("idx_job_entity", "entity_id"),
    )


class AuditLog(Base):
    """Audit trail for compliance tracking"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_id = Column(String(36), ForeignKey("institutions.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    
    # Action details
    action = Column(String(50), nullable=False)  # upload, delete, modify, verify, generate_report
    entity_type = Column(String(50))  # document, mapping, report, etc.
    entity_id = Column(String(36))
    
    # Change tracking
    old_value = Column(JSON)
    new_value = Column(JSON)
    description = Column(Text)
    
    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    timestamp = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("idx_audit_institution", "institution_id"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_action", "action"),
    )
