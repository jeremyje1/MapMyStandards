#!/usr/bin/env python3
"""
Reload standards corpus from existing YAML files in data/standards directory.
This script loads all available accreditation standards into the system.
"""
import os
import sys
import requests
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from a3e.services.standards_graph import standards_graph  # noqa: E402

def reload_standards():
    """Reload standards from the data/standards directory"""
    print("Reloading standards corpus...")
    
    # Get the path to standards directory
    repo_root = Path(__file__).parent
    standards_dir = repo_root / "data" / "standards"
    
    print(f"Loading standards from: {standards_dir}")
    
    # Reload the graph from corpus
    stats = standards_graph.reload_from_corpus(
        corpus_dir=str(standards_dir),
        fallback_to_seed=True
    )
    
    print("\nReload complete!")
    print(f"Graph statistics: {stats}")
    
    # Print detailed information about loaded standards
    print("\nLoaded accreditors:")
    for accreditor in sorted(standards_graph.accreditor_roots.keys()):
        standards = standards_graph.get_accreditor_standards(accreditor)
        print(f"  - {accreditor}: {len(standards)} standards")

def test_api_reload():
    """Test reloading via API endpoint"""
    print("\nTesting API reload endpoint...")
    
    # Get token from environment or use a test token
    token = os.environ.get('A3E_API_KEY', '')
    if not token:
        print("No API key found in environment. Trying without authentication...")
    
    api_url = "http://localhost:8000/api/user/intelligence-simple/standards/byol/reload"
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    try:
        response = requests.post(api_url, headers=headers, json={
            "path": "data/standards",
            "fallback_to_seed": True
        })
        
        if response.status_code == 200:
            print("API reload successful!")
            print(f"Response: {response.json()}")
        else:
            print(f"API reload failed with status {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error calling API: {e}")

def main():
    # First reload directly
    reload_standards()
    
    # Then try API reload if server is running
    print("\n" + "="*50)
    test_api_reload()

if __name__ == "__main__":
    main()
