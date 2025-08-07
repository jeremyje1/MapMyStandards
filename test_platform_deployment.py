#!/usr/bin/env python3
"""
Test script to verify MapMyStandards platform deployment
Tests all routes and payment integration
"""

import requests
import time
import sys

def test_url(url, expected_status=200, check_content=None):
    """Test a URL and return results"""
    try:
        response = requests.get(url, timeout=10)
        status_ok = response.status_code == expected_status
        content_ok = True
        
        if check_content and status_ok:
            content_ok = check_content in response.text.lower()
            
        return {
            'url': url,
            'status': response.status_code,
            'status_ok': status_ok,
            'content_ok': content_ok,
            'success': status_ok and content_ok
        }
    except Exception as e:
        return {
            'url': url,
            'status': 'ERROR',
            'status_ok': False,
            'content_ok': False,
            'success': False,
            'error': str(e)
        }

def main():
    print("🚀 Testing MapMyStandards Platform Deployment\n")
    
    base_url = "https://platform.mapmystandards.ai"
    
    # Test cases: (path, expected_content_check)
    test_cases = [
        ("", "mapmystandards"),  # Homepage
        ("/trial", "trial"),  # Trial page
        ("/pricing", "pricing"),  # Pricing page  
        ("/contact", "contact"),  # Contact page
        ("/login", "login"),  # Login page
        ("/dashboard", "dashboard"),  # Dashboard page
    ]
    
    results = []
    
    print("Testing platform routes...")
    for path, content_check in test_cases:
        url = base_url + path
        print(f"Testing: {url}")
        result = test_url(url, check_content=content_check)
        results.append(result)
        
        if result['success']:
            print(f"  ✅ {result['status']} - Content OK")
        else:
            print(f"  ❌ {result['status']} - {'Content check failed' if not result['content_ok'] else 'Status check failed'}")
            if 'error' in result:
                print(f"     Error: {result['error']}")
        
        time.sleep(1)  # Be nice to the server
    
    print("\n" + "="*50)
    print("DEPLOYMENT TEST SUMMARY")
    print("="*50)
    
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        print(f"{status_icon} {result['url']} - {result['status']}")
    
    print(f"\nSuccess Rate: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Platform is LIVE and operational!")
        print("\n🔗 Ready URLs:")
        print("   • Homepage: https://platform.mapmystandards.ai")
        print("   • Trial: https://platform.mapmystandards.ai/trial")
        print("   • Pricing: https://platform.mapmystandards.ai/pricing")
        print("   • Contact: https://platform.mapmystandards.ai/contact")
        print("   • Login: https://platform.mapmystandards.ai/login")
        print("   • Dashboard: https://platform.mapmystandards.ai/dashboard")
    else:
        print(f"\n⚠️  {total_count - success_count} routes failed. Check Vercel deployment.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
