#!/usr/bin/env python3
"""
Test script for new API endpoints
Tests org chart, scenarios, and enterprise metrics APIs
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# Test token (replace with actual token from login)
AUTH_TOKEN = "your_jwt_token_here"

# Headers
headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}


def test_org_chart_api():
    """Test organization chart endpoints"""
    print("\n=== Testing Organization Chart API ===")
    
    # Create org chart
    org_data = {
        "name": "Test University Org Chart",
        "description": "Compliance structure for Test University",
        "institution_type": "University",
        "total_employees": 500,
        "data": {
            "nodes": [
                {
                    "id": "1",
                    "label": "President",
                    "title": "University President",
                    "level": 1,
                    "compliance_areas": ["Overall Compliance", "Board Relations"]
                },
                {
                    "id": "2",
                    "label": "Provost",
                    "title": "Chief Academic Officer",
                    "level": 2,
                    "department": "Academic Affairs",
                    "compliance_areas": ["Academic Programs", "Faculty Credentials"]
                },
                {
                    "id": "3",
                    "label": "VP Finance",
                    "title": "VP of Finance & Administration",
                    "level": 2,
                    "department": "Finance",
                    "compliance_areas": ["Financial Compliance", "Audit"]
                }
            ],
            "edges": [
                {"id": "e1", "from": "1", "to": "2"},
                {"id": "e2", "from": "1", "to": "3"}
            ]
        }
    }
    
    # POST - Create chart
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/org-chart",
        headers=headers,
        json=org_data
    )
    print(f"Create org chart: {response.status_code}")
    if response.ok:
        result = response.json()
        print(f"Created chart ID: {result.get('id')}")
    else:
        print(f"Error: {response.text}")
    
    # GET - List charts
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/org-chart",
        headers=headers
    )
    print(f"List org charts: {response.status_code}")


def test_scenarios_api():
    """Test scenario modeling endpoints"""
    print("\n=== Testing Scenarios API ===")
    
    # Test calculation without saving
    scenario_inputs = {
        "institution_name": "Test Community College",
        "institution_type": "Community College",
        "student_enrollment": 5000,
        "faculty_count": 150,
        "staff_count": 100,
        "annual_budget": 35000000,
        "compliance_team_size": 2,
        "accreditations_count": 4,
        "reports_per_year": 16,
        "hours_per_report": 45,
        "avg_hourly_rate": 75
    }
    
    # POST - Calculate ROI
    response = requests.post(
        f"{BASE_URL}{API_PREFIX}/scenarios/calculate",
        headers=headers,
        json=scenario_inputs
    )
    print(f"Calculate scenario: {response.status_code}")
    if response.ok:
        results = response.json()
        print(f"Annual savings: ${results.get('annual_savings'):,.2f}")
        print(f"ROI percentage: {results.get('roi_percentage'):.1f}%")
        print(f"Payback period: {results.get('payback_period_months')} months")
    else:
        print(f"Error: {response.text}")
    
    # GET - Templates
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/scenarios/templates",
        headers=headers
    )
    print(f"Get templates: {response.status_code}")
    if response.ok:
        templates = response.json()
        print(f"Available templates: {len(templates)} found")


def test_enterprise_metrics_api():
    """Test enterprise metrics endpoints"""
    print("\n=== Testing Enterprise Metrics API ===")
    
    # GET - Enterprise metrics
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/metrics/enterprise?time_range=30d",
        headers=headers
    )
    print(f"Get enterprise metrics: {response.status_code}")
    if response.ok:
        metrics = response.json()
        overall = metrics.get('overall_metrics', {})
        print(f"Compliance score: {overall.get('compliance_score', {}).get('value')}%")
        print(f"Departments tracked: {len(metrics.get('department_performance', []))}")
        print(f"Upcoming deadlines: {len(metrics.get('upcoming_deadlines', []))}")
    else:
        print(f"Error: {response.text}")
    
    # GET - Department details
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/metrics/departments",
        headers=headers
    )
    print(f"Get department metrics: {response.status_code}")
    
    # GET - Compliance trend
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/metrics/compliance-trend?days=30",
        headers=headers
    )
    print(f"Get compliance trend: {response.status_code}")


def test_powerbi_api():
    """Test Power BI integration endpoints"""
    print("\n=== Testing Power BI API ===")
    
    # GET - Configuration status
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/powerbi/config",
        headers=headers
    )
    print(f"Check Power BI config: {response.status_code}")
    if response.ok:
        config = response.json()
        print(f"Configured: {config.get('configured')}")
        if config.get('error_message'):
            print(f"Error: {config.get('error_message')}")
    else:
        print(f"Error: {response.text}")
    
    # GET - Datasets
    response = requests.get(
        f"{BASE_URL}{API_PREFIX}/powerbi/datasets",
        headers=headers
    )
    print(f"List datasets: {response.status_code}")


def main():
    """Run all API tests"""
    print("Starting API tests...")
    print(f"Base URL: {BASE_URL}")
    print(f"API Prefix: {API_PREFIX}")
    
    # Note: You need to set a valid AUTH_TOKEN first
    if AUTH_TOKEN == "your_jwt_token_here":
        print("\n⚠️  WARNING: Please set a valid AUTH_TOKEN in the script!")
        print("You can get a token by logging in via the web interface or API")
        print("\nTo get a token via API:")
        print("curl -X POST http://localhost:8000/api/v1/auth/login \\")
        print('  -H "Content-Type: application/json" \\')
        print('  -d \'{"email": "your@email.com", "password": "yourpassword"}\'')
        return
    
    try:
        test_org_chart_api()
        test_scenarios_api()
        test_enterprise_metrics_api()
        test_powerbi_api()
        
        print("\n✅ All API tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the server.")
        print("Make sure the FastAPI server is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")


if __name__ == "__main__":
    main()
