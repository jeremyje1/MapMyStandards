"""
Evidence Mapping API Routes with Database Support

Provides endpoints for retrieving and managing evidence-to-standard mappings using the database.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update, delete
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json
import uuid

from ..dependencies import get_current_user, get_async_db
from ...models.database_schema import StandardMapping, Document, AccreditationStandard, Institution
from ...core.database import AsyncSession as DBAsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence"])

@router.get("/mappings/db")
async def get_evidence_mappings_db(
    accreditor: Optional[str] = Query("SACSCOC", description="Accreditor to filter by"),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all evidence mappings for the current user from database"""
    try:
        user_id = current_user.get("user_id") if current_user else "demo"
        
        # Query for mappings with joins to get document and standard info
        query = (
            select(StandardMapping, Document, AccreditationStandard)
            .join(Document, StandardMapping.document_id == Document.id)
            .join(AccreditationStandard, StandardMapping.standard_id == AccreditationStandard.id)
        )
        
        # Filter by accreditor if specified
        if accreditor:
            query = query.where(AccreditationStandard.accreditor == accreditor.upper())
        
        # Execute query
        result = await db.execute(query)
        mappings_data = result.all()
        
        # Format the response
        mappings = []
        unique_docs = set()
        unique_standards = set()
        
        for mapping, document, standard in mappings_data:
            unique_docs.add(document.id)
            unique_standards.add(standard.id)
            
            mappings.append({
                "id": mapping.id,
                "document_id": mapping.document_id,
                "document_name": document.filename,
                "standard_id": standard.code,
                "standard_title": standard.title,
                "confidence": mapping.confidence,
                "confidence_score": mapping.confidence_score or 0,
                "evidence_strength": mapping.evidence_strength,
                "mapping_method": mapping.mapping_method,
                "is_verified": mapping.is_verified,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None
            })
        
        # Calculate coverage percentage
        total_standards_query = select(func.count(AccreditationStandard.id))
        if accreditor:
            total_standards_query = total_standards_query.where(AccreditationStandard.accreditor == accreditor.upper())
        
        total_standards_result = await db.execute(total_standards_query)
        total_standards_count = total_standards_result.scalar() or 1
        
        coverage_percentage = (len(unique_standards) / total_standards_count) * 100 if total_standards_count > 0 else 0
        
        return {
            "success": True,
            "data": {
                "accreditor": accreditor,
                "total_documents": len(unique_docs),
                "total_standards": len(unique_standards),
                "total_standards_available": total_standards_count,
                "mappings": mappings,
                "coverage_percentage": round(coverage_percentage, 2),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting evidence mappings from database: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve mappings")

@router.get("/mappings/by-standard/{standard_code}")
async def get_mappings_by_standard_code(
    standard_code: str,
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all documents mapped to a specific standard by its code"""
    try:
        # First find the standard by code
        standard_query = select(AccreditationStandard).where(
            AccreditationStandard.code == standard_code
        )
        standard_result = await db.execute(standard_query)
        standard = standard_result.scalar_one_or_none()
        
        if not standard:
            return {
                "success": True,
                "data": {
                    "standard_id": standard_code,
                    "documents": [],
                    "total_evidence": 0,
                    "average_relevance": 0
                }
            }
        
        # Query for mappings with document info
        query = (
            select(StandardMapping, Document)
            .join(Document, StandardMapping.document_id == Document.id)
            .where(StandardMapping.standard_id == standard.id)
        )
        
        result = await db.execute(query)
        mappings_data = result.all()
        
        # Format documents with mapping details
        documents = []
        total_confidence = 0
        
        for mapping, document in mappings_data:
            confidence_score = mapping.confidence_score or 75
            total_confidence += confidence_score
            
            documents.append({
                "id": document.id,
                "name": document.filename,
                "upload_date": document.uploaded_at.isoformat() if document.uploaded_at else None,
                "type": document.document_type or "document",
                "relevance_score": confidence_score,
                "evidence_summary": mapping.evidence_text or "",
                "mapping_confidence": mapping.confidence or "medium",
                "evidence_strength": mapping.evidence_strength,
                "page_numbers": mapping.page_numbers or [],
                "is_verified": mapping.is_verified,
                "mapping_method": mapping.mapping_method
            })
        
        average_relevance = (total_confidence / len(documents)) if documents else 0
        
        return {
            "success": True,
            "data": {
                "standard_id": standard_code,
                "standard_title": standard.title,
                "documents": documents,
                "total_evidence": len(documents),
                "average_relevance": round(average_relevance, 2)
            }
        }
    except Exception as e:
        logger.error(f"Error getting mappings for standard {standard_code}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve standard mappings")

@router.post("/mappings/db")
async def create_mapping_db(
    mapping_data: Dict[str, Any] = Body(...),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Create a new evidence-to-standard mapping in the database"""
    try:
        user_id = current_user.get("user_id") if current_user else "demo"
        
        # Validate that document exists
        document_result = await db.execute(
            select(Document).where(Document.id == mapping_data.get("document_id"))
        )
        document = document_result.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Find standard by code
        standard_code = mapping_data.get("standard_id")
        standard_result = await db.execute(
            select(AccreditationStandard).where(
                AccreditationStandard.code == standard_code
            )
        )
        standard = standard_result.scalar_one_or_none()
        if not standard:
            raise HTTPException(status_code=404, detail="Standard not found")
        
        # Get institution_id from document
        institution_id = document.institution_id
        if not institution_id:
            # Try to get from user's default institution
            # For now, use a placeholder
            institution_id = "default-institution-id"
        
        # Check if mapping already exists
        existing_result = await db.execute(
            select(StandardMapping).where(
                and_(
                    StandardMapping.document_id == document.id,
                    StandardMapping.standard_id == standard.id
                )
            )
        )
        existing_mapping = existing_result.scalar_one_or_none()
        
        if existing_mapping:
            # Update existing mapping
            existing_mapping.confidence = mapping_data.get("mapping_confidence", "medium")
            existing_mapping.confidence_score = mapping_data.get("relevance_score", 75)
            existing_mapping.evidence_text = mapping_data.get("evidence_summary", "")
            existing_mapping.mapping_method = mapping_data.get("mapping_method", "manual")
            existing_mapping.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(existing_mapping)
            
            return {
                "success": True,
                "data": {
                    "id": existing_mapping.id,
                    "document_id": document.id,
                    "standard_id": standard_code,
                    "status": "updated",
                    "message": "Mapping updated successfully"
                }
            }
        else:
            # Create new mapping
            new_mapping = StandardMapping(
                id=str(uuid.uuid4()),
                document_id=document.id,
                standard_id=standard.id,
                institution_id=institution_id,
                confidence=mapping_data.get("mapping_confidence", "medium"),
                confidence_score=mapping_data.get("relevance_score", 75),
                evidence_text=mapping_data.get("evidence_summary", ""),
                mapping_method=mapping_data.get("mapping_method", "manual"),
                evidence_strength=mapping_data.get("evidence_strength", "Adequate"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(new_mapping)
            await db.commit()
            await db.refresh(new_mapping)
            
            return {
                "success": True,
                "data": {
                    "id": new_mapping.id,
                    "document_id": document.id,
                    "standard_id": standard_code,
                    "status": "created",
                    "message": "Mapping created successfully"
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating mapping: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create mapping")

@router.delete("/mappings/db/{mapping_id}")
async def delete_mapping_db(
    mapping_id: str,
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Delete an evidence-to-standard mapping"""
    try:
        # Find the mapping
        result = await db.execute(
            select(StandardMapping).where(StandardMapping.id == mapping_id)
        )
        mapping = result.scalar_one_or_none()
        
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        # Delete the mapping
        await db.delete(mapping)
        await db.commit()
        
        return {
            "success": True,
            "message": "Mapping deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting mapping: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete mapping")

@router.get("/coverage/heatmap/db")
async def get_coverage_heatmap_db(
    accreditor: str = Query(..., description="Accreditor to analyze"),
    current_user: Optional[dict] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get coverage heatmap data from database"""
    try:
        # Get all standards for the accreditor
        standards_result = await db.execute(
            select(AccreditationStandard)
            .where(AccreditationStandard.accreditor == accreditor.upper())
            .order_by(AccreditationStandard.category, AccreditationStandard.code)
        )
        standards = standards_result.scalars().all()
        
        # Get mapping counts for each standard
        mapping_counts_result = await db.execute(
            select(
                StandardMapping.standard_id,
                func.count(StandardMapping.id).label("evidence_count"),
                func.avg(StandardMapping.confidence_score).label("avg_confidence")
            )
            .group_by(StandardMapping.standard_id)
        )
        mapping_counts = {row.standard_id: {
            "count": row.evidence_count,
            "avg_confidence": row.avg_confidence or 0
        } for row in mapping_counts_result}
        
        # Build heatmap data
        heatmap_data = []
        categories = {}
        
        for standard in standards:
            mapping_info = mapping_counts.get(standard.id, {"count": 0, "avg_confidence": 0})
            evidence_count = mapping_info["count"]
            avg_confidence = mapping_info["avg_confidence"]
            
            # Calculate coverage score
            if evidence_count == 0:
                coverage_score = 0
                status = "gap"
            elif evidence_count == 1 and avg_confidence < 70:
                coverage_score = avg_confidence * 0.5
                status = "insufficient"
            elif evidence_count >= 2 and avg_confidence >= 70:
                coverage_score = min(avg_confidence * 1.1, 100)
                status = "complete" if coverage_score >= 90 else "partial"
            else:
                coverage_score = avg_confidence * 0.8
                status = "partial"
            
            category = standard.category or "Other"
            categories[category] = categories.get(category, [])
            categories[category].append(status)
            
            heatmap_data.append({
                "category": category,
                "standard_id": standard.code,
                "standard_title": standard.title,
                "coverage_score": round(coverage_score, 2),
                "evidence_count": evidence_count,
                "avg_confidence": round(avg_confidence, 2),
                "status": status
            })
        
        # Calculate summary
        summary = {
            "fully_covered": len([h for h in heatmap_data if h["status"] == "complete"]),
            "partially_covered": len([h for h in heatmap_data if h["status"] == "partial"]),
            "gaps": len([h for h in heatmap_data if h["status"] == "gap"]),
            "insufficient": len([h for h in heatmap_data if h["status"] == "insufficient"])
        }
        
        return {
            "success": True,
            "data": {
                "accreditor": accreditor,
                "categories": list(categories.keys()),
                "heatmap": heatmap_data,
                "summary": summary,
                "total_standards": len(standards)
            }
        }
    except Exception as e:
        logger.error(f"Error generating coverage heatmap from database: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate heatmap")
