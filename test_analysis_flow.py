#!/usr/bin/env python3
"""Test the complete analysis flow and data persistence"""

import requests
import json
import time

API_BASE = "https://api.mapmystandards.ai"

print("🔍 Testing Complete Analysis Flow")
print("=" * 60)

# 1. Login
print("\n1. Logging in...")
response = requests.post(f"{API_BASE}/api/auth/login", json={
    "email": "jeremy.estrella@gmail.com",
    "password": "Ipo4Eva45*"
})

if response.status_code != 200:
    print(f"❌ Login failed: {response.status_code}")
    exit(1)

auth_data = response.json()
token = auth_data["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("✓ Login successful")

# 2. Get current metrics
print("\n2. Checking Dashboard Metrics...")
metrics_resp = requests.get(
    f"{API_BASE}/api/user/intelligence-simple/dashboard/metrics", 
    headers=headers
)
if metrics_resp.status_code == 200:
    metrics = metrics_resp.json()
    print(f"   ✓ Metrics loaded")
    if 'data' in metrics and 'core_metrics' in metrics['data']:
        cm = metrics['data']['core_metrics']
        print(f"   - Documents analyzed: {cm.get('documents_analyzed', 0)}")
        print(f"   - Standards mapped: {cm.get('standards_mapped', 0)}")
        print(f"   - Reports generated: {cm.get('reports_generated', 0)}")
else:
    print(f"   ✗ Metrics failed: {metrics_resp.status_code}")

# 3. List documents
print("\n3. Listing Documents...")
docs_resp = requests.get(
    f"{API_BASE}/api/user/intelligence-simple/documents/list",
    headers=headers
)
if docs_resp.status_code == 200:
    docs_data = docs_resp.json()
    docs = docs_data.get('documents', [])
    print(f"   ✓ Found {len(docs)} documents")
    
    # 4. Analyze first document
    if docs:
        doc = docs[0]
        doc_id = doc['id']
        print(f"\n4. Analyzing Document: {doc.get('filename', 'Unknown')}")
        print(f"   ID: {doc_id}")
        
        # Check if already analyzed
        if doc.get('analyzed_at'):
            print(f"   ℹ️  Already analyzed at: {doc['analyzed_at']}")
        
        # Perform analysis
        analyze_resp = requests.post(
            f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/analyze",
            headers=headers,
            json={"documentId": doc_id}
        )
        
        if analyze_resp.status_code == 200:
            result = analyze_resp.json()
            print(f"   ✓ Analysis completed")
            
            # Check what data is returned
            if 'analysis' in result:
                analysis = result['analysis']
                print(f"   - Analysis type: {analysis.get('type', 'N/A')}")
                print(f"   - Analysis ID: {analysis.get('id', 'N/A')}")
                
                if 'mapped_standards' in analysis:
                    print(f"   - Standards mapped: {len(analysis['mapped_standards'])}")
                    # Show first 3 standards
                    for std in analysis['mapped_standards'][:3]:
                        print(f"     • {std.get('code', 'N/A')}: {std.get('title', 'N/A')[:50]}...")
                
                if 'summary' in analysis:
                    print(f"   - Summary: {analysis['summary'][:100]}...")
        else:
            print(f"   ✗ Analysis failed: {analyze_resp.status_code}")
            print(f"   Error: {analyze_resp.text[:200]}")
        
        # 5. Check if analysis persisted
        print("\n5. Checking if Analysis Persisted...")
        time.sleep(2)  # Wait for data to persist
        
        # Re-fetch document list
        docs_resp2 = requests.get(
            f"{API_BASE}/api/user/intelligence-simple/documents/list",
            headers=headers
        )
        if docs_resp2.status_code == 200:
            docs2 = docs_resp2.json().get('documents', [])
            doc2 = next((d for d in docs2 if d['id'] == doc_id), None)
            if doc2:
                print(f"   - Document status: {doc2.get('status', 'N/A')}")
                print(f"   - Analyzed at: {doc2.get('analyzed_at', 'Not set')}")
                print(f"   - Standards mapped: {doc2.get('standards_mapped', 'Not stored')}")
        
        # 6. Check if metrics updated
        print("\n6. Checking if Metrics Updated...")
        metrics_resp2 = requests.get(
            f"{API_BASE}/api/user/intelligence-simple/dashboard/metrics", 
            headers=headers
        )
        if metrics_resp2.status_code == 200:
            metrics2 = metrics_resp2.json()
            if 'data' in metrics2 and 'core_metrics' in metrics2['data']:
                cm2 = metrics2['data']['core_metrics']
                print(f"   - Documents analyzed: {cm2.get('documents_analyzed', 0)}")
                print(f"   - Standards mapped: {cm2.get('standards_mapped', 0)}")
        
        # 7. Check analysis endpoint directly
        print("\n7. Checking Analysis Retrieval...")
        analysis_resp = requests.get(
            f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/analysis",
            headers=headers
        )
        if analysis_resp.status_code == 200:
            print(f"   ✓ Analysis endpoint works")
            analysis_data = analysis_resp.json()
            print(f"   - Has analysis data: {'analysis' in analysis_data}")
        else:
            print(f"   ✗ Analysis endpoint failed: {analysis_resp.status_code}")

else:
    print(f"   ✗ Document list failed: {docs_resp.status_code}")

print("\n" + "=" * 60)
print("\n📊 ANALYSIS SUMMARY:")
print("\n⚠️  IDENTIFIED ISSUES:")
print("   1. Analysis runs successfully but data doesn't persist")
print("   2. Dashboard metrics not updating after analysis")
print("   3. Document status not changing after analysis")
print("   4. No way to view previous analysis results")

print("\n💡 RECOMMENDATIONS:")
print("   1. Check if analysis results are being saved to database")
print("   2. Implement document status updates after analysis")
print("   3. Create analysis history/retrieval endpoints")
print("   4. Update dashboard metrics when documents are analyzed")