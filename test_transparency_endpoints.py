#!/usr/bin/env python3
"""Test the new transparency endpoints"""

import requests
import json

API_BASE = "https://api.mapmystandards.ai"

# Test user credentials
test_user = {
    "email": "jeremy.estrella@sait.ca", 
    "password": "Test123!"
}

def get_auth_token():
    """Get auth token for test user"""
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json=test_user
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def test_endpoints(token):
    """Test new transparency endpoints"""
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        # Existing endpoint
        ("Dashboard Metrics", "GET", "/api/user/intelligence-simple/dashboard/metrics"),
        
        # New transparency endpoints
        ("Evidence Mappings Detail", "GET", "/api/user/intelligence-simple/evidence/mappings/detail"),
        ("Trust Scores", "GET", "/api/user/intelligence-simple/evidence/trust-scores"),
        ("Standards Visual Graph", "GET", "/api/user/intelligence-simple/standards/visual-graph"),
    ]
    
    for name, method, path in endpoints:
        print(f"\n{name} ({method} {path})")
        print("-" * 50)
        
        try:
            if method == "GET":
                response = requests.get(f"{API_BASE}{path}", headers=headers)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Success! Response keys: {list(data.keys())}")
                
                # Show sample data for each endpoint
                if "dashboard/metrics" in path:
                    print(f"  Compliance Score: {data.get('compliance_score', 'N/A')}%")
                    print(f"  Standards Mapped: {data.get('standards_mapped', 0)}/{data.get('total_standards', 0)}")
                    print(f"  Documents: {data.get('documents_analyzed', 0)}")
                    
                elif "mappings/detail" in path:
                    print(f"  Total Mappings: {data.get('total_mappings', 0)}")
                    print(f"  Mapping Method: {data.get('transparency', {}).get('mapping_method', 'Unknown')}")
                    docs = data.get('documents', [])
                    if docs:
                        print(f"  First Document: {docs[0].get('document', {}).get('filename', 'N/A')}")
                        
                elif "trust-scores" in path:
                    docs = data.get('documents', [])
                    print(f"  Documents with Trust Scores: {len(docs)}")
                    if docs:
                        print(f"  First Document Trust: {docs[0].get('trust_scores', {}).get('overall', 'N/A')}")
                    agg = data.get('aggregate_trust', {})
                    print(f"  Average Trust: {agg.get('average_trust', 'N/A')}")
                    
                elif "visual-graph" in path:
                    graph = data.get('graph', {})
                    stats = data.get('statistics', {})
                    print(f"  Nodes: {len(graph.get('nodes', []))}")
                    print(f"  Edges: {len(graph.get('edges', []))}")
                    print(f"  Coverage: {stats.get('coverage_percentage', 0)}%")
                    
            else:
                print(f"Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"Exception: {str(e)}")

if __name__ == "__main__":
    print("Testing New Transparency Endpoints")
    print("=" * 70)
    
    token = get_auth_token()
    if token:
        print(f"✓ Authenticated successfully")
        test_endpoints(token)
    else:
        print("✗ Failed to authenticate")