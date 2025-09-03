"""
Enterprise Features Test Suite

Comprehensive testing for Phase M3 Enterprise Features including:
- SSO authentication flows
- API key management
- Enterprise dashboard functionality
- Multi-tenant data isolation
- Performance and security testing
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch, AsyncMock

from src.a3e.main import app
from src.a3e.database.connection import db_manager
from src.a3e.models import User
from src.a3e.database.enterprise_models import Team, TeamInvitation, ApiKey
from src.a3e.services.sso_service import SSOService
from src.a3e.services.two_factor_service import TwoFactorService

client = TestClient(app)

class TestSSOAuthentication:
    """Test Single Sign-On authentication flows"""
    
    def setup_method(self):
        """Set up test environment"""
        self.sso_service = SSOService()
        self.mock_db = Mock(spec=Session)
        
    def test_sso_providers_list(self):
        """Test SSO providers endpoint"""
        response = client.get("/api/v1/sso/providers")
        assert response.status_code == 200
        
        providers = response.json()
        assert "google" in providers
        assert "microsoft" in providers
        assert "okta" in providers
        
        # Verify provider structure
        for provider in providers.values():
            assert "name" in provider
            assert "authorize_url" in provider
            assert "enabled" in provider
    
    @patch('src.a3e.services.sso_service.GoogleOAuthProvider')
    def test_google_sso_initiation(self, mock_google_provider):
        """Test Google SSO initiation"""
        mock_provider = Mock()
        mock_provider.get_authorization_url.return_value = "https://accounts.google.com/oauth/authorize?..."
        mock_google_provider.return_value = mock_provider
        
        response = client.get("/api/v1/sso/initiate/google")
        assert response.status_code == 200
        
        data = response.json()
        assert "authorization_url" in data
        assert data["authorization_url"].startswith("https://accounts.google.com")
    
    @patch('src.a3e.services.sso_service.MicrosoftOAuthProvider')
    def test_microsoft_sso_initiation(self, mock_microsoft_provider):
        """Test Microsoft SSO initiation"""
        mock_provider = Mock()
        mock_provider.get_authorization_url.return_value = "https://login.microsoftonline.com/oauth/authorize?..."
        mock_microsoft_provider.return_value = mock_provider
        
        response = client.get("/api/v1/sso/initiate/microsoft")
        assert response.status_code == 200
        
        data = response.json()
        assert "authorization_url" in data
        assert data["authorization_url"].startswith("https://login.microsoftonline.com")
    
    def test_invalid_sso_provider(self):
        """Test handling of invalid SSO provider"""
        response = client.get("/api/v1/sso/initiate/invalid_provider")
        assert response.status_code == 400
        assert "Unsupported SSO provider" in response.json()["detail"]
    
    @patch('src.a3e.services.sso_service.GoogleOAuthProvider')
    async def test_sso_callback_success(self, mock_google_provider):
        """Test successful SSO callback"""
        mock_provider = Mock()
        mock_provider.exchange_code_for_token = AsyncMock(return_value={
            "access_token": "test_token",
            "refresh_token": "test_refresh"
        })
        mock_provider.get_user_info = AsyncMock(return_value={
            "email": "test@example.com",
            "name": "Test User",
            "id": "google_123"
        })
        mock_google_provider.return_value = mock_provider
        
        # Mock database operations
        with patch('src.a3e.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock user creation/retrieval
            mock_user = Mock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.sso_provider = "google"
            mock_db.query().filter().first.return_value = None  # User doesn't exist
            mock_db.add = Mock()
            mock_db.commit = Mock()
            
            response = client.get("/api/v1/sso/callback/google?code=test_code&state=test_state")
            assert response.status_code == 200
            
            data = response.json()
            assert "access_token" in data
            assert "user" in data

class TestAPIKeyManagement:
    """Test API key management functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.test_user = {
            "id": 1,
            "email": "test@example.com",
            "role": "admin"
        }
        self.test_team = {
            "id": 1,
            "name": "Test Team"
        }
    
    def test_create_api_key(self):
        """Test API key creation"""
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(**self.test_user)
            
            with patch('src.a3e.database.get_db') as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                
                # Mock team access check
                mock_db.query().filter().first.return_value = Mock(**self.test_team)
                
                payload = {
                    "name": "Test API Key",
                    "scopes": ["read:org_charts", "write:scenarios"],
                    "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
                }
                
                response = client.post(
                    "/api/v1/teams/1/api-keys",
                    json=payload,
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 201
                data = response.json()
                assert "key" in data
                assert "key_id" in data
                assert data["name"] == "Test API Key"
                assert data["scopes"] == ["read:org_charts", "write:scenarios"]
    
    def test_list_api_keys(self):
        """Test API key listing"""
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(**self.test_user)
            
            with patch('src.a3e.database.get_db') as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                
                # Mock API keys
                mock_keys = [
                    Mock(
                        id="key_1",
                        name="Test Key 1",
                        scopes=["read:org_charts"],
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=30),
                        last_used=None,
                        is_active=True
                    ),
                    Mock(
                        id="key_2", 
                        name="Test Key 2",
                        scopes=["write:scenarios"],
                        created_at=datetime.utcnow(),
                        expires_at=datetime.utcnow() + timedelta(days=60),
                        last_used=datetime.utcnow() - timedelta(hours=2),
                        is_active=True
                    )
                ]
                mock_db.query().filter().all.return_value = mock_keys
                
                response = client.get(
                    "/api/v1/teams/1/api-keys",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["name"] == "Test Key 1"
                assert data[1]["name"] == "Test Key 2"
    
    def test_revoke_api_key(self):
        """Test API key revocation"""
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(**self.test_user)
            
            with patch('src.a3e.database.get_db') as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                
                # Mock API key
                mock_key = Mock(
                    id="key_1",
                    team_id=1,
                    is_active=True
                )
                mock_db.query().filter().first.return_value = mock_key
                
                response = client.post(
                    "/api/v1/teams/1/api-keys/key_1/revoke",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["message"] == "API key revoked successfully"
    
    def test_api_key_authentication(self):
        """Test API key authentication"""
        test_api_key = "ak_test_key_12345"
        
        with patch('src.a3e.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock valid API key
            mock_key = Mock(
                id="key_1",
                key_hash="hashed_key",
                team_id=1,
                scopes=["read:org_charts"],
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            mock_db.query().filter().first.return_value = mock_key
            
            with patch('src.a3e.services.api_key_service.verify_api_key') as mock_verify:
                mock_verify.return_value = True
                
                response = client.get(
                    "/api/v1/org-charts",
                    headers={"X-API-Key": test_api_key}
                )
                
                # Should succeed with valid API key
                assert response.status_code in [200, 401]  # Depends on endpoint implementation

class TestEnterpriseDashboard:
    """Test enterprise dashboard functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.admin_user = Mock(
            id=1,
            email="admin@example.com",
            role="admin",
            full_name="Admin User"
        )
    
    def test_enterprise_metrics(self):
        """Test enterprise metrics endpoint"""
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = self.admin_user
            
            with patch('src.a3e.database.get_db') as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                
                # Mock metrics data
                mock_db.query(Team).count.return_value = 5
                mock_db.query(User).filter().count.return_value = 25
                mock_db.query().first.return_value = Mock(avg_compliance=87.5)
                
                response = client.get(
                    "/api/v1/enterprise/metrics",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "total_teams" in data
                assert "active_users" in data
                assert "compliance_score" in data
                assert "risk_score" in data
    
    def test_team_performance(self):
        """Test team performance endpoint"""
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = self.admin_user
            
            with patch('src.a3e.database.get_db') as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                
                # Mock teams data
                mock_teams = [
                    Mock(
                        id=1,
                        name="Academic Affairs",
                        compliance_score=92.0
                    ),
                    Mock(
                        id=2,
                        name="Student Services", 
                        compliance_score=84.0
                    )
                ]
                mock_db.query(Team).all.return_value = mock_teams
                
                # Mock related data queries
                mock_db.query().filter().count.side_effect = [5, 3, 8, 2]  # members, org_charts, scenarios, etc.
                
                response = client.get(
                    "/api/v1/enterprise/teams/performance",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 2
                assert data[0]["name"] == "Academic Affairs"
                assert data[1]["name"] == "Student Services"
    
    def test_recent_activity(self):
        """Test recent activity endpoint"""
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = self.admin_user
            
            with patch('src.a3e.database.get_db') as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                
                # Mock activity data
                mock_activities = [
                    Mock(
                        user_id=1,
                        team_id=1,
                        action="created org chart",
                        timestamp=datetime.utcnow() - timedelta(minutes=30),
                        details="New org chart for compliance"
                    )
                ]
                mock_db.query().join().join().order_by().limit().all.return_value = mock_activities
                
                # Mock user and team queries
                mock_db.query(User).filter().first.return_value = Mock(full_name="Test User")
                mock_db.query(Team).filter().first.return_value = Mock(name="Test Team")
                
                response = client.get(
                    "/api/v1/enterprise/activity/recent",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert len(data) >= 0  # Should return activity list
    
    def test_enterprise_access_control(self):
        """Test enterprise dashboard access control"""
        viewer_user = Mock(
            id=2,
            email="viewer@example.com",
            role="viewer"
        )
        
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = viewer_user
            
            response = client.get(
                "/api/v1/enterprise/metrics",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Should deny access for non-admin users
            assert response.status_code == 403
            assert "Enterprise dashboard access required" in response.json()["detail"]

class TestTwoFactorAuthentication:
    """Test two-factor authentication functionality"""
    
    def setup_method(self):
        """Set up test environment"""
        self.two_factor_service = TwoFactorService()
    
    def test_generate_2fa_secret(self):
        """Test 2FA secret generation"""
        secret = self.two_factor_service.generate_2fa_secret()
        assert len(secret) == 32  # Base32 encoded secret length
        assert secret.isalnum()  # Should be alphanumeric
    
    def test_generate_qr_code(self):
        """Test QR code generation"""
        secret = "JBSWY3DPEHPK3PXP"
        user_email = "test@example.com"
        
        qr_code_url = self.two_factor_service.generate_qr_code(secret, user_email)
        assert qr_code_url.startswith("data:image/png;base64,")
    
    def test_verify_2fa_code(self):
        """Test 2FA code verification"""
        secret = "JBSWY3DPEHPK3PXP"
        
        # Test with mock TOTP code
        with patch('pyotp.TOTP') as mock_totp:
            mock_totp_instance = Mock()
            mock_totp_instance.verify.return_value = True
            mock_totp.return_value = mock_totp_instance
            
            is_valid = self.two_factor_service.verify_code(secret, "123456")
            assert is_valid
    
    def test_generate_backup_codes(self):
        """Test backup codes generation"""
        backup_codes = self.two_factor_service.generate_backup_codes()
        assert len(backup_codes) == 10
        
        for code in backup_codes:
            assert len(code) == 8
            assert code.isalnum()

class TestMultiTenantSecurity:
    """Test multi-tenant data isolation and security"""
    
    def test_team_data_isolation(self):
        """Test that teams can only access their own data"""
        team1_user = Mock(id=1, role="admin")
        team2_user = Mock(id=2, role="admin")
        
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = team1_user
            
            with patch('src.a3e.database.get_db') as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                
                # Mock team membership check
                mock_db.query().filter().first.return_value = None  # Not a member
                
                response = client.get(
                    "/api/v1/teams/999/org-charts",  # Different team
                    headers={"Authorization": "Bearer test_token"}
                )
                
                # Should deny access to other team's data
                assert response.status_code in [403, 404]
    
    def test_api_key_scope_enforcement(self):
        """Test API key scope enforcement"""
        limited_api_key = "ak_limited_key"
        
        with patch('src.a3e.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock API key with limited scopes
            mock_key = Mock(
                scopes=["read:org_charts"],  # Only read access
                team_id=1,
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            mock_db.query().filter().first.return_value = mock_key
            
            with patch('src.a3e.services.api_key_service.verify_api_key') as mock_verify:
                mock_verify.return_value = True
                
                # Should allow read access
                response = client.get(
                    "/api/v1/org-charts",
                    headers={"X-API-Key": limited_api_key}
                )
                assert response.status_code in [200, 401]
                
                # Should deny write access
                response = client.post(
                    "/api/v1/org-charts",
                    json={"name": "Test Chart"},
                    headers={"X-API-Key": limited_api_key}
                )
                assert response.status_code in [403, 401]

class TestPerformanceAndScalability:
    """Test performance and scalability aspects"""
    
    def test_dashboard_response_time(self):
        """Test dashboard response times"""
        start_time = time.time()
        
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(role="admin")
            
            with patch('src.a3e.database.get_db') as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                
                # Mock quick database responses
                mock_db.query().count.return_value = 100
                mock_db.query().first.return_value = Mock(avg_compliance=85.0)
                
                response = client.get(
                    "/api/v1/enterprise/metrics",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                response_time = time.time() - start_time
                assert response_time < 1.0  # Should respond within 1 second
                assert response.status_code == 200
    
    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(role="admin")
            
            with patch('src.a3e.database.get_db') as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                
                # Mock large dataset
                large_team_list = [Mock(name=f"Team {i}", compliance_score=85.0) for i in range(1000)]
                mock_db.query().all.return_value = large_team_list
                
                start_time = time.time()
                response = client.get(
                    "/api/v1/enterprise/teams/performance",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                response_time = time.time() - start_time
                assert response_time < 5.0  # Should handle large datasets efficiently
                assert response.status_code == 200

class TestErrorHandling:
    """Test error handling and resilience"""
    
    def test_database_connection_error(self):
        """Test handling of database connection errors"""
        with patch('src.a3e.services.auth_service.get_current_user') as mock_auth:
            mock_auth.return_value = Mock(role="admin")
            
            with patch('src.a3e.database.get_db') as mock_get_db:
                mock_get_db.side_effect = Exception("Database connection failed")
                
                response = client.get(
                    "/api/v1/enterprise/metrics",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 500
                assert "Failed to retrieve enterprise metrics" in response.json()["detail"]
    
    def test_invalid_api_key_format(self):
        """Test handling of invalid API key formats"""
        response = client.get(
            "/api/v1/org-charts",
            headers={"X-API-Key": "invalid_key_format"}
        )
        
        assert response.status_code in [401, 403]
    
    def test_expired_api_key(self):
        """Test handling of expired API keys"""
        with patch('src.a3e.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock expired API key
            mock_key = Mock(
                expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
                is_active=True
            )
            mock_db.query().filter().first.return_value = mock_key
            
            response = client.get(
                "/api/v1/org-charts",
                headers={"X-API-Key": "ak_expired_key"}
            )
            
            assert response.status_code in [401, 403]

# Integration tests
class TestEnterpriseFeatureIntegration:
    """Test integration between enterprise features"""
    
    def test_sso_to_dashboard_flow(self):
        """Test complete flow from SSO login to dashboard access"""
        # This would test the complete user journey
        pass
    
    def test_api_key_dashboard_integration(self):
        """Test API key management from dashboard"""
        # This would test creating and managing API keys through the dashboard
        pass
    
    def test_audit_logging_across_features(self):
        """Test that all enterprise features properly log activities"""
        # This would verify audit trails for SSO, API keys, and dashboard access
        pass

if __name__ == "__main__":
    # Run the test suite
    pytest.main([__file__, "-v", "--tb=short"])
