"""
Pinecone Vector Service for A3E
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)

# Optional imports
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not available - embeddings disabled")
    EMBEDDINGS_AVAILABLE = False
    
    class SentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass
        
        def encode(self, *args, **kwargs):
            return [0.0] * 384  # Return dummy embedding


class PineconeVectorService:
    """Pinecone-based vector service for semantic search"""
    
    def __init__(self):
        self.pc = None
        self.index = None
        self.index_name = "mapmystandards"
        self.embedding_model = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize Pinecone connection and embedding model"""
        try:
            api_key = os.environ.get("PINECONE_API_KEY")
            if not api_key:
                logger.warning("PINECONE_API_KEY not set - vector features disabled")
                return False
            
            # Initialize Pinecone
            self.pc = Pinecone(api_key=api_key)
            
            # Check if index exists, create if not
            existing_indexes = self.pc.list_indexes()
            if self.index_name not in existing_indexes.names():
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,  # for all-MiniLM-L6-v2
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='gcp',
                        region='us-central1'
                    )
                )
            
            self.index = self.pc.Index(self.index_name)
            
            # Initialize embedding model if available
            if EMBEDDINGS_AVAILABLE:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Sentence transformer model loaded")
            else:
                self.embedding_model = SentenceTransformer()  # Dummy
                logger.warning("⚠️ Using dummy embeddings - install sentence-transformers for real embeddings")
            
            self.initialized = True
            logger.info(f"✅ Pinecone vector service initialized with index: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            self.initialized = False
            return False
    
    async def index_documents(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """Index documents for semantic search"""
        if not self.initialized:
            logger.warning("Pinecone not initialized - skipping indexing")
            return
        
        try:
            vectors = []
            for doc in documents:
                # Create text for embedding
                text = f"{doc.get('title', '')} {doc.get('description', '')} {doc.get('content', '')}"
                
                # Generate embedding
                embedding = self.embedding_model.encode(text).tolist()
                
                # Prepare vector data
                vectors.append({
                    "id": str(doc.get('id', '')),
                    "values": embedding,
                    "metadata": {
                        "title": doc.get('title', '')[:500],  # Limit metadata size
                        "type": doc.get('type', 'document'),
                        "source": doc.get('source', ''),
                        "description": doc.get('description', '')[:1000]
                    }
                })
            
            # Upsert in batches
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Indexed batch {i//batch_size + 1}: {len(batch)} documents")
            
            logger.info(f"✅ Successfully indexed {len(vectors)} documents")
            
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise
    
    async def semantic_search(
        self, 
        query: str, 
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search"""
        if not self.initialized:
            logger.warning("Pinecone not initialized - returning empty results")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Perform search
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            # Format results
            search_results = []
            for match in results.matches:
                search_results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def find_similar_standards(
        self,
        evidence_text: str,
        accreditor_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find standards similar to evidence text"""
        filter_dict = {"type": "standard"}
        if accreditor_id:
            filter_dict["accreditor"] = accreditor_id
        
        return await self.semantic_search(evidence_text, top_k, filter_dict)
    
    async def find_similar_evidence(
        self,
        standard_text: str,
        institution_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Find evidence similar to standard text"""
        filter_dict = {"type": "evidence"}
        if institution_id:
            filter_dict["institution_id"] = institution_id
        
        return await self.semantic_search(standard_text, top_k, filter_dict)
    
    async def verify_citation_accuracy(
        self,
        narrative_text: str,
        evidence_text: str,
        cited_excerpt: str
    ) -> float:
        """Verify citation accuracy using cosine similarity"""
        if not self.initialized or not EMBEDDINGS_AVAILABLE:
            return 0.5  # Default score when embeddings not available
        
        try:
            import numpy as np
            
            # Generate embeddings
            narrative_embedding = self.embedding_model.encode(narrative_text)
            evidence_embedding = self.embedding_model.encode(evidence_text)
            excerpt_embedding = self.embedding_model.encode(cited_excerpt)
            
            # Calculate cosine similarities
            def cosine_similarity(a, b):
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
            # Evidence-excerpt similarity is most important
            evidence_excerpt_sim = cosine_similarity(evidence_embedding, excerpt_embedding)
            narrative_excerpt_sim = cosine_similarity(narrative_embedding, excerpt_embedding)
            
            # Weighted average
            accuracy_score = (0.7 * evidence_excerpt_sim + 0.3 * narrative_excerpt_sim)
            
            return float(accuracy_score)
            
        except Exception as e:
            logger.error(f"Failed to verify citation accuracy: {e}")
            return 0.0
    
    async def delete_vectors(self, ids: List[str]):
        """Delete vectors by IDs"""
        if not self.initialized:
            return
        
        try:
            self.index.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} vectors")
        except Exception as e:
            logger.error(f"Failed to delete vectors: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not self.initialized:
            return {"status": "not_initialized"}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                "status": "healthy",
                "total_vectors": stats.total_vector_count,
                "dimensions": stats.dimension,
                "index_name": self.index_name
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"status": "error", "error": str(e)}
    
    async def health_check(self) -> bool:
        """Check if Pinecone service is healthy"""
        if not self.initialized:
            return False
        
        try:
            stats = await self.get_stats()
            return stats.get("status") == "healthy"
        except:
            return False
    
    async def close(self):
        """Close Pinecone connections"""
        # Pinecone client doesn't need explicit closing
        self.initialized = False
        logger.info("Pinecone service closed")