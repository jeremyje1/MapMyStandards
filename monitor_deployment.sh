#!/bin/bash

echo "🔄 Monitoring deployment of new endpoints..."
echo "This will check every 30 seconds until the endpoints are live."
echo ""

while true; do
    # Check if the new upload endpoint exists
    STATUS=$(curl -X POST https://api.mapmystandards.ai/upload/presign \
        -H "Content-Type: application/json" \
        -d '{"filename":"test.txt","content_type":"text/plain","file_size":100}' \
        -s -o /dev/null -w "%{http_code}")
    
    TIMESTAMP=$(date '+%H:%M:%S')
    
    if [ "$STATUS" != "405" ] && [ "$STATUS" != "404" ]; then
        echo "[$TIMESTAMP] ✅ New endpoints are DEPLOYED! (Status: $STATUS)"
        echo ""
        echo "Testing endpoints:"
        echo "1. /upload/presign - Status: $STATUS"
        
        # Test auth endpoint
        AUTH_STATUS=$(curl -X POST https://api.mapmystandards.ai/auth/register \
            -H "Content-Type: application/json" \
            -d '{"test":"test"}' \
            -s -o /dev/null -w "%{http_code}")
        echo "2. /auth/register - Status: $AUTH_STATUS"
        
        echo ""
        echo "🎉 Deployment successful! You can now test the upload at:"
        echo "   http://localhost:8888/test_upload_simple.html"
        break
    else
        echo "[$TIMESTAMP] ⏳ Still deploying... (Current status: $STATUS)"
    fi
    
    sleep 30
done
