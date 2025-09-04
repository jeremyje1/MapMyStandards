"""
Patch for Pinecone service to use numpy-based embeddings instead of dummy hashes
"""

import numpy as np
import hashlib

def create_embedding(text: str, dimension: int = 1536) -> list:
    """Create a deterministic embedding from text using numpy"""
    # Create a seed from the text
    seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
    np.random.seed(seed)
    
    # Generate a normalized embedding vector
    embedding = np.random.randn(dimension)
    # Normalize to unit length
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding.tolist()

# Monkey patch the get_embedding function in pinecone_service
def patch_pinecone_service():
    try:
        from src.a3e.services import pinecone_service
        
        # Replace the dummy embedding function
        original_get_embedding = pinecone_service.get_embedding
        
        def improved_get_embedding(text: str) -> list:
            """Improved embedding function using numpy"""
            try:
                return create_embedding(text)
            except:
                # Fallback to original if numpy not available
                return original_get_embedding(text)
        
        pinecone_service.get_embedding = improved_get_embedding
        print("✅ Patched Pinecone service with improved embeddings")
    except Exception as e:
        print(f"⚠️  Could not patch Pinecone service: {e}")
