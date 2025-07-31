"""
Integration services for LMS, SIS, and document platforms.
Provides unified interfaces for Canvas, Banner, SharePoint, and other systems.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs, urlparse
import logging
from abc import ABC, abstractmethod

from ..core.config import settings

logger = logging.getLogger(__name__)
# settings imported from config module

class BaseIntegrationService(ABC):
    """Base class for all integration services."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the service."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the service."""
        pass

class CanvasLMSService(BaseIntegrationService):
    """Canvas LMS integration service."""
    
    def __init__(self):
        super().__init__()
        self.client_id = getattr(settings, 'CANVAS_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'CANVAS_CLIENT_SECRET', None)
        self.api_base = getattr(settings, 'CANVAS_API_BASE', 'https://canvas.instructure.com/api/v1')
        self.redirect_uri = getattr(settings, 'CANVAS_REDIRECT_URI', None)
        # Support for personal access token (simpler than OAuth)
        self.access_token: Optional[str] = getattr(settings, 'CANVAS_ACCESS_TOKEN', None)
        self.base_url = getattr(settings, 'CANVAS_BASE_URL', 'https://canvas.instructure.com')
    
    async def authenticate(self) -> bool:
        """Authenticate with Canvas using access token or OAuth 2.0."""
        try:
            # If we have a personal access token, use it directly
            if self.access_token:
                return await self.test_connection()
            
            # Otherwise, use OAuth flow for institutional integration
            if not self.client_id or not self.client_secret:
                logger.warning("No Canvas credentials configured")
                return False
                
            # For server-to-server integration, you'll typically use an access token
            # provided by the Canvas admin rather than OAuth flow
            # This is a placeholder for the OAuth flow
            auth_url = f"{self.base_url}/login/oauth2/auth"
            params = {
                'client_id': self.client_id,
                'response_type': 'code',
                'redirect_uri': self.redirect_uri,
                'scope': 'url:GET|/api/v1/courses url:GET|/api/v1/users url:GET|/api/v1/outcomes'
            }
            
            # In production, you would redirect user to auth_url and handle the callback
            logger.info(f"Canvas OAuth URL: {auth_url}?{urlencode(params)}")
            return True
            
        except Exception as e:
            logger.error(f"Canvas authentication failed: {e}")
            return False
    
    async def exchange_code_for_token(self, code: str) -> Optional[str]:
        """Exchange authorization code for access token."""
        try:
            token_url = f"{self.api_base.replace('/api/v1', '')}/login/oauth2/token"
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': self.redirect_uri,
                'code': code
            }
            
            async with self.session.post(token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data.get('access_token')
                    return self.access_token
                else:
                    logger.error(f"Token exchange failed: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None
    
    async def test_connection(self) -> bool:
        """Test connection to Canvas API."""
        try:
            if not self.access_token:
                return False
            
            headers = {'Authorization': f'Bearer {self.access_token}'}
            async with self.session.get(f"{self.api_base}/users/self", headers=headers) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Canvas connection test failed: {e}")
            return False
    
    async def get_courses(self, enrollment_type: str = 'teacher') -> List[Dict[str, Any]]:
        """Get courses for the authenticated user."""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            params = {'enrollment_type': enrollment_type, 'include[]': ['total_students', 'course_image']}
            
            async with self.session.get(f"{self.api_base}/courses", 
                                      headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get courses: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting courses: {e}")
            return []
    
    async def get_course_outcomes(self, course_id: int) -> List[Dict[str, Any]]:
        """Get learning outcomes for a specific course."""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            async with self.session.get(f"{self.api_base}/courses/{course_id}/outcome_groups", 
                                      headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get outcomes: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting outcomes: {e}")
            return []
    
    async def get_assignments(self, course_id: int) -> List[Dict[str, Any]]:
        """Get assignments for a specific course."""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            params = {'include[]': ['rubric', 'assignment_visibility']}
            
            async with self.session.get(f"{self.api_base}/courses/{course_id}/assignments", 
                                      headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get assignments: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting assignments: {e}")
            return []

class BannerSISService(BaseIntegrationService):
    """Banner SIS integration service."""
    
    def __init__(self):
        super().__init__()
        # Database connection option
        self.db_host = getattr(settings, 'BANNER_DB_HOST', None)
        self.db_port = getattr(settings, 'BANNER_DB_PORT', None)
        self.db_user = getattr(settings, 'BANNER_DB_USER', None)
        self.db_password = getattr(settings, 'BANNER_DB_PASSWORD', None)
        self.db_schema = getattr(settings, 'BANNER_DB_SCHEMA', None)
        
        # Ethos API option
        self.ethos_token = getattr(settings, 'BANNER_ETHOS_TOKEN', None)
        self.ethos_base_url = getattr(settings, 'BANNER_ETHOS_BASE_URL', None)
    
    async def authenticate(self) -> bool:
        """Authenticate with Banner (varies by integration method)."""
        if self.ethos_token:
            return await self._authenticate_ethos()
        elif self.db_host:
            return await self._authenticate_database()
        else:
            logger.error("No Banner authentication method configured")
            return False
    
    async def _authenticate_ethos(self) -> bool:
        """Authenticate with Ethos API."""
        try:
            headers = {'Authorization': f'Bearer {self.ethos_token}'}
            async with self.session.get(f"{self.ethos_base_url}/api", headers=headers) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Ethos authentication failed: {e}")
            return False
    
    async def _authenticate_database(self) -> bool:
        """Test database connection (requires additional DB driver)."""
        try:
            # This would require cx_Oracle or similar Oracle driver
            # Placeholder implementation
            logger.info("Database authentication would be implemented with Oracle driver")
            return True
        except Exception as e:
            logger.error(f"Database authentication failed: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to Banner."""
        return await self.authenticate()
    
    async def get_students(self, term_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get student data from Banner."""
        try:
            if self.ethos_token:
                return await self._get_students_ethos(term_id)
            else:
                return await self._get_students_database(term_id)
        except Exception as e:
            logger.error(f"Error getting students: {e}")
            return []
    
    async def _get_students_ethos(self, term_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get students via Ethos API."""
        headers = {'Authorization': f'Bearer {self.ethos_token}'}
        params = {}
        if term_id:
            params['term'] = term_id
            
        async with self.session.get(f"{self.ethos_base_url}/student-enrollments", 
                                  headers=headers, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to get students: {response.status}")
                return []
    
    async def _get_students_database(self, term_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get students via direct database query."""
        # Placeholder for database implementation
        logger.info("Database query would be implemented with Oracle driver")
        return []
    
    async def get_courses(self, term_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get course data from Banner."""
        try:
            if self.ethos_token:
                headers = {'Authorization': f'Bearer {self.ethos_token}'}
                params = {}
                if term_id:
                    params['term'] = term_id
                    
                async with self.session.get(f"{self.ethos_base_url}/courses", 
                                          headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get courses: {response.status}")
                        return []
            else:
                # Database implementation placeholder
                return []
        except Exception as e:
            logger.error(f"Error getting courses: {e}")
            return []

class SharePointService(BaseIntegrationService):
    """Microsoft SharePoint/OneDrive integration service."""
    
    def __init__(self):
        super().__init__()
        self.client_id = getattr(settings, 'MS_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'MS_CLIENT_SECRET', None)
        self.tenant_id = getattr(settings, 'MS_TENANT_ID', None)
        self.redirect_uri = getattr(settings, 'MS_REDIRECT_URI', None)
        self.access_token: Optional[str] = None
        self.base_url = f"https://graph.microsoft.com/v1.0"
    
    async def authenticate(self) -> bool:
        """Authenticate with Microsoft Graph API."""
        try:
            # Client credentials flow for app-only access
            token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            async with self.session.post(token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data.get('access_token')
                    return True
                else:
                    logger.error(f"MS authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"MS authentication error: {e}")
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to Microsoft Graph."""
        try:
            if not self.access_token:
                return False
            
            headers = {'Authorization': f'Bearer {self.access_token}'}
            async with self.session.get(f"{self.base_url}/sites", headers=headers) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"MS connection test failed: {e}")
            return False
    
    async def get_sites(self) -> List[Dict[str, Any]]:
        """Get SharePoint sites."""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            async with self.session.get(f"{self.base_url}/sites", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('value', [])
                else:
                    logger.error(f"Failed to get sites: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting sites: {e}")
            return []
    
    async def get_site_documents(self, site_id: str) -> List[Dict[str, Any]]:
        """Get documents from a SharePoint site."""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            async with self.session.get(f"{self.base_url}/sites/{site_id}/drive/root/children", 
                                      headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('value', [])
                else:
                    logger.error(f"Failed to get documents: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    async def download_document(self, site_id: str, item_id: str) -> Optional[bytes]:
        """Download a document from SharePoint."""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            async with self.session.get(f"{self.base_url}/sites/{site_id}/drive/items/{item_id}/content", 
                                      headers=headers) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f"Failed to download document: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            return None
    
    async def search_documents(self, query: str, site_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for documents in SharePoint."""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            
            if site_id:
                search_url = f"{self.base_url}/sites/{site_id}/drive/search(q='{query}')"
            else:
                search_url = f"{self.base_url}/search/query"
                body = {
                    "requests": [
                        {
                            "entityTypes": ["driveItem"],
                            "query": {
                                "queryString": query
                            }
                        }
                    ]
                }
                
                async with self.session.post(search_url, headers=headers, json=body) as response:
                    if response.status == 200:
                        data = await response.json()
                        hits = data.get('value', [{}])[0].get('hitsContainers', [{}])[0].get('hits', [])
                        return [hit.get('resource', {}) for hit in hits]
                    else:
                        logger.error(f"Failed to search documents: {response.status}")
                        return []
            
            # Simple site-specific search
            async with self.session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('value', [])
                else:
                    logger.error(f"Failed to search documents: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

class IntegrationManager:
    """Manages all integration services."""
    
    def __init__(self):
        self.canvas = CanvasLMSService()
        self.banner = BannerSISService()
        self.sharepoint = SharePointService()
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all configured services."""
        results = {}
        
        # Test Canvas
        async with self.canvas:
            if self.canvas.client_id and self.canvas.client_secret:
                results['canvas'] = await self.canvas.test_connection()
            else:
                results['canvas'] = False
        
        # Test Banner
        async with self.banner:
            if (self.banner.ethos_token or 
                (self.banner.db_host and self.banner.db_user)):
                results['banner'] = await self.banner.test_connection()
            else:
                results['banner'] = False
        
        # Test SharePoint
        async with self.sharepoint:
            if (self.sharepoint.client_id and 
                self.sharepoint.client_secret and 
                self.sharepoint.tenant_id):
                results['sharepoint'] = await self.sharepoint.test_connection()
            else:
                results['sharepoint'] = False
        
        return results
    
    async def sync_all_data(self) -> Dict[str, Any]:
        """Sync data from all integrated systems."""
        sync_results = {
            'canvas': {'courses': [], 'outcomes': []},
            'banner': {'students': [], 'courses': []},
            'sharepoint': {'sites': [], 'documents': []},
            'errors': []
        }
        
        try:
            # Sync Canvas data
            async with self.canvas:
                if await self.canvas.authenticate():
                    courses = await self.canvas.get_courses()
                    sync_results['canvas']['courses'] = courses
                    
                    # Get outcomes for each course
                    for course in courses[:5]:  # Limit for demo
                        outcomes = await self.canvas.get_course_outcomes(course['id'])
                        sync_results['canvas']['outcomes'].extend(outcomes)
            
            # Sync Banner data
            async with self.banner:
                if await self.banner.authenticate():
                    students = await self.banner.get_students()
                    courses = await self.banner.get_courses()
                    sync_results['banner']['students'] = students
                    sync_results['banner']['courses'] = courses
            
            # Sync SharePoint data
            async with self.sharepoint:
                if await self.sharepoint.authenticate():
                    sites = await self.sharepoint.get_sites()
                    sync_results['sharepoint']['sites'] = sites
                    
                    # Get documents from first site
                    if sites:
                        site_id = sites[0]['id']
                        documents = await self.sharepoint.get_site_documents(site_id)
                        sync_results['sharepoint']['documents'] = documents
        
        except Exception as e:
            sync_results['errors'].append(str(e))
            logger.error(f"Sync error: {e}")
        
        return sync_results

# Global instance
integration_manager = IntegrationManager()
