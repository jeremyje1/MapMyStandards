"""
API routes for integration management and configuration.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional
import logging

from ...services.integration_service import integration_manager
from ...services.mock_canvas_service import mock_integration_manager
from ...core.standards_config import standards_config
from ...core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])
# settings imported from config module

def get_integration_manager():
    """Get integration manager - use mock if no real Canvas credentials."""
    canvas_configured = bool(
        getattr(settings, 'CANVAS_ACCESS_TOKEN', None) or
        (getattr(settings, 'CANVAS_CLIENT_ID', None) and 
         getattr(settings, 'CANVAS_CLIENT_SECRET', None))
    )
    
    if canvas_configured and getattr(settings, 'CANVAS_ACCESS_TOKEN', None) != 'your_personal_access_token_here':
        return integration_manager
    else:
        logger.info("Using mock Canvas data for development")
        return mock_integration_manager

@router.get("/status")
async def get_integration_status() -> Dict[str, Any]:
    """Get status of all configured integrations."""
    try:
        manager = get_integration_manager()
        connection_results = await manager.test_all_connections()
        
        # Determine if we're using mock data
        using_mock = manager == mock_integration_manager
        
        status = {
            "timestamp": "2025-01-31T00:00:00Z",
            "mode": "mock" if using_mock else "live",
            "integrations": {
                "canvas": {
                    "configured": True if using_mock else bool(settings.CANVAS_CLIENT_ID and settings.CANVAS_CLIENT_SECRET),
                    "connected": connection_results.get('canvas', False),
                    "api_base": getattr(settings, 'CANVAS_API_BASE', 'https://canvas.instructure.com/api/v1'),
                    "mock_data": using_mock
                },
                "banner": {
                    "configured": bool(
                        getattr(settings, 'BANNER_ETHOS_TOKEN', None) or 
                        getattr(settings, 'BANNER_DB_HOST', None)
                    ),
                    "connected": connection_results.get('banner', False),
                    "method": "ethos" if getattr(settings, 'BANNER_ETHOS_TOKEN', None) else "database",
                    "mock_data": False
                },
                "sharepoint": {
                    "configured": bool(
                        getattr(settings, 'MS_CLIENT_ID', None) and 
                        getattr(settings, 'MS_CLIENT_SECRET', None) and 
                        getattr(settings, 'MS_TENANT_ID', None)
                    ),
                    "connected": connection_results.get('sharepoint', False),
                    "tenant_id": getattr(settings, 'MS_TENANT_ID', None),
                    "mock_data": False
                }
            }
        }
        
        if using_mock:
            status["notice"] = "Using mock Canvas data for development. Configure real Canvas credentials to use live data."
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting integration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get integration status")

@router.post("/sync")
async def sync_integration_data(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """Trigger data synchronization from all integrated systems."""
    try:
        manager = get_integration_manager()
        
        # Add sync task to background
        background_tasks.add_task(perform_sync, manager)
        
        return {
            "message": "Data synchronization started",
            "status": "running",
            "mode": "mock" if manager == mock_integration_manager else "live"
        }
        
    except Exception as e:
        logger.error(f"Error starting sync: {e}")
        raise HTTPException(status_code=500, detail="Failed to start synchronization")

async def perform_sync(manager):
    """Background task to perform data synchronization."""
    try:
        logger.info("Starting integration data sync...")
        results = await manager.sync_all_data()
        logger.info(f"Sync completed with results: {results}")
        
        # Here you would typically save the synced data to your database
        # For now, we'll just log the results
        
    except Exception as e:
        logger.error(f"Sync task failed: {e}")

@router.get("/canvas/test")
async def test_canvas_connection() -> Dict[str, Any]:
    """Test Canvas connection and get user info."""
    try:
        manager = get_integration_manager()
        
        if manager == mock_integration_manager:
            # Return mock user data
            await manager.canvas.authenticate()
            return {
                "status": "connected",
                "mode": "mock",
                "user": manager.canvas.current_user,
                "api_base": manager.canvas.api_base,
                "notice": "Using mock Canvas data for development"
            }
        
        # Real Canvas integration
        async with manager.canvas:
            if not await manager.canvas.authenticate():
                raise HTTPException(status_code=401, detail="Canvas authentication failed")
            
            # Get user info
            headers = {'Authorization': f'Bearer {manager.canvas.access_token}'}
            async with manager.canvas.session.get(
                f"{manager.canvas.api_base}/users/self", 
                headers=headers
            ) as response:
                if response.status == 200:
                    user_info = await response.json()
                    return {
                        "status": "connected",
                        "mode": "live",
                        "user": {
                            "id": user_info.get("id"),
                            "name": user_info.get("name"),
                            "email": user_info.get("email")
                        },
                        "api_base": manager.canvas.api_base
                    }
                else:
                    raise HTTPException(status_code=response.status, detail="Failed to get user info")
            
    except Exception as e:
        logger.error(f"Canvas test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Canvas test failed: {str(e)}")

@router.get("/canvas/courses")
async def get_canvas_courses() -> List[Dict[str, Any]]:
    """Get courses from Canvas LMS."""
    try:
        manager = get_integration_manager()
        
        if manager == mock_integration_manager:
            # Return mock courses
            await manager.canvas.authenticate()
            courses = await manager.canvas.get_courses()
            return courses
        
        # Real Canvas integration
        async with manager.canvas:
            if not await manager.canvas.authenticate():
                raise HTTPException(status_code=401, detail="Canvas authentication failed")
            
            courses = await manager.canvas.get_courses()
            return courses
            
    except Exception as e:
        logger.error(f"Error getting Canvas courses: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Canvas courses")

@router.get("/canvas/courses/{course_id}/outcomes")
async def get_canvas_course_outcomes(course_id: int) -> List[Dict[str, Any]]:
    """Get learning outcomes for a specific Canvas course."""
    try:
        manager = get_integration_manager()
        
        if manager == mock_integration_manager:
            # Return mock outcomes
            await manager.canvas.authenticate()
            outcomes = await manager.canvas.get_course_outcomes(course_id)
            return outcomes
        
        # Real Canvas integration
        async with manager.canvas:
            if not await manager.canvas.authenticate():
                raise HTTPException(status_code=401, detail="Canvas authentication failed")
            
            outcomes = await manager.canvas.get_course_outcomes(course_id)
            return outcomes
            
    except Exception as e:
        logger.error(f"Error getting Canvas outcomes: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Canvas outcomes")

@router.get("/banner/students")
async def get_banner_students(term_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get student data from Banner SIS."""
    try:
        async with integration_manager.banner:
            if not await integration_manager.banner.authenticate():
                raise HTTPException(status_code=401, detail="Banner authentication failed")
            
            students = await integration_manager.banner.get_students(term_id)
            return students
            
    except Exception as e:
        logger.error(f"Error getting Banner students: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Banner students")

