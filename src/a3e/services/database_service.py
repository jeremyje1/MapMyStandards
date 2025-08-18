"""
Database Service for A3E

Provides database operations and connection management using SQLAlchemy.
Handles all CRUD operations for institutions, evidence, standards, and workflows.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select, insert, update, delete, and_, or_
from sqlalchemy.orm import selectinload
import json
from datetime import datetime

from ..core.config import settings
from ..models import (
    Institution, Evidence, Standard, Accreditor, AgentWorkflow, 
    GapAnalysis, Narrative, AuditLog, ProcessingStatus, EvidenceType
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Database service for A3E system"""
    
    def __init__(self, database_url: str):
        # Normalize and adapt URL for async usage
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("sqlite://") and "+aiosqlite" not in database_url:
            # Use aiosqlite driver for async support
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
        
        self.database_url = database_url
        self.engine = None
        self.async_session = None
    
    async def initialize(self):
        """Initialize database connection and session factory"""
        try:
            engine_args = {
                "echo": getattr(settings, 'is_development', False)
            }
            # Only pass pool sizing for non-sqlite databases
            if not self.database_url.startswith("sqlite"):
                engine_args.update({
                    "pool_size": settings.database_pool_size,
                    "max_overflow": settings.database_max_overflow
                })
            self.engine = create_async_engine(self.database_url, **engine_args)
            
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            logger.info("✅ Database service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    # Additional methods for API routes
    async def list_standards(
        self,
        accreditor_id: Optional[str] = None,
        category: Optional[str] = None,
        is_required: Optional[bool] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Standard]:
        """List standards with filters"""
        try:
            query = select(Standard).where(Standard.is_active == True)
            
            if accreditor_id:
                query = query.where(Standard.accreditor_id == accreditor_id)
            
            if category:
                query = query.where(Standard.category == category)
            
            if is_required is not None:
                query = query.where(Standard.is_required == is_required)
            
            if search:
                query = query.where(
                    or_(
                        Standard.title.ilike(f"%{search}%"),
                        Standard.description.ilike(f"%{search}%")
                    )
                )
            
            query = query.offset(offset).limit(limit)
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error listing standards: {e}")
            raise
    
    async def create_standard(self, standard_data: Dict[str, Any]) -> Standard:
        """Create a new standard"""
        try:
            standard = Standard(**standard_data)
            self.session.add(standard)
            await self.session.commit()
            await self.session.refresh(standard)
            return standard
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating standard: {e}")
            raise
    
    async def get_accreditor_standards_stats(self, accreditor_id: str) -> Dict[str, Any]:
        """Get statistics for an accreditor's standards"""
        try:
            query = select(Standard).where(
                Standard.accreditor_id == accreditor_id,
                Standard.is_active == True
            )
            result = await self.session.execute(query)
            standards = result.scalars().all()
            
            total = len(standards)
            required = len([s for s in standards if s.is_required])
            optional = total - required
            categories = list(set(s.category for s in standards))
            
            return {
                "total": total,
                "required": required,
                "optional": optional,
                "categories": categories
            }
            
        except Exception as e:
            logger.error(f"Error getting accreditor standards stats: {e}")
            return {"total": 0, "required": 0, "optional": 0, "categories": []}
    
    async def get_standard_categories(self, accreditor_id: Optional[str] = None) -> List[str]:
        """Get list of all standard categories"""
        try:
            query = select(Standard.category).distinct()
            
            if accreditor_id:
                query = query.where(Standard.accreditor_id == accreditor_id)
            
            query = query.where(Standard.is_active == True)
            result = await self.session.execute(query)
            return [row[0] for row in result.all()]
            
        except Exception as e:
            logger.error(f"Error getting standard categories: {e}")
            return []
    
    async def search_standards(
        self,
        query: str,
        accreditor_id: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50
    ) -> List[Standard]:
        """Search standards using full-text search"""
        try:
            search_query = select(Standard).where(
                Standard.is_active == True,
                or_(
                    Standard.title.ilike(f"%{query}%"),
                    Standard.description.ilike(f"%{query}%")
                )
            )
            
            if accreditor_id:
                search_query = search_query.where(Standard.accreditor_id == accreditor_id)
            
            if category:
                search_query = search_query.where(Standard.category == category)
            
            search_query = search_query.limit(limit)
            result = await self.session.execute(search_query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching standards: {e}")
            return []
    
    async def list_evidence(
        self,
        institution_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        evidence_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        processed: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Evidence]:
        """List evidence with filters"""
        try:
            query = select(Evidence).where(Evidence.is_active == True)
            
            if institution_id:
                query = query.where(Evidence.institution_id == institution_id)
            
            if workflow_id:
                query = query.where(Evidence.workflow_id == workflow_id)
            
            if evidence_type:
                query = query.where(Evidence.evidence_type == evidence_type)
            
            if processed is not None:
                query = query.where(Evidence.processed == processed)
            
            if tags:
                # Check if any of the provided tags are in the evidence tags
                for tag in tags:
                    query = query.where(Evidence.tags.contains([tag]))
            
            query = query.offset(offset).limit(limit)
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error listing evidence: {e}")
            raise
    
    async def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID"""
        try:
            query = select(Evidence).where(Evidence.id == evidence_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting evidence {evidence_id}: {e}")
            return None
    
    async def create_evidence(self, evidence_data: Dict[str, Any]) -> Evidence:
        """Create new evidence"""
        try:
            evidence = Evidence(**evidence_data)
            self.session.add(evidence)
            await self.session.commit()
            await self.session.refresh(evidence)
            return evidence
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating evidence: {e}")
            raise
    
    async def update_evidence(self, evidence_id: str, update_data: Dict[str, Any]) -> Optional[Evidence]:
        """Update evidence"""
        try:
            query = select(Evidence).where(Evidence.id == evidence_id)
            result = await self.session.execute(query)
            evidence = result.scalar_one_or_none()
            
            if evidence:
                for key, value in update_data.items():
                    setattr(evidence, key, value)
                
                await self.session.commit()
                await self.session.refresh(evidence)
                return evidence
            
            return None
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating evidence {evidence_id}: {e}")
            raise
    
    async def get_evidence_types(self) -> List[str]:
        """Get list of all evidence types"""
        try:
            query = select(Evidence.evidence_type).distinct().where(Evidence.is_active == True)
            result = await self.session.execute(query)
            return [row[0] for row in result.all()]
            
        except Exception as e:
            logger.error(f"Error getting evidence types: {e}")
            return []
    
    async def get_institution_evidence_summary(self, institution_id: str) -> Dict[str, Any]:
        """Get evidence summary for an institution"""
        try:
            query = select(Evidence).where(
                Evidence.institution_id == institution_id,
                Evidence.is_active == True
            )
            result = await self.session.execute(query)
            evidence_list = result.scalars().all()
            
            total = len(evidence_list)
            processed = len([e for e in evidence_list if e.processed])
            by_type = {}
            for evidence in evidence_list:
                by_type[evidence.evidence_type] = by_type.get(evidence.evidence_type, 0) + 1
            
            return {
                "total_evidence": total,
                "processed_evidence": processed,
                "unprocessed_evidence": total - processed,
                "by_type": by_type
            }
            
        except Exception as e:
            logger.error(f"Error getting institution evidence summary: {e}")
            return {"total_evidence": 0, "processed_evidence": 0, "unprocessed_evidence": 0, "by_type": {}}
    
    async def list_workflows(
        self,
        institution_id: Optional[str] = None,
        accreditor_id: Optional[str] = None,
        workflow_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AgentWorkflow]:
        """List workflows with filters"""
        try:
            query = select(AgentWorkflow).where(AgentWorkflow.is_active == True)
            
            if institution_id:
                query = query.where(AgentWorkflow.institution_id == institution_id)
            
            if accreditor_id:
                query = query.where(AgentWorkflow.accreditor_id == accreditor_id)
            
            if workflow_type:
                query = query.where(AgentWorkflow.workflow_type == workflow_type)
            
            if status:
                query = query.where(AgentWorkflow.status == status)
            
            query = query.offset(offset).limit(limit)
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[AgentWorkflow]:
        """Get workflow by ID"""
        try:
            query = select(AgentWorkflow).where(AgentWorkflow.id == workflow_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting workflow {workflow_id}: {e}")
            return None
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> AgentWorkflow:
        """Create new workflow"""
        try:
            workflow = AgentWorkflow(**workflow_data)
            self.session.add(workflow)
            await self.session.commit()
            await self.session.refresh(workflow)
            return workflow
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating workflow: {e}")
            raise
    
    async def update_workflow(self, workflow_id: str, update_data: Dict[str, Any]) -> Optional[AgentWorkflow]:
        """Update workflow"""
        try:
            query = select(AgentWorkflow).where(AgentWorkflow.id == workflow_id)
            result = await self.session.execute(query)
            workflow = result.scalar_one_or_none()
            
            if workflow:
                for key, value in update_data.items():
                    setattr(workflow, key, value)
                
                await self.session.commit()
                await self.session.refresh(workflow)
                return workflow
            
            return None
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating workflow {workflow_id}: {e}")
            raise
    
    async def get_workflow_statistics(self, workflow_id: str) -> Dict[str, Any]:
        """Get statistics for a specific workflow"""
        try:
            # Get evidence count for this workflow
            evidence_query = select(Evidence).where(
                Evidence.workflow_id == workflow_id,
                Evidence.is_active == True
            )
            evidence_result = await self.session.execute(evidence_query)
            evidence_count = len(evidence_result.scalars().all())
            
            # Get mapping count for this workflow
            mapping_query = select(GapAnalysis).where(
                GapAnalysis.workflow_id == workflow_id
            )
            mapping_result = await self.session.execute(mapping_query)
            mapping_count = len(mapping_result.scalars().all())
            
            return {
                "evidence_count": evidence_count,
                "mapping_count": mapping_count
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow statistics: {e}")
            return {"evidence_count": 0, "mapping_count": 0}
    
    async def get_workflow_mappings(self, workflow_id: str) -> List[GapAnalysis]:
        """Get all mappings for a workflow"""
        try:
            query = select(GapAnalysis).where(GapAnalysis.workflow_id == workflow_id)
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting workflow mappings: {e}")
            return []
    
    async def get_all_workflow_statistics(
        self,
        institution_id: Optional[str] = None,
        accreditor_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get comprehensive workflow statistics"""
        try:
            query = select(AgentWorkflow).where(AgentWorkflow.is_active == True)
            
            if institution_id:
                query = query.where(AgentWorkflow.institution_id == institution_id)
            
            if accreditor_id:
                query = query.where(AgentWorkflow.accreditor_id == accreditor_id)
            
            result = await self.session.execute(query)
            workflows = result.scalars().all()
            
            total = len(workflows)
            active = len([w for w in workflows if w.status == "running"])
            completed = len([w for w in workflows if w.status == "completed"])
            failed = len([w for w in workflows if w.status == "failed"])
            
            by_type = {}
            by_status = {}
            by_institution = {}
            
            for workflow in workflows:
                by_type[workflow.workflow_type] = by_type.get(workflow.workflow_type, 0) + 1
                by_status[workflow.status] = by_status.get(workflow.status, 0) + 1
                by_institution[str(workflow.institution_id)] = by_institution.get(str(workflow.institution_id), 0) + 1
            
            return {
                "total_workflows": total,
                "active_workflows": active,
                "completed_workflows": completed,
                "failed_workflows": failed,
                "by_type": by_type,
                "by_status": by_status,
                "by_institution": by_institution
            }
            
        except Exception as e:
            logger.error(f"Error getting all workflow statistics: {e}")
            return {
                "total_workflows": 0,
                "active_workflows": 0,
                "completed_workflows": 0,
                "failed_workflows": 0,
                "by_type": {},
                "by_status": {},
                "by_institution": {}
            }
    
    async def close(self):
        """Close database connection"""
        if hasattr(self, 'session') and self.session:
            await self.session.close()
        if hasattr(self, 'engine') and self.engine:
            await self.engine.dispose()
    
    async def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            async with self.async_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute raw SQL query"""
        try:
            async with self.async_session() as session:
                result = await session.execute(text(query), params or {})
                await session.commit()
                return result
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def fetch_all(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all results from a query"""
        try:
            async with self.async_session() as session:
                result = await session.execute(text(query), params or {})
                return [dict(row._mapping) for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Fetch all failed: {e}")
            return []
    
    async def fetch_one(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch single result from a query"""
        try:
            async with self.async_session() as session:
                result = await session.execute(text(query), params or {})
                row = result.fetchone()
                return dict(row._mapping) if row else None
        except Exception as e:
            logger.error(f"Fetch one failed: {e}")
            return None
    
    # Institution operations
    async def create_institution(self, institution_data: Dict[str, Any]) -> Institution:
        """Create a new institution"""
        try:
            async with self.async_session() as session:
                institution = Institution(**institution_data)
                session.add(institution)
                await session.commit()
                await session.refresh(institution)
                return institution
        except Exception as e:
            logger.error(f"Failed to create institution: {e}")
            raise
    
    async def get_institution(self, institution_id: str) -> Optional[Institution]:
        """Get institution by ID"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Institution)
                    .where(Institution.id == institution_id)
                    .options(selectinload(Institution.accreditors))
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get institution: {e}")
            return None
    
    async def list_institutions(
        self,
        state: Optional[str] = None,
        institution_types: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Institution]:
        """List institutions with optional filters"""
        try:
            async with self.async_session() as session:
                query = select(Institution).where(Institution.is_active == True)
                
                if state:
                    query = query.where(Institution.state == state.upper())
                
                if institution_types:
                    # JSON array contains any of the specified types
                    type_conditions = []
                    for inst_type in institution_types:
                        type_conditions.append(
                            Institution.institution_types.op('?')([inst_type])
                        )
                    query = query.where(or_(*type_conditions))
                
                query = query.offset(offset).limit(limit)
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to list institutions: {e}")
            return []
    
    # Evidence operations
    async def create_evidence(self, evidence_data: Dict[str, Any]) -> Evidence:
        """Create new evidence item"""
        try:
            async with self.async_session() as session:
                evidence = Evidence(**evidence_data)
                session.add(evidence)
                await session.commit()
                await session.refresh(evidence)
                return evidence
        except Exception as e:
            logger.error(f"Failed to create evidence: {e}")
            raise
    
    async def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Get evidence by ID"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Evidence)
                    .where(Evidence.id == evidence_id)
                    .options(selectinload(Evidence.standards))
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get evidence: {e}")
            return None
    
    async def get_institution_evidence(
        self,
        institution_id: str,
        evidence_type: Optional[EvidenceType] = None,
        processing_status: Optional[ProcessingStatus] = None
    ) -> List[Evidence]:
        """Get all evidence for an institution"""
        try:
            async with self.async_session() as session:
                query = select(Evidence).where(Evidence.institution_id == institution_id)
                
                if evidence_type:
                    query = query.where(Evidence.evidence_type == evidence_type)
                
                if processing_status:
                    query = query.where(Evidence.processing_status == processing_status)
                
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get institution evidence: {e}")
            return []
    
    async def update_evidence_status(
        self,
        evidence_id: str,
        status: ProcessingStatus,
        error_message: Optional[str] = None
    ):
        """Update evidence processing status"""
        try:
            async with self.async_session() as session:
                update_data = {
                    "processing_status": status,
                    "updated_at": datetime.utcnow()
                }
                
                if status == ProcessingStatus.COMPLETED:
                    update_data["processed_at"] = datetime.utcnow()
                elif status == ProcessingStatus.FAILED and error_message:
                    update_data["processing_error"] = error_message
                
                await session.execute(
                    update(Evidence)
                    .where(Evidence.id == evidence_id)
                    .values(**update_data)
                )
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to update evidence status: {e}")
            raise
    
    # Standard operations
    async def get_accreditor_standards(
        self,
        accreditor_id: str,
        institution_types: Optional[List[str]] = None
    ) -> List[Standard]:
        """Get standards for an accreditor, optionally filtered by institution type"""
        try:
            async with self.async_session() as session:
                query = select(Standard).where(Standard.accreditor_id == accreditor_id)
                
                if institution_types:
                    # JSON array contains any of the specified types
                    type_conditions = []
                    for inst_type in institution_types:
                        type_conditions.append(
                            Standard.applicable_institution_types.op('?')([inst_type])
                        )
                    query = query.where(or_(*type_conditions))
                
                query = query.order_by(Standard.order_sequence)
                result = await session.execute(query)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get accreditor standards: {e}")
            return []
    
    async def get_standard(self, standard_id: str) -> Optional[Standard]:
        """Get standard by ID"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Standard)
                    .where(Standard.id == standard_id)
                    .options(selectinload(Standard.accreditor))
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get standard: {e}")
            return None
    
    # Workflow operations
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> AgentWorkflow:
        """Create new agent workflow"""
        try:
            async with self.async_session() as session:
                workflow = AgentWorkflow(**workflow_data)
                session.add(workflow)
                await session.commit()
                await session.refresh(workflow)
                return workflow
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            raise
    
    async def update_workflow(
        self,
        workflow_id: str,
        update_data: Dict[str, Any]
    ):
        """Update workflow with new data"""
        try:
            async with self.async_session() as session:
                update_data["updated_at"] = datetime.utcnow()
                await session.execute(
                    update(AgentWorkflow)
                    .where(AgentWorkflow.id == workflow_id)
                    .values(**update_data)
                )
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to update workflow: {e}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[AgentWorkflow]:
        """Get workflow by ID"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(AgentWorkflow)
                    .where(AgentWorkflow.id == workflow_id)
                    .options(selectinload(AgentWorkflow.institution))
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get workflow: {e}")
            return None
    
    async def list_institution_workflows(
        self,
        institution_id: str,
        limit: int = 50
    ) -> List[AgentWorkflow]:
        """List workflows for an institution"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(AgentWorkflow)
                    .where(AgentWorkflow.institution_id == institution_id)
                    .order_by(AgentWorkflow.created_at.desc())
                    .limit(limit)
                )
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to list institution workflows: {e}")
            return []
    
    async def save_workflow_results(self, results: Dict[str, Any], user_id: str):
        """Save complete workflow results to database"""
        try:
            async with self.async_session() as session:
                # Update workflow record
                workflow_id = results.get("workflow_id")
                final_results = results.get("final_results", {})
                
                if workflow_id:
                    await session.execute(
                        update(AgentWorkflow)
                        .where(AgentWorkflow.id == workflow_id)
                        .values(
                            status=ProcessingStatus.COMPLETED,
                            output_data=final_results,
                            completed_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                    )
                
                # Save gap analysis if present
                gap_analysis = final_results.get("gap_analysis")
                if gap_analysis:
                    gap_data = {
                        "institution_id": results.get("institution_id"),
                        "accreditor_id": results.get("accreditor_id"),
                        "academic_year": "2024-25",  # TODO: Make dynamic
                        "total_standards": gap_analysis.get("gap_summary", {}).get("total_standards", 0),
                        "standards_with_evidence": gap_analysis.get("gap_summary", {}).get("green_compliant", 0),
                        "standards_without_evidence": gap_analysis.get("gap_summary", {}).get("red_gaps", 0),
                        "standards_insufficient_evidence": gap_analysis.get("gap_summary", {}).get("amber_gaps", 0),
                        "gap_details": gap_analysis,
                        "confidence_score": gap_analysis.get("overall_confidence", 0.0),
                        "analyst_type": "agent"
                    }
                    
                    gap_analysis_obj = GapAnalysis(**gap_data)
                    session.add(gap_analysis_obj)
                
                # Save narratives if present
                narratives = final_results.get("narratives", [])
                for narrative_data in narratives:
                    narrative_obj = Narrative(
                        institution_id=results.get("institution_id"),
                        standard_id=narrative_data.get("standard_id"),
                        title=narrative_data.get("title"),
                        content=narrative_data.get("content"),
                        citations=narrative_data.get("citations", []),
                        generated_by="agent",
                        quality_score=narrative_data.get("completeness_score", 0.0),
                        citation_accuracy=0.85,  # Default from verifier
                        version=1,
                        is_current=True
                    )
                    session.add(narrative_obj)
                
                await session.commit()
                logger.info(f"Saved workflow results for {workflow_id}")
                
        except Exception as e:
            logger.error(f"Failed to save workflow results: {e}")
            raise
    
    # Gap Analysis operations
    async def get_latest_gap_analysis(
        self,
        institution_id: str,
        accreditor_id: str
    ) -> Optional[GapAnalysis]:
        """Get the most recent gap analysis for an institution and accreditor"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(GapAnalysis)
                    .where(
                        and_(
                            GapAnalysis.institution_id == institution_id,
                            GapAnalysis.accreditor_id == accreditor_id,
                            GapAnalysis.is_current == True
                        )
                    )
                    .order_by(GapAnalysis.analysis_date.desc())
                    .limit(1)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get gap analysis: {e}")
            return None
    
    # Audit logging
    async def log_audit_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        change_summary: Optional[str] = None
    ):
        """Log an audit event"""
        try:
            async with self.async_session() as session:
                audit_log = AuditLog(
                    event_type=event_type,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    user_id=user_id,
                    old_values=old_values,
                    new_values=new_values,
                    change_summary=change_summary,
                    timestamp=datetime.utcnow()
                )
                session.add(audit_log)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            # Don't raise - audit logging shouldn't break main functionality
    
    # Analytics and reporting
    async def get_institution_statistics(self, institution_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for an institution"""
        try:
            async with self.async_session() as session:
                # Evidence statistics
                evidence_stats = await session.execute(
                    text("""
                        SELECT 
                            evidence_type,
                            processing_status,
                            COUNT(*) as count
                        FROM evidence 
                        WHERE institution_id = :institution_id
                        GROUP BY evidence_type, processing_status
                    """),
                    {"institution_id": institution_id}
                )
                
                # Workflow statistics
                workflow_stats = await session.execute(
                    text("""
                        SELECT 
                            workflow_type,
                            status,
                            COUNT(*) as count,
                            AVG(execution_time_seconds) as avg_execution_time
                        FROM agent_workflows 
                        WHERE institution_id = :institution_id
                        GROUP BY workflow_type, status
                    """),
                    {"institution_id": institution_id}
                )
                
                return {
                    "evidence_statistics": [dict(row._mapping) for row in evidence_stats.fetchall()],
                    "workflow_statistics": [dict(row._mapping) for row in workflow_stats.fetchall()]
                }
        except Exception as e:
            logger.error(f"Failed to get institution statistics: {e}")
            return {}
