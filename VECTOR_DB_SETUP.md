# Vector DB and Agent Orchestrator Setup Guide

## Overview
This guide will help you add Vector Database (for semantic search) and Agent Orchestrator (for multi-agent AI workflows) to your MapMyStandards backend.

## Option 1: Pinecone (Recommended for Production)

Pinecone is a managed vector database service that's easier to set up and maintain.

### 1. Create Pinecone Account
1. Go to https://www.pinecone.io/
2. Sign up for a free account (includes 1 index with 100K vectors)
3. Create a new project
4. Get your API key and environment from the dashboard

### 2. Update Backend Code

Create a new file `src/a3e/services/pinecone_vector_service.py`:

```python
import os
from typing import List, Dict, Any, Optional
import logging
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class PineconeVectorService:
    """Pinecone-based vector service for semantic search"""
    
    def __init__(self):
        self.pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        self.index_name = "mapmystandards"
        self.embedding_model = None
        self.index = None
        
    async def initialize(self):
        """Initialize Pinecone connection and embedding model"""
        try:
            # Create index if it doesn't exist
            if self.index_name not in self.pc.list_indexes().names():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,  # for all-MiniLM-L6-v2
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
            
            self.index = self.pc.Index(self.index_name)
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Pinecone vector service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise
    
    async def index_documents(self, documents: List[Dict[str, Any]]):
        """Index documents for semantic search"""
        vectors = []
        for doc in documents:
            text = f"{doc.get('title', '')} {doc.get('description', '')} {doc.get('content', '')}"
            embedding = self.embedding_model.encode(text).tolist()
            vectors.append({
                "id": doc['id'],
                "values": embedding,
                "metadata": {
                    "title": doc.get('title', ''),
                    "type": doc.get('type', 'document'),
                    "source": doc.get('source', '')
                }
            })
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i+batch_size]
            self.index.upsert(vectors=batch)
        
        logger.info(f"Indexed {len(vectors)} documents")
    
    async def semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Perform semantic search"""
        query_embedding = self.embedding_model.encode(query).tolist()
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return [
            {
                "id": match.id,
                "score": match.score,
                "metadata": match.metadata
            }
            for match in results.matches
        ]
    
    async def health_check(self) -> bool:
        """Check if Pinecone service is healthy"""
        try:
            stats = self.index.describe_index_stats()
            return stats.total_vector_count >= 0
        except:
            return False
```

### 3. Add Railway Environment Variables

```bash
# Set Pinecone API key
railway variables set PINECONE_API_KEY=your-pinecone-api-key

# Set Pinecone environment 
railway variables set PINECONE_ENVIRONMENT=us-east-1-aws

# Enable vector features
railway variables set ENABLE_VECTOR_DB=true
railway variables set VECTOR_DB_PROVIDER=pinecone
```

## Option 2: Milvus (Self-Hosted)

Milvus is an open-source vector database that you can self-host.

### 1. Deploy Milvus on Railway

Create a new service in your Railway project:

```yaml
# milvus.yaml
services:
  milvus:
    image: milvusdb/milvus:latest
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    ports:
      - 19530:19530
      - 9091:9091
    volumes:
      - milvus-data:/var/lib/milvus
    
  etcd:
    image: quay.io/coreos/etcd:latest
    environment:
      ETCD_AUTO_COMPACTION_MODE: revision
      ETCD_AUTO_COMPACTION_RETENTION: 1000
      ETCD_QUOTA_BACKEND_BYTES: 4294967296
    volumes:
      - etcd-data:/etcd
    
  minio:
    image: minio/minio:latest
    environment:
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    volumes:
      - minio-data:/minio_data
    command: minio server /minio_data
```

### 2. Update Railway Environment Variables

```bash
# Milvus configuration
railway variables set MILVUS_HOST=${{Milvus.RAILWAY_PRIVATE_DOMAIN}}
railway variables set MILVUS_PORT=19530
railway variables set ENABLE_VECTOR_DB=true
railway variables set VECTOR_DB_PROVIDER=milvus
```

