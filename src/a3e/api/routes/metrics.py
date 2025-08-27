"""
Real-time metrics API for dashboard
Provides live counts and statistics from uploaded files and generated reports
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

from ...core.config import settings
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

# Storage paths
JOBS_DIR = Path("jobs_status")
REPORTS_DIR = Path("reports_generated")

def load_all_user_jobs(user_id: str) -> list:
    """Load all job data for a user"""
    user_jobs = []
    
    # Create directories if they don't exist
    JOBS_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    
    try:
        for job_file in JOBS_DIR.glob("*.json"):
            try:
                with open(job_file, 'r') as f:
                    job_data = json.load(f)
                    if job_data.get("user_id") == user_id:
                        user_jobs.append(job_data)
            except Exception as e:
                logger.warning(f"Could not load job file {job_file}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error loading user jobs: {e}")
    
    return user_jobs

def load_all_user_reports(user_id: str) -> list:
    """Load all report data for a user"""
    user_reports = []
    
    try:
        for report_file in REPORTS_DIR.glob("*_status.json"):
            try:
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                    if report_data.get("user_id") == user_id:
                        user_reports.append(report_data)
            except Exception as e:
                logger.warning(f"Could not load report file {report_file}: {e}")
                continue
    except Exception as e:
        logger.error(f"Error loading user reports: {e}")
    
    return user_reports

@router.get("/dashboard")
async def get_dashboard_metrics(
    current_user: dict = Depends(get_current_user)
):
    """Get real-time dashboard metrics for current user"""
    try:
        user_id = current_user.get("user_id")
        
        # Load user's jobs and reports
        user_jobs = load_all_user_jobs(user_id)
        user_reports = load_all_user_reports(user_id)
        
        # Calculate metrics
        documents_analyzed = len([j for j in user_jobs if j.get("status") == "completed"])
        documents_processing = len([j for j in user_jobs if j.get("status") in ["queued", "extracting", "parsing", "embedding", "matching", "analyzing"]])
        
        # Count unique standards mapped across all completed jobs
        standards_mapped = set()
        total_standards = 12  # SACSCOC has 12 core standards
        
        for job in user_jobs:
            if job.get("status") == "completed" and job.get("results"):
                mapped = job.get("results", {}).get("mapped_standards", [])
                for standard in mapped:
                    standards_mapped.add(standard.get("standard_id"))
        
        reports_generated = len([r for r in user_reports if r.get("status") == "completed"])
        reports_pending = len([r for r in user_reports if r.get("status") in ["queued", "generating"]])
        
        # Calculate overall compliance score based on standards coverage
        compliance_score = min(int((len(standards_mapped) / total_standards) * 100), 100) if standards_mapped else 0
        
        # Calculate time and money saved (estimates)
        hours_saved_per_doc = 8  # Estimated hours saved per document analysis
        consultant_rate = 150  # USD per hour
        time_saved_hours = documents_analyzed * hours_saved_per_doc
        money_saved = time_saved_hours * consultant_rate
        
        # Calculate trial days remaining (mock for demo)
        trial_start = datetime.now() - timedelta(days=3)  # Assume trial started 3 days ago
        trial_days_remaining = max(0, 14 - (datetime.now() - trial_start).days)
        
        return {
            "success": True,
            "data": {
                "core_metrics": {
                    "documents_analyzed": documents_analyzed,
                    "documents_processing": documents_processing,
                    "standards_mapped": len(standards_mapped),
                    "total_standards": total_standards,
                    "reports_generated": reports_generated,
                    "reports_pending": reports_pending
                },
                "performance_metrics": {
                    "compliance_score": compliance_score,
                    "coverage_percentage": int((len(standards_mapped) / total_standards) * 100) if standards_mapped else 0,
                    "time_saved_hours": time_saved_hours,
                    "money_saved_usd": money_saved
                },
                "account_info": {
                    "is_trial": True,  # Assume trial user for demo
                    "trial_days_remaining": trial_days_remaining,
                    "subscription_tier": "trial"
                },
                "recent_activity": {
                    "last_upload": user_jobs[-1].get("created_at") if user_jobs else None,
                    "last_report": user_reports[-1].get("created_at") if user_reports else None,
                    "total_files_uploaded": len(user_jobs),
                    "successful_analyses": documents_analyzed
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Dashboard metrics error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard metrics")

@router.get("/summary")
async def get_metrics_summary(
    period: str = "week",  # week, month, all
    current_user: dict = Depends(get_current_user)
):
    """Get metrics summary for a specific time period"""
    try:
        user_id = current_user.get("user_id")
        
        # Calculate date range
        now = datetime.now()
        if period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = None  # All time
        
        # Load and filter data
        user_jobs = load_all_user_jobs(user_id)
        user_reports = load_all_user_reports(user_id)
        
        # Filter by date if specified
        if start_date:
            user_jobs = [
                j for j in user_jobs
                if datetime.fromisoformat(j.get("created_at", "2000-01-01")) >= start_date
            ]
            user_reports = [
                r for r in user_reports  
                if datetime.fromisoformat(r.get("created_at", "2000-01-01")) >= start_date
            ]
        
        # Calculate period metrics
        uploads_this_period = len(user_jobs)
        analyses_completed = len([j for j in user_jobs if j.get("status") == "completed"])
        reports_this_period = len(user_reports)
        
        # Standards coverage trend
        standards_coverage = []
        if user_jobs:
            # Group by day and calculate cumulative coverage
            daily_coverage = {}
            cumulative_standards = set()
            
            for job in sorted(user_jobs, key=lambda x: x.get("created_at", "")):
                if job.get("status") == "completed" and job.get("results"):
                    day = job.get("created_at", "")[:10]  # Get YYYY-MM-DD
                    mapped = job.get("results", {}).get("mapped_standards", [])
                    for standard in mapped:
                        cumulative_standards.add(standard.get("standard_id"))
                    daily_coverage[day] = len(cumulative_standards)
            
            # Convert to list of dicts
            for day, count in sorted(daily_coverage.items()):
                standards_coverage.append({
                    "date": day,
                    "standards_mapped": count,
                    "coverage_percentage": int((count / 12) * 100)  # 12 total SACSCOC standards
                })
        
        return {
            "success": True,
            "data": {
                "period": period,
                "period_metrics": {
                    "uploads": uploads_this_period,
                    "analyses_completed": analyses_completed,
                    "reports_generated": reports_this_period,
                    "success_rate": int((analyses_completed / uploads_this_period) * 100) if uploads_this_period > 0 else 0
                },
                "trends": {
                    "standards_coverage": standards_coverage,
                    "daily_activity": self._calculate_daily_activity(user_jobs, start_date)
                },
                "top_standards": self._get_top_mapped_standards(user_jobs),
                "most_recent_activity": {
                    "last_upload": user_jobs[-1].get("created_at") if user_jobs else None,
                    "last_completion": next(
                        (j.get("updated_at") for j in reversed(user_jobs) if j.get("status") == "completed"),
                        None
                    )
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Metrics summary error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics summary")

def _calculate_daily_activity(user_jobs: list, start_date: Optional[datetime]) -> list:
    """Calculate daily activity counts"""
    daily_activity = {}
    
    for job in user_jobs:
        try:
            job_date = datetime.fromisoformat(job.get("created_at", ""))
            if start_date is None or job_date >= start_date:
                day = job_date.strftime("%Y-%m-%d")
                if day not in daily_activity:
                    daily_activity[day] = {"uploads": 0, "completions": 0}
                
                daily_activity[day]["uploads"] += 1
                if job.get("status") == "completed":
                    daily_activity[day]["completions"] += 1
        except Exception:
            continue
    
    # Convert to sorted list
    activity_list = []
    for day, counts in sorted(daily_activity.items()):
        activity_list.append({
            "date": day,
            "uploads": counts["uploads"],
            "completions": counts["completions"]
        })
    
    return activity_list

def _get_top_mapped_standards(user_jobs: list) -> list:
    """Get most frequently mapped standards"""
    standard_counts = {}
    
    for job in user_jobs:
        if job.get("status") == "completed" and job.get("results"):
            mapped = job.get("results", {}).get("mapped_standards", [])
            for standard in mapped:
                std_id = standard.get("standard_id")
                if std_id:
                    if std_id not in standard_counts:
                        standard_counts[std_id] = {
                            "standard_id": std_id,
                            "title": standard.get("title", ""),
                            "count": 0,
                            "avg_confidence": 0,
                            "confidence_sum": 0
                        }
                    
                    standard_counts[std_id]["count"] += 1
                    confidence = standard.get("confidence", 0)
                    standard_counts[std_id]["confidence_sum"] += confidence
                    standard_counts[std_id]["avg_confidence"] = (
                        standard_counts[std_id]["confidence_sum"] / standard_counts[std_id]["count"]
                    )
    
    # Sort by count and return top 5
    top_standards = sorted(
        standard_counts.values(),
        key=lambda x: x["count"],
        reverse=True
    )[:5]
    
    return top_standards

@router.get("/progress/{job_id}")
async def get_job_progress(
    job_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get real-time progress for a specific job"""
    try:
        job_file = JOBS_DIR / f"{job_id}.json"
        
        if not job_file.exists():
            raise HTTPException(status_code=404, detail="Job not found")
        
        with open(job_file, 'r') as f:
            job_data = json.load(f)
        
        # Check ownership
        if job_data.get("user_id") != current_user.get("user_id"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "success": True,
            "data": {
                "job_id": job_id,
                "status": job_data.get("status"),
                "progress": job_data.get("progress", 0),
                "description": job_data.get("description", ""),
                "updated_at": job_data.get("updated_at"),
                "results": job_data.get("results") if job_data.get("status") == "completed" else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Job progress error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get job progress")

# Append these methods to the router class
router._calculate_daily_activity = _calculate_daily_activity
router._get_top_mapped_standards = _get_top_mapped_standards