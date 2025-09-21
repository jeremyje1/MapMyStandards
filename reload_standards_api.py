#!/usr/bin/env python3
"""
Reload standards corpus via API endpoint.
This script calls the reload API to refresh all available standards.
"""
import os
import sys
import requests
import json

def get_api_token():
    """Get API token from environment or database"""
    # Try environment first
    token = os.environ.get('A3E_API_KEY')
    if token:
        return token
    
    # Try reading from database
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        from a3e.core.database import DatabaseService
        
        db = DatabaseService()
        with db.get_session() as session:
            # Get the first user's API key as a fallback
            result = session.execute("SELECT api_key FROM users WHERE api_key IS NOT NULL LIMIT 1")
            row = result.fetchone()
            if row:
                return row[0]
    except Exception as e:
        print(f"Warning: Could not fetch API key from database: {e}")
    
    return None

def reload_standards_via_api(base_url="https://platform.mapmystandards.ai"):
    """Reload standards using the API endpoint"""
    token = get_api_token()
    
    if not token:
        print("Error: No API token found. Please set A3E_API_KEY environment variable.")
        return False
    
    # Prepare headers
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Call reload endpoint
    reload_url = f"{base_url}/api/user/intelligence-simple/standards/byol/reload"
    
    print(f"Calling reload endpoint at: {reload_url}")
    
    try:
        # Try POST first
        response = requests.post(reload_url, headers=headers, json={
            "path": "data/standards",
            "fallback_to_seed": True
        })
        
        # If POST fails with 405, try GET
        if response.status_code == 405:
            print("POST not allowed, trying GET...")
            response = requests.get(reload_url, headers=headers, params={
                "path": "data/standards",
                "fallback_to_seed": "true"
            })
        
        if response.status_code == 200:
            print("\nReload successful!")
            result = response.json()
            
            # Display results
            if 'graph' in result:
                print(f"\nGraph statistics:")
                print(json.dumps(result['graph'], indent=2))
            
            if 'corpus' in result:
                print(f"\nCorpus information:")
                print(json.dumps(result['corpus'], indent=2))
            
            return True
        else:
            print(f"\nReload failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\nError: Cannot connect to {base_url}")
        print("Make sure the server is running or use a different base URL.")
        return False
    except Exception as e:
        print(f"\nError calling API: {e}")
        return False

def check_corpus_status(base_url="https://platform.mapmystandards.ai"):
    """Check the current corpus status"""
    token = get_api_token()
    
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    status_url = f"{base_url}/api/user/intelligence-simple/standards/corpus/status"
    
    try:
        response = requests.get(status_url, headers=headers)
        if response.status_code == 200:
            print("\nCurrent corpus status:")
            print(json.dumps(response.json(), indent=2))
    except Exception as e:
        print(f"Error checking status: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Reload standards corpus via API')
    parser.add_argument('--url', default='https://platform.mapmystandards.ai',
                        help='Base URL of the platform (default: https://platform.mapmystandards.ai)')
    parser.add_argument('--local', action='store_true',
                        help='Use local development server (http://localhost:8000)')
    
    args = parser.parse_args()
    
    base_url = 'http://localhost:8000' if args.local else args.url
    
    print(f"Using platform at: {base_url}")
    
    # First check current status
    check_corpus_status(base_url)
    
    # Then reload
    print("\n" + "="*50)
    success = reload_standards_via_api(base_url)
    
    # Check status again after reload
    if success:
        print("\n" + "="*50)
        check_corpus_status(base_url)

if __name__ == "__main__":
    main()
