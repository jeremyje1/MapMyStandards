"""
Power BI Integration API endpoints
Handles Power BI embed token generation and configuration
"""

import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

from ...database.connection import db_manager
from ..dependencies import get_current_user, has_active_subscription
from ...models import User
from ...database.enterprise_models import PowerBIConfig as PowerBIConfigModel
from ...services.powerbi_service import create_powerbi_service, PowerBIService

router = APIRouter()
# Dependency for async database session
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        yield session



class PowerBIConfig(BaseModel):
    """Power BI embed configuration"""
    workspace_id: str = Field(..., description="Power BI workspace ID")
    report_id: str = Field(..., description="Power BI report ID")
    embed_url: str = Field(..., description="Embed URL for the report")
    access_token: str = Field(..., description="Access token for embedding")
    token_expiry: datetime = Field(..., description="Token expiration time")
    token_id: Optional[str] = Field(None, description="Token ID for refresh")


class PowerBIEmbedRequest(BaseModel):
    """Request for Power BI embed token"""
    report_ids: List[str] = Field(..., description="List of report IDs to embed")
    dataset_ids: Optional[List[str]] = Field(None, description="List of dataset IDs")
    username: Optional[str] = Field(None, description="Username for RLS")
    roles: Optional[List[str]] = Field(None, description="Roles for RLS")
    filters: Optional[Dict[str, Any]] = Field(None, description="Report filters")


class PowerBIStatus(BaseModel):
    """Power BI configuration status"""
    configured: bool
    has_credentials: bool
    connection_test: bool
    last_sync: Optional[datetime]
    error_message: Optional[str]
    workspace_info: Optional[Dict[str, Any]]


class PowerBIReport(BaseModel):
    """Power BI report information"""
    id: str
    name: str
    embed_url: str
    dataset_id: str
    modified_date: datetime
    is_owned_by_me: bool


class PowerBIDataset(BaseModel):
    """Power BI dataset information"""
    id: str
    name: str
    configured_by: Optional[str]
    is_refreshable: bool
    last_refresh: Optional[datetime]
    next_refresh: Optional[datetime]


@router.get("/powerbi/config", response_model=PowerBIStatus)
async def get_powerbi_config(
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """
    Check Power BI configuration status and test connection
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Check environment variables
    required_vars = [
        "POWERBI_CLIENT_ID",
        "POWERBI_TENANT_ID",
        "POWERBI_WORKSPACE_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        return PowerBIStatus(
            configured=False,
            has_credentials=False,
            connection_test=False,
            last_sync=None,
            error_message=f"Missing environment variables: {', '.join(missing_vars)}",
            workspace_info=None
        )
    
    # Test actual Power BI connection
    powerbi_service = create_powerbi_service()
    if not powerbi_service:
        return PowerBIStatus(
            configured=False,
            has_credentials=False,
            connection_test=False,
            last_sync=None,
            error_message="Failed to initialize Power BI service",
            workspace_info=None
        )
    
    try:
        # Test connection
        connection_test = await powerbi_service.test_connection()
        
        workspace_info = None
        if connection_test:
            # Get workspace information
            workspaces = await powerbi_service.get_workspaces()
            current_workspace = next(
                (ws for ws in workspaces if ws['id'] == os.getenv("POWERBI_WORKSPACE_ID")), 
                None
            )
            if current_workspace:
                workspace_info = {
                    "name": current_workspace.get("name", "Unknown"),
                    "type": current_workspace.get("type", "Unknown"),
                    "state": current_workspace.get("state", "Unknown")
                }
        
        return PowerBIStatus(
            configured=True,
            has_credentials=True,
            connection_test=connection_test,
            last_sync=datetime.utcnow(),
            error_message=None if connection_test else "Connection test failed",
            workspace_info=workspace_info
        )
        
    except Exception as e:
        return PowerBIStatus(
            configured=True,
            has_credentials=True,
            connection_test=False,
            last_sync=None,
            error_message=f"Connection error: {str(e)}",
            workspace_info=None
        )


@router.post("/powerbi/embed-token", response_model=PowerBIConfig)
async def create_embed_token(
    request: PowerBIEmbedRequest,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate Power BI embed token with Row-Level Security
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    powerbi_service = create_powerbi_service()
    if not powerbi_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Power BI service not available"
        )
    
    try:
        # If no dataset IDs provided, get them from reports
        dataset_ids = request.dataset_ids or []
        if not dataset_ids and request.report_ids:
            reports = await powerbi_service.get_reports()
            for report in reports:
                if report.id in request.report_ids and report.dataset_id:
                    dataset_ids.append(report.dataset_id)
        
        # Apply Row-Level Security based on user's institution
        username = request.username or current_user.email
        roles = request.roles or ["User"]  # Default role
        
        # Generate embed token
        embed_token = await powerbi_service.generate_embed_token(
            report_ids=request.report_ids,
            dataset_ids=dataset_ids,
            username=username,
            roles=roles
        )
        
        # Get the first report's embed URL
        reports = await powerbi_service.get_reports()
        embed_url = next(
            (r.embed_url for r in reports if r.id in request.report_ids),
            f"https://app.powerbi.com/reportEmbed"
        )
        
        # Save configuration to database
        config = PowerBIConfigModel(
            user_id=current_user.id,
            workspace_id=powerbi_service.credentials.workspace_id,
            report_id=request.report_ids[0] if request.report_ids else "",
            last_sync=datetime.utcnow(),
            rls_config={
                "username": username,
                "roles": roles,
                "filters": request.filters or {}
            }
        )
        db.add(config)
        db.commit()
        
        return PowerBIConfig(
            workspace_id=powerbi_service.credentials.workspace_id,
            report_id=request.report_ids[0] if request.report_ids else "",
            embed_url=embed_url,
            access_token=embed_token.token,
            token_expiry=embed_token.expiration,
            token_id=embed_token.token_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate embed token: {str(e)}"
        )


@router.get("/powerbi/reports", response_model=List[PowerBIReport])
async def list_powerbi_reports(
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """
    List available Power BI reports in the workspace
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    powerbi_service = create_powerbi_service()
    if not powerbi_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Power BI service not available"
        )
    
    try:
        reports = await powerbi_service.get_reports()
        return [
            PowerBIReport(
                id=report.id,
                name=report.name,
                embed_url=report.embed_url,
                dataset_id=report.dataset_id,
                modified_date=report.modified_date,
                is_owned_by_me=report.is_owned_by_me
            )
            for report in reports
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch reports: {str(e)}"
        )


