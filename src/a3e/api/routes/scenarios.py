"""
Scenario Modeling and ROI Calculator API endpoints
Handles saving, retrieving, and calculating ROI scenarios
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.connection import db_manager
from ..dependencies import get_current_user, has_active_subscription
from ...models import User
from ...database.models import Scenario
from ...services.subscription_value_engine import SubscriptionValueEngine

router = APIRouter()

# Dependency for async database session
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        yield session


class ScenarioInputs(BaseModel):
    """Input parameters for ROI scenario"""
    institution_name: str = Field(..., description="Name of the institution")
    institution_type: str = Field(..., description="Type of institution (e.g., Community College, University)")
    student_enrollment: int = Field(..., ge=0, description="Number of enrolled students")
    faculty_count: int = Field(..., ge=0, description="Number of faculty members")
    staff_count: int = Field(..., ge=0, description="Number of staff members")
    annual_budget: float = Field(..., gt=0, description="Annual budget in USD")
    compliance_team_size: int = Field(..., ge=0, description="Current compliance team size")
    accreditations_count: int = Field(..., ge=1, description="Number of accreditations to manage")
    reports_per_year: int = Field(..., ge=0, description="Number of compliance reports per year")
    hours_per_report: float = Field(..., gt=0, description="Average hours spent per report")
    avg_hourly_rate: float = Field(default=75.0, gt=0, description="Average hourly rate for compliance work")


class ScenarioResults(BaseModel):
    """Calculated results for ROI scenario"""
    current_annual_cost: float
    projected_annual_cost: float
    annual_savings: float
    five_year_savings: float
    roi_percentage: float
    payback_period_months: int
    efficiency_gain_percentage: float
    time_saved_hours: float
    risk_reduction_value: float
    productivity_metrics: Dict[str, float]
    savings_breakdown: Dict[str, float]
    year_over_year_projection: List[Dict[str, float]]


class ScenarioCreate(BaseModel):
    """Request model for creating a scenario"""
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    inputs: ScenarioInputs
    is_template: bool = Field(default=False, description="Save as template for others")


class ScenarioResponse(BaseModel):
    """Response model for saved scenario"""
    id: str
    name: str
    description: Optional[str]
    inputs: ScenarioInputs
    results: ScenarioResults
    is_template: bool
    created_at: datetime
    updated_at: datetime
    created_by: str


@router.post("/scenarios/calculate", response_model=ScenarioResults)
async def calculate_scenario(
    inputs: ScenarioInputs,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription)
):
    """
    Calculate ROI for given scenario inputs without saving
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Use the existing SubscriptionValueEngine for calculations
    value_engine = SubscriptionValueEngine()
    
    # Calculate current costs
    report_costs = inputs.reports_per_year * inputs.hours_per_report * inputs.avg_hourly_rate
    team_costs = inputs.compliance_team_size * inputs.avg_hourly_rate * 2000  # Assume 2000 hours/year
    current_annual_cost = report_costs + team_costs
    
    # MapMyStandards reduces time by 70-80%
    time_reduction_factor = 0.75
    time_saved_hours = inputs.reports_per_year * inputs.hours_per_report * time_reduction_factor
    
    # Calculate projected costs with MapMyStandards
    subscription_cost = 199 * 12  # $199/month
    reduced_report_costs = inputs.reports_per_year * inputs.hours_per_report * (1 - time_reduction_factor) * inputs.avg_hourly_rate
    efficient_team_costs = inputs.compliance_team_size * inputs.avg_hourly_rate * 2000 * 0.5  # 50% more efficient team
    projected_annual_cost = subscription_cost + reduced_report_costs + efficient_team_costs
    
    annual_savings = current_annual_cost - projected_annual_cost
    five_year_savings = annual_savings * 5 - subscription_cost * 4  # Subtract 4 years of subscription
    
    # ROI calculation
    roi_percentage = (annual_savings / subscription_cost) * 100
    payback_period_months = int((subscription_cost / annual_savings) * 12) if annual_savings > 0 else 999
    
    # Risk reduction value (compliance penalties avoided)
    risk_reduction_value = inputs.annual_budget * 0.002  # 0.2% of budget as potential penalty avoidance
    
    # Productivity metrics
    productivity_metrics = {
        "reports_completed_faster": time_reduction_factor * 100,
        "evidence_organized": 95.0,
        "audit_readiness": 90.0,
        "team_efficiency_gain": 50.0
    }
    
    # Savings breakdown
    savings_breakdown = {
        "time_savings": time_saved_hours * inputs.avg_hourly_rate,
        "efficiency_gains": inputs.compliance_team_size * inputs.avg_hourly_rate * 2000 * 0.5,
        "risk_mitigation": risk_reduction_value,
        "process_improvement": annual_savings * 0.1
    }
    
    # Year-over-year projection
    year_over_year = []
    for year in range(1, 6):
        year_savings = annual_savings * year
        year_cost = subscription_cost * year
        net_benefit = year_savings - year_cost
        
        year_over_year.append({
            "year": year,
            "savings": year_savings,
            "cost": year_cost,
            "net_benefit": net_benefit,
            "cumulative_roi": (net_benefit / year_cost * 100) if year_cost > 0 else 0
        })
    
    return ScenarioResults(
        current_annual_cost=current_annual_cost,
        projected_annual_cost=projected_annual_cost,
        annual_savings=annual_savings,
        five_year_savings=five_year_savings,
        roi_percentage=roi_percentage,
        payback_period_months=payback_period_months,
        efficiency_gain_percentage=50.0,
        time_saved_hours=time_saved_hours,
        risk_reduction_value=risk_reduction_value,
        productivity_metrics=productivity_metrics,
        savings_breakdown=savings_breakdown,
        year_over_year_projection=year_over_year
    )


