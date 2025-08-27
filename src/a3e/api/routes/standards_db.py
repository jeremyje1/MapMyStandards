"""
Database-powered standards API
Production-ready standards management with PostgreSQL persistence
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...database.services import StandardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/standards", tags=["standards"])

@router.get("")
async def list_standards(
    accreditor: Optional[str] = Query(None, description="Filter by accreditor (e.g., SACSCOC)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and description")
):
    """List all available standards with optional filtering from database"""
    try:
        # Get standards from database
        standards = await StandardService.get_standards(
            accreditor_id=accreditor,
            category=category,
            search=search
        )
        
        # Convert SQLAlchemy objects to dicts
        standards_data = []
        for std in standards:
            std_dict = {
                "id": std.standard_id,
                "accreditor": std.accreditor_id.upper() if std.accreditor_id else "",
                "code": std.code,
                "title": std.title,
                "description": std.description,
                "category": std.category,
                "parentId": std.parent_id,
                "evidence_requirements": std.evidence_requirements or [],
                "is_required": std.is_required,
                "weight": std.weight or 100,
                "compliance_level": std.compliance_level or "must",
                "keywords": std.keywords or []
            }
            standards_data.append(std_dict)
        
        return {
            "success": True,
            "message": "Standards retrieved successfully",
            "data": {
                "standards": standards_data,
                "total_count": len(standards_data),
                "filters_applied": {
                    "accreditor": accreditor,
                    "category": category,
                    "search": search
                },
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error retrieving standards: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve standards")

@router.get("/accreditors")
async def list_accreditors():
    """List all available accreditors from database"""
    try:
        # Get accreditors from database
        accreditors = await StandardService.get_accreditors()
        
        # Convert to response format
        accreditors_data = []
        for acc in accreditors:
            # Count standards for this accreditor
            standards = await StandardService.get_standards(accreditor_id=acc.accreditor_id)
            
            acc_dict = {
                "id": acc.accreditor_id,
                "name": acc.name,
                "acronym": acc.acronym,
                "description": acc.description,
                "website_url": acc.website_url,
                "standards_version": acc.standards_version,
                "standards_count": len(standards),
                "categories": list(set(std.category for std in standards))
            }
            accreditors_data.append(acc_dict)
        
        return {
            "success": True,
            "data": {
                "accreditors": accreditors_data,
                "total_count": len(accreditors_data)
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing accreditors: {e}")
        raise HTTPException(status_code=500, detail="Failed to list accreditors")

@router.get("/categories")
async def list_categories(
    accreditor: Optional[str] = Query(None, description="Filter by accreditor")
):
    """List all standard categories from database"""
    try:
        # Get standards for category extraction
        standards = await StandardService.get_standards(accreditor_id=accreditor)
        
        # Extract unique categories
        categories = list(set(std.category for std in standards if std.category))
        categories.sort()
        
        return {
            "success": True,
            "data": {
                "categories": categories,
                "total_count": len(categories),
                "accreditor": accreditor
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="Failed to list categories")

@router.get("/{standard_id}")
async def get_standard_detail(standard_id: str):
    """Get detailed information about a specific standard from database"""
    try:
        # Get all standards and find the specific one
        # TODO: Optimize this with a direct database query
        all_standards = await StandardService.get_standards()
        
        standard = None
        for std in all_standards:
            if std.standard_id == standard_id:
                standard = std
                break
        
        if not standard:
            raise HTTPException(status_code=404, detail=f"Standard not found: {standard_id}")
        
        # Convert to detailed response
        standard_detail = {
            "id": standard.standard_id,
            "accreditor": standard.accreditor_id.upper() if standard.accreditor_id else "",
            "code": standard.code,
            "title": standard.title,
            "description": standard.description,
            "category": standard.category,
            "parentId": standard.parent_id,
            "evidence_requirements": standard.evidence_requirements or [],
            "is_required": standard.is_required,
            "weight": standard.weight or 100,
            "compliance_level": standard.compliance_level or "must",
            "keywords": standard.keywords or [],
            "created_at": standard.created_at.isoformat() if standard.created_at else None,
            "updated_at": standard.updated_at.isoformat() if standard.updated_at else None,
            "version": "2018",  # From accreditor data
            "status": "active"
        }
        
        return {
            "success": True,
            "data": standard_detail
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting standard detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get standard detail")

@router.get("/tree/{accreditor}")
async def get_standards_tree(accreditor: str):
    """Get hierarchical tree of standards for an accreditor from database"""
    try:
        # Get standards for the accreditor
        standards = await StandardService.get_standards(accreditor_id=accreditor.lower())
        
        if not standards:
            raise HTTPException(status_code=404, detail=f"No standards found for accreditor: {accreditor}")
        
        # Convert to dict format
        standards_dict = {}
        for std in standards:
            std_dict = {
                "id": std.standard_id,
                "accreditor": std.accreditor_id.upper() if std.accreditor_id else "",
                "code": std.code,
                "title": std.title,
                "description": std.description,
                "category": std.category,
                "parentId": std.parent_id,
                "evidence_requirements": std.evidence_requirements or [],
                "is_required": std.is_required,
                "weight": std.weight or 100,
            }
            standards_dict[std.standard_id] = std_dict
        
        # Build hierarchical structure
        root_standards = [std for std in standards_dict.values() if std.get("parentId") is None]
        
        def add_children(standard):
            children = [s for s in standards_dict.values() if s.get("parentId") == standard["id"]]
            if children:
                standard["children"] = children
                for child in children:
                    add_children(child)
            return standard
        
        # Build tree
        tree = [add_children(std.copy()) for std in root_standards]
        
        return {
            "success": True,
            "data": {
                "accreditor": accreditor.upper(),
                "standards_tree": tree,
                "total_standards": len(standards)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building standards tree: {e}")
        raise HTTPException(status_code=500, detail="Failed to build standards tree")