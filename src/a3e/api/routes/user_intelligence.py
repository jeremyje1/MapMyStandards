"""
User Dashboard API Integration Service
Provides authenticated access to AI intelligence features for dashboard users
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
import uuid
import os

from ...models.user import User
from ...services.database_service import DatabaseService
from ...services.standards_graph import standards_graph
from ...services.evidence_mapper import evidence_mapper, EvidenceDocument
from ...services.evidence_trust import evidence_trust_scorer, EvidenceType, SourceSystem
from ...services.gap_risk_predictor import gap_risk_predictor
from ...core.config import get_settings
from ..routes.auth_impl import verify_jwt_token_email as verify_jwt_token

router = APIRouter(prefix="/api/user/intelligence", tags=["user-intelligence"])
security = HTTPBearer()
settings = get_settings()
logger = logging.getLogger(__name__)

# Database dependency
async def get_db():
    db_service = DatabaseService(settings.database_url)
    async with db_service.get_session() as session:
        yield session

# Auth dependency
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    email = verify_jwt_token(token)
    
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    # Check trial status
    if user.is_trial and not user.is_trial_active:
        raise HTTPException(status_code=403, detail="Trial period has expired")
    
    return user


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized dashboard overview with compliance insights"""
    try:
        # Get user's onboarding data for personalization
        onboarding_data = current_user.onboarding_data or {}
        institution_name = onboarding_data.get("merged", {}).get("institution_name", "Your Institution")
        primary_accreditor = onboarding_data.get("merged", {}).get("primary_accreditor", "HLC")
        
        # Get standards graph overview for their accreditor
        graph_overview = standards_graph.get_overview()
        accreditor_standards = standards_graph.get_accreditor_standards(primary_accreditor)
        
        # Get user's document count
        upload_dir = os.path.join(getattr(settings, "data_dir", "/app/data"), "uploads", str(current_user.get("id")))
        document_count = 0
        if os.path.exists(upload_dir):
            document_count = len([f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))])
        
        # Calculate basic compliance metrics
        compliance_score = min(95, 60 + (document_count * 5))  # Basic score based on documents
        
        return {
            "user": {
                "email": current_user.get("email"),
                "institution_name": institution_name,
                "primary_accreditor": primary_accreditor,
                "trial_active": current_user.is_trial_active if current_user.is_trial else True,
                "documents_analyzed": current_user.documents_analyzed or document_count
            },
            "compliance_overview": {
                "overall_score": compliance_score,
                "documents_uploaded": document_count,
                "standards_mapped": len(accreditor_standards),
                "gaps_identified": max(0, 10 - document_count),
                "risk_level": "Low" if compliance_score > 80 else "Medium" if compliance_score > 60 else "High"
            },
            "standards_summary": {
                "total_standards": len(accreditor_standards),
                "accreditor": primary_accreditor,
                "categories": graph_overview.get("categories", [])
            },
            "recent_activity": [
                {
                    "type": "account_created",
                    "message": f"Welcome to MapMyStandards A³E!",
                    "timestamp": current_user.created_at.isoformat()
                }
            ]
        }
        
    except Exception as e:
        logger.error(f"Dashboard overview error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard overview")


