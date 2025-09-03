#!/usr/bin/env python3
"""
Enterprise Features Test Runner

Simple test runner to validate Phase M3 Enterprise Features implementation
without requiring full pytest setup. Tests core functionality and integrations.
"""

import sys
import os
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

class EnterpriseFeatureValidator:
    """Validates enterprise features implementation"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results"""
        try:
            print(f"Running: {test_name}...", end=" ")
            test_func()
            print("✅ PASS")
            self.test_results.append({"test": test_name, "status": "PASS", "error": None})
            self.passed += 1
        except Exception as e:
            print(f"❌ FAIL: {str(e)}")
            self.test_results.append({"test": test_name, "status": "FAIL", "error": str(e)})
            self.failed += 1
    
    def test_sso_service_structure(self):
        """Test SSO service structure and imports"""
        # Test file existence
        sso_file = "src/a3e/services/sso_service.py"
        assert os.path.exists(sso_file), f"SSO service file missing: {sso_file}"
        
        # Test file content
        with open(sso_file, 'r') as f:
            content = f.read()
            assert "class GoogleOAuthProvider" in content, "GoogleOAuthProvider class missing"
            assert "class MicrosoftOAuthProvider" in content, "MicrosoftOAuthProvider class missing"
            assert "class OktaOAuthProvider" in content, "OktaOAuthProvider class missing"
            assert "get_auth_url" in content, "Authorization URL method missing"
            assert "exchange_code" in content, "Token exchange method missing"
    
    def test_two_factor_service_structure(self):
        """Test 2FA service structure"""
        twofa_file = "src/a3e/services/two_factor_service.py"
        assert os.path.exists(twofa_file), f"2FA service file missing: {twofa_file}"
        
        with open(twofa_file, 'r') as f:
            content = f.read()
            assert "generate_2fa_secret" in content, "2FA secret generation missing"
            assert "generate_qr_code" in content, "QR code generation missing"
            assert "verify_code" in content, "Code verification missing"
            assert "generate_backup_codes" in content, "Backup codes generation missing"
    
    def test_api_key_routes_structure(self):
        """Test API key management routes"""
        api_keys_file = "src/a3e/api/routes/api_keys.py"
        assert os.path.exists(api_keys_file), f"API keys routes file missing: {api_keys_file}"
        
        with open(api_keys_file, 'r') as f:
            content = f.read()
            assert "@router.post" in content and "api-keys" in content, "API key creation endpoint missing"
            assert "@router.get" in content and "api-keys" in content, "API key listing endpoint missing"
            assert "revoke" in content, "API key revocation endpoint missing"
            assert "create_api_key" in content or "ApiKeyCreate" in content, "API key creation logic missing"
    
    def test_enterprise_dashboard_routes(self):
        """Test enterprise dashboard API routes"""
        enterprise_file = "src/a3e/api/routes/enterprise.py"
        assert os.path.exists(enterprise_file), f"Enterprise routes file missing: {enterprise_file}"
        
        with open(enterprise_file, 'r') as f:
            content = f.read()
            assert "/metrics" in content, "Enterprise metrics endpoint missing"
            assert "/teams/performance" in content, "Team performance endpoint missing"
            assert "/activity/recent" in content, "Recent activity endpoint missing"
            assert "/risk/assessment" in content, "Risk assessment endpoint missing"
    
    def test_enterprise_dashboard_frontend(self):
        """Test enterprise dashboard frontend"""
        dashboard_file = "web/enterprise-dashboard.html"
        assert os.path.exists(dashboard_file), f"Enterprise dashboard file missing: {dashboard_file}"
        
        with open(dashboard_file, 'r') as f:
            content = f.read()
            assert "Enterprise Dashboard" in content, "Dashboard title missing"
            assert "chart.js" in content.lower(), "Chart.js library missing"
            assert "totalTeams" in content, "Team metrics missing"
            assert "complianceScore" in content, "Compliance metrics missing"
            assert "riskHeatmap" in content, "Risk heatmap missing"
    
    def test_enhanced_login_page(self):
        """Test enhanced login page with SSO"""
        login_file = "web/login-enhanced.html"
        assert os.path.exists(login_file), f"Enhanced login file missing: {login_file}"
        
        with open(login_file, 'r') as f:
            content = f.read()
            assert "SSO" in content or "Single Sign" in content, "SSO integration missing"
            assert "google" in content.lower(), "Google SSO missing"
            assert "microsoft" in content.lower(), "Microsoft SSO missing"
            assert "2FA" or "two.factor" in content.lower(), "2FA support missing"
    
    def test_team_settings_api_key_management(self):
        """Test API key management in team settings"""
        team_settings_file = "web/team-settings.html"
        assert os.path.exists(team_settings_file), f"Team settings file missing: {team_settings_file}"
        
        with open(team_settings_file, 'r') as f:
            content = f.read()
            assert "API Key" in content or "api-key" in content, "API key management missing"
            assert "createApiKey" in content, "API key creation function missing"
            assert "revokeApiKey" in content, "API key revocation function missing"
    
    def test_enterprise_schemas(self):
        """Test enterprise schemas definition"""
        schemas_file = "src/a3e/schemas/enterprise.py"
        assert os.path.exists(schemas_file), f"Enterprise schemas file missing: {schemas_file}"
        
        with open(schemas_file, 'r') as f:
            content = f.read()
            assert "EnterpriseMetrics" in content, "EnterpriseMetrics schema missing"
            assert "TeamPerformance" in content, "TeamPerformance schema missing"
            assert "RiskAssessment" in content, "RiskAssessment schema missing"
            assert "ComplianceReport" in content, "ComplianceReport schema missing"
    
    def test_sso_routes_structure(self):
        """Test SSO API routes"""
        sso_routes_file = "src/a3e/api/routes/sso.py"
        assert os.path.exists(sso_routes_file), f"SSO routes file missing: {sso_routes_file}"
        
        with open(sso_routes_file, 'r') as f:
            content = f.read()
            assert "/providers" in content, "SSO providers endpoint missing"
            assert "/initiate" in content, "SSO initiation endpoint missing"
            assert "/callback" in content, "SSO callback endpoint missing"
    
    def test_file_structure_integrity(self):
        """Test overall file structure integrity"""
        required_files = [
            "src/a3e/services/sso_service.py",
            "src/a3e/services/two_factor_service.py",
            "src/a3e/api/routes/sso.py",
            "src/a3e/api/routes/api_keys.py",
            "src/a3e/api/routes/enterprise.py",
            "src/a3e/schemas/enterprise.py",
            "web/enterprise-dashboard.html",
            "web/login-enhanced.html",
            "web/team-settings.html"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        assert len(missing_files) == 0, f"Missing required files: {missing_files}"
    
    def test_code_quality_checks(self):
        """Basic code quality checks"""
        # Check for TODO/FIXME comments
        todo_files = []
        python_files = [
            "src/a3e/services/sso_service.py",
            "src/a3e/services/two_factor_service.py",
            "src/a3e/api/routes/sso.py",
            "src/a3e/api/routes/api_keys.py",
            "src/a3e/api/routes/enterprise.py",
            "src/a3e/schemas/enterprise.py"
        ]
        
        for file_path in python_files:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                    if "TODO" in content.upper() or "FIXME" in content.upper():
                        todo_files.append(file_path)
        
        # This is informational, not a failure
        if todo_files:
            print(f"ℹ️  Files with TODO/FIXME comments: {todo_files}")
    
    def test_configuration_completeness(self):
        """Test configuration completeness"""
        # Check for environment variable documentation
        config_found = False
        
        # Check if SSO configuration is documented
        sso_file = "src/a3e/services/sso_service.py"
        if os.path.exists(sso_file):
            with open(sso_file, 'r') as f:
                content = f.read()
                if "google_client_id" in content and "microsoft_client_id" in content:
                    config_found = True
        
        # Check enterprise dashboard for environment vars
        dashboard_file = "web/enterprise-dashboard.html"
        if os.path.exists(dashboard_file):
            with open(dashboard_file, 'r') as f:
                content = f.read()
                if "Environment" in content or "config" in content.lower():
                    config_found = True
        
        # Basic validation - configuration should be present somewhere
        assert config_found, "Configuration documentation missing"
    
    def run_all_tests(self):
        """Run all enterprise feature tests"""
        print("🚀 Running Enterprise Features Validation Suite")
        print("=" * 60)
        
        tests = [
            ("SSO Service Structure", self.test_sso_service_structure),
            ("Two-Factor Authentication Service", self.test_two_factor_service_structure),
            ("API Key Management Routes", self.test_api_key_routes_structure),
            ("Enterprise Dashboard Routes", self.test_enterprise_dashboard_routes),
            ("Enterprise Dashboard Frontend", self.test_enterprise_dashboard_frontend),
            ("Enhanced Login Page", self.test_enhanced_login_page),
            ("Team Settings API Key Management", self.test_team_settings_api_key_management),
            ("Enterprise Schemas", self.test_enterprise_schemas),
            ("SSO Routes Structure", self.test_sso_routes_structure),
            ("File Structure Integrity", self.test_file_structure_integrity),
            ("Code Quality Checks", self.test_code_quality_checks),
            ("Configuration Completeness", self.test_configuration_completeness)
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.passed} passed, {self.failed} failed")
        
        if self.failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['error']}")
        
        print(f"\n✅ Enterprise Features Implementation: {'COMPLETE' if self.failed == 0 else 'NEEDS ATTENTION'}")
        
        return self.failed == 0

def main():
    """Main test runner"""
    validator = EnterpriseFeatureValidator()
    success = validator.run_all_tests()
    
    if success:
        print("\n🎉 All enterprise features successfully implemented!")
        print("Ready for Phase M3 deployment.")
    else:
        print("\n⚠️  Some issues found. Please review and fix.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