@router.get("/sharepoint/sites")
async def get_sharepoint_sites() -> List[Dict[str, Any]]:
    """Get SharePoint sites."""
    try:
        async with integration_manager.sharepoint:
            if not await integration_manager.sharepoint.authenticate():
                raise HTTPException(status_code=401, detail="SharePoint authentication failed")
            
            sites = await integration_manager.sharepoint.get_sites()
            return sites
            
    except Exception as e:
        logger.error(f"Error getting SharePoint sites: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SharePoint sites")

@router.get("/sharepoint/sites/{site_id}/documents")
async def get_sharepoint_documents(site_id: str) -> List[Dict[str, Any]]:
    """Get documents from a SharePoint site."""
    try:
        async with integration_manager.sharepoint:
            if not await integration_manager.sharepoint.authenticate():
                raise HTTPException(status_code=401, detail="SharePoint authentication failed")
            
            documents = await integration_manager.sharepoint.get_site_documents(site_id)
            return documents
            
    except Exception as e:
        logger.error(f"Error getting SharePoint documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get SharePoint documents")

@router.post("/canvas/oauth/callback")
async def canvas_oauth_callback(code: str) -> Dict[str, str]:
    """Handle Canvas OAuth callback."""
    try:
        async with integration_manager.canvas:
            token = await integration_manager.canvas.exchange_code_for_token(code)
            
            if token:
                return {"message": "Canvas authentication successful", "status": "connected"}
            else:
                raise HTTPException(status_code=400, detail="Failed to exchange Canvas authorization code")
                
    except Exception as e:
        logger.error(f"Canvas OAuth callback error: {e}")
        raise HTTPException(status_code=500, detail="OAuth callback failed")

# Configuration routes
config_router = APIRouter(prefix="/api/v1/config", tags=["configuration"])

@config_router.get("/accreditors")
async def get_accreditors() -> List[Dict[str, Any]]:
    """Get all configured accreditors."""
    try:
        accreditors = standards_config.get_accreditors()
        return [
            {
                "id": acc.id,
                "name": acc.name,
                "full_name": acc.full_name,
                "type": acc.type,
                "region": acc.region,
                "geographic_scope": acc.geographic_scope,
                "standards_uri": acc.standards_uri,
                "standards_version": acc.standards_version,
                "mapping_rules": acc.mapping_rules,
                "recognition_authority": acc.recognition_authority,
                "website": acc.website,
                "applicable_institution_types": acc.applicable_institution_types,
                "applicable_programs": acc.applicable_programs,
                "standards_count": len(acc.standards)
            }
            for acc in accreditors
        ]
        
    except Exception as e:
        logger.error(f"Error getting accreditors: {e}")
        raise HTTPException(status_code=500, detail="Failed to get accreditors")

