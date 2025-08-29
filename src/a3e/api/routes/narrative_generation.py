"""
Narrative Generation API

Real-time AI-powered narrative generation for accreditation responses.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ...services.narrative_generation_service import get_narrative_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/narratives", tags=["narrative-generation"])


class EvidenceNarrativeRequest(BaseModel):
    """Request for evidence narrative generation"""
    evidence_text: str
    standard_id: str
    standard_description: str
    institution_context: Optional[Dict[str, Any]] = None


class GapNarrativeRequest(BaseModel):
    """Request for gap narrative generation"""
    gap_description: str
    standard_id: str
    current_evidence: List[str]
    improvement_plan: Optional[Dict[str, Any]] = None


class ComprehensiveResponseRequest(BaseModel):
    """Request for comprehensive standard response"""
    standard_id: str
    standard_title: str
    evidence_documents: List[Dict[str, Any]]
    institution_data: Dict[str, Any]


class QEPNarrativeRequest(BaseModel):
    """Request for QEP narrative generation"""
    qep_topic: str
    qep_goals: List[str]
    current_state_data: Dict[str, Any]
    evidence_of_need: List[str]


class BatchNarrativeRequest(BaseModel):
    """Request for batch narrative generation"""
    narratives: List[Dict[str, Any]]
    priority: str = "normal"  # normal, high


class NarrativeResponse(BaseModel):
    """Response for narrative generation"""
    success: bool
    narrative: str
    metadata: Dict[str, Any]
    quality_metrics: Optional[Dict[str, Any]] = None
    generated_at: str


@router.post("/evidence", response_model=NarrativeResponse)
async def generate_evidence_narrative(request: EvidenceNarrativeRequest):
    """
    Generate a narrative connecting evidence to an accreditation standard
    
    This creates real, institution-specific narratives that demonstrate
    how evidence supports compliance with specific standards.
    """
    try:
        narrative_service = get_narrative_service()
        
        result = await narrative_service.generate_evidence_narrative(
            evidence_text=request.evidence_text,
            standard_id=request.standard_id,
            standard_description=request.standard_description,
            institution_context=request.institution_context
        )
        
        if result.get("success"):
            return NarrativeResponse(
                success=True,
                narrative=result["narrative"],
                metadata={
                    "standard_id": result["standard_id"],
                    "word_count": result["word_count"]
                },
                quality_metrics=result.get("quality_metrics"),
                generated_at=result["generated_at"]
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate narrative")
            
    except Exception as e:
        logger.error(f"Error generating evidence narrative: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gap", response_model=NarrativeResponse)
async def generate_gap_narrative(request: GapNarrativeRequest):
    """
    Generate a narrative addressing compliance gaps
    
    Creates constructive narratives that acknowledge gaps while
    demonstrating commitment to improvement.
    """
    try:
        narrative_service = get_narrative_service()
        
        result = await narrative_service.generate_gap_narrative(
            gap_description=request.gap_description,
            standard_id=request.standard_id,
            current_evidence=request.current_evidence,
            improvement_plan=request.improvement_plan
        )
        
        if result.get("success"):
            return NarrativeResponse(
                success=True,
                narrative=result["narrative"],
                metadata={
                    "gap_addressed": result["gap_addressed"],
                    "improvement_focus": result["improvement_focus"],
                    "timeline": result.get("timeline")
                },
                generated_at=result["generated_at"]
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate gap narrative")
            
    except Exception as e:
        logger.error(f"Error generating gap narrative: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comprehensive", response_model=NarrativeResponse)
async def generate_comprehensive_response(request: ComprehensiveResponseRequest):
    """
    Generate a complete standard response narrative
    
    Creates full, structured responses for accreditation standards
    using all available evidence.
    """
    try:
        narrative_service = get_narrative_service()
        
        result = await narrative_service.generate_comprehensive_response(
            standard_id=request.standard_id,
            standard_title=request.standard_title,
            evidence_documents=request.evidence_documents,
            institution_data=request.institution_data
        )
        
        if result.get("success"):
            return NarrativeResponse(
                success=True,
                narrative=result["narrative"],
                metadata={
                    "standard_id": result["standard_id"],
                    "standard_title": result["standard_title"],
                    "structured_sections": result["structured_sections"],
                    "compliance_statement": result["compliance_statement"],
                    "evidence_count": result["evidence_count"],
                    "word_count": result["word_count"]
                },
                generated_at=result["generated_at"]
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate comprehensive response")
            
    except Exception as e:
        logger.error(f"Error generating comprehensive response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qep", response_model=NarrativeResponse)
async def generate_qep_narrative(request: QEPNarrativeRequest):
    """
    Generate QEP narrative sections
    
    Creates compelling Quality Enhancement Plan narratives that
    demonstrate evidence-based planning and measurable outcomes.
    """
    try:
        narrative_service = get_narrative_service()
        
        result = await narrative_service.generate_qep_section(
            qep_topic=request.qep_topic,
            qep_goals=request.qep_goals,
            current_state_data=request.current_state_data,
            evidence_of_need=request.evidence_of_need
        )
        
        if result.get("success"):
            return NarrativeResponse(
                success=True,
                narrative=result["narrative"],
                metadata={
                    "qep_topic": result["qep_topic"],
                    "key_themes": result["key_themes"],
                    "measurable_outcomes": result["measurable_outcomes"],
                    "word_count": result["word_count"]
                },
                generated_at=result["generated_at"]
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate QEP narrative")
            
    except Exception as e:
        logger.error(f"Error generating QEP narrative: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def generate_batch_narratives(
    request: BatchNarrativeRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate multiple narratives in batch
    
    Efficiently processes multiple narrative requests for
    comprehensive documentation needs.
    """
    try:
        narrative_service = get_narrative_service()
        
        # For high priority, process immediately
        if request.priority == "high":
            results = await narrative_service.batch_generate_narratives(request.narratives)
            
            return {
                "success": True,
                "total_requested": len(request.narratives),
                "total_generated": len([r for r in results if r.get("success")]),
                "results": results,
                "generated_at": datetime.utcnow().isoformat()
            }
        else:
            # Queue for background processing
            batch_id = str(datetime.utcnow().timestamp())
            
            background_tasks.add_task(
                narrative_service.batch_generate_narratives,
                request.narratives
            )
            
            return {
                "success": True,
                "batch_id": batch_id,
                "status": "processing",
                "message": "Batch narrative generation queued",
                "total_narratives": len(request.narratives)
            }
            
    except Exception as e:
        logger.error(f"Error in batch narrative generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def get_narrative_templates():
    """
    Get available narrative templates and their descriptions
    """
    templates = {
        "evidence_summary": {
            "description": "Generate narratives connecting evidence to specific standards",
            "typical_length": "150-250 words",
            "use_case": "Individual evidence documentation"
        },
        "gap_narrative": {
            "description": "Address compliance gaps with improvement plans",
            "typical_length": "200-300 words",
            "use_case": "Gap analysis responses"
        },
        "comprehensive_response": {
            "description": "Complete standard response with all evidence",
            "typical_length": "300-400 words",
            "use_case": "Full standard documentation"
        },
        "qep_narrative": {
            "description": "Quality Enhancement Plan narrative sections",
            "typical_length": "400-500 words",
            "use_case": "QEP documentation"
        },
        "institutional_overview": {
            "description": "Institution-wide compliance overview",
            "typical_length": "400-500 words",
            "use_case": "Executive summaries"
        }
    }
    
    return {
        "templates": templates,
        "total_templates": len(templates)
    }


@router.post("/preview")
async def preview_narrative(
    narrative_type: str,
    sample_data: Optional[Dict[str, Any]] = None
):
    """
    Preview narrative generation with sample data
    
    Allows users to see examples of generated narratives
    before processing actual documents.
    """
    try:
        narrative_service = get_narrative_service()
        
        # Use sample data if not provided
        if not sample_data:
            sample_data = {
                "evidence_text": "The institution conducts regular assessment of student learning outcomes...",
                "standard_id": "CR 8",
                "standard_description": "Student Achievement"
            }
        
        if narrative_type == "evidence_summary":
            result = await narrative_service.generate_evidence_narrative(
                evidence_text=sample_data.get("evidence_text", "Sample evidence"),
                standard_id=sample_data.get("standard_id", "CR 1"),
                standard_description=sample_data.get("standard_description", "Sample standard"),
                institution_context=sample_data.get("institution_context")
            )
        else:
            return {"error": "Unsupported narrative type for preview"}
        
        return {
            "preview": result.get("narrative", ""),
            "type": narrative_type,
            "quality_metrics": result.get("quality_metrics"),
            "note": "This is a preview with sample data"
        }
        
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))