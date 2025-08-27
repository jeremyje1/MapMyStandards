"""
Mock standards API that returns SACSCOC standards data
Provides immediate working standards list to unblock trial
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/standards", tags=["standards"])

# Mock SACSCOC Standards Data
SACSCOC_STANDARDS = [
    {
        "id": "sacscoc_1_1",
        "accreditor": "SACSCOC",
        "code": "1.1",
        "title": "Mission",
        "description": "The institution has a clearly defined mission statement that articulates the institution's purpose, student population served, and commitment to student learning and student achievement.",
        "category": "Institutional Mission and Effectiveness",
        "parentId": None,
        "evidence_requirements": ["Mission Statement", "Board Approval Documentation", "Strategic Plan"],
        "is_required": True,
        "weight": 100
    },
    {
        "id": "sacscoc_2_1",
        "accreditor": "SACSCOC", 
        "code": "2.1",
        "title": "Degree Standards",
        "description": "The institution offers one or more degree programs based on at least 60 semester credit hours or the equivalent at the baccalaureate level; at least 30 semester credit hours or the equivalent at the master's level.",
        "category": "Academic and Student Affairs",
        "parentId": None,
        "evidence_requirements": ["Degree Program Documentation", "Credit Hour Requirements", "Catalog Pages"],
        "is_required": True,
        "weight": 100
    },
    {
        "id": "sacscoc_8_1",
        "accreditor": "SACSCOC",
        "code": "8.1", 
        "title": "Faculty",
        "description": "The institution employs a sufficient number of qualified faculty to support the mission of the institution and the goals of the degree programs.",
        "category": "Faculty",
        "parentId": None,
        "evidence_requirements": ["Faculty CVs", "Qualification Matrix", "Teaching Load Documentation"],
        "is_required": True,
        "weight": 100
    },
    {
        "id": "sacscoc_8_2_a",
        "accreditor": "SACSCOC",
        "code": "8.2.a",
        "title": "Faculty Evaluation", 
        "description": "The institution regularly evaluates the effectiveness of each faculty member in accord with published criteria, regardless of contractual or employment terms.",
        "category": "Faculty",
        "parentId": "sacscoc_8_1",
        "evidence_requirements": ["Faculty Evaluation Process", "Evaluation Criteria", "Performance Reviews"],
        "is_required": True,
        "weight": 90
    },
    {
        "id": "sacscoc_9_1",
        "accreditor": "SACSCOC",
        "code": "9.1",
        "title": "Academic Support Services",
        "description": "The institution provides appropriate academic support services.",
        "category": "Academic and Student Affairs", 
        "parentId": None,
        "evidence_requirements": ["Academic Support Services Documentation", "Tutoring Programs", "Advising Services"],
        "is_required": True,
        "weight": 85
    },
    {
        "id": "sacscoc_10_1", 
        "accreditor": "SACSCOC",
        "code": "10.1",
        "title": "Financial Resources",
        "description": "The institution's recent financial history demonstrates financial stability with the capacity to support its programs and services.",
        "category": "Financial Resources",
        "parentId": None,
        "evidence_requirements": ["Audited Financial Statements", "Budget Documentation", "Revenue Analysis"],
        "is_required": True,
        "weight": 95
    },
    {
        "id": "sacscoc_11_1",
        "accreditor": "SACSCOC", 
        "code": "11.1",
        "title": "Physical Resources",
        "description": "The institution's physical resources support student learning and the effective delivery of programs and services.",
        "category": "Physical Resources",
        "parentId": None,
        "evidence_requirements": ["Facilities Master Plan", "Campus Maps", "Safety Documentation"],
        "is_required": True,
        "weight": 80
    },
    {
        "id": "sacscoc_12_1",
        "accreditor": "SACSCOC",
        "code": "12.1", 
        "title": "Resource Development",
        "description": "The institution has a sound financial base and demonstrated financial stability to support the mission of the institution and the scope of its programs and services.",
        "category": "Financial Resources",
        "parentId": None,
        "evidence_requirements": ["Fundraising Documentation", "Grant Records", "Endowment Reports"],
        "is_required": True,
        "weight": 75
    }
]

@router.get("")
async def list_standards(
    accreditor: Optional[str] = Query(None, description="Filter by accreditor (e.g., SACSCOC)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and description")
):
    """List all available standards with optional filtering"""
    try:
        standards = SACSCOC_STANDARDS.copy()
        
        # Apply filters
        if accreditor:
            standards = [s for s in standards if s["accreditor"].upper() == accreditor.upper()]
        
        if category:
            standards = [s for s in standards if category.lower() in s["category"].lower()]
        
        if search:
            search_lower = search.lower()
            standards = [
                s for s in standards 
                if (search_lower in s["title"].lower() or 
                    search_lower in s["description"].lower() or
                    search_lower in s["code"].lower())
            ]
        
        return {
            "success": True,
            "message": "Standards retrieved successfully",
            "data": {
                "standards": standards,
                "total_count": len(standards),
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
    """List all available accreditors"""
    try:
        # Group standards by accreditor
        accreditors = {}
        for standard in SACSCOC_STANDARDS:
            acc = standard["accreditor"]
            if acc not in accreditors:
                accreditors[acc] = {
                    "id": acc.lower(),
                    "name": "Southern Association of Colleges and Schools Commission on Colleges",
                    "acronym": acc,
                    "standards_count": 0,
                    "categories": set()
                }
            accreditors[acc]["standards_count"] += 1
            accreditors[acc]["categories"].add(standard["category"])
        
        # Convert sets to lists for JSON serialization
        for acc_data in accreditors.values():
            acc_data["categories"] = list(acc_data["categories"])
        
        return {
            "success": True,
            "data": {
                "accreditors": list(accreditors.values()),
                "total_count": len(accreditors)
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing accreditors: {e}")
        raise HTTPException(status_code=500, detail="Failed to list accreditors")

@router.get("/categories")
async def list_categories(
    accreditor: Optional[str] = Query(None, description="Filter by accreditor")
):
    """List all standard categories"""
    try:
        standards = SACSCOC_STANDARDS.copy()
        
        # Filter by accreditor if specified
        if accreditor:
            standards = [s for s in standards if s["accreditor"].upper() == accreditor.upper()]
        
        # Extract unique categories
        categories = list(set(s["category"] for s in standards))
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
    """Get detailed information about a specific standard"""
    try:
        # Find standard by ID
        standard = next((s for s in SACSCOC_STANDARDS if s["id"] == standard_id), None)
        
        if not standard:
            raise HTTPException(status_code=404, detail=f"Standard not found: {standard_id}")
        
        # Add additional details
        standard_detail = standard.copy()
        standard_detail.update({
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": datetime.utcnow().isoformat(),
            "version": "2024",
            "status": "active"
        })
        
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
    """Get hierarchical tree of standards for an accreditor"""
    try:
        # Filter standards by accreditor
        standards = [s for s in SACSCOC_STANDARDS if s["accreditor"].upper() == accreditor.upper()]
        
        if not standards:
            raise HTTPException(status_code=404, detail=f"No standards found for accreditor: {accreditor}")
        
        # Build hierarchical structure
        root_standards = [s for s in standards if s.get("parentId") is None]
        
        def add_children(standard):
            children = [s for s in standards if s.get("parentId") == standard["id"]]
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