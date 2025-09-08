"""
Pinecone Vector Service for A3E
"""

import os
import logging
import json
import hashlib
import numpy as np
import httpx
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec

logger = logging.getLogger(__name__)

# Embedding backends
# Default priority: sentence-transformers > OpenAI > deterministic hash
# Can be overridden with env EMBEDDINGS_BACKEND in {"st"|"sentence-transformers", "openai", "hash"}
EMBEDDING_DIM = 384  # Pinecone index dimension we standardize to

try:
    from sentence_transformers import SentenceTransformer as _STModel
    EMBEDDINGS_BACKEND = "sentence-transformers"
except ImportError:
    _STModel = None  # type: ignore
    EMBEDDINGS_BACKEND = None

class _HashEmbedder:
    """Deterministic lightweight embeddings (no network/deps)."""
    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim

    def encode(self, text, *args, **kwargs):
        if isinstance(text, list):
            return np.array([self._hash_embed(t) for t in text])
        return self._hash_embed(text)

    def _hash_embed(self, text):
        text_bytes = str(text).encode('utf-8')
        embeddings = []
        for i in range(self.dim):
            h = hashlib.sha256(text_bytes + str(i).encode()).digest()
            value = (int.from_bytes(h[:4], 'big') / 2147483647.0) - 1.0
            embeddings.append(value)
        embedding = np.array(embeddings)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        return embedding

class _OpenAIEmbedder:
    """OpenAI embeddings via HTTP with projection to EMBEDDING_DIM (no SDK)."""
    def __init__(self, model: str = "text-embedding-3-small", dim: int = EMBEDDING_DIM):
        self._model = model
        self._dim = dim
        self._api_key = os.environ.get("OPENAI_API_KEY")
        self._org = os.environ.get("OPENAI_ORG") or os.environ.get("OPENAI_ORGANIZATION")
        self._project = os.environ.get("OPENAI_PROJECT")
        self._disabled = os.environ.get("DISABLE_OPENAI_EMBEDDINGS", "0").lower() in ("1", "true", "yes")
        # Build a fixed random projection for dimensionality reduction (seeded)
        rng = np.random.default_rng(42)
        # text-embedding-3-small returns 1536 dims
        self._source_dim = 1536
        self._proj = rng.normal(0, 1, size=(self._source_dim, self._dim)) / np.sqrt(self._dim)
        self._available = bool(self._api_key) and not self._disabled

    def encode(self, text, *args, **kwargs):
        if not self._available:
            return _HashEmbedder(self._dim).encode(text)
        try:
            texts = text if isinstance(text, list) else [text]
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            if self._org:
                headers["OpenAI-Organization"] = self._org
            if self._project:
                headers["OpenAI-Project"] = self._project
            payload = {"model": self._model, "input": texts}
            with httpx.Client(timeout=30.0) as client:
                r = client.post("https://api.openai.com/v1/embeddings", headers=headers, json=payload)
                if r.status_code in (401, 403):
                    # Disable further attempts this process to avoid log spam
                    self._available = False
                    try:
                        err = r.json().get("error", {})
                        code = err.get("code") or err.get("type")
                        msg = err.get("message") or ""
                        logger.warning(f"OpenAI embeddings disabled after {r.status_code} ({code}): {msg}")
                    except Exception:
                        logger.warning(f"OpenAI embeddings disabled after status {r.status_code}")
                    return _HashEmbedder(self._dim).encode(text)
                r.raise_for_status()
                data = r.json()
                vecs = [np.array(item["embedding"]) for item in data.get("data", [])]
            # Project to EMBEDDING_DIM
            reduced = [np.asarray(v[:self._source_dim]) @ self._proj for v in vecs]
            if isinstance(text, list):
                return np.stack(reduced)
            return reduced[0]
        except Exception as e:
            logger.warning(f"OpenAI embedding failed, using hash fallback: {e}")
            return _HashEmbedder(self._dim).encode(text)

