"""
Database-backed Evidence Mapping API

Provides real evidence mappings from the StandardMapping table
to replace the in-memory version used by reports page.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Dict, Any, List, Optional
import logging

from ..dependencies import get_current_user, get_async_db
from ...models.database_schema import (
    StandardMapping, Document, AccreditationStandard, User
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence-mapping"])

@router.get("/map-database")
async def get_evidence_map_from_database(
    accreditor: Optional[str] = Query(None, description="Filter by accreditor"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """
    Get evidence-to-standard mappings from the database.
    Returns the same format as the legacy endpoint but with real data.
    """
    try:
        # Get all documents for the current user
        docs_result = await db.execute(
            select(Document).where(Document.owner_id == current_user.id)
        )
        documents = docs_result.scalars().all()
        
        # Build document metadata
        documents_meta = {}
        for doc in documents:
            documents_meta[doc.filename] = {
                "filename": doc.filename,
                "doc_type": doc.doc_type,
                "trust_score": doc.trust_score,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "id": doc.id
            }
        
        # Get all mappings for the user's documents
        mappings_result = await db.execute(
            select(StandardMapping, Document, AccreditationStandard)
            .join(Document, StandardMapping.document_id == Document.id)
            .join(AccreditationStandard, StandardMapping.standard_id == AccreditationStandard.id)
            .where(Document.owner_id == current_user.id)
        )
        mappings_data = mappings_result.all()
        
        # Build the mapping structure
        mapping: Dict[str, List[Dict[str, Any]]] = {}
        
        for std_mapping, document, standard in mappings_data:
            # Apply accreditor filter if specified
            if accreditor and standard.accreditor.upper() != accreditor.upper():
                continue
            
            # Use standard code as key (matching legacy format)
            standard_code = standard.code
            
            mapping.setdefault(standard_code, []).append({
                "filename": document.filename,
                "doc_type": document.doc_type,
                "accreditor": standard.accreditor,
                "confidence": std_mapping.confidence_score,
                "text": std_mapping.mapped_text[:200] if std_mapping.mapped_text else None,
                "snippet": std_mapping.mapped_text[:200] if std_mapping.mapped_text else None,
                "is_verified": std_mapping.is_verified,
                "mapped_at": std_mapping.created_at.isoformat() if std_mapping.created_at else None
            })
        
        # Build standards summary
        standards_list: List[Dict[str, Any]] = []
        for sid, arr in mapping.items():
            if not arr:
                continue
            confs = [float(m.get("confidence") or 0.0) for m in arr if isinstance(m.get("confidence"), (int, float))]
            avg_conf = float(sum(confs) / len(confs)) if confs else 0.0
            verified_count = sum(1 for m in arr if m.get("is_verified"))
            
            standards_list.append({
                "standard_id": sid,
                "evidence_count": len(arr),
                "avg_confidence": round(avg_conf, 2),
                "verified_count": verified_count
            })
        
        # Get total standards for this accreditor
        acc = accreditor or "HLC"
        standards_count_result = await db.execute(
            select(func.count(AccreditationStandard.id))
            .where(AccreditationStandard.accreditor == acc.upper())
        )
        total_standards = standards_count_result.scalar() or 0
        
        # Calculate metrics
        standards_mapped = len(standards_list)
        coverage_rate = round((standards_mapped / total_standards * 100), 1) if total_standards > 0 else 0
        
        # Count statistics
        counts = {
            "documents": len(documents),
            "standards": standards_mapped,
            "mappings": sum(len(arr) for arr in mapping.values()),
            "verified": sum(s.get("verified_count", 0) for s in standards_list)
        }
        
        return {
            "mapping": mapping,
            "documents": list(documents_meta.values()),
            "standards": standards_list,
            "counts": counts,
            "metrics": {
                "coverage_rate": coverage_rate,
                "standards_total": total_standards,
                "standards_mapped": standards_mapped,
                "avg_confidence": round(
                    sum(s.get("avg_confidence", 0) for s in standards_list) / len(standards_list), 2
                ) if standards_list else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching evidence map from database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch evidence map: {str(e)}")


@router.get("/standards/{standard_code}/evidence")
async def get_evidence_for_standard(
    standard_code: str,
    accreditor: Optional[str] = Query("HLC", description="Accreditor code"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Get all evidence mapped to a specific standard"""
    try:
        # Find the standard
        standard_result = await db.execute(
            select(AccreditationStandard).where(
                and_(
                    AccreditationStandard.code == standard_code,
                    AccreditationStandard.accreditor == accreditor.upper()
                )
            )
        )
        standard = standard_result.scalar_one_or_none()
        
        if not standard:
            return {
                "standard_code": standard_code,
                "accreditor": accreditor,
                "evidence": [],
                "count": 0
            }
        
        # Get mappings for this standard
        mappings_result = await db.execute(
            select(StandardMapping, Document)
            .join(Document, StandardMapping.document_id == Document.id)
            .where(
                and_(
                    StandardMapping.standard_id == standard.id,
                    Document.owner_id == current_user.id
                )
            )
        )
        mappings_data = mappings_result.all()
        
        evidence = []
        for mapping, document in mappings_data:
            evidence.append({
                "filename": document.filename,
                "doc_type": document.doc_type,
                "confidence": mapping.confidence_score,
                "text": mapping.mapped_text,
                "is_verified": mapping.is_verified,
                "mapped_at": mapping.created_at.isoformat() if mapping.created_at else None,
                "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None
            })
        
        return {
            "standard_code": standard_code,
            "standard_title": standard.title,
            "accreditor": accreditor,
            "evidence": evidence,
            "count": len(evidence)
        }
        
    except Exception as e:
        logger.error(f"Error fetching evidence for standard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch evidence: {str(e)}")
