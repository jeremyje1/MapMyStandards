"""
Tests for file upload endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import uuid

from src.a3e.main import app
from src.a3e.models.user import User
from src.a3e.models.document import Document

client = TestClient(app)

@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    return User(
        id="test-user-id",
        email="test@example.com",
        name="Test User",
        institution_name="Test University"
    )

@pytest.fixture
def mock_s3_client():
    """Mock S3 client"""
    mock = MagicMock()
    mock.generate_presigned_post.return_value = {
        "url": "https://s3.amazonaws.com/test-bucket",
        "fields": {
            "key": "test-key",
            "policy": "test-policy",
            "signature": "test-signature"
        }
    }
    mock.head_object.return_value = {
        "Metadata": {
            "user-id": "test-user-id"
        }
    }
    return mock

class TestUpload:
    
    def test_presign_success(self, mock_user, mock_s3_client):
        """Test successful presigned URL generation"""
        with patch('src.a3e.api.routes.upload.get_current_user', return_value=mock_user):
            with patch('src.a3e.api.routes.upload.s3_client', mock_s3_client):
                response = client.post("/upload/presign", json={
                    "filename": "test.pdf",
                    "content_type": "application/pdf",
                    "file_size": 1024000  # 1MB
                })
                
                assert response.status_code == 200
                data = response.json()
                assert "upload_url" in data
                assert "upload_fields" in data
                assert "file_key" in data
                assert "expires_at" in data
    
    def test_presign_file_too_large(self, mock_user):
        """Test presign with file exceeding size limit"""
        with patch('src.a3e.api.routes.upload.get_current_user', return_value=mock_user):
            response = client.post("/upload/presign", json={
                "filename": "large.pdf",
                "content_type": "application/pdf",
                "file_size": 200 * 1024 * 1024  # 200MB
            })
            
            assert response.status_code == 400
            assert "exceeds maximum" in response.json()["detail"]
    
    def test_presign_invalid_file_type(self, mock_user):
        """Test presign with unsupported file type"""
        with patch('src.a3e.api.routes.upload.get_current_user', return_value=mock_user):
            response = client.post("/upload/presign", json={
                "filename": "test.exe",
                "content_type": "application/x-msdownload",
                "file_size": 1024000
            })
            
            assert response.status_code == 400
            assert "not allowed" in response.json()["detail"]
    
    def test_complete_upload_success(self, mock_user, mock_s3_client):
        """Test successful upload completion"""
        mock_db = MagicMock()
        mock_document = Document(
            id=str(uuid.uuid4()),
            user_id=mock_user.id,
            filename="test.pdf",
            file_key="test-key",
            file_size=1024000,
            content_type="application/pdf",
            status="uploaded",
            uploaded_at=datetime.utcnow()
        )
        
        with patch('src.a3e.api.routes.upload.get_current_user', return_value=mock_user):
            with patch('src.a3e.api.routes.upload.get_db', return_value=mock_db):
                with patch('src.a3e.api.routes.upload.s3_client', mock_s3_client):
                    # Configure mock to return the document after commit
                    mock_db.add = MagicMock()
                    mock_db.commit = MagicMock()
                    mock_db.refresh = MagicMock(side_effect=lambda x: setattr(x, 'id', mock_document.id))
                    
                    response = client.post("/upload/complete", json={
                        "file_key": "test-key",
                        "filename": "test.pdf",
                        "file_size": 1024000,
                        "content_type": "application/pdf",
                        "sha256": "abc123"
                    })
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["filename"] == "test.pdf"
                    assert data["status"] == "uploaded"
                    assert "download_url" in data
    
    def test_complete_upload_unauthorized(self, mock_user):
        """Test upload completion with unauthorized file"""
        mock_s3_client = MagicMock()
        mock_s3_client.head_object.return_value = {
            "Metadata": {
                "user-id": "different-user-id"  # Different user
            }
        }
        
        with patch('src.a3e.api.routes.upload.get_current_user', return_value=mock_user):
            with patch('src.a3e.api.routes.upload.s3_client', mock_s3_client):
                response = client.post("/upload/complete", json={
                    "file_key": "test-key",
                    "filename": "test.pdf",
                    "file_size": 1024000,
                    "content_type": "application/pdf"
                })
                
                assert response.status_code == 403
                assert "Unauthorized" in response.json()["detail"]
    
    def test_complete_upload_file_not_found(self, mock_user):
        """Test upload completion with non-existent file"""
        mock_s3_client = MagicMock()
        from botocore.exceptions import ClientError
        mock_s3_client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404"}}, "HeadObject"
        )
        
        with patch('src.a3e.api.routes.upload.get_current_user', return_value=mock_user):
            with patch('src.a3e.api.routes.upload.s3_client', mock_s3_client):
                response = client.post("/upload/complete", json={
                    "file_key": "non-existent-key",
                    "filename": "test.pdf",
                    "file_size": 1024000,
                    "content_type": "application/pdf"
                })
                
                assert response.status_code == 404
                assert "not found" in response.json()["detail"]
    
    def test_list_documents(self, mock_user):
        """Test listing user's documents"""
        mock_db = MagicMock()
        mock_documents = [
            Document(
                id=str(uuid.uuid4()),
                user_id=mock_user.id,
                filename="doc1.pdf",
                file_key="key1",
                file_size=1024000,
                content_type="application/pdf",
                status="uploaded",
                uploaded_at=datetime.utcnow()
            ),
            Document(
                id=str(uuid.uuid4()),
                user_id=mock_user.id,
                filename="doc2.docx",
                file_key="key2",
                file_size=2048000,
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                status="analyzed",
                uploaded_at=datetime.utcnow()
            )
        ]
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = mock_documents
        mock_db.query.return_value = mock_query
        
        with patch('src.a3e.api.routes.upload.get_current_user', return_value=mock_user):
            with patch('src.a3e.api.routes.upload.get_db', return_value=mock_db):
                with patch('src.a3e.api.routes.upload.s3_client.generate_presigned_url', 
                          return_value="https://example.com/download"):
                    response = client.get("/upload/documents")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert len(data) == 2
                    assert data[0]["filename"] == "doc1.pdf"
                    assert data[1]["filename"] == "doc2.docx"
                    assert all("download_url" in doc for doc in data)
    
    def test_delete_document(self, mock_user):
        """Test document deletion"""
        mock_db = MagicMock()
        mock_document = Document(
            id="doc-id",
            user_id=mock_user.id,
            filename="test.pdf",
            status="uploaded"
        )
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_document
        mock_db.query.return_value = mock_query
        
        with patch('src.a3e.api.routes.upload.get_current_user', return_value=mock_user):
            with patch('src.a3e.api.routes.upload.get_db', return_value=mock_db):
                response = client.delete("/upload/documents/doc-id")
                
                assert response.status_code == 200
                assert response.json()["success"] == True
                assert mock_document.status == "deleted"
                assert mock_document.deleted_at is not None
    
    def test_delete_document_not_found(self, mock_user):
        """Test deleting non-existent document"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        with patch('src.a3e.api.routes.upload.get_current_user', return_value=mock_user):
            with patch('src.a3e.api.routes.upload.get_db', return_value=mock_db):
                response = client.delete("/upload/documents/non-existent-id")
                
                assert response.status_code == 404
                assert "not found" in response.json()["detail"]
    
    def test_cross_org_access_protection(self, mock_user):
        """Test that users cannot access documents from other organizations"""
        other_user = User(
            id="other-user-id",
            email="other@example.com",
            institution_name="Other University"
        )
        
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No document found for this user
        mock_db.query.return_value = mock_query
        
        with patch('src.a3e.api.routes.upload.get_current_user', return_value=mock_user):
            with patch('src.a3e.api.routes.upload.get_db', return_value=mock_db):
                response = client.delete("/upload/documents/other-org-doc-id")
                
                assert response.status_code == 404
                # User should not be able to access documents from other orgs