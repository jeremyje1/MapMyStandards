from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from src.a3e.core.database import get_db
from src.a3e.core.auth import get_current_user
from src.a3e.models.user import User
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/documents", tags=["documents"])

# In-memory storage for demo
documents_db = {}

@router.get("/")
async def list_documents(current_user: User = Depends(get_current_user)):
    """List user's documents"""
    user_docs = documents_db.get(str(current_user.id), [])
    return {"documents": user_docs}

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    category: str = "general",
    current_user: User = Depends(get_current_user)
):
    """Upload a document"""
    user_id = str(current_user.id)
    
    if user_id not in documents_db:
        documents_db[user_id] = []
    
    doc_id = str(uuid.uuid4())
    doc_info = {
        "id": doc_id,
        "filename": file.filename,
        "category": category,
        "size": file.size if hasattr(file, 'size') else 0,
        "uploaded_at": datetime.utcnow().isoformat(),
        "status": "processed"
    }
    
    documents_db[user_id].append(doc_info)
    
    return {
        "message": "Document uploaded successfully",
        "document": doc_info
    }

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document"""
    user_id = str(current_user.id)
    
    if user_id in documents_db:
        documents_db[user_id] = [
            doc for doc in documents_db[user_id]
            if doc["id"] != document_id
        ]
    
    return {"message": "Document deleted successfully"}
