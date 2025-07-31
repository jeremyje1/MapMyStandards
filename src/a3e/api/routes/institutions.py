"""
Institution API Routes for A3E

Provides REST endpoints for managing institutions and their accreditation context.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from ...core.config import settings
from ...core.accreditation_registry import InstitutionType, get_accreditors_by_institution_type, get_accreditors_by_state
from ...services.database_service import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class InstitutionCreate(BaseModel):
    name: str = Field(..., description="Institution name")
    ipeds_id: Optional[str] = Field(None, description="IPEDS Unit ID")
    ope_id: Optional[str] = Field(None, description="OPE ID")
    ein: Optional[str] = Field(None, description="Employer Identification Number")
    institution_types: List[str] = Field(..., description="List of institution types")
    state: str = Field(..., description="Two-letter state code")
    city: str = Field(..., description="City name")
    zip_code: Optional[str] = Field(None, description="ZIP code")
    control: Optional[str] = Field(None, description="Institutional control")
    sector: Optional[str] = Field(None, description="Institutional sector")
    total_enrollment: Optional[int] = Field(None, description="Total enrollment")
    undergraduate_enrollment: Optional[int] = Field(None, description="Undergraduate enrollment")
    graduate_enrollment: Optional[int] = Field(None, description="Graduate enrollment")
    website: Optional[str] = Field(None, description="Institution website")
    primary_contact_email: Optional[str] = Field(None, description="Primary contact email")
    phone: Optional[str] = Field(None, description="Phone number")

class InstitutionResponse(BaseModel):
    id: str
    name: str
    ipeds_id: Optional[str]
    ope_id: Optional[str]
    institution_types: List[str]
    state: str
    city: str
    control: Optional[str]
    total_enrollment: Optional[int]
    website: Optional[str]
    is_active: bool

class InstitutionDetail(InstitutionResponse):
    ein: Optional[str]
    zip_code: Optional[str]
    sector: Optional[str]
    undergraduate_enrollment: Optional[int]
    graduate_enrollment: Optional[int]
    primary_contact_email: Optional[str]
    phone: Optional[str]
    created_at: str
    updated_at: str

# Dependency for database service
async def get_db_service():
    db_service = DatabaseService(settings.database_url)
    await db_service.initialize()
    try:
        yield db_service
    finally:
        await db_service.close()

@router.get("/institutions", response_model=List[InstitutionResponse])
async def list_institutions(
    state: Optional[str] = Query(None, description="Filter by state code"),
    institution_type: Optional[str] = Query(None, description="Filter by institution type"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: DatabaseService = Depends(get_db_service)
):
    """List institutions with optional filters"""
    try:
        # Validate institution type if provided
        institution_types = None
        if institution_type:
            try:
                InstitutionType(institution_type.lower())
                institution_types = [institution_type.lower()]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid institution type: {institution_type}"
                )
        
        institutions = await db.list_institutions(
            state=state,
            institution_types=institution_types,
            limit=limit,
            offset=offset
        )
        
        return [
            InstitutionResponse(
                id=str(inst.id),
                name=inst.name,
                ipeds_id=inst.ipeds_id,
                ope_id=inst.ope_id,
                institution_types=inst.institution_types,
                state=inst.state,
                city=inst.city,
                control=inst.control,
                total_enrollment=inst.total_enrollment,
                website=inst.website,
                is_active=inst.is_active
            )
            for inst in institutions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing institutions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/institutions/{institution_id}", response_model=InstitutionDetail)
async def get_institution(
    institution_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Get detailed information about a specific institution"""
    try:
        institution = await db.get_institution(institution_id)
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        
        return InstitutionDetail(
            id=str(institution.id),
            name=institution.name,
            ipeds_id=institution.ipeds_id,
            ope_id=institution.ope_id,
            ein=institution.ein,
            institution_types=institution.institution_types,
            state=institution.state,
            city=institution.city,
            zip_code=institution.zip_code,
            control=institution.control,
            sector=institution.sector,
            total_enrollment=institution.total_enrollment,
            undergraduate_enrollment=institution.undergraduate_enrollment,
            graduate_enrollment=institution.graduate_enrollment,
            website=institution.website,
            primary_contact_email=institution.primary_contact_email,
            phone=institution.phone,
            is_active=institution.is_active,
            created_at=institution.created_at.isoformat(),
            updated_at=institution.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting institution {institution_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/institutions", response_model=InstitutionDetail, status_code=201)
async def create_institution(
    institution_data: InstitutionCreate,
    db: DatabaseService = Depends(get_db_service)
):
    """Create a new institution"""
    try:
        # Validate institution types
        for inst_type in institution_data.institution_types:
            try:
                InstitutionType(inst_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid institution type: {inst_type}"
                )
        
        # Create institution
        institution = await db.create_institution(institution_data.dict())
        
        return InstitutionDetail(
            id=str(institution.id),
            name=institution.name,
            ipeds_id=institution.ipeds_id,
            ope_id=institution.ope_id,
            ein=institution.ein,
            institution_types=institution.institution_types,
            state=institution.state,
            city=institution.city,
            zip_code=institution.zip_code,
            control=institution.control,
            sector=institution.sector,
            total_enrollment=institution.total_enrollment,
            undergraduate_enrollment=institution.undergraduate_enrollment,
            graduate_enrollment=institution.graduate_enrollment,
            website=institution.website,
            primary_contact_email=institution.primary_contact_email,
            phone=institution.phone,
            is_active=institution.is_active,
            created_at=institution.created_at.isoformat(),
            updated_at=institution.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating institution: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/institutions/{institution_id}/applicable-accreditors")
async def get_applicable_accreditors(
    institution_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Get accreditors applicable to this institution based on type and location"""
    try:
        institution = await db.get_institution(institution_id)
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        
        # Get applicable accreditors by type and state
        applicable_accreditors = set()
        
        for inst_type_str in institution.institution_types:
            try:
                inst_type = InstitutionType(inst_type_str)
                type_accreditors = get_accreditors_by_institution_type(inst_type)
                applicable_accreditors.update(type_accreditors)
            except ValueError:
                continue
        
        state_accreditors = get_accreditors_by_state(institution.state)
        applicable_accreditors.update(state_accreditors)
        
        # Format response
        accreditor_list = []
        for accreditor in applicable_accreditors:
            accreditor_list.append({
                "id": accreditor.id,
                "name": accreditor.name,
                "acronym": accreditor.acronym,
                "type": accreditor.type.value,
                "recognition_authority": accreditor.recognition_authority,
                "geographic_scope": accreditor.geographic_scope,
                "applicable_institution_types": [t.value for t in accreditor.applicable_institution_types],
                "standards_count": len(accreditor.standards),
                "website": accreditor.website
            })
        
        return {
            "institution_id": institution_id,
            "institution_name": institution.name,
            "institution_types": institution.institution_types,
            "state": institution.state,
            "applicable_accreditors": accreditor_list,
            "total_count": len(accreditor_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting applicable accreditors for {institution_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/institutions/{institution_id}/statistics")
async def get_institution_statistics(
    institution_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Get comprehensive statistics for an institution"""
    try:
        institution = await db.get_institution(institution_id)
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        
        statistics = await db.get_institution_statistics(institution_id)
        
        return {
            "institution_id": institution_id,
            "institution_name": institution.name,
            **statistics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting statistics for {institution_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/institution-types")
async def list_institution_types():
    """List all supported institution types"""
    return {
        "institution_types": [
            {
                "value": inst_type.value,
                "name": inst_type.value.replace("_", " ").title(),
                "description": f"{inst_type.value.replace('_', ' ').title()} institution type"
            }
            for inst_type in InstitutionType
        ]
    }
