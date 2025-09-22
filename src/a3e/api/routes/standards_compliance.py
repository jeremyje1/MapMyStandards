"""
Standards Compliance API Routes

Provides endpoints for managing standard compliance status based on evidence mappings.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, func, Column, String, DateTime, Boolean, Float, Text, ForeignKey, JSON, Index, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid

from ..dependencies import get_current_user, get_async_db
from ...models.database_schema import (
    StandardMapping, Document, AccreditationStandard, 
    User, Base, generate_uuid
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/standards", tags=["standards-compliance"])

# Create StandardComplianceStatus model if it doesn't exist in database_schema
class StandardComplianceStatus(Base):
    """Track compliance status for each standard"""
    __tablename__ = "standard_compliance_status"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    standard_id = Column(String(36), ForeignKey("accreditation_standards.id"), nullable=False)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False)
    
    # Compliance status
    compliance_status = Column(String(20))  # compliant, non_compliant, in_progress, not_started
    compliance_level = Column(String(20))  # full, partial, minimal, none
    compliance_score = Column(Float)  # 0-100
    
    # Evidence summary
    evidence_count = Column(Integer, default=0)
    verified_evidence_count = Column(Integer, default=0)
    average_evidence_strength = Column(String(20))  # Strong, Adequate, Weak
    
    # Review details
    last_reviewed_by_id = Column(String(36), ForeignKey("users.id"))
    last_reviewed_at = Column(DateTime)
    review_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    standard = relationship("AccreditationStandard")
    institution = relationship("Institution")
    last_reviewed_by = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index("idx_standard_compliance", "standard_id", "institution_id"),
        UniqueConstraint("standard_id", "institution_id"),
    )

@router.post("/compliance/update")
async def update_standard_compliance(
    data: Dict[str, Any] = Body(...),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update compliance status for selected standards"""
    try:
        standard_codes = data.get("standard_ids", [])
        new_status = data.get("status", "compliant")
        accreditor = data.get("accreditor", "SACSCOC")
        
        if not standard_codes:
            raise HTTPException(status_code=400, detail="No standards provided")
        
        updated_count = 0
        
        for standard_code in standard_codes:
            # Find the standard
            standard_result = await db.execute(
                select(AccreditationStandard).where(
                    and_(
                        AccreditationStandard.code == standard_code,
                        AccreditationStandard.accreditor == accreditor.upper()
                    )
                )
            )
            standard = standard_result.scalar_one_or_none()
            
            if not standard:
                logger.warning(f"Standard not found: {standard_code}")
                continue
            
            # Count evidence mappings
            mappings_result = await db.execute(
                select(
                    func.count(StandardMapping.id).label("total_count"),
                    func.count(StandardMapping.id).filter(StandardMapping.is_verified.is_(True)).label("verified_count"),
                    func.avg(StandardMapping.confidence_score).label("avg_confidence")
                )
                .where(StandardMapping.standard_id == standard.id)
            )
            mapping_stats = mappings_result.one()
            
            # Determine compliance level based on evidence
            evidence_count = mapping_stats.total_count or 0
            verified_count = mapping_stats.verified_count or 0
            avg_confidence = mapping_stats.avg_confidence or 0
            
            if new_status == "compliant":
                if evidence_count >= 3 and verified_count >= 1 and avg_confidence >= 80:
                    compliance_level = "full"
                    compliance_score = min(avg_confidence * 1.1, 100)
                elif evidence_count >= 2 and avg_confidence >= 70:
                    compliance_level = "partial"
                    compliance_score = avg_confidence
                else:
                    compliance_level = "minimal"
                    compliance_score = avg_confidence * 0.8
            else:
                compliance_level = "none"
                compliance_score = 0
            
            # Get or create compliance status record
            # For demo purposes, use a default institution_id
            institution_id = "default-institution-id"
            
            status_result = await db.execute(
                select(StandardComplianceStatus).where(
                    and_(
                        StandardComplianceStatus.standard_id == standard.id,
                        StandardComplianceStatus.institution_id == institution_id
                    )
                )
            )
            compliance_status = status_result.scalar_one_or_none()
            
            if compliance_status:
                # Update existing
                compliance_status.compliance_status = new_status
                compliance_status.compliance_level = compliance_level
                compliance_status.compliance_score = compliance_score
                compliance_status.evidence_count = evidence_count
                compliance_status.verified_evidence_count = verified_count
                compliance_status.last_reviewed_by_id = current_user.get("user_id") if current_user else None
                compliance_status.last_reviewed_at = datetime.utcnow()
                compliance_status.updated_at = datetime.utcnow()
            else:
                # Create new
                compliance_status = StandardComplianceStatus(
                    id=str(uuid.uuid4()),
                    standard_id=standard.id,
                    institution_id=institution_id,
                    compliance_status=new_status,
                    compliance_level=compliance_level,
                    compliance_score=compliance_score,
                    evidence_count=evidence_count,
                    verified_evidence_count=verified_count,
                    last_reviewed_by_id=current_user.get("user_id") if current_user else None,
                    last_reviewed_at=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(compliance_status)
            
            updated_count += 1
        
        await db.commit()
        
        return {
            "success": True,
            "data": {
                "updated_count": updated_count,
                "status": new_status,
                "message": f"Successfully updated compliance status for {updated_count} standard(s)"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating compliance status: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update compliance status")

@router.get("/compliance/status/{standard_code}")
async def get_standard_compliance_status(
    standard_code: str,
    accreditor: str = "SACSCOC",
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get compliance status for a specific standard"""
    try:
        # Find the standard
        standard_result = await db.execute(
            select(AccreditationStandard).where(
                and_(
                    AccreditationStandard.code == standard_code,
                    AccreditationStandard.accreditor == accreditor.upper()
                )
            )
        )
        standard = standard_result.scalar_one_or_none()
        
        if not standard:
            raise HTTPException(status_code=404, detail="Standard not found")
        
        # Get compliance status
        institution_id = "default-institution-id"
        status_result = await db.execute(
            select(StandardComplianceStatus).where(
                and_(
                    StandardComplianceStatus.standard_id == standard.id,
                    StandardComplianceStatus.institution_id == institution_id
                )
            )
        )
        compliance_status = status_result.scalar_one_or_none()
        
        if compliance_status:
            return {
                "success": True,
                "data": {
                    "standard_code": standard_code,
                    "standard_title": standard.title,
                    "compliance_status": compliance_status.compliance_status,
                    "compliance_level": compliance_status.compliance_level,
                    "compliance_score": compliance_status.compliance_score,
                    "evidence_count": compliance_status.evidence_count,
                    "verified_evidence_count": compliance_status.verified_evidence_count,
                    "last_reviewed_at": compliance_status.last_reviewed_at.isoformat() if compliance_status.last_reviewed_at else None,
                    "review_notes": compliance_status.review_notes
                }
            }
        else:
            # No status recorded yet
            return {
                "success": True,
                "data": {
                    "standard_code": standard_code,
                    "standard_title": standard.title,
                    "compliance_status": "not_started",
                    "compliance_level": "none",
                    "compliance_score": 0,
                    "evidence_count": 0,
                    "verified_evidence_count": 0,
                    "last_reviewed_at": None,
                    "review_notes": None
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting compliance status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get compliance status")

@router.get("/compliance/summary")
async def get_compliance_summary(
    accreditor: str = "SACSCOC",
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get overall compliance summary for all standards"""
    try:
        institution_id = "default-institution-id"
        
        # Get all standards for the accreditor
        standards_result = await db.execute(
            select(func.count(AccreditationStandard.id))
            .where(AccreditationStandard.accreditor == accreditor.upper())
        )
        total_standards = standards_result.scalar() or 0
        
        # Get compliance status counts
        status_counts_result = await db.execute(
            select(
                StandardComplianceStatus.compliance_status,
                func.count(StandardComplianceStatus.id).label("count")
            )
            .join(AccreditationStandard)
            .where(
                and_(
                    StandardComplianceStatus.institution_id == institution_id,
                    AccreditationStandard.accreditor == accreditor.upper()
                )
            )
            .group_by(StandardComplianceStatus.compliance_status)
        )
        
        status_counts = {row.compliance_status: row.count for row in status_counts_result}
        
        # Calculate percentages
        compliant_count = status_counts.get("compliant", 0)
        non_compliant_count = status_counts.get("non_compliant", 0)
        in_progress_count = status_counts.get("in_progress", 0)
        not_started_count = total_standards - sum(status_counts.values())
        
        overall_compliance_rate = (compliant_count / total_standards * 100) if total_standards > 0 else 0
        
        return {
            "success": True,
            "data": {
                "accreditor": accreditor,
                "total_standards": total_standards,
                "compliance_summary": {
                    "compliant": compliant_count,
                    "non_compliant": non_compliant_count,
                    "in_progress": in_progress_count,
                    "not_started": not_started_count
                },
                "overall_compliance_rate": round(overall_compliance_rate, 2),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting compliance summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get compliance summary")
