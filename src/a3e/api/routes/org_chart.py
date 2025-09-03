"""
Organization Chart API endpoints
Handles saving, retrieving, and managing organizational structures
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database import get_db
from ..dependencies import get_current_user, has_active_subscription
from ...models import User
from ...database.models import OrgChart

router = APIRouter()


class OrgNode(BaseModel):
    """Individual node in the organization chart"""
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display name for the node")
    title: Optional[str] = Field(None, description="Job title")
    level: int = Field(..., description="Hierarchy level (1=Executive, 2=Director, etc.)")
    department: Optional[str] = Field(None, description="Department name")
    compliance_areas: List[str] = Field(default_factory=list, description="Areas of compliance responsibility")
    x: Optional[float] = Field(None, description="X position")
    y: Optional[float] = Field(None, description="Y position")


class OrgEdge(BaseModel):
    """Connection between nodes"""
    id: str = Field(..., description="Unique edge identifier")
    from_node: str = Field(..., alias="from", description="Source node ID")
    to_node: str = Field(..., alias="to", description="Target node ID")


class OrgChartData(BaseModel):
    """Complete organization chart structure"""
    nodes: List[OrgNode]
    edges: List[OrgEdge]
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional chart metadata")

    class Config:
        populate_by_name = True


class OrgChartCreate(BaseModel):
    """Request model for creating/updating org chart"""
    name: str = Field(..., description="Chart name")
    description: Optional[str] = Field(None, description="Chart description")
    data: OrgChartData = Field(..., description="Chart structure data")
    institution_type: Optional[str] = Field(None, description="Type of institution")
    total_employees: Optional[int] = Field(None, description="Total number of employees")


class OrgChartResponse(BaseModel):
    """Response model for org chart"""
    id: str
    name: str
    description: Optional[str]
    data: OrgChartData
    institution_type: Optional[str]
    total_employees: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: str


@router.post("/org-chart", response_model=OrgChartResponse)
async def create_org_chart(
    chart: OrgChartCreate,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: Session = Depends(get_db)
):
    """
    Create or update organization chart
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Create new organization chart in database
    chart_data = chart.data.dict()
    if chart.institution_type:
        chart_data['institution_type'] = chart.institution_type
    if chart.total_employees:
        chart_data['total_employees'] = chart.total_employees
    
    db_chart = OrgChart(
        user_id=current_user.id,
        name=chart.name,
        description=chart.description,
        chart_data=chart_data
    )
    
    db.add(db_chart)
    db.commit()
    db.refresh(db_chart)
    
    # Extract data back from database
    chart_data = db_chart.chart_data.copy()
    institution_type = chart_data.pop('institution_type', None)
    total_employees = chart_data.pop('total_employees', None)
    
    response = OrgChartResponse(
        id=str(db_chart.id),
        name=db_chart.name,
        description=db_chart.description,
        data=OrgChartData(**chart_data),
        institution_type=institution_type,
        total_employees=total_employees,
        created_at=db_chart.created_at,
        updated_at=db_chart.updated_at,
        created_by=current_user.email
    )
    
    return response


@router.get("/org-chart", response_model=List[OrgChartResponse])
async def list_org_charts(
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: Session = Depends(get_db)
):
    """
    List all organization charts for the current user's institution
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Query organization charts for the current user
    db_charts = db.query(OrgChart).filter(OrgChart.user_id == current_user.id).all()
    
    charts = []
    for db_chart in db_charts:
        chart_data = db_chart.chart_data.copy()
        institution_type = chart_data.pop('institution_type', None)
        total_employees = chart_data.pop('total_employees', None)
        
        charts.append(OrgChartResponse(
            id=str(db_chart.id),
            name=db_chart.name,
            description=db_chart.description,
            data=OrgChartData(**chart_data),
            institution_type=institution_type,
            total_employees=total_employees,
            created_at=db_chart.created_at,
            updated_at=db_chart.updated_at,
            created_by=current_user.email
        ))
    
    return charts


@router.get("/org-chart/{chart_id}", response_model=OrgChartResponse)
async def get_org_chart(
    chart_id: str,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: Session = Depends(get_db)
):
    """
    Get a specific organization chart
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Query organization chart by ID and user
    db_chart = db.query(OrgChart).filter(
        OrgChart.id == int(chart_id),
        OrgChart.user_id == current_user.id
    ).first()
    
    if not db_chart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization chart not found"
        )
    
    # Extract data from database
    chart_data = db_chart.chart_data.copy()
    institution_type = chart_data.pop('institution_type', None)
    total_employees = chart_data.pop('total_employees', None)
    
    return OrgChartResponse(
        id=str(db_chart.id),
        name=db_chart.name,
        description=db_chart.description,
        data=OrgChartData(**chart_data),
        institution_type=institution_type,
        total_employees=total_employees,
        created_at=db_chart.created_at,
        updated_at=db_chart.updated_at,
        created_by=current_user.email
    )


@router.put("/org-chart/{chart_id}", response_model=OrgChartResponse)
async def update_org_chart(
    chart_id: str,
    chart: OrgChartCreate,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: Session = Depends(get_db)
):
    """
    Update an existing organization chart
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Query and update organization chart
    db_chart = db.query(OrgChart).filter(
        OrgChart.id == int(chart_id),
        OrgChart.user_id == current_user.id
    ).first()
    
    if not db_chart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization chart not found"
        )
    
    # Update chart data
    chart_data = chart.data.dict()
    if chart.institution_type:
        chart_data['institution_type'] = chart.institution_type
    if chart.total_employees:
        chart_data['total_employees'] = chart.total_employees
    
    db_chart.name = chart.name
    db_chart.description = chart.description
    db_chart.chart_data = chart_data
    db_chart.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_chart)
    
    # Extract data back from database
    chart_data = db_chart.chart_data.copy()
    institution_type = chart_data.pop('institution_type', None)
    total_employees = chart_data.pop('total_employees', None)
    
    response = OrgChartResponse(
        id=str(db_chart.id),
        name=db_chart.name,
        description=db_chart.description,
        data=OrgChartData(**chart_data),
        institution_type=institution_type,
        total_employees=total_employees,
        created_at=db_chart.created_at,
        updated_at=db_chart.updated_at,
        created_by=current_user.email
    )
    
    return response


@router.delete("/org-chart/{chart_id}")
async def delete_org_chart(
    chart_id: str,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: Session = Depends(get_db)
):
    """
    Delete an organization chart
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Query and delete organization chart
    db_chart = db.query(OrgChart).filter(
        OrgChart.id == int(chart_id),
        OrgChart.user_id == current_user.id
    ).first()
    
    if not db_chart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization chart not found"
        )
    
    db.delete(db_chart)
    db.commit()
    
    return {"message": "Organization chart deleted successfully"}


@router.post("/org-chart/{chart_id}/analyze")
async def analyze_org_chart(
    chart_id: str,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: Session = Depends(get_db)
):
    """
    Analyze organization chart for compliance coverage and gaps
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # TODO: Implement actual analysis logic
    # This would analyze the org structure against compliance requirements
    
    analysis = {
        "coverage_score": 85,
        "gaps": [
            {
                "area": "Assessment Coordination",
                "severity": "medium",
                "recommendation": "Consider adding a dedicated Assessment Coordinator role"
            }
        ],
        "strengths": [
            "Clear reporting structure",
            "Compliance areas well distributed"
        ],
        "recommendations": [
            "Add backup responsible parties for critical compliance areas",
            "Consider creating a compliance committee"
        ]
    }
    
    return analysis
