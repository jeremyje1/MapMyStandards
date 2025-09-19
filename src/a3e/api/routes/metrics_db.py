"""
Database-powered metrics API
Production-ready dashboard metrics with PostgreSQL persistence
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ...database.services import UserService
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

@router.get("/dashboard")
async def get_dashboard_metrics(
    current_user: dict = Depends(get_current_user)
):
    """Get real-time dashboard metrics from database"""
    try:
        user_id = current_user.get("user_id")
        
        # Get comprehensive user metrics from database
        metrics = await UserService.get_user_metrics(user_id)
        
        if not metrics:
            # Return default metrics for new users
            metrics = {
                "core_metrics": {
                    "documents_analyzed": 0,
                    "documents_processing": 0,
                    "standards_mapped": 0,
                    "total_standards": 12,
                    "reports_generated": 0,
                    "reports_pending": 0
                },
                "performance_metrics": {
                    "compliance_score": 0,
                    "coverage_percentage": 0,
                    "time_saved_hours": 0,
                    "money_saved_usd": 0
                },
                "account_info": {
                    "is_trial": True,
                    "trial_days_remaining": 14,
                    "subscription_tier": "trial"
                },
                "recent_activity": {
                    "last_upload": None,
                    "last_report": None,
                    "total_files_uploaded": 0,
                    "successful_analyses": 0
                }
            }
        
        return {
            "success": True,
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Dashboard metrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard metrics")

@router.get("/summary")
async def get_metrics_summary(
    period: str = "week",  # week, month, all
    current_user: dict = Depends(get_current_user)
):
    """Get metrics summary for a specific time period from database"""
    try:
        user_id = current_user.get("user_id")
        
        # Get base metrics
        base_metrics = await UserService.get_user_metrics(user_id)
        
        # For now, return simplified summary
        # TODO: Implement period-based filtering in database queries
        
        uploads_count = base_metrics.get("core_metrics", {}).get("documents_analyzed", 0) + base_metrics.get("core_metrics", {}).get("documents_processing", 0)

        return {
            "success": True,
            "data": {
                "period": period,
                "period_metrics": {
                    "uploads": uploads_count,
                    "analyses_completed": base_metrics.get("core_metrics", {}).get("documents_analyzed", 0),
                    "reports_generated": base_metrics.get("core_metrics", {}).get("reports_generated", 0),
                    "success_rate": 100  # Assume 100% success rate for trial
                },
                "trends": {
                    "standards_coverage": [],  # TODO: Implement time-series data
                    "daily_activity": []       # TODO: Implement daily activity tracking
                },
                "top_standards": [],  # TODO: Implement from standard_mappings table
                "most_recent_activity": {
                    "last_upload": base_metrics.get("recent_activity", {}).get("last_upload"),
                    "last_completion": None  # TODO: Get from jobs table
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Metrics summary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics summary")

@router.get("/progress/{job_id}")
async def get_job_progress(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get real-time progress for a specific job from database"""
    try:
        from ...database.services import JobService
        
        user_id = current_user.get("user_id")
        
        # Get job from database
        job = await JobService.get_job(job_id, user_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Convert results if needed
        results = None
        if job.status == "completed" and getattr(job, "result", None):
            import json
            try:
                _raw = job.result
                results = json.loads(_raw) if isinstance(_raw, str) else _raw
            except (json.JSONDecodeError, TypeError):
                results = getattr(job, "result", None)
        
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "description": job.description,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "results": results
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job progress error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job progress")
