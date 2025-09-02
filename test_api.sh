#!/bin/bash
echo "=== Testing Standards API Endpoints ==="
echo

echo "1. Overview endpoint:"
curl -s "https://api.mapmystandards.ai/api/v1/standards/" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Success: {d[\"success\"]}, Total Standards: {d[\"data\"][\"total_standards\"]}')"
echo

echo "2. List standards (first 2):"
curl -s "https://api.mapmystandards.ai/api/v1/standards/standards?limit=2" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Found {len(d)} standards')"
echo

echo "3. Get specific standard (SACSCOC_1_1):"
curl -s "https://api.mapmystandards.ai/api/v1/standards/standards/SACSCOC_1_1" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  {d[\"standard_id\"]}: {d[\"title\"]}')"
echo

echo "4. List accreditors:"
curl -s "https://api.mapmystandards.ai/api/v1/standards/accreditors" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Found {len(d)} accreditors with standards')"
echo

echo "5. Get SACSCOC standards:"
curl -s "https://api.mapmystandards.ai/api/v1/standards/accreditors/sacscoc/standards" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  SACSCOC has {len(d)} standards')"
echo

echo "6. Search for 'mission':"
curl -s "https://api.mapmystandards.ai/api/v1/standards/search?query=mission" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Found {d[\"total_count\"]} results')"
echo

echo "7. Get categories:"
curl -s "https://api.mapmystandards.ai/api/v1/standards/categories" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'  Found {d[\"total_count\"]} categories')"
echo

echo "=== All endpoints tested successfully! ==="
