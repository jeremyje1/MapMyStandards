"""
Document model for file uploads and analysis
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from . import Base

class Document(Base):
    """Document/file upload model"""
    __tablename__ = 'documents'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    organization_id = Column(String(255))
    
    # File metadata
    filename = Column(String(255), nullable=False)
    file_key = Column(String(500), nullable=False, unique=True)  # S3/storage key
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100))
    sha256 = Column(String(64))  # File hash for integrity
    
    # Processing status
    status = Column(String(50), default="uploaded")  # uploaded, processing, analyzed, failed, deleted
    error_message = Column(Text)
    
    # Analysis results
    analysis_id = Column(String(36), ForeignKey('analyses.id'))
    extracted_text = Column(Text)
    page_count = Column(Integer)
    word_count = Column(Integer)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    # Relationships
    # user = relationship("User", back_populates="documents")
    # analysis = relationship("Analysis", back_populates="document")
    
    def __repr__(self):
        return f"<Document(id='{self.id}', filename='{self.filename}', status='{self.status}')>"

class Analysis(Base):
    """Document analysis results"""
    __tablename__ = 'analyses'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    document_id = Column(String(36), ForeignKey('documents.id'))
    
    # Analysis type and configuration
    analysis_type = Column(String(50), nullable=False)  # mapping, compliance, gap_analysis
    standards_set = Column(String(100))  # SACSCOC, HLC, etc.
    configuration = Column(Text)  # JSON configuration
    
    # Status tracking
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    progress = Column(Float, default=0.0)  # 0-100
    error_message = Column(Text)
    
    # Results
    results = Column(Text)  # JSON results
    mapped_standards = Column(Text)  # JSON array of mapped standards
    confidence_score = Column(Float)
    quick_wins = Column(Text)  # JSON array of quick wins
    recommendations = Column(Text)  # JSON recommendations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    # user = relationship("User", back_populates="analyses")
    # document = relationship("Document", back_populates="analysis")
    
    def __repr__(self):
        return f"<Analysis(id='{self.id}', type='{self.analysis_type}', status='{self.status}')>"