## Agent Orchestrator Setup

### 1. Install Required Dependencies

Update your `requirements.txt`:

```txt
# Existing dependencies...

# Agent Orchestrator
pyautogen==0.2.0
langchain==0.1.0
sentence-transformers==2.2.2

# Vector DB (choose one)
pinecone-client==3.0.0  # For Pinecone
pymilvus==2.3.0  # For Milvus

# Additional AI dependencies
numpy==1.24.0
pandas==2.0.0
scikit-learn==1.3.0
```

### 2. Update Main Application

Update `src/a3e/main_production.py` to initialize vector service:

```python
# Add to imports
from .services.pinecone_vector_service import PineconeVectorService

# In startup event
@app.on_event("startup")
async def startup_event():
    # ... existing code ...
    
    # Initialize vector service if enabled
    if os.environ.get("ENABLE_VECTOR_DB") == "true":
        vector_provider = os.environ.get("VECTOR_DB_PROVIDER", "pinecone")
        
        if vector_provider == "pinecone":
            app.state.vector_service = PineconeVectorService()
        else:
            from .services.vector_service import VectorService
            app.state.vector_service = VectorService(
                host=os.environ.get("MILVUS_HOST", "localhost"),
                port=int(os.environ.get("MILVUS_PORT", 19530))
            )
        
        await app.state.vector_service.initialize()
        logger.info(f"✅ Vector service ({vector_provider}) initialized")
    
    # Initialize agent orchestrator if vector service is available
    if hasattr(app.state, "vector_service"):
        from .agents import A3EAgentOrchestrator
        app.state.agent_orchestrator = A3EAgentOrchestrator(
            llm_service=app.state.llm_service,
            vector_service=app.state.vector_service
        )
        logger.info("✅ Agent orchestrator initialized")
```

### 3. Add API Endpoints

Create `src/a3e/api/routes/agents.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from ...dependencies import get_agent_orchestrator, get_current_user

router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/execute-workflow")
async def execute_workflow(
    institution_id: str,
    accreditor_id: str,
    evidence_ids: List[str],
    orchestrator = Depends(get_agent_orchestrator),
    current_user = Depends(get_current_user)
):
    """Execute the four-agent workflow for accreditation"""
    try:
        # Get institution and evidence from database
        # ... database queries ...
        
        result = await orchestrator.execute_workflow(
            institution=institution,
            accreditor_id=accreditor_id,
            evidence_items=evidence_items
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow-status/{workflow_id}")
async def get_workflow_status(
    workflow_id: str,
    orchestrator = Depends(get_agent_orchestrator)
):
    """Get status of a running workflow"""
    # Implementation for checking workflow status
    pass
```

## Testing the Setup

### 1. Check Vector DB Health

```bash
curl https://api.mapmystandards.ai/health
```

Should show:
```json
{
  "services": {
    "vector_db": {
      "status": "healthy"
    },
    "agent_orchestrator": {
      "status": "available"
    }
  }
}
```

### 2. Test Semantic Search

```bash
curl -X POST https://api.mapmystandards.ai/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "mission statement requirements"}'
```

### 3. Test Agent Workflow

```bash
curl -X POST https://api.mapmystandards.ai/api/v1/agents/execute-workflow \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "institution_id": "test-institution",
    "accreditor_id": "SACSCOC",
    "evidence_ids": ["doc1", "doc2"]
  }'
```

## Deployment Steps

1. Choose your vector DB provider (Pinecone recommended for simplicity)
2. Set up the service account/API keys
3. Update Railway environment variables
4. Deploy the updated backend code
5. Test the health endpoint to verify everything is working

## Cost Considerations

- **Pinecone Free Tier**: 100K vectors, 1 index (sufficient for testing)
- **Pinecone Starter**: $70/month for 1M vectors
- **Milvus Self-Hosted**: Only Railway compute costs (~$20-40/month)

## Next Steps

After setup:
1. Index your existing standards and documents
2. Test the semantic search functionality
3. Run a sample agent workflow
4. Monitor performance and adjust as needed