@router.get("/standards/graph")
async def get_standards_graph(
    accreditor: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """Get standards graph data for visualization"""
    try:
        if not accreditor:
            # Use user's primary accreditor from onboarding
            onboarding_data = current_user.onboarding_data or {}
            accreditor = onboarding_data.get("merged", {}).get("primary_accreditor", "HLC")
        
        # Get standards for the accreditor
        standards = standards_graph.get_accreditor_standards(accreditor)
        relationships = standards_graph.get_relationships(list(standards.keys())[:50])  # Limit for performance
        
        return {
            "accreditor": accreditor,
            "total_standards": len(standards),
            "standards": dict(list(standards.items())[:50]),  # Limit for UI
            "relationships": relationships[:100],  # Limit relationships
            "available_accreditors": standards_graph.get_available_accreditors()
        }
        
    except Exception as e:
        logger.error(f"Standards graph error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load standards graph")


@router.post("/evidence/analyze")
async def analyze_evidence(
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Analyze uploaded document and map to standards"""
    try:
        # Read file content
        content = await file.read()
        text_content = content.decode('utf-8', errors='ignore')
        
        if len(text_content.strip()) < 50:
            raise HTTPException(status_code=400, detail="Document content too short for analysis")
        
        # Create evidence document
        evidence_doc = EvidenceDocument(
            document_id=str(uuid.uuid4()),
            content=text_content,
            metadata={
                "filename": file.filename,
                "user_id": str(current_user.get("id")),
                "upload_time": datetime.utcnow().isoformat()
            }
        )
        
        # Map evidence to standards
        mappings = evidence_mapper.map_evidence_to_standards(
            evidence_doc,
            top_k=10,
            min_confidence=0.3
        )
        
        # Calculate trust score
        trust_score = evidence_trust_scorer.calculate_trust_score(
            evidence_id=evidence_doc.document_id,
            evidence_type=EvidenceType.POLICY,
            source_system=SourceSystem.MANUAL,
            content_length=len(text_content),
            last_modified=datetime.utcnow(),
            metadata=evidence_doc.metadata,
            mapping_confidence=mappings[0]["confidence"] if mappings else 0.0
        )
        
        # Update user stats
        current_user.documents_analyzed = (current_user.documents_analyzed or 0) + 1
        await db.commit()
        
        return {
            "document_id": evidence_doc.document_id,
            "filename": file.filename,
            "analysis": {
                "mappings": mappings,
                "trust_score": {
                    "overall_score": trust_score.overall_score,
                    "quality_score": trust_score.quality_score,
                    "reliability_score": trust_score.reliability_score,
                    "freshness_score": trust_score.freshness_score,
                    "confidence_score": trust_score.confidence_score
                },
                "content_length": len(text_content),
                "standards_mapped": len(mappings)
            }
        }
        
    except Exception as e:
        logger.error(f"Evidence analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze evidence")


@router.get("/compliance/gaps")
async def get_compliance_gaps(
    current_user: Dict = Depends(get_current_user)
):
    """Get compliance gap analysis for user's institution"""
    try:
        # Get user's data
        onboarding_data = current_user.onboarding_data or {}
        merged_data = onboarding_data.get("merged", {})
        
        accreditor = merged_data.get("primary_accreditor", "HLC")
        institution_size = merged_data.get("institution_size", "medium")
        
        # Get user's documents for analysis
        upload_dir = os.path.join(getattr(settings, "data_dir", "/app/data"), "uploads", str(current_user.get("id")))
        evidence_count = 0
        if os.path.exists(upload_dir):
            evidence_count = len([f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))])
        
        # Get gap risk prediction
        gap_risk = gap_risk_predictor.predict_compliance_gaps(
            institution_profile={
                "accreditor": accreditor,
                "size": institution_size,
                "evidence_count": evidence_count,
                "last_review": merged_data.get("launch_timing", "next_year")
            },
            evidence_summary={
                "total_documents": evidence_count,
                "coverage_percentage": min(90, evidence_count * 10),
                "quality_scores": [0.8, 0.7, 0.9] if evidence_count > 0 else []
            }
        )
        
        return {
            "risk_assessment": {
                "overall_risk": gap_risk.overall_risk,
                "risk_level": gap_risk.risk_level,
                "confidence": gap_risk.confidence,
                "timeline_months": gap_risk.timeline_months
            },
            "category_risks": gap_risk.category_risks,
            "recommendations": gap_risk.recommendations,
            "identified_issues": gap_risk.identified_issues,
            "next_actions": [
                "Upload additional evidence documents",
                "Review high-risk categories",
                "Schedule compliance assessment",
                "Update institutional documentation"
            ]
        }
        
    except Exception as e:
        logger.error(f"Compliance gaps error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze compliance gaps")


@router.get("/metrics/summary")
async def get_metrics_summary(
    current_user: Dict = Depends(get_current_user)
):
    """Get summarized metrics for dashboard widgets"""
    try:
        # Get user's upload directory
        upload_dir = os.path.join(getattr(settings, "data_dir", "/app/data"), "uploads", str(current_user.get("id")))
        document_count = 0
        if os.path.exists(upload_dir):
            document_count = len([f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))])
        
        # Get user's accreditor
        onboarding_data = current_user.onboarding_data or {}
        accreditor = onboarding_data.get("merged", {}).get("primary_accreditor", "HLC")
        
        # Get standards count for their accreditor
        accreditor_standards = standards_graph.get_accreditor_standards(accreditor)
        
        # Calculate metrics
        compliance_percentage = min(95, 40 + (document_count * 8))
        evidence_strength = min(100, 50 + (document_count * 10))
        gap_count = max(0, 15 - document_count * 2)
        
        return {
            "compliance_metrics": {
                "overall_percentage": compliance_percentage,
                "evidence_strength": evidence_strength,
                "standards_total": len(accreditor_standards),
                "standards_covered": min(len(accreditor_standards), document_count * 3),
                "gaps_identified": gap_count,
                "documents_analyzed": document_count
            },
            "trend_data": {
                "compliance_trend": "improving" if document_count > 2 else "stable",
                "risk_trend": "decreasing" if document_count > 3 else "stable",
                "coverage_trend": "increasing" if document_count > 1 else "stable"
            },
            "accreditor_info": {
                "name": accreditor,
                "standards_count": len(accreditor_standards),
                "coverage_percentage": min(100, (document_count * 3 / len(accreditor_standards)) * 100) if accreditor_standards else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Metrics summary error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load metrics summary")
