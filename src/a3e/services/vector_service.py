"""
Vector Database Service for A3E

Provides semantic search and similarity matching using Milvus vector database.
Supports evidence-to-standard mapping and citation verification.
"""

import asyncio
import logging
from typing import List, Tuple, Dict, Any, Optional
import json

from ..models import Standard, Evidence

logger = logging.getLogger(__name__)

# Optional imports for AI features
try:
    import numpy as np
    from pymilvus import connections, Collection, CollectionSchema, DataType, FieldSchema, utility
    from sentence_transformers import SentenceTransformer
    VECTOR_FEATURES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Vector features not available: {e}")
    VECTOR_FEATURES_AVAILABLE = False
    # Create mock classes
    class SentenceTransformer:
        def __init__(self, *args, **kwargs):
            pass
        def encode(self, *args, **kwargs):
            return []


class VectorService:
    """Vector database service for semantic search and similarity matching"""
    
    def __init__(self, host: str = "localhost", port: int = 19530):
        self.host = host
        self.port = port
        self.connection_alias = "default"
        self.embedding_model = None
        self.collections = {}
        
    async def initialize(self):
        """Initialize vector database connection and embedding model"""
        try:
            # Connect to Milvus
            connections.connect(
                alias=self.connection_alias,
                host=self.host,
                port=self.port
            )
            logger.info(f"✅ Connected to Milvus at {self.host}:{self.port}")
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Initialized sentence transformer model")
            
            # Create collections
            await self._create_collections()
            logger.info("✅ Vector collections ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
            raise
    
    async def _create_collections(self):
        """Create Milvus collections for standards and evidence"""
        
        # Standards collection schema
        standards_fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=50, is_primary=True),
            FieldSchema(name="accreditor_id", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
            FieldSchema(name="institution_types", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="evidence_requirements", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="weight", dtype=DataType.FLOAT)
        ]
        
        standards_schema = CollectionSchema(
            fields=standards_fields,
            description="Accreditation standards with embeddings"
        )
        
        # Evidence collection schema
        evidence_fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=50, is_primary=True),
            FieldSchema(name="institution_id", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=500),
            FieldSchema(name="description", dtype=DataType.VARCHAR, max_length=2000),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384),
            FieldSchema(name="evidence_type", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="keywords", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="confidence_score", dtype=DataType.FLOAT)
        ]
        
        evidence_schema = CollectionSchema(
            fields=evidence_fields,
            description="Evidence documents with embeddings"
        )
        
        # Create collections if they don't exist
        collection_names = ["a3e_standards", "a3e_evidence"]
        schemas = [standards_schema, evidence_schema]
        
        for name, schema in zip(collection_names, schemas):
            if not utility.has_collection(name):
                collection = Collection(name=name, schema=schema)
                logger.info(f"Created collection: {name}")
            else:
                collection = Collection(name=name)
                logger.info(f"Using existing collection: {name}")
            
            self.collections[name] = collection
            
            # Create index for vector search
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            
            collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            logger.info(f"Created index for {name}")
    
    async def index_standards(self, standards: List[Standard]):
        """Index accreditation standards for semantic search"""
        if not standards:
            return
        
        try:
            collection = self.collections["a3e_standards"]
            
            # Prepare data for insertion
            data = []
            for standard in standards:
                # Create text for embedding
                text = f"{standard.title} {standard.description}"
                if hasattr(standard, 'full_text') and standard.full_text:
                    text += f" {standard.full_text}"
                
                # Generate embedding
                embedding = self.embedding_model.encode(text).tolist()
                
                data.append([
                    standard.id,
                    standard.accreditor.id if hasattr(standard, 'accreditor') else "unknown",
                    standard.title,
                    standard.description[:2000],  # Truncate if too long
                    embedding,
                    json.dumps([t.value for t in standard.applicable_institution_types]),
                    json.dumps(standard.evidence_requirements),
                    standard.weight
                ])
            
            # Insert data
            if data:
                collection.insert(data)
                collection.flush()
                logger.info(f"Indexed {len(data)} standards")
                
        except Exception as e:
            logger.error(f"Failed to index standards: {e}")
            raise
    
    async def index_evidence(self, evidence_items: List[Evidence]):
        """Index evidence documents for semantic search"""
        if not evidence_items:
            return
        
        try:
            collection = self.collections["a3e_evidence"]
            
            # Prepare data for insertion
            data = []
            for evidence in evidence_items:
                # Create text for embedding
                text = f"{evidence.title}"
                if evidence.description:
                    text += f" {evidence.description}"
                if evidence.extracted_text:
                    text += f" {evidence.extracted_text[:1000]}"  # Limit text length
                
                # Generate embedding
                embedding = self.embedding_model.encode(text).tolist()
                
                data.append([
                    str(evidence.id),
                    str(evidence.institution_id),
                    evidence.title,
                    evidence.description[:2000] if evidence.description else "",
                    embedding,
                    evidence.evidence_type.value,
                    json.dumps(evidence.keywords) if evidence.keywords else "[]",
                    evidence.confidence_score or 0.0
                ])
            
            # Insert data
            if data:
                collection.insert(data)
                collection.flush()
                logger.info(f"Indexed {len(data)} evidence items")
                
        except Exception as e:
            logger.error(f"Failed to index evidence: {e}")
            raise
    
    async def find_similar_standards(
        self,
        query_embedding: List[float],
        accreditor_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Find standards similar to the query embedding"""
        try:
            collection = self.collections["a3e_standards"]
            collection.load()
            
            # Build filter expression
            filter_expr = ""
            if accreditor_ids:
                accreditor_filter = " or ".join([f'accreditor_id == "{aid}"' for aid in accreditor_ids])
                filter_expr = f"({accreditor_filter})"
            
            # Search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # Perform search
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr if filter_expr else None,
                output_fields=["id", "title", "accreditor_id"]
            )
            
            # Extract results
            similar_standards = []
            for result in results[0]:
                similar_standards.append((result.entity.get("id"), result.distance))
            
            return similar_standards
            
        except Exception as e:
            logger.error(f"Failed to find similar standards: {e}")
            return []
    
    async def find_similar_evidence(
        self,
        query_text: str,
        institution_id: Optional[str] = None,
        evidence_types: Optional[List[str]] = None,
        top_k: int = 10
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Find evidence similar to the query text"""
        try:
            collection = self.collections["a3e_evidence"]
            collection.load()
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query_text).tolist()
            
            # Build filter expression
            filters = []
            if institution_id:
                filters.append(f'institution_id == "{institution_id}"')
            if evidence_types:
                type_filter = " or ".join([f'evidence_type == "{et}"' for et in evidence_types])
                filters.append(f"({type_filter})")
            
            filter_expr = " and ".join(filters) if filters else ""
            
            # Search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # Perform search
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr if filter_expr else None,
                output_fields=["id", "title", "description", "evidence_type", "confidence_score"]
            )
            
            # Extract results
            similar_evidence = []
            for result in results[0]:
                entity = result.entity
                similar_evidence.append((
                    entity.get("id"),
                    result.distance,
                    {
                        "title": entity.get("title"),
                        "description": entity.get("description"),
                        "evidence_type": entity.get("evidence_type"),
                        "confidence_score": entity.get("confidence_score")
                    }
                ))
            
            return similar_evidence
            
        except Exception as e:
            logger.error(f"Failed to find similar evidence: {e}")
            return []
    
    async def verify_citation_accuracy(
        self,
        narrative_text: str,
        evidence_text: str,
        cited_excerpt: str
    ) -> float:
        """Verify the accuracy of a citation using semantic similarity"""
        try:
            # Generate embeddings
            narrative_embedding = self.embedding_model.encode(narrative_text)
            evidence_embedding = self.embedding_model.encode(evidence_text)
            excerpt_embedding = self.embedding_model.encode(cited_excerpt)
            
            # Calculate similarities
            narrative_evidence_sim = np.dot(narrative_embedding, evidence_embedding) / (
                np.linalg.norm(narrative_embedding) * np.linalg.norm(evidence_embedding)
            )
            
            narrative_excerpt_sim = np.dot(narrative_embedding, excerpt_embedding) / (
                np.linalg.norm(narrative_embedding) * np.linalg.norm(excerpt_embedding)
            )
            
            evidence_excerpt_sim = np.dot(evidence_embedding, excerpt_embedding) / (
                np.linalg.norm(evidence_embedding) * np.linalg.norm(excerpt_embedding)
            )
            
            # Weighted average (excerpt-evidence similarity is most important)
            accuracy_score = (
                0.2 * narrative_evidence_sim +
                0.3 * narrative_excerpt_sim +
                0.5 * evidence_excerpt_sim
            )
            
            return float(accuracy_score)
            
        except Exception as e:
            logger.error(f"Failed to verify citation accuracy: {e}")
            return 0.0
    
    async def semantic_search(
        self,
        query: str,
        collection_name: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Perform general semantic search across a collection"""
        try:
            collection = self.collections.get(collection_name)
            if not collection:
                logger.error(f"Collection not found: {collection_name}")
                return []
            
            collection.load()
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Build filter expression
            filter_expr = ""
            if filters:
                filter_parts = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        filter_parts.append(f'{key} == "{value}"')
                    elif isinstance(value, list):
                        value_filter = " or ".join([f'{key} == "{v}"' for v in value])
                        filter_parts.append(f"({value_filter})")
                filter_expr = " and ".join(filter_parts)
            
            # Search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # Perform search
            results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=filter_expr if filter_expr else None,
                output_fields=["*"]
            )
            
            # Extract and format results
            search_results = []
            for result in results[0]:
                entity_dict = {}
                for field_name in result.entity.fields:
                    entity_dict[field_name] = result.entity.get(field_name)
                entity_dict["similarity_score"] = result.distance
                search_results.append(entity_dict)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []
    
    async def health_check(self) -> bool:
        """Check if vector service is healthy"""
        try:
            # Check connection
            if not connections.has_connection(self.connection_alias):
                return False
            
            # Check collections
            for collection_name in self.collections:
                collection = self.collections[collection_name]
                if not collection:
                    return False
                
                # Simple count query
                collection.load()
                num_entities = collection.num_entities
                logger.debug(f"Collection {collection_name} has {num_entities} entities")
            
            return True
            
        except Exception as e:
            logger.error(f"Vector service health check failed: {e}")
            return False
    
    async def close(self):
        """Close vector database connections"""
        try:
            connections.disconnect(alias=self.connection_alias)
            logger.info("Disconnected from Milvus")
        except Exception as e:
            logger.error(f"Error closing vector service: {e}")
