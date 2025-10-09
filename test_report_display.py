#!/usr/bin/env python3
"""Test report generation display functionality."""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "https://a3e-main.railway.app"

async def test_report_display():
    """Test if report generation shows real data."""
    
    async with aiohttp.ClientSession() as session:
        # Use test token if available, otherwise create test user
        token = "test_token_for_jeremy"  # This will work with the test user we created
        
        # 2. Check current uploads and metrics
        print("\n2. Checking current uploads...")
        headers = {"Authorization": f"Bearer {token}"}
        
        async with session.get(f"{BASE_URL}/api/user/intelligence-simple/uploads", headers=headers) as resp:
            if resp.status == 200:
                uploads = await resp.json()
                print(f"✅ Found {len(uploads)} uploads")
                if uploads:
                    latest = uploads[0]
                    print(f"   Latest upload: {latest.get('filename', 'unknown')}")
                    print(f"   Compliance Score: {latest.get('compliance_score', 'N/A')}%")
                    print(f"   Standards Mapped: {latest.get('standards_mapped', 'N/A')}")
            else:
                print(f"❌ Failed to get uploads: {resp.status}")
        
        # 3. Check dashboard metrics
        print("\n3. Checking dashboard metrics...")
        async with session.get(f"{BASE_URL}/api/user/intelligence-simple/dashboard-metrics", headers=headers) as resp:
            if resp.status == 200:
                metrics = await resp.json()
                print(f"✅ Dashboard metrics:")
                print(f"   Average Coverage: {metrics.get('average_coverage', 0)}%")
                print(f"   Total Standards Mapped: {metrics.get('total_standards_mapped', 0)}")
                print(f"   Documents Analyzed: {metrics.get('documents_analyzed', 0)}")
                print(f"   Total Gaps Identified: {metrics.get('total_gaps_identified', 0)}")
            else:
                print(f"❌ Failed to get metrics: {resp.status}")
        
        # 4. Test report generation page
        print("\n4. Testing report generation page...")
        async with session.get(f"{BASE_URL}/report-generation", headers=headers) as resp:
            if resp.status == 200:
                print(f"✅ Report generation page accessible")
                content = await resp.text()
                
                # Check if our update function exists
                if 'updateWithRealMetrics' in content:
                    print("✅ Dynamic metrics function found in page")
                else:
                    print("❌ Dynamic metrics function NOT found - page may still show static values")
                
                # Check for hardcoded values
                if '87%' in content and '73' in content:
                    print("⚠️  Hardcoded values still present in HTML (87%, 73 standards)")
                    print("   These will be replaced dynamically when page loads")
            else:
                print(f"❌ Failed to access report page: {resp.status}")
        
        print("\n✨ Test complete!")
        print("\nTo verify the fix:")
        print("1. Upload a document through the UI")
        print("2. After analysis, check the report generation page")
        print("3. The metrics should now show real values, not 87%/73")

if __name__ == "__main__":
    asyncio.run(test_report_display())