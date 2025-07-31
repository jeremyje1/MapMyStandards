"""
Dependency injection for proprietary A³E services
"""

from functools import lru_cache
from typing import Optional
import os
import logging

from .services.proprietary_a3e_service import ProprietaryA3EService
from .services.llm_service import LLMService
from .core import TraceabilityLevel

logger = logging.getLogger(__name__)

@lru_cache()
def get_llm_service() -> LLMService:
    """Get LLM service singleton."""
    return LLMService()

@lru_cache() 
def get_proprietary_a3e_service() -> ProprietaryA3EService:
    """Get proprietary A³E service singleton."""
    
    # Get configuration from environment
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    audit_db_path = os.getenv("AUDIT_DB_PATH", "data/audit/audit_trail.db")
    traceability_level_str = os.getenv("TRACEABILITY_LEVEL", "standard")
    
    # Convert traceability level
    try:
        traceability_level = TraceabilityLevel(traceability_level_str)
    except ValueError:
        traceability_level = TraceabilityLevel.STANDARD
        logger.warning(f"Invalid traceability level '{traceability_level_str}', using default")
    
    # Get LLM service
    llm_service = get_llm_service()
    
    # Create proprietary service
    service = ProprietaryA3EService(
        llm_service=llm_service,
        embedding_model_name=embedding_model,
        audit_db_path=audit_db_path
    )
    
    logger.info("Proprietary A³E service initialized with full capabilities")
    return service
