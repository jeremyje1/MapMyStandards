"""
Workflows API Routes for A3E

Provides REST endpoints for managing accreditation workflows and agent orchestration.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from ...core.config import settings
from ...services.database_service import DatabaseService
try:  # Optional heavy dependency
    from ...agents import A3EAgentOrchestrator  # type: ignore
    _workflow_orchestrator_available = True
except Exception as e:  # Catch broad to handle transitive ImportError chain
    _workflow_orchestrator_available = False
    _workflow_orchestrator_import_error = e
    # Provide stub type for type-checkers while avoiding runtime NameError
    if TYPE_CHECKING:  # pragma: no cover
        class A3EAgentOrchestrator:  # type: ignore
            ...

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class WorkflowCreate(BaseModel):
    title: str = Field(..., description="Workflow title")
    description: Optional[str] = Field(None, description="Workflow description")
    institution_id: str = Field(..., description="Institution ID")
    accreditor_id: str = Field(..., description="Accreditor ID")
    workflow_type: str = Field(..., description="Type of workflow")
    target_standards: List[str] = Field(..., description="List of standard IDs to evaluate")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Workflow parameters")

class WorkflowResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    institution_id: str
    accreditor_id: str
    workflow_type: str
    status: str
    target_standards: List[str]
    progress: float
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    is_active: bool

class WorkflowDetail(WorkflowResponse):
    parameters: Dict[str, Any]
    results: Dict[str, Any]
    error_message: Optional[str]
    agent_logs: List[Dict[str, Any]]
    evidence_count: int
    mapping_count: int
    updated_at: str
    institution_name: Optional[str]
    accreditor_name: Optional[str]

class WorkflowExecution(BaseModel):
    workflow_id: str
    parameters: Optional[Dict[str, Any]] = Field(None, description="Runtime parameters")
    force_restart: bool = Field(False, description="Force restart if already running")

class AgentLogEntry(BaseModel):
    timestamp: str
    agent_name: str
    agent_type: str
    message: str
    level: str
    metadata: Dict[str, Any]

class WorkflowStatistics(BaseModel):
    total_workflows: int
    active_workflows: int
    completed_workflows: int
    failed_workflows: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_institution: Dict[str, int]

# Dependency for database service
async def get_db_service():
    db_service = DatabaseService(settings.database_url)
    await db_service.initialize()
    try:
        yield db_service
    finally:
        await db_service.close()

# Dependency for agent orchestrator
async def get_agent_orchestrator():
    if not _workflow_orchestrator_available:
        raise HTTPException(status_code=503, detail="Agent orchestrator unavailable on this deployment")
    return A3EAgentOrchestrator()

@router.get("/workflows", response_model=List[WorkflowResponse])
async def list_workflows(
    institution_id: Optional[str] = Query(None, description="Filter by institution"),
    accreditor_id: Optional[str] = Query(None, description="Filter by accreditor"),
    workflow_type: Optional[str] = Query(None, description="Filter by workflow type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: DatabaseService = Depends(get_db_service)
):
    """List workflows with optional filters"""
    try:
        workflows = await db.list_workflows(
            institution_id=institution_id,
            accreditor_id=accreditor_id,
            workflow_type=workflow_type,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            WorkflowResponse(
                id=str(wf.id),
                title=wf.title,
                description=wf.description,
                institution_id=str(wf.institution_id),
                accreditor_id=wf.accreditor_id,
                workflow_type=wf.workflow_type,
                status=wf.status,
                target_standards=wf.target_standards,
                progress=wf.progress,
                created_at=wf.created_at.isoformat(),
                started_at=wf.started_at.isoformat() if wf.started_at else None,
                completed_at=wf.completed_at.isoformat() if wf.completed_at else None,
                is_active=wf.is_active
            )
            for wf in workflows
        ]
        
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/workflows/{workflow_id}", response_model=WorkflowDetail)
async def get_workflow(
    workflow_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Get detailed information about a specific workflow"""
    try:
        workflow = await db.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get related entities
        institution = await db.get_institution(str(workflow.institution_id))
        
        # Get workflow statistics
        stats = await db.get_workflow_statistics(workflow_id)
        
        return WorkflowDetail(
            id=str(workflow.id),
            title=workflow.title,
            description=workflow.description,
            institution_id=str(workflow.institution_id),
            accreditor_id=workflow.accreditor_id,
            workflow_type=workflow.workflow_type,
            status=workflow.status,
            target_standards=workflow.target_standards,
            progress=workflow.progress,
            parameters=workflow.parameters,
            results=workflow.results,
            error_message=workflow.error_message,
            agent_logs=workflow.agent_logs,
            evidence_count=stats.get("evidence_count", 0),
            mapping_count=stats.get("mapping_count", 0),
            created_at=workflow.created_at.isoformat(),
            started_at=workflow.started_at.isoformat() if workflow.started_at else None,
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
            updated_at=workflow.updated_at.isoformat(),
            is_active=workflow.is_active,
            institution_name=institution.name if institution else None,
            accreditor_name=workflow.accreditor_id  # This could be enhanced with actual accreditor lookup
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/workflows", response_model=WorkflowDetail, status_code=201)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: DatabaseService = Depends(get_db_service)
):
    """Create a new workflow"""
    try:
        # Validate institution
        institution = await db.get_institution(workflow_data.institution_id)
        if not institution:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid institution ID: {workflow_data.institution_id}"
            )
        
        # Validate standards exist
        for standard_id in workflow_data.target_standards:
            standard = await db.get_standard(standard_id)
            if not standard:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid standard ID: {standard_id}"
                )
        
        # Create workflow
        workflow = await db.create_workflow(workflow_data.dict())
        
        return WorkflowDetail(
            id=str(workflow.id),
            title=workflow.title,
            description=workflow.description,
            institution_id=str(workflow.institution_id),
            accreditor_id=workflow.accreditor_id,
            workflow_type=workflow.workflow_type,
            status=workflow.status,
            target_standards=workflow.target_standards,
            progress=workflow.progress,
            parameters=workflow.parameters,
            results=workflow.results,
            error_message=workflow.error_message,
            agent_logs=workflow.agent_logs,
            evidence_count=0,
            mapping_count=0,
            created_at=workflow.created_at.isoformat(),
            started_at=workflow.started_at.isoformat() if workflow.started_at else None,
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
            updated_at=workflow.updated_at.isoformat(),
            is_active=workflow.is_active,
            institution_name=institution.name,
            accreditor_name=workflow.accreditor_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    execution_data: WorkflowExecution,
    background_tasks: BackgroundTasks,
    db: DatabaseService = Depends(get_db_service),
    orchestrator: 'A3EAgentOrchestrator' = Depends(get_agent_orchestrator)
):
    """Execute a workflow using the agent orchestrator"""
    try:
        workflow = await db.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Check if workflow is already running
        if workflow.status == "running" and not execution_data.force_restart:
            raise HTTPException(
                status_code=400,
                detail="Workflow is already running. Use force_restart=true to restart."
            )
        
        # Update workflow status to running
        await db.update_workflow(workflow_id, {
            "status": "running",
            "started_at": datetime.utcnow(),
            "progress": 0.0,
            "error_message": None,
            "parameters": {**workflow.parameters, **(execution_data.parameters or {})}
        })
        
        # Execute workflow in background
        background_tasks.add_task(
            _execute_workflow_background,
            workflow_id,
            orchestrator,
            db
        )
        
        return {
            "workflow_id": workflow_id,
            "status": "running",
            "message": "Workflow execution started",
            "started_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def _execute_workflow_background(
    workflow_id: str,
    orchestrator: 'A3EAgentOrchestrator',
    db: DatabaseService
):
    """Background task for workflow execution"""
    try:
        workflow = await db.get_workflow(workflow_id)
        if not workflow:
            return
        
        # Execute workflow through orchestrator
        result = await orchestrator.execute_workflow(workflow_id)
        
        # Update workflow with results
        await db.update_workflow(workflow_id, {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "progress": 100.0,
            "results": result
        })
        
    except Exception as e:
        logger.error(f"Error in background workflow execution {workflow_id}: {e}")
        await db.update_workflow(workflow_id, {
            "status": "failed",
            "completed_at": datetime.utcnow(),
            "error_message": str(e)
        })

