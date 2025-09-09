"""
Personalization and analysis API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import json
from sqlalchemy.orm import Session
import logging

from ...models.user import User
from ...models.document import Analysis
from ...core.database import get_db
from .auth_enhanced import get_current_user
from ...services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["personalization"])

# Pydantic models
class ProfileRequest(BaseModel):
    institution_type: str  # college, university, multi_campus, system
    accreditor: str  # SACSCOC, HLC, MSCHE, etc.
    enrollment_size: str  # small, medium, large
    focus_areas: List[str]  # academic_programs, student_services, governance, etc.
    current_challenges: List[str]
    goals: List[str]
    timeline: str  # immediate, 3_months, 6_months, 1_year
    
class ProfileResponse(BaseModel):
    profile_id: str
    message: str
    recommendations: List[Dict[str, Any]]

class AnalysisRequest(BaseModel):
    document_id: str
    analysis_type: str  # mapping, compliance, gap_analysis
    standards_set: str  # SACSCOC, HLC, etc.
    focus_areas: Optional[List[str]] = None
    custom_parameters: Optional[Dict[str, Any]] = None

class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str
    estimated_time: Optional[int] = None  # seconds

class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str
    progress: float
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

class QuickWin(BaseModel):
    id: str
    title: str
    description: str
    impact: str  # high, medium, low
    effort: str  # high, medium, low
    category: str
    standard_reference: Optional[str] = None

class MappedStandard(BaseModel):
    standard_id: str
    standard_text: str
    evidence_found: str
    confidence_score: float
    location: str  # page/section reference
    recommendations: List[str]

@router.post("/profiles", response_model=ProfileResponse)
async def create_profile(
    request: ProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update user's personalization profile
    """
    try:
        # Update user's onboarding data
        onboarding_data = {
            "institution_type": request.institution_type,
            "accreditor": request.accreditor,
            "enrollment_size": request.enrollment_size,
            "focus_areas": request.focus_areas,
            "current_challenges": request.current_challenges,
            "goals": request.goals,
            "timeline": request.timeline,
            "profile_created_at": datetime.utcnow().isoformat()
        }
        
        current_user.onboarding_data = onboarding_data
        current_user.onboarding_completed = True
        current_user.institution_type = request.institution_type
        db.commit()
        
        # Generate personalized recommendations
        recommendations = generate_recommendations(onboarding_data)
        
        return ProfileResponse(
            profile_id=str(current_user.id),
            message="Profile created successfully",
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Profile creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create profile")

@router.post("/analyses", response_model=AnalysisResponse)
async def create_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new document analysis
    """
    try:
        # Create analysis record
        analysis = Analysis(
            user_id=current_user.id,
            document_id=request.document_id,
            analysis_type=request.analysis_type,
            standards_set=request.standards_set,
            configuration=json.dumps({
                "focus_areas": request.focus_areas,
                "custom_parameters": request.custom_parameters
            }),
            status="pending",
            created_at=datetime.utcnow()
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Queue background analysis task
        background_tasks.add_task(
            run_analysis,
            analysis_id=str(analysis.id),
            db=db
        )
        
        # Estimate processing time based on document size and analysis type
        estimated_time = estimate_processing_time(request.analysis_type)
        
        return AnalysisResponse(
            analysis_id=str(analysis.id),
            status="pending",
            message="Analysis started successfully",
            estimated_time=estimated_time
        )
        
    except Exception as e:
        logger.error(f"Analysis creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analysis")

@router.get("/analyses/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analysis status and results
    """
    try:
        analysis = db.query(Analysis).filter(
            Analysis.id == analysis_id,
            Analysis.user_id == current_user.id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Parse results if analysis is complete
        results = None
        if analysis.status == "completed" and analysis.results:
            try:
                results = json.loads(analysis.results)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse analysis results for {analysis_id}")
        
        return AnalysisStatusResponse(
            analysis_id=str(analysis.id),
            status=analysis.status,
            progress=analysis.progress or 0.0,
            results=results,
            error=analysis.error_message,
            created_at=analysis.created_at.isoformat(),
            completed_at=analysis.completed_at.isoformat() if analysis.completed_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get analysis status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analysis status")

@router.get("/analyses", response_model=List[AnalysisStatusResponse])
async def list_analyses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """
    List user's analyses
    """
    try:
        analyses = db.query(Analysis).filter(
            Analysis.user_id == current_user.id
        ).order_by(
            Analysis.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        results = []
        for analysis in analyses:
            # Parse results if available
            analysis_results = None
            if analysis.status == "completed" and analysis.results:
                try:
                    analysis_results = json.loads(analysis.results)
                except json.JSONDecodeError:
                    pass
            
            results.append(AnalysisStatusResponse(
                analysis_id=str(analysis.id),
                status=analysis.status,
                progress=analysis.progress or 0.0,
                results=analysis_results,
                error=analysis.error_message,
                created_at=analysis.created_at.isoformat(),
                completed_at=analysis.completed_at.isoformat() if analysis.completed_at else None
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"List analyses error: {e}")
        raise HTTPException(status_code=500, detail="Failed to list analyses")

@router.get("/quick-wins")
async def get_quick_wins(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized quick wins based on user's profile and analyses
    """
    try:
        # Get user's latest completed analysis
        latest_analysis = db.query(Analysis).filter(
            Analysis.user_id == current_user.id,
            Analysis.status == "completed"
        ).order_by(Analysis.completed_at.desc()).first()
        
        if not latest_analysis or not latest_analysis.quick_wins:
            # Return default quick wins
            return generate_default_quick_wins(current_user)
        
        # Parse and return quick wins
        quick_wins = json.loads(latest_analysis.quick_wins)
        return quick_wins
        
    except Exception as e:
        logger.error(f"Get quick wins error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quick wins")

# Helper functions
def generate_recommendations(profile_data: dict) -> List[Dict[str, Any]]:
    """Generate personalized recommendations based on profile"""
    recommendations = []
    
    # Based on institution type
    if profile_data.get("institution_type") == "college":
        recommendations.append({
            "title": "Start with Core Requirements",
            "description": "Focus on fundamental accreditation standards",
            "priority": "high",
            "action": "Review Section 5: Administration and Organization"
        })
    
    # Based on challenges
    if "documentation" in profile_data.get("current_challenges", []):
        recommendations.append({
            "title": "Document Organization System",
            "description": "Implement a structured document management approach",
            "priority": "high",
            "action": "Use our document mapping feature to organize evidence"
        })
    
    # Based on timeline
    if profile_data.get("timeline") == "immediate":
        recommendations.append({
            "title": "Quick Assessment",
            "description": "Run a gap analysis on your QEP documentation",
            "priority": "urgent",
            "action": "Upload your QEP for instant analysis"
        })
    
    return recommendations

def estimate_processing_time(analysis_type: str) -> int:
    """Estimate processing time in seconds"""
    base_times = {
        "mapping": 30,
        "compliance": 60,
        "gap_analysis": 45,
    }
    return base_times.get(analysis_type, 60)

def generate_default_quick_wins(user: User) -> List[Dict[str, Any]]:
    """Generate default quick wins"""
    return [
        {
            "id": "qw1",
            "title": "Update Mission Statement",
            "description": "Ensure your mission statement aligns with current strategic plan",
            "impact": "high",
            "effort": "low",
            "category": "governance",
            "standard_reference": "SACSCOC 2.1"
        },
        {
            "id": "qw2",
            "title": "Document Faculty Credentials",
            "description": "Create a centralized faculty credentials database",
            "impact": "high",
            "effort": "medium",
            "category": "faculty",
            "standard_reference": "SACSCOC 6.2.a"
        },
        {
            "id": "qw3",
            "title": "Student Learning Outcomes",
            "description": "Review and update SLOs for all programs",
            "impact": "medium",
            "effort": "medium",
            "category": "academic",
            "standard_reference": "SACSCOC 8.2"
        }
    ]

async def run_analysis(analysis_id: str, db: Session):
    """Background task to run document analysis"""
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return
        
        # Update status to processing
        analysis.status = "processing"
        analysis.started_at = datetime.utcnow()
        analysis.progress = 10.0
        db.commit()
        
        # TODO: Integrate with actual analysis service
        # For now, simulate analysis
        import asyncio
        await asyncio.sleep(5)
        
        # Generate mock results
        results = {
            "mapped_standards": [
                {
                    "standard_id": "SACSCOC 5.4",
                    "standard_text": "Qualified administrative/academic officers",
                    "evidence_found": "Leadership structure documented on pages 12-15",
                    "confidence_score": 0.92,
                    "location": "Pages 12-15",
                    "recommendations": [
                        "Add CVs for new administrators",
                        "Update organizational chart"
                    ]
                }
            ],
            "quick_wins": generate_default_quick_wins(None),
            "compliance_score": 0.78,
            "gaps_identified": 3,
            "recommendations": [
                "Focus on faculty qualifications documentation",
                "Update assessment procedures",
                "Strengthen QEP implementation evidence"
            ]
        }
        
        # Update analysis with results
        analysis.status = "completed"
        analysis.completed_at = datetime.utcnow()
        analysis.progress = 100.0
        analysis.results = json.dumps(results)
        analysis.mapped_standards = json.dumps(results["mapped_standards"])
        analysis.quick_wins = json.dumps(results["quick_wins"])
        analysis.confidence_score = results["compliance_score"]
        analysis.recommendations = json.dumps(results["recommendations"])
        db.commit()
        
    except Exception as e:
        logger.error(f"Analysis processing error: {e}")
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            analysis.completed_at = datetime.utcnow()
            db.commit()