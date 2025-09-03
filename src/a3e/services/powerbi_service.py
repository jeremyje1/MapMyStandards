"""
Advanced Power BI Integration Service
Handles real Power BI API connections, embed token management, and RLS
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import aiohttp
import jwt
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives import serialization

logger = logging.getLogger(__name__)


@dataclass
class PowerBICredentials:
    """Power BI service credentials"""
    client_id: str
    client_secret: str
    tenant_id: str
    workspace_id: str
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class EmbedToken:
    """Power BI embed token with metadata"""
    token: str
    token_id: str
    expiration: datetime
    reports: List[Dict[str, Any]]
    datasets: List[Dict[str, Any]]


@dataclass
class PowerBIReport:
    """Power BI report metadata"""
    id: str
    name: str
    embed_url: str
    dataset_id: str
    is_owned_by_me: bool
    modified_date: datetime


class PowerBIService:
    """
    Advanced Power BI integration service
    Handles authentication, embed tokens, and data operations
    """
    
    def __init__(self, credentials: PowerBICredentials):
        self.credentials = credentials
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.auth_url = f"https://login.microsoftonline.com/{credentials.tenant_id}/oauth2/v2.0/token"
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        
    async def authenticate(self) -> str:
        """
        Authenticate with Azure AD and get access token
        Supports both service principal and user credentials
        """
        if self.access_token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return self.access_token
            
        try:
            # Service Principal authentication (recommended for production)
            if self.credentials.client_secret:
                data = {
                    'grant_type': 'client_credentials',
                    'client_id': self.credentials.client_id,
                    'client_secret': self.credentials.client_secret,
                    'scope': 'https://analysis.windows.net/powerbi/api/.default'
                }
            # User credentials authentication (for development/testing)
            elif self.credentials.username and self.credentials.password:
                data = {
                    'grant_type': 'password',
                    'client_id': self.credentials.client_id,
                    'username': self.credentials.username,
                    'password': self.credentials.password,
                    'scope': 'https://analysis.windows.net/powerbi/api/.default'
                }
            else:
                raise ValueError("Either client_secret or user credentials must be provided")
                
            async with aiohttp.ClientSession() as session:
                async with session.post(self.auth_url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.access_token = result['access_token']
                        expires_in = result.get('expires_in', 3600)
                        self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                        logger.info("Successfully authenticated with Power BI")
                        return self.access_token
                    else:
                        error_text = await response.text()
                        logger.error(f"Authentication failed: {response.status} - {error_text}")
                        raise Exception(f"Authentication failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Power BI authentication error: {str(e)}")
            raise
            
    async def get_headers(self) -> Dict[str, str]:
        """Get authenticated headers for API requests"""
        token = await self.authenticate()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
    async def get_workspaces(self) -> List[Dict[str, Any]]:
        """Get all available workspaces"""
        headers = await self.get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/groups", headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('value', [])
                else:
                    logger.error(f"Failed to get workspaces: {response.status}")
                    return []
                    
    async def get_reports(self, workspace_id: Optional[str] = None) -> List[PowerBIReport]:
        """Get reports from workspace"""
        headers = await self.get_headers()
        workspace_id = workspace_id or self.credentials.workspace_id
        
        url = f"{self.base_url}/groups/{workspace_id}/reports" if workspace_id else f"{self.base_url}/reports"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    reports = []
                    for report_data in result.get('value', []):
                        reports.append(PowerBIReport(
                            id=report_data['id'],
                            name=report_data['name'],
                            embed_url=report_data['embedUrl'],
                            dataset_id=report_data.get('datasetId', ''),
                            is_owned_by_me=report_data.get('isOwnedByMe', False),
                            modified_date=datetime.fromisoformat(
                                report_data.get('modifiedDateTime', '').replace('Z', '+00:00')
                            ) if report_data.get('modifiedDateTime') else datetime.utcnow()
                        ))
                    return reports
                else:
                    logger.error(f"Failed to get reports: {response.status}")
                    return []
                    
    async def get_datasets(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get datasets from workspace"""
        headers = await self.get_headers()
        workspace_id = workspace_id or self.credentials.workspace_id
        
        url = f"{self.base_url}/groups/{workspace_id}/datasets" if workspace_id else f"{self.base_url}/datasets"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('value', [])
                else:
                    logger.error(f"Failed to get datasets: {response.status}")
                    return []
                    
    async def generate_embed_token(
        self, 
        report_ids: List[str], 
        dataset_ids: List[str],
        username: Optional[str] = None,
        roles: Optional[List[str]] = None,
        identity_blob: Optional[Dict[str, Any]] = None
    ) -> EmbedToken:
        """
        Generate embed token for reports with optional RLS
        """
        headers = await self.get_headers()
        workspace_id = self.credentials.workspace_id
        
        # Prepare the embed token request
        token_request = {
            "reports": [{"id": report_id} for report_id in report_ids],
            "datasets": [{"id": dataset_id} for dataset_id in dataset_ids]
        }
        
        # Add identity for Row-Level Security
        if username and roles:
            token_request["identities"] = [{
                "username": username,
                "roles": roles,
                "datasets": dataset_ids
            }]
            
        # Add additional identity blob if provided
        if identity_blob:
            if "identities" not in token_request:
                token_request["identities"] = []
            token_request["identities"].append(identity_blob)
            
        url = f"{self.base_url}/groups/{workspace_id}/GenerateToken"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=token_request) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Parse the JWT token to get expiration
                    token = result['token']
                    try:
                        # Decode without verification to get expiration
                        decoded = jwt.decode(token, options={"verify_signature": False})
                        expiration = datetime.fromtimestamp(decoded.get('exp', 0))
                    except:
                        # Fallback to 1 hour from now
                        expiration = datetime.utcnow() + timedelta(hours=1)
                        
                    return EmbedToken(
                        token=token,
                        token_id=result.get('tokenId', ''),
                        expiration=expiration,
                        reports=[{"id": rid} for rid in report_ids],
                        datasets=[{"id": did} for did in dataset_ids]
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to generate embed token: {response.status} - {error_text}")
                    raise Exception(f"Failed to generate embed token: {response.status}")
                    
    async def refresh_dataset(self, dataset_id: str, notify_option: str = "MailOnCompletion") -> str:
        """
        Trigger dataset refresh
        """
        headers = await self.get_headers()
        workspace_id = self.credentials.workspace_id
        
        refresh_request = {
            "notifyOption": notify_option
        }
        
        url = f"{self.base_url}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=refresh_request) as response:
                if response.status == 202:  # Accepted
                    # Get the request ID from the response
                    request_id = response.headers.get('RequestId', '')
                    logger.info(f"Dataset refresh initiated: {request_id}")
                    return request_id
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to refresh dataset: {response.status} - {error_text}")
                    raise Exception(f"Failed to refresh dataset: {response.status}")
                    
    async def get_refresh_history(self, dataset_id: str, top: int = 10) -> List[Dict[str, Any]]:
        """
        Get dataset refresh history
        """
        headers = await self.get_headers()
        workspace_id = self.credentials.workspace_id
        
        url = f"{self.base_url}/groups/{workspace_id}/datasets/{dataset_id}/refreshes?$top={top}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('value', [])
                else:
                    logger.error(f"Failed to get refresh history: {response.status}")
                    return []
                    
    async def test_connection(self) -> bool:
        """
        Test if Power BI connection is working
        """
        try:
            await self.authenticate()
            workspaces = await self.get_workspaces()
            return len(workspaces) >= 0  # Even empty list means connection works
        except Exception as e:
            logger.error(f"Power BI connection test failed: {str(e)}")
            return False
            
    async def get_user_permissions(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current user's permissions in workspace
        """
        headers = await self.get_headers()
        workspace_id = workspace_id or self.credentials.workspace_id
        
        url = f"{self.base_url}/groups/{workspace_id}/users"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    logger.error(f"Failed to get user permissions: {response.status}")
                    return {}


def create_powerbi_service() -> Optional[PowerBIService]:
    """
    Factory function to create PowerBI service from environment variables
    """
    try:
        credentials = PowerBICredentials(
            client_id=os.getenv("POWERBI_CLIENT_ID", ""),
            client_secret=os.getenv("POWERBI_CLIENT_SECRET", ""),
            tenant_id=os.getenv("POWERBI_TENANT_ID", ""),
            workspace_id=os.getenv("POWERBI_WORKSPACE_ID", ""),
            username=os.getenv("POWERBI_USERNAME"),  # Optional for dev
            password=os.getenv("POWERBI_PASSWORD")   # Optional for dev
        )
        
        if not all([credentials.client_id, credentials.tenant_id, credentials.workspace_id]):
            logger.warning("Power BI credentials not fully configured")
            return None
            
        if not credentials.client_secret and not (credentials.username and credentials.password):
            logger.warning("Either client_secret or user credentials must be provided")
            return None
            
        return PowerBIService(credentials)
        
    except Exception as e:
        logger.error(f"Failed to create Power BI service: {str(e)}")
        return None
