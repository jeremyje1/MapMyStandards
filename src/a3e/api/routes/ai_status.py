"""
AI Service Status API

Provides endpoints for monitoring AI provider status and capabilities.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from ...services.ai_service import get_ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

@router.get("/status")
async def get_ai_status():
    """Get AI service status and available providers"""
    
    try:
        ai_service = get_ai_service()
        status = ai_service.get_status()
        
        return {
            "success": True,
            "data": {
                **status,
                "message": "AI service operational" if status['ai_enabled'] else "No AI providers configured"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get AI status: {e}")
        return {
            "success": False,
            "data": {
                "ai_enabled": False,
                "error": str(e)
            }
        }

@router.get("/providers")
async def get_ai_providers():
    """Get detailed information about available AI providers"""
    
    try:
        ai_service = get_ai_service()
        status = ai_service.get_status()
        
        providers = []
        
        if status['anthropic_available']:
            providers.append({
                "name": "Anthropic Claude",
                "status": "active",
                "role": "primary" if status['primary_provider'] == 'anthropic' else "fallback",
                "model": "claude-3-haiku-20240307",
                "capabilities": [
                    "Document analysis",
                    "Evidence mapping",
                    "Standard compliance checking",
                    "Gap identification"
                ]
            })
        
        if status['openai_available']:
            providers.append({
                "name": "OpenAI GPT",
                "status": "active",
                "role": "primary" if status['primary_provider'] == 'openai' else "fallback",
                "model": "gpt-4o-mini",
                "capabilities": [
                    "Document analysis",
                    "Evidence mapping",
                    "Standard compliance checking",
                    "Gap identification"
                ]
            })
        
        return {
            "success": True,
            "data": {
                "total_providers": len(providers),
                "providers": providers,
                "failover_enabled": len(providers) > 1
            }
        }
    except Exception as e:
        logger.error(f"Failed to get provider info: {e}")
        raise HTTPException(status_code=500, detail=str(e))