@config_router.get("/accreditors/{accreditor_id}")
async def get_accreditor(accreditor_id: str) -> Dict[str, Any]:
    """Get specific accreditor details."""
    try:
        accreditor = standards_config.get_accreditor_by_id(accreditor_id)
        
        if not accreditor:
            raise HTTPException(status_code=404, detail="Accreditor not found")
        
        return {
            "id": accreditor.id,
            "name": accreditor.name,
            "full_name": accreditor.full_name,
            "type": accreditor.type,
            "region": accreditor.region,
            "geographic_scope": accreditor.geographic_scope,
            "standards_uri": accreditor.standards_uri,
            "standards_version": accreditor.standards_version,
            "mapping_rules": accreditor.mapping_rules,
            "recognition_authority": accreditor.recognition_authority,
            "website": accreditor.website,
            "applicable_institution_types": accreditor.applicable_institution_types,
            "applicable_programs": accreditor.applicable_programs,
            "standards": [
                {
                    "id": std.id,
                    "title": std.title,
                    "category": std.category,
                    "subcategory": std.subcategory,
                    "description": std.description,
                    "evidence_requirements": std.evidence_requirements
                }
                for std in accreditor.standards
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting accreditor: {e}")
        raise HTTPException(status_code=500, detail="Failed to get accreditor")

@config_router.get("/accreditors/{accreditor_id}/standards")
async def get_accreditor_standards(accreditor_id: str) -> List[Dict[str, Any]]:
    """Get standards for a specific accreditor."""
    try:
        standards = standards_config.get_standards_for_accreditor(accreditor_id)
        
        return [
            {
                "id": std.id,
                "title": std.title,
                "category": std.category,
                "subcategory": std.subcategory,
                "description": std.description,
                "evidence_requirements": std.evidence_requirements
            }
            for std in standards
        ]
        
    except Exception as e:
        logger.error(f"Error getting standards: {e}")
        raise HTTPException(status_code=500, detail="Failed to get standards")

@config_router.get("/institution-types")
async def get_institution_types() -> List[Dict[str, Any]]:
    """Get all configured institution types."""
    try:
        institution_types = standards_config.get_institution_types()
        
        return [
            {
                "id": inst.id,
                "name": inst.name,
                "description": inst.description,
                "typical_accreditors": inst.typical_accreditors
            }
            for inst in institution_types
        ]
        
    except Exception as e:
        logger.error(f"Error getting institution types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get institution types")

@config_router.get("/evidence-tags")
async def get_evidence_tags() -> List[Dict[str, Any]]:
    """Get all configured evidence tags."""
    try:
        evidence_tags = standards_config.get_evidence_tags()
        
        return [
            {
                "id": tag.id,
                "category": tag.category,
                "description": tag.description,
                "keywords": tag.keywords
            }
            for tag in evidence_tags
        ]
        
    except Exception as e:
        logger.error(f"Error getting evidence tags: {e}")
        raise HTTPException(status_code=500, detail="Failed to get evidence tags")

@config_router.get("/mapping-rules")
async def get_mapping_rules() -> Dict[str, Dict[str, Any]]:
    """Get all configured mapping rules."""
    try:
        mapping_rules = standards_config.get_mapping_rules()
        
        return {
            rule_name: {
                "description": rule.description,
                "confidence_threshold": rule.confidence_threshold,
                "requires_manual_review": rule.requires_manual_review,
                "evidence_multiplier": rule.evidence_multiplier
            }
            for rule_name, rule in mapping_rules.items()
        }
        
    except Exception as e:
        logger.error(f"Error getting mapping rules: {e}")
        raise HTTPException(status_code=500, detail="Failed to get mapping rules")

@config_router.get("/search/standards")
async def search_standards(keyword: str) -> List[Dict[str, Any]]:
    """Search standards by keyword."""
    try:
        results = standards_config.search_standards_by_keyword(keyword)
        
        return [
            {
                "accreditor": {
                    "id": accreditor.id,
                    "name": accreditor.name,
                    "type": accreditor.type
                },
                "standard": {
                    "id": standard.id,
                    "title": standard.title,
                    "category": standard.category,
                    "subcategory": standard.subcategory,
                    "description": standard.description,
                    "evidence_requirements": standard.evidence_requirements
                }
            }
            for accreditor, standard in results
        ]
        
    except Exception as e:
        logger.error(f"Error searching standards: {e}")
        raise HTTPException(status_code=500, detail="Failed to search standards")

@config_router.post("/evidence/classify")
async def classify_evidence(text: str) -> List[Dict[str, Any]]:
    """Classify evidence text using keyword matching."""
    try:
        tags = standards_config.classify_evidence_by_keywords(text)
        
        return [
            {
                "id": tag.id,
                "category": tag.category,
                "description": tag.description,
                "keywords": tag.keywords
            }
            for tag in tags
        ]
        
    except Exception as e:
        logger.error(f"Error classifying evidence: {e}")
        raise HTTPException(status_code=500, detail="Failed to classify evidence")
