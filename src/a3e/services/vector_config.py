"""
Vector Database Configuration for Semantic Search

Provides configuration for vector database integration when available.
Falls back gracefully when vector services are not available.
"""

from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)

class VectorConfig:
    """Configuration for vector database services"""
    
    def __init__(self):
        self.enabled = False
        self.provider = None
        self.config = {}
        
        # Try to configure based on available services
        self._configure_provider()
    
    def _configure_provider(self):
        """Detect and configure available vector database"""
        
        # Option 1: Milvus (self-hosted or cloud)
        if os.getenv('MILVUS_HOST'):
            try:
                import pymilvus
                self.enabled = True
                self.provider = 'milvus'
                self.config = {
                    'host': os.getenv('MILVUS_HOST', 'localhost'),
                    'port': int(os.getenv('MILVUS_PORT', '19530')),
                    'collection_prefix': os.getenv('MILVUS_COLLECTION_PREFIX', 'a3e')
                }
                logger.info("✅ Milvus vector database configured")
            except ImportError:
                logger.warning("Milvus host configured but pymilvus not installed")
        
        # Option 2: Pinecone (cloud-based)
        elif os.getenv('PINECONE_API_KEY'):
            try:
                import pinecone
                self.enabled = True
                self.provider = 'pinecone'
                self.config = {
                    'api_key': os.getenv('PINECONE_API_KEY'),
                    'environment': os.getenv('PINECONE_ENVIRONMENT', 'us-east-1'),
                    'index_name': os.getenv('PINECONE_INDEX', 'a3e-standards')
                }
                logger.info("✅ Pinecone vector database configured")
            except ImportError:
                logger.warning("Pinecone API key configured but pinecone-client not installed")
        
        # Option 3: Weaviate (self-hosted or cloud)
        elif os.getenv('WEAVIATE_URL'):
            try:
                import weaviate
                self.enabled = True
                self.provider = 'weaviate'
                self.config = {
                    'url': os.getenv('WEAVIATE_URL'),
                    'api_key': os.getenv('WEAVIATE_API_KEY'),
                    'class_prefix': os.getenv('WEAVIATE_CLASS_PREFIX', 'A3E')
                }
                logger.info("✅ Weaviate vector database configured")
            except ImportError:
                logger.warning("Weaviate URL configured but weaviate-client not installed")
        
        # Option 4: ChromaDB (lightweight, embedded option)
        elif os.getenv('ENABLE_CHROMADB', 'false').lower() == 'true':
            try:
                import chromadb
                self.enabled = True
                self.provider = 'chroma'
                self.config = {
                    'persist_directory': os.getenv('CHROMA_PERSIST_DIR', './chroma_db'),
                    'collection_name': os.getenv('CHROMA_COLLECTION', 'a3e_standards')
                }
                logger.info("✅ ChromaDB vector database configured")
            except ImportError:
                logger.warning("ChromaDB enabled but chromadb not installed")
        
        if not self.enabled:
            logger.info("⚠️ No vector database configured - semantic search disabled")
    
    def get_embeddings_model(self) -> Optional[str]:
        """Get the embeddings model to use"""
        if not self.enabled:
            return None
        
        # Use OpenAI embeddings if available
        if os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY'):
            return 'text-embedding-3-small'
        
        # Fall back to open-source embeddings
        return 'sentence-transformers/all-MiniLM-L6-v2'
    
    def is_available(self) -> bool:
        """Check if vector database is available"""
        return self.enabled
    
    def get_config(self) -> Dict[str, Any]:
        """Get vector database configuration"""
        return self.config if self.enabled else {}

# Singleton instance
_vector_config = None

def get_vector_config() -> VectorConfig:
    """Get or create vector configuration"""
    global _vector_config
    if _vector_config is None:
        _vector_config = VectorConfig()
    return _vector_config