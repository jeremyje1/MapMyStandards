"""
Database services for MapMyStandards trial platform
Production-ready CRUD operations with Railway PostgreSQL
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import text, func, and_, or_
from sqlalchemy.orm import selectinload
import json
import uuid

from ..models import (
    User, Accreditor, Standard
)
from ..models.database_schema import (
    StandardMapping, Report
)
# TODO: File, Job, SystemMetrics models need to be created or services need to be updated
# Temporarily creating placeholder classes to avoid import errors
class File:
    pass

class Job:
    pass

class SystemMetrics:
    pass
from .connection import db_manager

logger = logging.getLogger(__name__)

class UserService:
    """User management service"""
    
    @staticmethod
    async def get_or_create_user(user_id: str, email: str = None, name: str = None) -> User:
        """Get existing user or create new trial user"""
        async with db_manager.get_session() as session:
            # Try to find existing user
            result = await session.execute(
                text("SELECT * FROM users WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            user_data = result.fetchone()
            
            if user_data:
                return User(**dict(user_data._mapping))
            
            # Create new trial user
            user = User(
                user_id=user_id,
                email=email or f"{user_id}@trial.mapmystandards.ai",
                name=name,
                subscription_tier="trial",
                trial_expires_at=datetime.utcnow() + timedelta(days=14)
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"✅ Created trial user: {user_id}")
            return user
    
    @staticmethod
    async def get_user_metrics(user_id: str) -> Dict[str, Any]:
        """Get comprehensive user metrics for dashboard"""
        async with db_manager.get_session() as session:
            # Get user info
            user_result = await session.execute(
                text("SELECT * FROM users WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            user = user_result.fetchone()
            
            if not user:
                return {}
            
            # Count documents analyzed (completed jobs)
            docs_result = await session.execute(
                text("SELECT COUNT(*) FROM jobs WHERE user_id = :user_id AND status = 'completed'"),
                {"user_id": user_id}
            )
            documents_analyzed = docs_result.scalar() or 0
            
            # Count processing documents
            processing_result = await session.execute(
                text("SELECT COUNT(*) FROM jobs WHERE user_id = :user_id AND status IN ('queued', 'extracting', 'embedding', 'matching', 'analyzing')"),
                {"user_id": user_id}
            )
            documents_processing = processing_result.scalar() or 0
            
            # Count unique standards mapped
            standards_result = await session.execute(
                text("""
                    SELECT COUNT(DISTINCT sm.standard_id) 
                    FROM standard_mappings sm 
                    JOIN jobs j ON sm.job_id = j.job_id 
                    WHERE j.user_id = :user_id AND j.status = 'completed'
                """),
                {"user_id": user_id}
            )
            standards_mapped = standards_result.scalar() or 0
            
            # Get total SACSCOC standards for percentage
            total_result = await session.execute(
                text("SELECT COUNT(*) FROM standards WHERE accreditor_id = 'sacscoc'")
            )
            total_standards = total_result.scalar() or 12
            
            # Count reports generated
            reports_result = await session.execute(
                text("SELECT COUNT(*) FROM reports WHERE user_id = :user_id AND status = 'completed'"),
                {"user_id": user_id}
            )
            reports_generated = reports_result.scalar() or 0
            
            # Count pending reports
            reports_pending_result = await session.execute(
                text("SELECT COUNT(*) FROM reports WHERE user_id = :user_id AND status IN ('queued', 'generating')"),
                {"user_id": user_id}
            )
            reports_pending = reports_pending_result.scalar() or 0
            
            # Calculate compliance score
            compliance_score = min(int((standards_mapped / total_standards) * 100), 100) if standards_mapped else 0
            
            # Calculate trial days remaining
            trial_expires = user.trial_expires_at if hasattr(user, 'trial_expires_at') and user.trial_expires_at else datetime.utcnow() + timedelta(days=14)
            trial_days_remaining = max(0, (trial_expires - datetime.utcnow()).days)
            
            # Time and money saved estimates
            hours_saved_per_doc = 8
            consultant_rate = 150
            time_saved_hours = documents_analyzed * hours_saved_per_doc
            money_saved = time_saved_hours * consultant_rate
            
            return {
                "core_metrics": {
                    "documents_analyzed": documents_analyzed,
                    "documents_processing": documents_processing,
                    "standards_mapped": standards_mapped,
                    "total_standards": total_standards,
                    "reports_generated": reports_generated,
                    "reports_pending": reports_pending
                },
                "performance_metrics": {
                    "compliance_score": compliance_score,
                    "coverage_percentage": int((standards_mapped / total_standards) * 100) if standards_mapped else 0,
                    "time_saved_hours": time_saved_hours,
                    "money_saved_usd": money_saved
                },
                "account_info": {
                    "is_trial": True,
                    "trial_days_remaining": trial_days_remaining,
                    "subscription_tier": "trial"
                },
                "recent_activity": {
                    "last_upload": None,  # TODO: Get from files table
                    "last_report": None,  # TODO: Get from reports table
                    "total_files_uploaded": documents_analyzed + documents_processing,
                    "successful_analyses": documents_analyzed
                }
            }

class FileService:
    """File upload and management service"""
    
    @staticmethod
    async def create_file(
        user_id: str,
        filename: str,
        content: bytes,
        content_type: str,
        title: str = None,
        description: str = None,
        accreditor_id: str = None
    ) -> File:
        """Create new file record with content stored in database"""
        async with db_manager.get_session() as session:
            file = File(
                file_id=f"file_{uuid.uuid4().hex[:16]}",
                user_id=user_id,
                filename=f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}",
                original_filename=filename,
                content_type=content_type,
                file_size=len(content),
                file_content=content,  # Store in database for Railway
                title=title,
                description=description,
                accreditor_id=accreditor_id
            )
            
            session.add(file)
            await session.commit()
            await session.refresh(file)
            
            logger.info(f"✅ Created file: {file.file_id} ({file.file_size} bytes)")
            return file
    
    @staticmethod
    async def get_file(file_id: str, user_id: str = None) -> Optional[File]:
        """Get file by ID with optional user check"""
        async with db_manager.get_session() as session:
            query = "SELECT * FROM files WHERE file_id = :file_id"
            params = {"file_id": file_id}
            
            if user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = user_id
            
            result = await session.execute(text(query), params)
            file_data = result.fetchone()
            
            if file_data:
                return File(**dict(file_data._mapping))
            return None
    
    @staticmethod
    async def get_file_content(file_id: str, user_id: str = None) -> Optional[bytes]:
        """Get file content from database"""
        file = await FileService.get_file(file_id, user_id)
        if file and file.file_content:
            return file.file_content
        return None

class JobService:
    """Background job management service"""
    
    @staticmethod
    async def create_job(user_id: str, file_id: str) -> Job:
        """Create new analysis job"""
        async with db_manager.get_session() as session:
            job = Job(
                job_id=f"job_{uuid.uuid4().hex[:24]}",
                user_id=user_id,
                file_id=file_id,
                status="queued",
                progress=0,
                description="Analysis queued"
            )
            
            session.add(job)
            await session.commit()
            await session.refresh(job)
            
            logger.info(f"✅ Created job: {job.job_id}")
            return job
    
    @staticmethod
    async def get_job(job_id: str, user_id: str = None) -> Optional[Job]:
        """Get job by ID with optional user check"""
        async with db_manager.get_session() as session:
            query = "SELECT * FROM jobs WHERE job_id = :job_id"
            params = {"job_id": job_id}
            
            if user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = user_id
            
            result = await session.execute(text(query), params)
            job_data = result.fetchone()
            
            if job_data:
                return Job(**dict(job_data._mapping))
            return None
    
    @staticmethod
    async def update_job_status(
        job_id: str,
        status: str,
        progress: int = None,
        description: str = None,
        results: Dict[str, Any] = None,
        error_message: str = None
    ) -> bool:
        """Update job status and metadata"""
        async with db_manager.get_session() as session:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if progress is not None:
                update_data["progress"] = progress
            if description:
                update_data["description"] = description
            if results:
                update_data["results"] = json.dumps(results)
            if error_message:
                update_data["error_message"] = error_message
            if status == "completed":
                update_data["completed_at"] = datetime.utcnow()
            
            # Build update query
            set_clause = ", ".join([f"{k} = :{k}" for k in update_data.keys()])
            query = f"UPDATE jobs SET {set_clause} WHERE job_id = :job_id"
            update_data["job_id"] = job_id
            
            result = await session.execute(text(query), update_data)
            await session.commit()
            
            logger.info(f"✅ Updated job {job_id}: {status} ({progress}%)")
            return result.rowcount > 0
    
    @staticmethod
    async def complete_job_with_mappings(
        job_id: str,
        mapped_standards: List[Dict[str, Any]]
    ) -> bool:
        """Complete job and create standard mappings"""
        async with db_manager.get_session() as session:
            # Update job status
            await JobService.update_job_status(
                job_id, 
                "completed", 
                100, 
                "Analysis complete",
                {
                    "standards_matched": len(mapped_standards),
                    "total_standards": 12,  # SACSCOC total
                    "confidence_score": sum(s.get("confidence", 0) for s in mapped_standards) / len(mapped_standards) if mapped_standards else 0,
                    "gaps_identified": 12 - len(mapped_standards),
                    "coverage_percentage": int((len(mapped_standards) / 12) * 100),
                    "mapped_standards": mapped_standards
                }
            )
            
            # Create standard mappings
            for std in mapped_standards:
                mapping = StandardMapping(
                    mapping_id=f"map_{uuid.uuid4().hex[:16]}",
                    job_id=job_id,
                    standard_id=std.get("standard_id"),
                    confidence_score=std.get("confidence", 0.0),
                    matched_text=std.get("matched_text", ""),
                    text_spans=std.get("text_spans", [])
                )
                session.add(mapping)
            
            await session.commit()
            logger.info(f"✅ Completed job {job_id} with {len(mapped_standards)} mappings")
            return True

class ReportService:
    """Report generation and management service"""
    
    @staticmethod
    async def create_report(
        user_id: str,
        report_type: str,
        parameters: Dict[str, Any] = None,
        title: str = None
    ) -> Report:
        """Create new report generation request"""
        async with db_manager.get_session() as session:
            report = Report(
                report_id=f"rpt_{uuid.uuid4().hex[:24]}",
                user_id=user_id,
                type=report_type,
                status="queued",
                progress=0,
                title=title or f"{report_type.replace('_', ' ').title()} Report",
                parameters=parameters
            )
            
            session.add(report)
            await session.commit()
            await session.refresh(report)
            
            logger.info(f"✅ Created report: {report.report_id} ({report_type})")
            return report
    
    @staticmethod
    async def get_report(report_id: str, user_id: str = None) -> Optional[Report]:
        """Get report by ID with optional user check"""
        async with db_manager.get_session() as session:
            query = "SELECT * FROM reports WHERE report_id = :report_id"
            params = {"report_id": report_id}
            
            if user_id:
                query += " AND user_id = :user_id"
                params["user_id"] = user_id
            
            result = await session.execute(text(query), params)
            report_data = result.fetchone()
            
            if report_data:
                return Report(**dict(report_data._mapping))
            return None
    
    @staticmethod
    async def update_report_status(
        report_id: str,
        status: str,
        progress: int = None,
        content: bytes = None,
        filename: str = None,
        error_message: str = None
    ) -> bool:
        """Update report status and content"""
        async with db_manager.get_session() as session:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if progress is not None:
                update_data["progress"] = progress
            if content:
                update_data["content"] = content
                update_data["file_size"] = len(content)
            if filename:
                update_data["filename"] = filename
            if error_message:
                update_data["error_message"] = error_message
            if status == "completed":
                update_data["completed_at"] = datetime.utcnow()
            
            # Build update query
            set_clause = ", ".join([f"{k} = :{k}" for k in update_data.keys()])
            query = f"UPDATE reports SET {set_clause} WHERE report_id = :report_id"
            update_data["report_id"] = report_id
            
            result = await session.execute(text(query), update_data)
            await session.commit()
            
            logger.info(f"✅ Updated report {report_id}: {status} ({progress}%)")
            return result.rowcount > 0
    
    @staticmethod
    async def get_report_content(report_id: str, user_id: str = None) -> Optional[bytes]:
        """Get report PDF content"""
        report = await ReportService.get_report(report_id, user_id)
        if report and report.content:
            return report.content
        return None

class StandardService:
    """Standards and accreditor management service"""
    
    @staticmethod
    async def get_standards(
        accreditor_id: str = None,
        category: str = None,
        search: str = None,
        limit: int = 100
    ) -> List[Standard]:
        """Get standards with optional filtering"""
        async with db_manager.get_session() as session:
            query = "SELECT * FROM standards WHERE 1=1"
            params = {}
            
            if accreditor_id:
                query += " AND UPPER(accreditor_id) = UPPER(:accreditor_id)"
                params["accreditor_id"] = accreditor_id
            
            if category:
                query += " AND LOWER(category) LIKE LOWER(:category)"
                params["category"] = f"%{category}%"
            
            if search:
                query += " AND (LOWER(title) LIKE LOWER(:search) OR LOWER(description) LIKE LOWER(:search) OR LOWER(code) LIKE LOWER(:search))"
                params["search"] = f"%{search}%"
            
            query += f" ORDER BY code LIMIT :limit"
            params["limit"] = limit
            
            result = await session.execute(text(query), params)
            standards_data = result.fetchall()
            
            return [Standard(**dict(row._mapping)) for row in standards_data]
    
    @staticmethod
    async def get_accreditors() -> List[Accreditor]:
        """Get all accreditors"""
        async with db_manager.get_session() as session:
            result = await session.execute(text("SELECT * FROM accreditors ORDER BY acronym"))
            accreditors_data = result.fetchall()
            
            return [Accreditor(**dict(row._mapping)) for row in accreditors_data]