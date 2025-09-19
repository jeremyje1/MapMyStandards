"""
Vector admin endpoints: status + reindex standards corpus.

Requires an admin bearer token (shared secret) via ADMIN_API_TOKEN env.
"""

import os
import logging
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Header, Depends

from ...services.standards_graph import standards_graph
from ...main import VECTOR_SERVICE_AVAILABLE, USING_PINECONE

router = APIRouter(prefix="/api/admin/vector", tags=["admin-vector"])
logger = logging.getLogger(__name__)


def _require_admin(authorization: str | None = Header(default=None)):
    expected = os.environ.get("ADMIN_API_TOKEN")
    if not expected:
        # If unset, do not expose endpoints publicly
        raise HTTPException(status_code=403, detail="Admin API disabled")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return True


@router.get("/status")
async def vector_status(_: bool = Depends(_require_admin)):
    try:
        status: Dict[str, Any] = {
            "vector_service_available": VECTOR_SERVICE_AVAILABLE,
            "using_pinecone": USING_PINECONE,
        }
        try:
            # Count known standards in graph
            totals = standards_graph.get_graph_stats()
            status["graph_nodes"] = totals.get("total_nodes")
            status["graph_edges"] = totals.get("total_edges")
            status["accreditors"] = list(standards_graph.accreditor_roots.keys())
        except Exception as e:
            status["graph_error"] = str(e)
        return {"success": True, "status": status}
    except Exception as e:
        logger.error(f"Vector status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get vector status")


@router.post("/reindex")
async def vector_reindex(_: bool = Depends(_require_admin)):
    if not VECTOR_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Vector service not available")
    try:
        # Collect standards from graph as simple docs
        docs: List[Dict[str, Any]] = []
        for node_id, node in standards_graph.nodes.items():
            if node.level != "standard":
                continue
            docs.append({
                "id": node_id,
                "title": f"{node.accreditor} {node.standard_id}: {node.title}",
                "description": node.description,
                "content": node.text_content,
                "type": "standard",
                "source": node.accreditor,
            })

        # Get vector service instance from main app module
        from ...main import VectorService  # type: ignore
        vs = VectorService()
        init_ok = await vs.initialize()
        if not init_ok:
            raise HTTPException(status_code=503, detail="Failed to initialize vector service")

        # Index documents in batches
        await vs.index_documents(docs, batch_size=100)

        return {"success": True, "indexed": len(docs)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Vector reindex error: {e}")
        raise HTTPException(status_code=500, detail="Vector reindex failed")