@router.get("/powerbi/datasets", response_model=List[PowerBIDataset])
async def list_powerbi_datasets(
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """
    List available Power BI datasets in the workspace
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    powerbi_service = create_powerbi_service()
    if not powerbi_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Power BI service not available"
        )
    
    try:
        datasets = await powerbi_service.get_datasets()
        return [
            PowerBIDataset(
                id=dataset["id"],
                name=dataset["name"],
                configured_by=dataset.get("configuredBy"),
                is_refreshable=dataset.get("isRefreshable", False),
                last_refresh=datetime.fromisoformat(
                    dataset["lastRefresh"].replace("Z", "+00:00")
                ) if dataset.get("lastRefresh") else None,
                next_refresh=datetime.fromisoformat(
                    dataset["nextRefresh"].replace("Z", "+00:00")
                ) if dataset.get("nextRefresh") else None
            )
            for dataset in datasets
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch datasets: {str(e)}"
        )


@router.post("/powerbi/refresh/{dataset_id}")
async def refresh_powerbi_dataset(
    dataset_id: str,
    notify_option: str = "MailOnCompletion",
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """
    Trigger a dataset refresh in Power BI
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    powerbi_service = create_powerbi_service()
    if not powerbi_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Power BI service not available"
        )
    
    try:
        request_id = await powerbi_service.refresh_dataset(dataset_id, notify_option)
        return {
            "status": "refresh_initiated",
            "message": "Power BI dataset refresh has been initiated",
            "request_id": request_id,
            "dataset_id": dataset_id,
            "notify_option": notify_option
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh dataset: {str(e)}"
        )


@router.get("/powerbi/refresh/{dataset_id}/history")
async def get_refresh_history(
    dataset_id: str,
    top: int = 10,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """
    Get dataset refresh history
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    powerbi_service = create_powerbi_service()
    if not powerbi_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Power BI service not available"
        )
    
    try:
        history = await powerbi_service.get_refresh_history(dataset_id, top)
        return {"refresh_history": history}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get refresh history: {str(e)}"
        )


@router.post("/powerbi/row-level-security")
async def configure_rls(
    institution_filter: str,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Configure Row-Level Security for Power BI reports
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    try:
        # Save RLS configuration to database
        existing_config = db.query(PowerBIConfigModel).filter(
            PowerBIConfigModel.user_id == current_user.id
        ).first()
        
        if existing_config:
            # Update existing configuration
            existing_config.rls_config = {
                "institution_filter": institution_filter,
                "configured_by": current_user.email,
                "configured_at": datetime.utcnow().isoformat()
            }
            existing_config.updated_at = datetime.utcnow()
        else:
            # Create new configuration
            config = PowerBIConfigModel(
                user_id=current_user.id,
                workspace_id=os.getenv("POWERBI_WORKSPACE_ID", ""),
                report_id="",  # Will be set when generating embed tokens
                rls_config={
                    "institution_filter": institution_filter,
                    "configured_by": current_user.email,
                    "configured_at": datetime.utcnow().isoformat()
                }
            )
            db.add(config)
        
        db.commit()
        
        return {
            "status": "configured",
            "institution_filter": institution_filter,
            "user": current_user.email,
            "message": "Row-level security has been configured for your reports"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to configure RLS: {str(e)}"
        )
