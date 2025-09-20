"""
Storage service for handling file uploads with S3 and local fallback
"""

import os
import uuid
import hashlib
import logging
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class StorageService:
    """Unified storage service supporting S3 and local storage"""
    
    def __init__(self, settings=None):
        """Initialize storage service with configuration"""
        self.settings = settings
        self.storage_type = "local"  # Default to local
        self.s3_client = None
        self.bucket_name = None
        self.local_upload_path = Path("uploads")
        
        # Try to initialize S3 if credentials are available
        if settings and settings.aws_access_key_id and settings.aws_secret_access_key:
            try:
                import boto3
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region or 'us-east-1'
                )
                # Support multiple env var names for the bucket for convenience
                self.bucket_name = os.getenv("S3_BUCKET_NAME") or os.getenv("S3_BUCKET") or os.getenv("MMS_ARTIFACTS_BUCKET") or "mapmystandards-uploads"
                self.storage_type = "s3"
                logger.info("Storage service initialized with S3")
            except ImportError:
                logger.warning("boto3 not installed, falling back to local storage")
            except Exception as e:
                logger.error(f"Failed to initialize S3: {e}")
        
        # Ensure local upload directory exists
        self.local_upload_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage service initialized with {self.storage_type} storage")
    
    def generate_file_key(self, org_id: str, user_id: str, filename: str) -> str:
        """Generate a unique file key for storage"""
        file_uuid = uuid.uuid4().hex[:8]
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
        return f"org/{org_id}/user/{user_id}/{file_uuid}-{safe_filename}"
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA256 hash of file content"""
        return hashlib.sha256(file_content).hexdigest()
    
    async def get_presigned_upload_url(
        self,
        org_id: str,
        user_id: str,
        filename: str,
        content_type: str,
        max_size: int = 10 * 1024 * 1024  # 10MB default
    ) -> Dict[str, Any]:
        """
        Get presigned URL for direct upload to storage
        Returns dict with url and any required fields
        """
        file_key = self.generate_file_key(org_id, user_id, filename)
        
        if self.storage_type == "s3" and self.s3_client:
            try:
                # Generate presigned POST for S3
                response = self.s3_client.generate_presigned_post(
                    Bucket=self.bucket_name,
                    Key=file_key,
                    Fields={
                        "Content-Type": content_type,
                        "x-amz-meta-org-id": org_id,
                        "x-amz-meta-user-id": user_id,
                        "x-amz-meta-original-name": filename
                    },
                    Conditions=[
                        ["content-length-range", 0, max_size],
                        ["starts-with", "$Content-Type", content_type.split("/")[0]]
                    ],
                    ExpiresIn=3600  # 1 hour
                )
                
                return {
                    "type": "s3",
                    "url": response["url"],
                    "fields": response["fields"],
                    "key": file_key,
                    "expires_in": 3600
                }
            except Exception as e:
                logger.error(f"Failed to generate S3 presigned URL: {e}")
                # Fall back to local storage
        
        # Local storage fallback - return upload endpoint
        return {
            "type": "local",
            "url": "/api/upload/direct",
            "fields": {
                "key": file_key,
                "org_id": org_id,
                "user_id": user_id
            },
            "key": file_key,
            "expires_in": 3600
        }
    
    async def save_file(
        self,
        file_content: bytes,
        file_key: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Save file to storage (used for local storage path)"""
        if self.storage_type == "s3" and self.s3_client:
            try:
                # Upload to S3
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=file_key,
                    Body=file_content,
                    ContentType=content_type,
                    Metadata=metadata or {}
                )
                
                return {
                    "success": True,
                    "storage_type": "s3",
                    "key": file_key,
                    "size": len(file_content),
                    "hash": self.calculate_file_hash(file_content)
                }
            except Exception as e:
                logger.error(f"Failed to upload to S3: {e}")
                # Fall back to local storage
        
        # Local storage
        file_path = self.local_upload_path / file_key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Save metadata
        meta_path = file_path.with_suffix(file_path.suffix + ".meta")
        with open(meta_path, "w") as f:
            json.dump({
                "content_type": content_type,
                "uploaded_at": datetime.utcnow().isoformat(),
                "size": len(file_content),
                "hash": self.calculate_file_hash(file_content),
                **(metadata or {})
            }, f)
        
        return {
            "success": True,
            "storage_type": "local",
            "key": file_key,
            "size": len(file_content),
            "hash": self.calculate_file_hash(file_content)
        }
    
    async def get_file(self, file_key: str) -> Optional[bytes]:
        """Retrieve file content from storage"""
        if self.storage_type == "s3" and self.s3_client:
            try:
                response = self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
                return response["Body"].read()
            except Exception as e:
                logger.error(f"Failed to retrieve from S3: {e}")
                # Try local fallback
        
        # Local storage
        file_path = self.local_upload_path / file_key
        if file_path.exists():
            with open(file_path, "rb") as f:
                return f.read()
        
        return None
    
    async def get_download_url(
        self,
        file_key: str,
        expires_in: int = 3600,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """Get a signed download URL for the file"""
        if self.storage_type == "s3" and self.s3_client:
            try:
                params = {
                    "Bucket": self.bucket_name,
                    "Key": file_key
                }
                if filename:
                    params["ResponseContentDisposition"] = f'attachment; filename="{filename}"'
                
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params=params,
                    ExpiresIn=expires_in
                )
                return url
            except Exception as e:
                logger.error(f"Failed to generate download URL: {e}")
        
        # Local storage - return API endpoint
        return f"/api/files/download/{file_key}"
    
    async def delete_file(self, file_key: str) -> bool:
        """Delete file from storage"""
        if self.storage_type == "s3" and self.s3_client:
            try:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_key
                )
                return True
            except Exception as e:
                logger.error(f"Failed to delete from S3: {e}")
        
        # Local storage
        file_path = self.local_upload_path / file_key
        meta_path = file_path.with_suffix(file_path.suffix + ".meta")
        
        if file_path.exists():
            file_path.unlink()
        if meta_path.exists():
            meta_path.unlink()
        
        return True
    
    async def list_files(
        self,
        org_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """List files with optional filtering"""
        prefix = ""
        if org_id:
            prefix = f"org/{org_id}/"
            if user_id:
                prefix += f"user/{user_id}/"
        
        files = []
        
        if self.storage_type == "s3" and self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=limit
                )
                
                for obj in response.get("Contents", []):
                    files.append({
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat(),
                        "storage_type": "s3"
                    })
                
                return files
            except Exception as e:
                logger.error(f"Failed to list S3 objects: {e}")
        
        # Local storage
        search_path = self.local_upload_path
        if prefix:
            search_path = search_path / prefix
        
        if search_path.exists():
            for file_path in search_path.rglob("*"):
                if file_path.is_file() and not file_path.suffix == ".meta":
                    relative_key = str(file_path.relative_to(self.local_upload_path))
                    files.append({
                        "key": relative_key,
                        "size": file_path.stat().st_size,
                        "last_modified": datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat(),
                        "storage_type": "local"
                    })
                    
                    if len(files) >= limit:
                        break
        
        return files

# Global instance
storage_service = None

def get_storage_service():
    """Get or create storage service instance"""
    global storage_service
    if storage_service is None:
        from ..core.config import get_settings
        storage_service = StorageService(get_settings())
    return storage_service
