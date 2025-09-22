"""
Dynamic Risk Analysis API Routes

Calculates risk scores based on actual evidence mappings in the database.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ..dependencies import get_current_user, get_async_db
from ...models.database_schema import (
    StandardMapping, Document, AccreditationStandard, 
    StandardComplianceStatus
)
from ...services.risk_explainer import RiskExplainer, StandardEvidenceSnapshot
from ...services.gap_risk_predictor import GapRiskScore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/risk", tags=["risk-analysis"])

# Create instance of risk explainer
risk_explainer = RiskExplainer()

async def get_evidence_data_for_standard(
    standard_id: str, 
    accreditor: str,
    db: AsyncSession
) -> Dict[str, Any]:
    """Get real evidence data for a standard from database"""
    try:
        # Find the standard
        standard_result = await db.execute(
            select(AccreditationStandard).where(
                and_(
                    AccreditationStandard.code == standard_id,
                    AccreditationStandard.accreditor == accreditor.upper()
                )
            )
        )
        standard = standard_result.scalar_one_or_none()
        
        if not standard:
            return {
                "coverage": 0.0,
                "trust_scores": [],
                "evidence_ages_days": [],
                "evidence_count": 0,
                "verified_count": 0
            }
        
        # Get all mappings for this standard with document details
        mappings_result = await db.execute(
            select(StandardMapping, Document)
            .join(Document, StandardMapping.document_id == Document.id)
            .where(StandardMapping.standard_id == standard.id)
        )
        mappings_data = mappings_result.all()
        
        # Calculate metrics from real data
        trust_scores = []
        evidence_ages_days = []
        evidence_count = len(mappings_data)
        verified_count = 0
        
        for mapping, document in mappings_data:
            # Trust score from confidence
            trust_score = (mapping.confidence_score or 75) / 100.0
            trust_scores.append(trust_score)
            
            # Age in days
            if document.uploaded_at:
                age_days = (datetime.utcnow() - document.uploaded_at).days
                evidence_ages_days.append(age_days)
            else:
                evidence_ages_days.append(365)  # Default to 1 year if no date
            
            # Count verified
            if mapping.is_verified:
                verified_count += 1
        
        # Calculate coverage based on evidence count and quality
        if evidence_count == 0:
            coverage = 0.0
        elif evidence_count == 1:
            coverage = min(trust_scores[0] * 60, 60)  # Max 60% for single evidence
        elif evidence_count >= 3 and verified_count >= 1:
            avg_trust = sum(trust_scores) / len(trust_scores)
            coverage = min(avg_trust * 100, 95)  # Max 95% for multiple verified
        else:
            avg_trust = sum(trust_scores) / len(trust_scores)
            coverage = min(avg_trust * 80, 80)  # Max 80% for multiple unverified
        
        return {
            "coverage": coverage,
            "trust_scores": trust_scores,
            "evidence_ages_days": evidence_ages_days,
            "evidence_count": evidence_count,
            "verified_count": verified_count,
            "avg_confidence": sum(trust_scores) / len(trust_scores) * 100 if trust_scores else 0
        }
    except Exception as e:
        logger.error(f"Error getting evidence data for standard {standard_id}: {e}")
        return {
            "coverage": 0.0,
            "trust_scores": [],
            "evidence_ages_days": [],
            "evidence_count": 0,
            "verified_count": 0
        }

@router.post("/score-standard-dynamic")
async def score_standard_dynamic(
    data: Dict[str, Any],
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Calculate risk score for a standard using real evidence data from database"""
    try:
        standard_id = data.get("standard_id")
        accreditor = data.get("accreditor", "SACSCOC")
        
        if not standard_id:
            raise HTTPException(status_code=400, detail="Standard ID required")
        
        # Get real evidence data
        evidence_data = await get_evidence_data_for_standard(standard_id, accreditor, db)
        
        # Get compliance status if exists
        standard_result = await db.execute(
            select(AccreditationStandard).where(
                and_(
                    AccreditationStandard.code == standard_id,
                    AccreditationStandard.accreditor == accreditor.upper()
                )
            )
        )
        standard = standard_result.scalar_one_or_none()
        
        overdue_tasks = 0
        total_tasks = 0
        recent_changes = 0
        historical_findings = 0
        
        if standard:
            # Check compliance status
            compliance_result = await db.execute(
                select(StandardComplianceStatus).where(
                    StandardComplianceStatus.standard_id == standard.id
                )
            )
            compliance = compliance_result.scalar_one_or_none()
            
            if compliance:
                # Use compliance data to adjust risk
                if compliance.compliance_status == "non_compliant":
                    historical_findings = 2
                elif compliance.compliance_status == "in_progress":
                    total_tasks = 1
                
                # Check if review is overdue
                if compliance.last_reviewed_at:
                    days_since_review = (datetime.utcnow() - compliance.last_reviewed_at).days
                    if days_since_review > 180:
                        overdue_tasks = 1
                        total_tasks = max(total_tasks, 1)
        
        # Create snapshot with real data
        snapshot = StandardEvidenceSnapshot(
            standard_id=standard_id,
            coverage_percent=evidence_data["coverage"],
            trust_scores=evidence_data["trust_scores"],
            evidence_ages_days=evidence_data["evidence_ages_days"] or [365],
            overdue_tasks=overdue_tasks,
            total_tasks=total_tasks,
            recent_changes=recent_changes,
            historical_findings=historical_findings,
            days_to_review=180
        )
        
        # Calculate risk score
        risk_score = risk_explainer.compute_standard_risk(snapshot)
        
        # Enhance predicted issues based on actual evidence data
        enhanced_issues = list(risk_score.predicted_issues)
        
        # Add specific issues based on real evidence gaps
        if evidence_data["evidence_count"] == 0:
            enhanced_issues.insert(0, "No evidence mapped - complete documentation gap")
        elif evidence_data["evidence_count"] == 1:
            enhanced_issues.insert(0, "Single evidence source - requires additional supporting documents")
        elif evidence_data["verified_count"] == 0:
            enhanced_issues.append("No verified evidence - requires reviewer validation")
        
        # Check for old evidence
        if evidence_data["evidence_ages_days"]:
            avg_age = sum(evidence_data["evidence_ages_days"]) / len(evidence_data["evidence_ages_days"])
            if avg_age > 365:
                enhanced_issues.append(f"Evidence averaging {int(avg_age)} days old - refresh recommended")
        
        # Check confidence levels
        if evidence_data.get("avg_confidence", 0) < 60:
            enhanced_issues.append("Low confidence scores - evidence may not adequately support standard")
        
        # Add evidence metadata to response
        result = risk_score.to_dict()
        result["predicted_issues"] = enhanced_issues[:5]  # Limit to top 5 issues
        result["evidence_metadata"] = {
            "evidence_count": evidence_data["evidence_count"],
            "verified_count": evidence_data["verified_count"],
            "average_confidence": round(evidence_data.get("avg_confidence", 0), 2),
            "data_source": "database"
        }
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating dynamic risk score: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate risk score")

