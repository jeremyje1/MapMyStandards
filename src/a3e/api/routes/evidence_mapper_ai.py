"""EvidenceMapper API backed by the new AI pipeline."""

from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import feature_enabled, get_ai_session, get_ai_settings
from ..models import EvidenceMapRequest, EvidenceMapResponse
from ...services.ai_evidence_mapper import EvidenceMapperService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evidence", tags=["EvidenceMapper"])


@router.post("/map", response_model=EvidenceMapResponse)
async def map_evidence(
    payload: EvidenceMapRequest,
    _=Depends(feature_enabled("FEATURE_EVIDENCE_MAPPER")),
    session: AsyncSession = Depends(get_ai_session),
    settings=Depends(get_ai_settings),
):
    service = EvidenceMapperService(settings)
    response = await service.map(session, payload)
    logger.info(
        "Evidence mapping produced %s matches for artifact %s in %sms",
        len(response.matches),
        payload.artifact_id,
        int((datetime.utcnow() - response.computed_at).total_seconds() * 1000),
    )
    return response