@router.post("/workflows/{workflow_id}/stop")
async def stop_workflow(
    workflow_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Stop a running workflow"""
    try:
        workflow = await db.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status != "running":
            raise HTTPException(
                status_code=400,
                detail="Workflow is not currently running"
            )
        
        # Update workflow status
        await db.update_workflow(workflow_id, {
            "status": "stopped",
            "completed_at": datetime.utcnow(),
            "error_message": "Workflow stopped by user"
        })
        
        return {
            "workflow_id": workflow_id,
            "status": "stopped",
            "message": "Workflow stopped successfully",
            "stopped_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/workflows/{workflow_id}/logs", response_model=List[AgentLogEntry])
async def get_workflow_logs(
    workflow_id: str,
    agent_type: Optional[str] = Query(None, description="Filter by agent type"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(100, le=1000, description="Maximum number of logs"),
    db: DatabaseService = Depends(get_db_service)
):
    """Get agent logs for a workflow"""
    try:
        workflow = await db.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        logs = workflow.agent_logs
        
        # Apply filters
        if agent_type:
            logs = [log for log in logs if log.get("agent_type") == agent_type]
        
        if level:
            logs = [log for log in logs if log.get("level") == level]
        
        # Limit results
        logs = logs[-limit:] if len(logs) > limit else logs
        
        return [
            AgentLogEntry(
                timestamp=log.get("timestamp", ""),
                agent_name=log.get("agent_name", ""),
                agent_type=log.get("agent_type", ""),
                message=log.get("message", ""),
                level=log.get("level", "info"),
                metadata=log.get("metadata", {})
            )
            for log in logs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow logs {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/workflows/{workflow_id}/results")
async def get_workflow_results(
    workflow_id: str,
    db: DatabaseService = Depends(get_db_service)
):
    """Get detailed results from a completed workflow"""
    try:
        workflow = await db.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status not in ["completed", "failed"]:
            raise HTTPException(
                status_code=400,
                detail="Workflow has not completed yet"
            )
        
        # Get related mappings
        mappings = await db.get_workflow_mappings(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "status": workflow.status,
            "progress": workflow.progress,
            "results": workflow.results,
            "error_message": workflow.error_message,
            "mappings": [
                {
                    "id": str(mapping.id),
                    "standard_id": mapping.standard_id,
                    "evidence_id": str(mapping.evidence_id),
                    "confidence_score": mapping.confidence_score,
                    "mapping_rationale": mapping.mapping_rationale,
                    "gap_analysis": mapping.gap_analysis,
                    "created_at": mapping.created_at.isoformat()
                }
                for mapping in mappings
            ],
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow results {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/workflow-statistics", response_model=WorkflowStatistics)
async def get_workflow_statistics(
    institution_id: Optional[str] = Query(None, description="Filter by institution"),
    accreditor_id: Optional[str] = Query(None, description="Filter by accreditor"),
    db: DatabaseService = Depends(get_db_service)
):
    """Get comprehensive workflow statistics"""
    try:
        stats = await db.get_all_workflow_statistics(
            institution_id=institution_id,
            accreditor_id=accreditor_id
        )
        
        return WorkflowStatistics(
            total_workflows=stats.get("total_workflows", 0),
            active_workflows=stats.get("active_workflows", 0),
            completed_workflows=stats.get("completed_workflows", 0),
            failed_workflows=stats.get("failed_workflows", 0),
            by_type=stats.get("by_type", {}),
            by_status=stats.get("by_status", {}),
            by_institution=stats.get("by_institution", {})
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/workflow-types")
async def list_workflow_types():
    """List all supported workflow types"""
    return {
        "workflow_types": [
            {
                "type": "evidence_mapping",
                "name": "Evidence Mapping",
                "description": "Map institutional evidence to accreditation standards"
            },
            {
                "type": "gap_analysis",
                "name": "Gap Analysis",
                "description": "Identify gaps in evidence coverage for standards"
            },
            {
                "type": "narrative_generation",
                "name": "Narrative Generation",
                "description": "Generate compliance narratives based on evidence"
            },
            {
                "type": "full_review",
                "name": "Full Review",
                "description": "Complete evidence mapping, gap analysis, and narrative generation"
            }
        ]
    }
