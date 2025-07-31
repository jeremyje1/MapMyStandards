"""
Standards API Routes for A3E

Provides REST endpoints for managing accreditation standards across all US accreditors.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from ...core.config import settings
from ...core.accreditation_registry import AccreditorType, get_accreditor_by_id, list_all_accreditors
from ...services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def list_standards_overview():
    """Get overview of all standards in the system"""
    try:
        accreditors = list_all_accreditors()
        
        overview = {
            "total_accreditors": len(accreditors),
            "accreditors": [
                {
                    "id": acc.id,  # Use 'id' instead of 'accreditor_id'
                    "name": acc.name,
                    "type": acc.type.value,
                    "institution_types": [it.value for it in acc.institution_types],
                    "standards_count": len(acc.standards) if hasattr(acc, 'standards') else 0
                }
                for acc in accreditors
            ],
            "total_standards": sum(len(getattr(acc, 'standards', [])) for acc in accreditors),
            "api_version": "1.0.0",
            "last_updated": "2025-07-31"
        }
        
        return {
            "success": True,
            "message": "Standards overview retrieved successfully",
            "data": overview
        }
        
    except Exception as e:
        logger.error(f"Error retrieving standards overview: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve standards overview")

# Pydantic models for request/response
class StandardCreate(BaseModel):
    standard_id: str = Field(..., description="Unique identifier for the standard")
    accreditor_id: str = Field(..., description="ID of the accrediting body")
    title: str = Field(..., description="Standard title")
    description: str = Field(..., description="Detailed description")
    category: str = Field(..., description="Standard category")
    subcategory: Optional[str] = Field(None, description="Standard subcategory")
    version: str = Field(..., description="Standard version")
    effective_date: str = Field(..., description="Effective date (ISO format)")
    is_required: bool = Field(True, description="Whether the standard is required")
    evidence_requirements: List[str] = Field(..., description="List of required evidence types")

class StandardResponse(BaseModel):
    id: str
    standard_id: str
    accreditor_id: str
    title: str
    description: str
    category: str
    subcategory: Optional[str]
    version: str
    effective_date: str
    is_required: bool
    is_active: bool
    evidence_requirements: List[str]

class StandardDetail(StandardResponse):
    created_at: str
    updated_at: str
    accreditor_name: Optional[str]
    accreditor_acronym: Optional[str]

class AccreditorStandardsSummary(BaseModel):
    accreditor_id: str
    accreditor_name: str
    accreditor_acronym: str
    total_standards: int
    required_standards: int
    optional_standards: int
    categories: List[str]

# Dependency for database service
async def get_db_service():
    db_service = DatabaseService(settings.database_url)
    await db_service.initialize()
    try:
        yield db_service
    finally:
        await db_service.close()

@router.get("/standards", response_model=List[StandardResponse])
async def list_standards(
    accreditor_id: Optional[str] = Query(None, description="Filter by accreditor ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_required: Optional[bool] = Query(None, description="Filter by required status"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: DatabaseService = Depends(get_db_service)
):
    """List standards with optional filters"""
    try:
        # Validate accreditor if provided
        if accreditor_id:
            accreditor = get_accreditor_by_id(accreditor_id)
            if not accreditor:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid accreditor ID: {accreditor_id}"
                )
        
        standards = await db.list_standards(
            accreditor_id=accreditor_id,
            category=category,
            is_required=is_required,
            search=search,
            limit=limit,
            offset=offset
        )
        
        return [
            StandardResponse(
                id=str(std.id),
                standard_id=std.standard_id,
                accreditor_id=std.accreditor_id,
                title=std.title,
                description=std.description,
                category=std.category,
                subcategory=std.subcategory,
                version=std.version,
                effective_date=std.effective_date.isoformat(),
                is_required=std.is_required,
                is_active=std.is_active,
                evidence_requirements=std.evidence_requirements
            )
            for std in standards
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing standards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/standards/{standard_id}", response_model=StandardDetail)
async def get_standard(
    standard_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Get detailed information about a specific standard"""
    try:
        standard = await db.get_standard(standard_id)
        if not standard:
            raise HTTPException(status_code=404, detail="Standard not found")
        
        # Get accreditor info
        accreditor = get_accreditor_by_id(standard.accreditor_id)
        
        return StandardDetail(
            id=str(standard.id),
            standard_id=standard.standard_id,
            accreditor_id=standard.accreditor_id,
            title=standard.title,
            description=standard.description,
            category=standard.category,
            subcategory=standard.subcategory,
            version=standard.version,
            effective_date=standard.effective_date.isoformat(),
            is_required=standard.is_required,
            is_active=standard.is_active,
            evidence_requirements=standard.evidence_requirements,
            created_at=standard.created_at.isoformat(),
            updated_at=standard.updated_at.isoformat(),
            accreditor_name=accreditor.name if accreditor else None,
            accreditor_acronym=accreditor.acronym if accreditor else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting standard {standard_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/standards", response_model=StandardDetail, status_code=201)
async def create_standard(
    standard_data: StandardCreate,
    db: DatabaseService = Depends(get_db_service)
):
    """Create a new standard"""
    try:
        # Validate accreditor
        accreditor = get_accreditor_by_id(standard_data.accreditor_id)
        if not accreditor:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid accreditor ID: {standard_data.accreditor_id}"
            )
        
        # Create standard
        standard = await db.create_standard(standard_data.dict())
        
        return StandardDetail(
            id=str(standard.id),
            standard_id=standard.standard_id,
            accreditor_id=standard.accreditor_id,
            title=standard.title,
            description=standard.description,
            category=standard.category,
            subcategory=standard.subcategory,
            version=standard.version,
            effective_date=standard.effective_date.isoformat(),
            is_required=standard.is_required,
            is_active=standard.is_active,
            evidence_requirements=standard.evidence_requirements,
            created_at=standard.created_at.isoformat(),
            updated_at=standard.updated_at.isoformat(),
            accreditor_name=accreditor.name,
            accreditor_acronym=accreditor.acronym
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating standard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/accreditors", response_model=List[AccreditorStandardsSummary])
async def list_accreditors_with_standards(
    accreditor_type: Optional[str] = Query(None, description="Filter by accreditor type"),
    state: Optional[str] = Query(None, description="Filter by state coverage"),
    db: DatabaseService = Depends(get_db_service)
):
    """List all accreditors with their standards summary"""
    try:
        # Validate accreditor type if provided
        if accreditor_type:
            try:
                AccreditorType(accreditor_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid accreditor type: {accreditor_type}"
                )
        
        # Get all accreditors from registry
        all_accreditors = list_all_accreditors()
        
        # Filter by type if specified
        if accreditor_type:
            acc_type = AccreditorType(accreditor_type.lower())
            all_accreditors = [acc for acc in all_accreditors if acc.type == acc_type]
        
        # Filter by state if specified
        if state:
            all_accreditors = [
                acc for acc in all_accreditors
                if state.upper() in acc.geographic_scope or acc.geographic_scope == ["NATIONAL"]
            ]
        
        summaries = []
        for accreditor in all_accreditors:
            # Get standards count from database
            standards_stats = await db.get_accreditor_standards_stats(accreditor.id)
            
            summaries.append(AccreditorStandardsSummary(
                accreditor_id=accreditor.id,
                accreditor_name=accreditor.name,
                accreditor_acronym=accreditor.acronym,
                total_standards=standards_stats.get("total", len(accreditor.standards)),
                required_standards=standards_stats.get("required", 0),
                optional_standards=standards_stats.get("optional", 0),
                categories=standards_stats.get("categories", [])
            ))
        
        return summaries
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing accreditors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/accreditors/{accreditor_id}/standards", response_model=List[StandardResponse])
async def get_accreditor_standards(
    accreditor_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    is_required: Optional[bool] = Query(None, description="Filter by required status"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: DatabaseService = Depends(get_db_service)
):
    """Get all standards for a specific accreditor"""
    try:
        # Validate accreditor
        accreditor = get_accreditor_by_id(accreditor_id)
        if not accreditor:
            raise HTTPException(
                status_code=404,
                detail=f"Accreditor not found: {accreditor_id}"
            )
        
        standards = await db.list_standards(
            accreditor_id=accreditor_id,
            category=category,
            is_required=is_required,
            limit=limit,
            offset=offset
        )
        
        return [
            StandardResponse(
                id=str(std.id),
                standard_id=std.standard_id,
                accreditor_id=std.accreditor_id,
                title=std.title,
                description=std.description,
                category=std.category,
                subcategory=std.subcategory,
                version=std.version,
                effective_date=std.effective_date.isoformat(),
                is_required=std.is_required,
                is_active=std.is_active,
                evidence_requirements=std.evidence_requirements
            )
            for std in standards
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting standards for accreditor {accreditor_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/categories")
async def list_standard_categories(
    accreditor_id: Optional[str] = Query(None, description="Filter by accreditor"),
    db: DatabaseService = Depends(get_db_service)
):
    """List all standard categories across accreditors"""
    try:
        categories = await db.get_standard_categories(accreditor_id)
        
        return {
            "categories": categories,
            "accreditor_id": accreditor_id,
            "total_count": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/search")
async def search_standards(
    query: str = Query(..., description="Search query"),
    accreditor_id: Optional[str] = Query(None, description="Filter by accreditor"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, le=500, description="Maximum number of results"),
    db: DatabaseService = Depends(get_db_service)
):
    """Search standards using full-text search"""
    try:
        results = await db.search_standards(
            query=query,
            accreditor_id=accreditor_id,
            category=category,
            limit=limit
        )
        
        return {
            "query": query,
            "filters": {
                "accreditor_id": accreditor_id,
                "category": category
            },
            "results": [
                {
                    "id": str(std.id),
                    "standard_id": std.standard_id,
                    "accreditor_id": std.accreditor_id,
                    "title": std.title,
                    "description": std.description[:200] + "..." if len(std.description) > 200 else std.description,
                    "category": std.category,
                    "is_required": std.is_required,
                    "relevance_score": std.relevance_score if hasattr(std, "relevance_score") else None
                }
                for std in results
            ],
            "total_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching standards: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
