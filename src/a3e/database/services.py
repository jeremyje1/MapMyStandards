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
from types import SimpleNamespace as _Obj
from .connection import db_manager

logger = logging.getLogger(__name__)


async def _get_table_columns(session, table_name: str) -> set:
    try:
        res = await session.execute(
            text(
                """
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :t
                """
            ),
            {"t": table_name},
        )
        return {r[0] for r in res.fetchall()}
    except Exception:
        return set()

class UserService:
    """User management service"""
    
    @staticmethod
    async def get_or_create_user(user_id: str, email: str = None, name: str = None) -> User:
        """Get existing user or return a lightweight stub without creating one.
        Avoids schema mismatches and NOT NULL constraints during uploads.
        """
        try:
            async with db_manager.get_session() as session:
                cols_users = await _get_table_columns(session, "users")
                pk_col = "id" if "id" in cols_users else ("user_id" if "user_id" in cols_users else "id")
                # Lookup existing
                result = await session.execute(
                    text(f"SELECT {pk_col} AS id, email, name FROM users WHERE {pk_col} = :user_id"),
                    {"user_id": user_id}
                )
                row = result.fetchone()
                if row:
                    m = row._mapping
                    return _Obj(id=m.get("id"), email=m.get("email"), name=m.get("name"))

                # Create minimal row if not exists (schema-aware)
                cols = cols_users
                candidate = {
                    (pk_col): user_id,
                    "email": email or f"{user_id}@trial.mapmystandards.ai",
                    "name": name or (email.split("@")[0] if email else user_id),
                    "password_hash": "trial-placeholder-hash",
                    "is_trial": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                use_cols = [k for k in candidate.keys() if (not cols) or (k in cols)]
                column_list = ", ".join(use_cols)
                placeholders = ", ".join([f":{c}" for c in use_cols])
                on_conflict_target = pk_col
                sql = f"INSERT INTO users ({column_list}) VALUES ({placeholders}) ON CONFLICT ({on_conflict_target}) DO NOTHING RETURNING {pk_col} AS id, email, name"
                ins = await session.execute(text(sql), {k: candidate[k] for k in use_cols})
                created = ins.fetchone()
                await session.commit()
                if created:
                    m = created._mapping
                    logger.info(f"✅ Created minimal user row for {m.get('id')}")
                    return _Obj(id=m.get("id"), email=m.get("email"), name=m.get("name"))

                # Re-select in case of ON CONFLICT
                result2 = await session.execute(
                    text(f"SELECT {pk_col} AS id, email, name FROM users WHERE {pk_col} = :user_id"),
                    {"user_id": user_id}
                )
                row2 = result2.fetchone()
                if row2:
                    m = row2._mapping
                    return _Obj(id=m.get("id"), email=m.get("email"), name=m.get("name"))
        except Exception as e:
            logger.warning(f"User upsert failed, proceeding with stub: {e}")
        # Fallback stub
        return _Obj(id=user_id, email=email or f"{user_id}@trial.mapmystandards.ai", name=name or user_id)
    
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
    ) -> _Obj:
        """Create new file record in the 'files' table using SQL and return a lightweight object."""
        async with db_manager.get_session() as session:
            file_id = f"file_{uuid.uuid4().hex[:16]}"
            new_name = f"{file_id}_{filename}"

            cols = await _get_table_columns(session, "files")
            if not cols:
                logger.warning("'files' table not introspectable; attempting blind insert")
            # Build dynamic column/value maps based on available columns
            candidate = {
                "file_id": file_id,
                "user_id": user_id,
                "filename": new_name,
                "original_filename": filename,
                "content_type": content_type,
                "file_size": len(content),
                "file_content": content,
                "title": title,
                "description": description,
                "accreditor_id": accreditor_id,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            use_cols = [k for k in candidate.keys() if (not cols) or (k in cols)]
            placeholders = ", ".join([f":{c}" for c in use_cols])
            column_list = ", ".join(use_cols)
            returning = [c for c in ["file_id", "user_id", "filename", "original_filename", "content_type", "file_size", "created_at", "updated_at"] if (not cols) or (c in cols)]
            returning_sql = ", ".join(returning) if returning else "file_id"

            sql = f"INSERT INTO files ({column_list}) VALUES ({placeholders}) RETURNING {returning_sql}"
            params = {k: candidate[k] for k in use_cols}
            result = await session.execute(text(sql), params)
            row = result.fetchone()
            await session.commit()
            if not row:
                raise RuntimeError("Failed to insert file record")
            m = row._mapping
            logger.info(f"✅ Created file: {m.get('file_id')} ({m.get('file_size')})")
            return _Obj(**dict(m))
    
    @staticmethod
    async def get_file(file_id: str, user_id: str = None) -> Optional[_Obj]:
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
                return _Obj(**dict(file_data._mapping))
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
    async def create_job(user_id: str, file_id: str) -> _Obj:
        """Create new analysis job via SQL insert and return a lightweight object"""
        async with db_manager.get_session() as session:
            job_id = f"job_{uuid.uuid4().hex[:24]}"
            cols = await _get_table_columns(session, "jobs")
            candidate = {
                "job_id": job_id,
                "user_id": user_id,
                "file_id": file_id,
                "status": "queued",
                "progress": 0,
                "description": "Analysis queued",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            use_cols = [k for k in candidate.keys() if (not cols) or (k in cols)]
            placeholders = ", ".join([f":{c}" for c in use_cols])
            column_list = ", ".join(use_cols)
            returning = [c for c in ["job_id", "user_id", "file_id", "status", "progress", "description", "created_at", "updated_at"] if (not cols) or (c in cols)]
            returning_sql = ", ".join(returning) if returning else "job_id"

            sql = f"INSERT INTO jobs ({column_list}) VALUES ({placeholders}) RETURNING {returning_sql}"
            result = await session.execute(text(sql), {k: candidate[k] for k in use_cols})
            row = result.fetchone()
            await session.commit()
            if not row:
                raise RuntimeError("Failed to insert job record")
            m = row._mapping
            logger.info(f"✅ Created job: {m.get('job_id')}")
            return _Obj(**dict(m))
    
    @staticmethod
    async def get_job(job_id: str, user_id: str = None) -> Optional[_Obj]:
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
                return _Obj(**dict(job_data._mapping))
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
                update_data["result"] = json.dumps(results)
            if error_message:
                update_data["error_message"] = error_message
            if status == "completed":
                update_data["completed_at"] = datetime.utcnow()
            
            # Build update query
            set_clause = ", ".join([f"{k} = :{k}" for k in update_data.keys()])
            query = f"UPDATE jobs SET {set_clause} WHERE job_id = :job_id"
            update_data["job_id"] = job_id
            
            try:
                result = await session.execute(text(query), update_data)
                await session.commit()
                logger.info(f"✅ Updated job {job_id}: {status} ({progress}%)")
                return result.rowcount > 0
            except Exception as e:
                # Backward-compat: some DBs may use 'results' column name
                if "result" in update_data and "column \"result\"" in str(e).lower():
                    alt_data = dict(update_data)
                    alt_data["results"] = alt_data.pop("result")
                    set_clause_alt = ", ".join([f"{k} = :{k}" for k in alt_data.keys() if k != "job_id"]) 
                    query_alt = f"UPDATE jobs SET {set_clause_alt} WHERE job_id = :job_id"
                    result = await session.execute(text(query_alt), alt_data)
                    await session.commit()
                    logger.info(f"✅ Updated job {job_id} with legacy column: {status} ({progress}%)")
                    return result.rowcount > 0
                raise
    
    @staticmethod
    async def complete_job_with_mappings(
        job_id: str,
        mapped_standards: List[Dict[str, Any]]
    ) -> bool:
        """Complete job and store results on the job row. Skip mapping inserts to avoid schema mismatch."""
        await JobService.update_job_status(
            job_id,
            "completed",
            100,
            "Analysis complete",
            {
                "standards_matched": len(mapped_standards),
                "total_standards": 12,
                "confidence_score": sum(s.get("confidence", 0) for s in mapped_standards) / len(mapped_standards) if mapped_standards else 0,
                "gaps_identified": 12 - len(mapped_standards),
                "coverage_percentage": int((len(mapped_standards) / 12) * 100),
                "mapped_standards": mapped_standards,
            },
        )
        logger.info(f"✅ Completed job {job_id} with {len(mapped_standards)} mappings (stored in job.result)")
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