def _get_embedder():
    """
    Select embedding backend based on availability and env override.

    Order of resolution:
    1) If EMBEDDINGS_BACKEND env is set, honor it (st | sentence-transformers | openai | hash)
    2) Otherwise, try sentence-transformers, then OpenAI, then hash.
    """
    backend_pref = (os.environ.get("EMBEDDINGS_BACKEND") or "").strip().lower()

    def _try_st():
        if _STModel is None:
            return None
        try:
            model = _STModel('all-MiniLM-L6-v2')
            logger.info("✅ Sentence-transformers backend loaded: all-MiniLM-L6-v2 (384d)")
            return model
        except Exception as e:
            logger.warning(f"Sentence-transformers load failed: {e}")
            return None

    def _try_openai():
        emb = _OpenAIEmbedder()
        if getattr(emb, '_available', False):
            logger.info("✅ OpenAI embedding backend enabled (projected to 384d)")
            return emb
        return None

    if backend_pref in {"st", "sentence-transformers"}:
        st = _try_st()
        if st is not None:
            return st
        logger.warning("Requested EMBEDDINGS_BACKEND=sentence-transformers but it's unavailable; falling back")
        # fall through
    elif backend_pref == "openai":
        oa = _try_openai()
        if oa is not None:
            return oa
        logger.warning("Requested EMBEDDINGS_BACKEND=openai but it's unavailable; falling back")
        # fall through
    elif backend_pref == "hash":
        logger.warning("EMBEDDINGS_BACKEND=hash selected; using deterministic fallback embeddings")
        return _HashEmbedder()

    # Default priority: sentence-transformers > OpenAI > hash
    st = _try_st()
    if st is not None:
        return st
    oa = _try_openai()
    if oa is not None:
        return oa
    logger.warning("⚠️ Using dummy embeddings - install sentence-transformers or set OPENAI_API_KEY for real embeddings")
    return _HashEmbedder()


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
                    dimension=EMBEDDING_DIM,  # standardized dimension
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='gcp',
                        region='us-central1'
                    ),
                )

            self.index = self.pc.Index(self.index_name)

            # Initialize embedding model with best available backend
            self.embedding_model = _get_embedder()

            self.initialized = True
            logger.info(
                f"✅ Pinecone vector service initialized with index: {self.index_name}"
            )
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
                embedding = self.embedding_model.encode(text)
                if hasattr(embedding, 'tolist'):
                    embedding = embedding.tolist()

                # Prepare vector data
                vectors.append(
                    {
                        "id": str(doc.get("id", "")),
                        "values": embedding,
                        "metadata": {
                            "title": doc.get("title", "")[:500],  # Limit metadata size
                            "type": doc.get("type", "document"),
                            "source": doc.get("source", ""),
                            "description": doc.get("description", "")[:1000],
                        },
                    }
                )

            # Upsert in batches
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                logger.info(
                    f"Indexed batch {i // batch_size + 1}: {len(batch)} documents"
                )

            logger.info(f"✅ Successfully indexed {len(vectors)} documents")

        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            raise
    
    async def index_standards(self, standards: List[Any], batch_size: int = 100):
        """Index accreditation standards for semantic search"""
        if not self.initialized:
            logger.warning("Pinecone not initialized - skipping standards indexing")
            return
        
        try:
            vectors = []
            for standard in standards:
                # Create text for embedding from standard object
                text = f"{standard.title} {standard.description}"
                if hasattr(standard, 'full_text') and standard.full_text:
                    text += f" {standard.full_text}"
                
                # Generate embedding
                embedding = self.embedding_model.encode(text)
                # Convert to list if it's not already (handles both numpy arrays and lists)
                if hasattr(embedding, 'tolist'):
                    embedding = embedding.tolist()
                
                # Prepare vector data
                metadata = {
                    "title": standard.title[:500],
                    "type": "standard",
                    "accreditor": getattr(standard, 'accreditor_id', 'unknown'),
                    "description": standard.description[:1000] if standard.description else "",
                    "weight": getattr(standard, 'weight', 1.0)
                }
                
                # Add evidence requirements if available
                if hasattr(standard, 'evidence_requirements'):
                    metadata["requirements"] = json.dumps(standard.evidence_requirements)[:1000]
                
                vectors.append({
                    "id": str(standard.id),
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Upsert in batches
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                self.index.upsert(vectors=batch)
                logger.info(f"Indexed batch {i//batch_size + 1}: {len(batch)} standards")
            
            logger.info(f"✅ Successfully indexed {len(vectors)} standards")
            
        except Exception as e:
            logger.error(f"Failed to index standards: {e}")
            # Don't raise - allow app to continue without vector indexing
            pass
    
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
            query_embedding = self.embedding_model.encode(query)
            # Convert to list if it's not already (handles both numpy arrays and lists)
            if hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()
            
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
        if not self.initialized or self.embedding_model is None:
            return 0.5  # Default score when embeddings not available
        
        try:
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
