#!/usr/bin/env python3
"""Test the standards graph endpoint to verify it's working correctly."""

import requests
import json
import sys
import os

# Get the base URL and auth token
BASE_URL = os.getenv('API_BASE_URL', 'https://app.mapmystandards.com')
AUTH_TOKEN = os.getenv('AUTH_TOKEN', '')

if not AUTH_TOKEN:
    print("Error: Please set AUTH_TOKEN environment variable")
    print("You can get this from localStorage.getItem('access_token') in the browser console")
    sys.exit(1)

# Test the graph endpoint
def test_graph_endpoint():
    headers = {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Test without accreditor
    print("Testing /api/user/intelligence-simple/standards/graph without accreditor...")
    url = f"{BASE_URL}/api/user/intelligence-simple/standards/graph"
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Success! Response structure:")
            print(f"- Accreditor: {data.get('accreditor', 'N/A')}")
            print(f"- Total Standards: {data.get('total_standards', 0)}")
            print(f"- Relationships: {len(data.get('relationships', []))}")
            print(f"- Available Accreditors: {data.get('available_accreditors', [])}")
            
            # Test with a specific accreditor if available
            if data.get('available_accreditors'):
                accreditor = data['available_accreditors'][0]
                print(f"\nTesting with specific accreditor: {accreditor}")
                url_with_acc = f"{BASE_URL}/api/user/intelligence-simple/standards/graph?accreditor={accreditor}"
                response2 = requests.get(url_with_acc, headers=headers)
                print(f"Status Code: {response2.status_code}")
                if response2.status_code == 200:
                    data2 = response2.json()
                    print(f"- Standards for {accreditor}: {data2.get('total_standards', 0)}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_graph_endpoint()