@router.post("/scenarios", response_model=ScenarioResponse)
async def create_scenario(
    scenario: ScenarioCreate,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Save a new ROI scenario
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Calculate results
    results = await calculate_scenario(scenario.inputs, current_user, has_subscription)
    
    # Create scenario ID
    scenario_id = f"scenario_{current_user.id}_{datetime.utcnow().timestamp()}"
    
    response = ScenarioResponse(
        id=scenario_id,
        name=scenario.name,
        description=scenario.description,
        inputs=scenario.inputs,
        results=results,
        is_template=scenario.is_template,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.email
    )
    
    # Save to database
    db_scenario = Scenario(
        user_id=current_user.id,
        name=scenario.name,
        description=scenario.description,
        inputs=scenario.inputs.dict(),
        results=results,
        is_template=scenario.is_template
    )
    
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    
    # Return response with database ID
    response.id = str(db_scenario.id)
    return response


@router.get("/scenarios", response_model=List[ScenarioResponse])
async def list_scenarios(
    include_templates: bool = True,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: AsyncSession = Depends(get_db_session)
):
    """
    List all saved scenarios for the current user
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Query scenarios from database
    query = db.query(Scenario).filter(Scenario.user_id == current_user.id)
    
    if not include_templates:
        query = query.filter(Scenario.is_template.is_(False))
    
    db_scenarios = query.all()
    
    scenarios = []
    for db_scenario in db_scenarios:
        scenarios.append(ScenarioResponse(
            id=str(db_scenario.id),
            name=db_scenario.name,
            description=db_scenario.description,
            inputs=ScenarioInputs(**db_scenario.inputs),
            results=db_scenario.results,
            is_template=db_scenario.is_template,
            created_at=db_scenario.created_at,
            updated_at=db_scenario.updated_at,
            created_by=current_user.email
        ))
    
    return scenarios


@router.get("/scenarios/templates")
async def get_scenario_templates():
    """
    Get pre-built scenario templates (no auth required)
    """
    templates = [
        {
            "id": "small_college",
            "name": "Small Community College",
            "description": "2,000-5,000 students, regional accreditation",
            "inputs": {
                "institution_type": "Community College",
                "student_enrollment": 3000,
                "faculty_count": 100,
                "staff_count": 75,
                "annual_budget": 25000000,
                "compliance_team_size": 2,
                "accreditations_count": 3,
                "reports_per_year": 12,
                "hours_per_report": 40
            }
        },
        {
            "id": "medium_university",
            "name": "Medium University",
            "description": "10,000-20,000 students, multiple accreditations",
            "inputs": {
                "institution_type": "University",
                "student_enrollment": 15000,
                "faculty_count": 600,
                "staff_count": 400,
                "annual_budget": 150000000,
                "compliance_team_size": 5,
                "accreditations_count": 8,
                "reports_per_year": 24,
                "hours_per_report": 60
            }
        },
        {
            "id": "large_system",
            "name": "Large University System",
            "description": "50,000+ students, complex multi-campus",
            "inputs": {
                "institution_type": "University System",
                "student_enrollment": 75000,
                "faculty_count": 3000,
                "staff_count": 2000,
                "annual_budget": 800000000,
                "compliance_team_size": 15,
                "accreditations_count": 20,
                "reports_per_year": 48,
                "hours_per_report": 80
            }
        }
    ]
    
    return templates


@router.get("/scenarios/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get a specific saved scenario
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Query scenario by ID
    db_scenario = db.query(Scenario).filter(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    ).first()
    
    if not db_scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    return ScenarioResponse(
        id=str(db_scenario.id),
        name=db_scenario.name,
        description=db_scenario.description,
        inputs=ScenarioInputs(**db_scenario.inputs),
        results=db_scenario.results,
        is_template=db_scenario.is_template,
        created_at=db_scenario.created_at,
        updated_at=db_scenario.updated_at,
        created_by=current_user.email
    )


@router.delete("/scenarios/{scenario_id}")
async def delete_scenario(
    scenario_id: str,
    current_user: User = Depends(get_current_user),
    has_subscription: bool = Depends(has_active_subscription),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Delete a saved scenario
    """
    if not has_subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required"
        )
    
    # Query and delete scenario
    db_scenario = db.query(Scenario).filter(
        Scenario.id == scenario_id,
        Scenario.user_id == current_user.id
    ).first()
    
    if not db_scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scenario not found"
        )
    
    db.delete(db_scenario)
    db.commit()
    
    return {"message": "Scenario deleted successfully"}
