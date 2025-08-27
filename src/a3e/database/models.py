"""
Database models for MapMyStandards trial platform
Production-ready SQLAlchemy models for persistent storage
"""

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, JSON, Boolean, 
    Float, LargeBinary, ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """User model for trial accounts"""
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True, default=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    subscription_tier = Column(String, default="trial")
    trial_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")

class Accreditor(Base):
    """Accreditor organizations (SACSCOC, HLC, etc.)"""
    __tablename__ = "accreditors"
    
    accreditor_id = Column(String, primary_key=True)  # e.g., "sacscoc", "hlc"
    name = Column(String, nullable=False)  # "Southern Association of Colleges..."
    acronym = Column(String, nullable=False)  # "SACSCOC"
    description = Column(Text, nullable=True)
    website_url = Column(String, nullable=True)
    standards_version = Column(String, default="2024")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    standards = relationship("Standard", back_populates="accreditor", cascade="all, delete-orphan")

class Standard(Base):
    """Individual accreditation standards"""
    __tablename__ = "standards"
    
    standard_id = Column(String, primary_key=True)  # e.g., "sacscoc_1_1"
    accreditor_id = Column(String, ForeignKey("accreditors.accreditor_id"), nullable=False)
    code = Column(String, nullable=False)  # "1.1"
    title = Column(String, nullable=False)  # "Mission"
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # "Institutional Mission"
    parent_id = Column(String, ForeignKey("standards.standard_id"), nullable=True)
    evidence_requirements = Column(JSON, nullable=True)  # List of required evidence types
    is_required = Column(Boolean, default=True)
    weight = Column(Integer, default=100)
    compliance_level = Column(String, default="must")  # "must", "should", "may"
    keywords = Column(JSON, nullable=True)  # List of keywords for matching
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    accreditor = relationship("Accreditor", back_populates="standards")
    parent = relationship("Standard", remote_side=[standard_id], post_update=True)
    children = relationship("Standard", remote_side=[parent_id])
    mappings = relationship("StandardMapping", back_populates="standard", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("ix_standards_accreditor_category", "accreditor_id", "category"),
        Index("ix_standards_code", "code"),
    )

class File(Base):
    """User uploaded files"""
    __tablename__ = "files"
    
    file_id = Column(String, primary_key=True, default=lambda: f"file_{uuid.uuid4().hex[:16]}")
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_content = Column(LargeBinary, nullable=True)  # Store file content in DB for Railway
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    accreditor_id = Column(String, ForeignKey("accreditors.accreditor_id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="files")
    accreditor = relationship("Accreditor")
    jobs = relationship("Job", back_populates="file", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_files_user_created", "user_id", "created_at"),
    )

class Job(Base):
    """Background analysis jobs"""
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True, default=lambda: f"job_{uuid.uuid4().hex[:24]}")
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    file_id = Column(String, ForeignKey("files.file_id"), nullable=False)
    status = Column(String, nullable=False, default="queued")  # queued, extracting, embedding, matching, analyzing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    description = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    results = Column(JSON, nullable=True)  # Analysis results, mapped standards, etc.
    job_metadata = Column(JSON, nullable=True)  # Additional job metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
    file = relationship("File", back_populates="jobs")
    mappings = relationship("StandardMapping", back_populates="job", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("ix_jobs_user_status", "user_id", "status"),
        Index("ix_jobs_status_created", "status", "created_at"),
    )

class StandardMapping(Base):
    """Mapping between files/jobs and standards"""
    __tablename__ = "standard_mappings"
    
    mapping_id = Column(String, primary_key=True, default=lambda: f"map_{uuid.uuid4().hex[:16]}")
    job_id = Column(String, ForeignKey("jobs.job_id"), nullable=False)
    standard_id = Column(String, ForeignKey("standards.standard_id"), nullable=False)
    confidence_score = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    matched_text = Column(Text, nullable=True)  # Text that matched the standard
    text_spans = Column(JSON, nullable=True)  # Character positions of matches
    mapping_metadata = Column(JSON, nullable=True)  # Additional mapping metadata
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="mappings")
    standard = relationship("Standard", back_populates="mappings")
    
    # Indexes
    __table_args__ = (
        Index("ix_mappings_job_confidence", "job_id", "confidence_score"),
        Index("ix_mappings_standard_confidence", "standard_id", "confidence_score"),
    )

class Report(Base):
    """Generated reports"""
    __tablename__ = "reports"
    
    report_id = Column(String, primary_key=True, default=lambda: f"rpt_{uuid.uuid4().hex[:24]}")
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    type = Column(String, nullable=False)  # "evidence_mapping_summary", "qep_impact_assessment"
    status = Column(String, nullable=False, default="queued")  # queued, generating, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    title = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=True)  # Report generation parameters
    content = Column(LargeBinary, nullable=True)  # PDF content stored in database
    filename = Column(String, nullable=True)  # Generated filename
    file_size = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    report_metadata = Column(JSON, nullable=True)  # Additional report metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="reports")
    
    # Indexes
    __table_args__ = (
        Index("ix_reports_user_status", "user_id", "status"),
        Index("ix_reports_type_created", "type", "created_at"),
    )

class SystemMetrics(Base):
    """System-wide metrics for analytics"""
    __tablename__ = "system_metrics"
    
    metric_id = Column(String, primary_key=True, default=lambda: f"metric_{uuid.uuid4().hex[:12]}")
    metric_type = Column(String, nullable=False)  # "daily_uploads", "completion_rate", etc.
    metric_date = Column(DateTime, nullable=False, default=func.now())
    value = Column(Float, nullable=False)
    metric_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Indexes
    __table_args__ = (
        Index("ix_metrics_type_date", "metric_type", "metric_date"),
    )
