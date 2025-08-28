"""
Evidence Mapping API Routes

Provides endpoints for retrieving and managing evidence-to-standard mappings.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json

from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence"])

# In-memory storage for mappings (should use database in production)
evidence_mappings = {}
standards_coverage = {}

@router.get("/mappings")
async def get_evidence_mappings(
    accreditor: Optional[str] = Query("SACSCOC", description="Accreditor to filter by"),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get all evidence mappings for the current user"""
    try:
        user_id = current_user.get("user_id") if current_user else "demo"
        
        # Get user's mappings or generate sample data
        user_mappings = evidence_mappings.get(user_id, {})
        
        if not user_mappings:
            # Generate sample mappings for demonstration
            user_mappings = generate_sample_mappings(accreditor)
            evidence_mappings[user_id] = user_mappings
        
        return {
            "success": True,
            "data": {
                "accreditor": accreditor,
                "total_documents": len(user_mappings.get("documents", [])),
                "total_standards": len(user_mappings.get("standards", [])),
                "mappings": user_mappings.get("mappings", []),
                "coverage_percentage": calculate_coverage(user_mappings),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting evidence mappings: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mappings")

@router.get("/mappings/by-standard/{standard_id}")
async def get_mappings_by_standard(
    standard_id: str,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get all documents mapped to a specific standard"""
    try:
        user_id = current_user.get("user_id") if current_user else "demo"
        user_mappings = evidence_mappings.get(user_id, {})
        
        # Filter mappings for this standard
        standard_mappings = [
            m for m in user_mappings.get("mappings", [])
            if m.get("standard_id") == standard_id
        ]
        
        # Get document details
        documents = []
        for mapping in standard_mappings:
            doc = next(
                (d for d in user_mappings.get("documents", []) 
                 if d["id"] == mapping["document_id"]),
                None
            )
            if doc:
                documents.append({
                    **doc,
                    "relevance_score": mapping.get("relevance_score", 0),
                    "evidence_summary": mapping.get("evidence_summary", ""),
                    "mapping_confidence": mapping.get("mapping_confidence", "medium")
                })
        
        return {
            "success": True,
            "data": {
                "standard_id": standard_id,
                "documents": documents,
                "total_evidence": len(documents),
                "average_relevance": sum(d.get("relevance_score", 0) for d in documents) / max(len(documents), 1)
            }
        }
    except Exception as e:
        logger.error(f"Error getting mappings for standard {standard_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve standard mappings")

@router.get("/mappings/by-document/{document_id}")
async def get_mappings_by_document(
    document_id: str,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get all standards mapped to a specific document"""
    try:
        user_id = current_user.get("user_id") if current_user else "demo"
        user_mappings = evidence_mappings.get(user_id, {})
        
        # Filter mappings for this document
        doc_mappings = [
            m for m in user_mappings.get("mappings", [])
            if m.get("document_id") == document_id
        ]
        
        # Get standard details
        standards = []
        for mapping in doc_mappings:
            std = next(
                (s for s in user_mappings.get("standards", [])
                 if s["id"] == mapping["standard_id"]),
                None
            )
            if std:
                standards.append({
                    **std,
                    "relevance_score": mapping.get("relevance_score", 0),
                    "evidence_summary": mapping.get("evidence_summary", ""),
                    "mapping_confidence": mapping.get("mapping_confidence", "medium")
                })
        
        return {
            "success": True,
            "data": {
                "document_id": document_id,
                "standards": standards,
                "total_standards": len(standards),
                "compliance_score": calculate_document_compliance(standards)
            }
        }
    except Exception as e:
        logger.error(f"Error getting mappings for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document mappings")

@router.get("/coverage/heatmap")
async def get_coverage_heatmap(
    accreditor: Optional[str] = Query("SACSCOC"),
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Get coverage heatmap data for visualization"""
    try:
        # Generate heatmap data
        categories = [
            "Mission & Governance",
            "Academic Programs", 
            "Faculty Resources",
            "Student Achievement",
            "Financial Resources",
            "Physical Resources",
            "Institutional Effectiveness",
            "Student Support Services"
        ]
        
        heatmap_data = []
        for cat in categories:
            standards = get_standards_for_category(cat, accreditor)
            for std in standards:
                coverage = calculate_standard_coverage(std["id"])
                heatmap_data.append({
                    "category": cat,
                    "standard_id": std["id"],
                    "standard_title": std["title"],
                    "coverage_score": coverage["score"],
                    "evidence_count": coverage["evidence_count"],
                    "status": get_coverage_status(coverage["score"])
                })
        
        return {
            "success": True,
            "data": {
                "accreditor": accreditor,
                "categories": categories,
                "heatmap": heatmap_data,
                "summary": {
                    "fully_covered": len([h for h in heatmap_data if h["status"] == "complete"]),
                    "partially_covered": len([h for h in heatmap_data if h["status"] == "partial"]),
                    "gaps": len([h for h in heatmap_data if h["status"] == "gap"]),
                    "not_applicable": len([h for h in heatmap_data if h["status"] == "n/a"])
                }
            }
        }
    except Exception as e:
        logger.error(f"Error generating coverage heatmap: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate heatmap")

@router.post("/mappings")
async def create_mapping(
    mapping_data: Dict[str, Any],
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Create a new evidence-to-standard mapping"""
    try:
        user_id = current_user.get("user_id") if current_user else "demo"
        
        if user_id not in evidence_mappings:
            evidence_mappings[user_id] = {
                "documents": [],
                "standards": [],
                "mappings": []
            }
        
        # Add the new mapping
        new_mapping = {
            "id": f"map_{len(evidence_mappings[user_id]['mappings'])}",
            "document_id": mapping_data.get("document_id"),
            "standard_id": mapping_data.get("standard_id"),
            "relevance_score": mapping_data.get("relevance_score", 75),
            "evidence_summary": mapping_data.get("evidence_summary", ""),
            "mapping_confidence": mapping_data.get("mapping_confidence", "medium"),
            "created_at": datetime.utcnow().isoformat(),
            "created_by": user_id
        }
        
        evidence_mappings[user_id]["mappings"].append(new_mapping)
        
        return {
            "success": True,
            "data": new_mapping,
            "message": "Mapping created successfully"
        }
    except Exception as e:
        logger.error(f"Error creating mapping: {e}")
        raise HTTPException(status_code=500, detail="Failed to create mapping")

# Helper functions

def generate_sample_mappings(accreditor: str) -> Dict[str, Any]:
    """Generate sample mapping data for demonstration"""
    
    documents = [
        {"id": "doc_1", "name": "Strategic Plan 2024-2029.pdf", "upload_date": "2024-01-15", "type": "strategic_plan"},
        {"id": "doc_2", "name": "Student Learning Outcomes Report.docx", "upload_date": "2024-01-20", "type": "assessment"},
        {"id": "doc_3", "name": "Faculty Qualifications Matrix.xlsx", "upload_date": "2024-01-22", "type": "faculty"},
        {"id": "doc_4", "name": "Financial Audit 2023.pdf", "upload_date": "2024-01-25", "type": "financial"},
        {"id": "doc_5", "name": "QEP Impact Report.pdf", "upload_date": "2024-01-28", "type": "qep"}
    ]
    
    standards = [
        {"id": "8.1", "title": "Student Achievement", "category": "Student Success"},
        {"id": "8.2.a", "title": "Student Outcomes: Educational Programs", "category": "Student Success"},
        {"id": "10.1", "title": "Academic Governance", "category": "Educational Policies"},
        {"id": "10.3", "title": "Archived Information", "category": "Educational Policies"},
        {"id": "13.7", "title": "Physical Resources", "category": "Resources"},
        {"id": "13.8", "title": "Financial Resources", "category": "Resources"}
    ]
    
    mappings = [
        {"document_id": "doc_1", "standard_id": "10.1", "relevance_score": 95, 
         "evidence_summary": "Strategic plan clearly outlines governance structure", "mapping_confidence": "high"},
        {"document_id": "doc_1", "standard_id": "8.1", "relevance_score": 85,
         "evidence_summary": "Contains student achievement goals and metrics", "mapping_confidence": "high"},
        {"document_id": "doc_2", "standard_id": "8.2.a", "relevance_score": 98,
         "evidence_summary": "Comprehensive SLO assessment data for all programs", "mapping_confidence": "high"},
        {"document_id": "doc_3", "standard_id": "10.3", "relevance_score": 75,
         "evidence_summary": "Faculty credentials documented and archived", "mapping_confidence": "medium"},
        {"document_id": "doc_4", "standard_id": "13.8", "relevance_score": 100,
         "evidence_summary": "Complete financial audit with unqualified opinion", "mapping_confidence": "high"},
        {"document_id": "doc_5", "standard_id": "8.1", "relevance_score": 90,
         "evidence_summary": "QEP shows measurable impact on student success", "mapping_confidence": "high"}
    ]
    
    return {
        "documents": documents,
        "standards": standards,
        "mappings": mappings
    }

def calculate_coverage(mappings_data: Dict[str, Any]) -> float:
    """Calculate overall coverage percentage"""
    if not mappings_data.get("standards"):
        return 0.0
    
    covered_standards = set(m["standard_id"] for m in mappings_data.get("mappings", []))
    total_standards = len(mappings_data.get("standards", []))
    
    return (len(covered_standards) / max(total_standards, 1)) * 100

def calculate_document_compliance(standards: List[Dict[str, Any]]) -> float:
    """Calculate compliance score for a document based on its mapped standards"""
    if not standards:
        return 0.0
    
    total_score = sum(s.get("relevance_score", 0) for s in standards)
    return min(total_score / len(standards), 100)

def get_standards_for_category(category: str, accreditor: str) -> List[Dict[str, Any]]:
    """Get standards for a specific category"""
    # Sample standards by category
    category_standards = {
        "Mission & Governance": [
            {"id": "1.1", "title": "Mission Statement"},
            {"id": "2.1", "title": "Governing Board"},
            {"id": "2.2", "title": "CEO Evaluation"}
        ],
        "Academic Programs": [
            {"id": "8.1", "title": "Student Achievement"},
            {"id": "8.2.a", "title": "Educational Programs"},
            {"id": "9.1", "title": "Program Content"}
        ],
        "Faculty Resources": [
            {"id": "6.1", "title": "Faculty Qualifications"},
            {"id": "6.2.a", "title": "Faculty Competence"},
            {"id": "6.3", "title": "Faculty Development"}
        ],
        "Student Achievement": [
            {"id": "8.1", "title": "Student Achievement"},
            {"id": "8.2.b", "title": "General Education"},
            {"id": "8.2.c", "title": "Academic Services"}
        ]
    }
    
    return category_standards.get(category, [])

def calculate_standard_coverage(standard_id: str) -> Dict[str, Any]:
    """Calculate coverage for a specific standard"""
    # Mock calculation - in production would check actual evidence
    import random
    
    evidence_count = random.randint(0, 5)
    if evidence_count == 0:
        score = 0
    elif evidence_count == 1:
        score = random.randint(40, 60)
    elif evidence_count <= 3:
        score = random.randint(60, 85)
    else:
        score = random.randint(85, 100)
    
    return {
        "score": score,
        "evidence_count": evidence_count
    }

def get_coverage_status(score: float) -> str:
    """Get status label based on coverage score"""
    if score >= 90:
        return "complete"
    elif score >= 60:
        return "partial"
    elif score > 0:
        return "insufficient"
    else:
        return "gap"