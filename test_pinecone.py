#!/usr/bin/env python3
"""
Test Pinecone connection
Run: python3 test_pinecone.py
"""

import os
from pinecone import Pinecone, ServerlessSpec

def test_pinecone_connection():
    """Test Pinecone API connection"""
    
    # Get API key from environment
    api_key = os.environ.get("PINECONE_API_KEY")
    
    if not api_key:
        print("❌ PINECONE_API_KEY not set in environment")
        print("Set it with: export PINECONE_API_KEY='your-key-here'")
        return False
    
    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        
        # List existing indexes
        existing_indexes = pc.list_indexes()
        print(f"✅ Connected to Pinecone!")
        print(f"📊 Existing indexes: {existing_indexes.names()}")
        
        # Check if our index exists
        index_name = "mapmystandards"
        if index_name not in existing_indexes.names():
            print(f"📝 Creating index '{index_name}'...")
            pc.create_index(
                name=index_name,
                dimension=384,  # for all-MiniLM-L6-v2 embeddings
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='gcp',
                    region='us-central1'
                )
            )
            print(f"✅ Index '{index_name}' created!")
        else:
            print(f"✅ Index '{index_name}' already exists")
        
        # Get index stats
        index = pc.Index(index_name)
        stats = index.describe_index_stats()
        print(f"📈 Index stats:")
        print(f"   - Total vectors: {stats.total_vector_count}")
        print(f"   - Dimensions: {stats.dimension}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Pinecone: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Pinecone Connection...")
    print("-" * 40)
    
    success = test_pinecone_connection()
    
    if success:
        print("\n✅ Pinecone is ready to use!")
        print("\nNext steps:")
        print("1. Add PINECONE_API_KEY to Railway variables")
        print("2. Deploy your backend with: railway up")
    else:
        print("\n❌ Pinecone setup incomplete")
        print("\nTroubleshooting:")
        print("1. Make sure you have a Pinecone account")
        print("2. Get your API key from: https://app.pinecone.io/")
        print("3. Set the environment variable: export PINECONE_API_KEY='your-key'")