@router.get("/standard/{standard_code}/risk-summary")
async def get_standard_risk_summary(
    standard_code: str,
    accreditor: str = Query("SACSCOC"),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get comprehensive risk summary for a standard including evidence details"""
    try:
        # Get evidence data
        evidence_data = await get_evidence_data_for_standard(standard_code, accreditor, db)
        
        # Calculate risk score
        snapshot = StandardEvidenceSnapshot(
            standard_id=standard_code,
            coverage_percent=evidence_data["coverage"],
            trust_scores=evidence_data["trust_scores"],
            evidence_ages_days=evidence_data["evidence_ages_days"] or [365],
            overdue_tasks=0,
            total_tasks=0,
            recent_changes=0,
            historical_findings=0,
            days_to_review=180
        )
        
        risk_score = risk_explainer.compute_standard_risk(snapshot)
        
        # Get document details for the summary
        standard_result = await db.execute(
            select(AccreditationStandard).where(
                and_(
                    AccreditationStandard.code == standard_code,
                    AccreditationStandard.accreditor == accreditor.upper()
                )
            )
        )
        standard = standard_result.scalar_one_or_none()
        
        documents = []
        if standard:
            docs_result = await db.execute(
                select(StandardMapping, Document)
                .join(Document, StandardMapping.document_id == Document.id)
                .where(StandardMapping.standard_id == standard.id)
                .order_by(StandardMapping.confidence_score.desc())
            )
            
            for mapping, doc in docs_result:
                age_days = (datetime.utcnow() - doc.uploaded_at).days if doc.uploaded_at else 365
                documents.append({
                    "id": doc.id,
                    "name": doc.filename,
                    "confidence_score": mapping.confidence_score or 75,
                    "is_verified": mapping.is_verified,
                    "age_days": age_days,
                    "evidence_strength": mapping.evidence_strength or "Adequate"
                })
        
        return {
            "success": True,
            "data": {
                "standard_code": standard_code,
                "risk_score": risk_score.risk_score,
                "risk_level": risk_score.risk_level.value,
                "coverage_percent": evidence_data["coverage"],
                "evidence_count": evidence_data["evidence_count"],
                "verified_count": evidence_data["verified_count"],
                "average_confidence": evidence_data.get("avg_confidence", 0),
                "predicted_issues": risk_score.predicted_issues,
                "remediation_priority": risk_score.remediation_priority.value,
                "documents": documents,
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting risk summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk summary")

@router.post("/bulk-score-dynamic")
async def bulk_score_dynamic(
    data: Dict[str, Any],
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Calculate risk scores for multiple standards using real evidence data"""
    try:
        standard_ids = data.get("standard_ids", [])
        accreditor = data.get("accreditor", "SACSCOC")
        
        if not standard_ids:
            raise HTTPException(status_code=400, detail="No standards provided")
        
        results = []
        
        for standard_id in standard_ids[:50]:  # Limit to 50 standards
            try:
                # Get evidence data
                evidence_data = await get_evidence_data_for_standard(standard_id, accreditor, db)
                
                # Create snapshot
                snapshot = StandardEvidenceSnapshot(
                    standard_id=standard_id,
                    coverage_percent=evidence_data["coverage"],
                    trust_scores=evidence_data["trust_scores"],
                    evidence_ages_days=evidence_data["evidence_ages_days"] or [365],
                    overdue_tasks=0,
                    total_tasks=0,
                    recent_changes=0,
                    historical_findings=0,
                    days_to_review=180
                )
                
                # Calculate risk
                risk_score = risk_explainer.compute_standard_risk(snapshot)
                
                result = {
                    "standard_id": standard_id,
                    "risk_score": risk_score.risk_score,
                    "risk_level": risk_score.risk_level.value,
                    "coverage": evidence_data["coverage"],
                    "evidence_count": evidence_data["evidence_count"]
                }
                results.append(result)
            except Exception as e:
                logger.error(f"Error scoring standard {standard_id}: {e}")
                continue
        
        return {
            "success": True,
            "data": {
                "scored_count": len(results),
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk scoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to score standards")
