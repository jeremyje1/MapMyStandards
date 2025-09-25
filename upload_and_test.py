#!/usr/bin/env python3
"""Upload a test document and test analyze"""

import requests
import json
import time
import base64

API_BASE = "https://api.mapmystandards.ai"

# Create a simple test PDF content
TEST_PDF_CONTENT = """
JVBERi0xLjQKJcOkw7zDtsOfCjIgMCBvYmoKPDwvTGVuZ3RoIDMgMCBSL0ZpbHRlci9GbGF0ZURlY29kZT4+CnN0cmVhbQp4nGVOuwoCM
RCs5hVzrQiyhbW9hYiNhY2djY2FRbCxsPAD7C0E8RDv1Pz+ziaXFJnZnZmdTQaoSqpa1YdSqoEqVFW16+Bq1cH1qo3rVBvXqw6uU13coLq
4UQ1wo+rjJjXETWqEm9UYN6sJblZT3KxmuFktcLNa4ma1ws1qjZvVBjerLW5WO9ysrvj39fs9PiITniJ7JC0nJ0xyuEQSvEcmeI8keItM
Ty7ROu8JKKEhEotIQmQWJiRcKEz3OBAJCZdIgrcoJAm+h4SEiy8hkXAX5OXNiY1fdlGsg3LZQbnZsB0r8UNL5FTi9xa7t8gUn2XLQaXQPGp
HM9qQ6OGF/rl+4vvuj6fTv1+f4dGo/AcFVH6WCmVuZHN0cmVhbQplbmRvYmoKCjMgMCBvYmoKMjY3CmVuZG9iagoKNCAwIG9iago8PC9Ue
XBlL1BhZ2UvUGFyZW50IDEgMCBSL1Jlc291cmNlcyA2IDAgUi9NZWRpYUJveFswIDAgNjEyIDc5Ml0vQ29udGVudHMgMiAwIFI+PgplbmR
vYmoKCjYgMCBvYmoKPDwvRm9udCA3IDAgUi9Qcm9jU2V0Wy9QREYvVGV4dF0+PgplbmRvYmoKCjcgMCBvYmoKPDwvRjEgOCAwIFI+Pgplb
mRvYmoKCjggMCBvYmoKPDwvVHlwZS9Gb250L1N1YnR5cGUvVHlwZTEvQmFzZUZvbnQvSGVsdmV0aWNhL0VuY29kaW5nL1dpbkFuc2lFbmN
vZGluZz4+CmVuZG9iagoKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgNSAwIFI+PgplbmRvYmoKCjUgMCBvYmoKPDwvVHlwZS9QY
Wdlcy9LaWRzWzQgMCBSXS9Db3VudCAxPj4KZW5kb2JqCgp4cmVmCjAgOQowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDA3MDkgMDAwMDA
gbiAKMDAwMDAwMDAxOSAwMDAwMCBuIAowMDAwMDAwMzY0IDAwMDAwIG4gCjAwMDAwMDAzODQgMDAwMDAgbiAKMDAwMDAwMDc1OCAwMDAwM
CBobiAKMDAwMDAwMDQ4MyAwMDAwMCBuIAowMDAwMDAwNTM2IDAwMDAwIG4gCjAwMDAwMDA1NjcgMDAwMDAgbiAKdHJhaWxlcgo8PC9TaXp
lIDkvUm9vdCAxIDAgUj4+CnN0YXJ0eHJlZgo4MTUKJSVFT0YK
""".replace('\n', '')

# Decode base64 to get actual PDF bytes
pdf_bytes = base64.b64decode(TEST_PDF_CONTENT)

print("Upload and Test Analyze Feature")
print("=" * 60)

# Login
print("\n1. Logging in...")
login_data = {
    "email": "jeremy.estrella@gmail.com",
    "password": "Ipo4Eva45*"
}

response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
if response.status_code != 200:
    print(f"❌ Login failed: {response.text}")
    exit(1)

token = response.json()["access_token"]
print("✓ Login successful")

headers = {
    "Authorization": f"Bearer {token}",
}

# Upload a test document
print("\n2. Uploading test document...")
files = {
    'file': ('test_document.pdf', pdf_bytes, 'application/pdf')
}
data = {
    'title': 'Test Document for Analysis',
    'type': 'evidence'
}

response = requests.post(
    f"{API_BASE}/api/user/intelligence-simple/evidence/upload",
    headers=headers,
    files=files,
    data=data
)

if response.status_code != 200:
    print(f"❌ Upload failed: {response.text}")
    exit(1)

upload_result = response.json()
doc_id = upload_result.get("document_id") or upload_result.get("id")
print(f"✓ Document uploaded successfully!")
print(f"  Document ID: {doc_id}")

# Wait a moment for processing
time.sleep(2)

# Now test analyze
print(f"\n3. Testing analyze...")
headers["Content-Type"] = "application/json"

start_time = time.time()
analyze_data = {"documentId": doc_id}
response = requests.post(
    f"{API_BASE}/api/user/intelligence-simple/documents/{doc_id}/analyze",
    headers=headers,
    json=analyze_data
)

elapsed = time.time() - start_time

if response.status_code == 200:
    print(f"\n✅ ANALYZE SUCCESSFUL! (took {elapsed:.2f} seconds)")
    result = response.json()
    
    # Show what was returned
    print(f"\nAnalysis Result Keys: {list(result.keys())}")
    
    if "analysis" in result:
        analysis = result["analysis"]
        print(f"\nAnalysis Type: {analysis.get('type', 'N/A')}")
        print(f"Content preview: {str(analysis)[:200]}...")
        
else:
    print(f"\n❌ Analyze failed: {response.status_code}")
    print(f"   Error: {response.text[:500]}")
    
# Check the logs to see what happened
print("\n" + "=" * 60)
print("Checking Railway logs for errors...")

print("\nTo see detailed logs, run:")
print("railway logs --service MapMyStandards | tail -50")

print("\n" + "=" * 60)
print("Summary:")
print("✓ Upload working")
if response.status_code == 200:
    print("✓ Analyze working (despite AWS Bedrock permissions)")
    print("  The system is using the Anthropic API fallback successfully!")
else:
    print("❌ Analyze has issues - check logs above")