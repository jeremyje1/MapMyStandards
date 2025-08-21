#!/bin/bash

# Monitor Railway deployment
echo "🔄 Monitoring Railway deployment..."
echo "URL: https://mapmystandards-prod-production.up.railway.app"
echo "Waiting for API to be ready..."
echo ""

start_time=$(date +%s)
max_wait=300  # 5 minutes

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -gt $max_wait ]; then
        echo ""
        echo "❌ Timeout waiting for deployment. Check Railway logs."
        exit 1
    fi
    
    # Check if docs are available
    response=$(curl -s -o /dev/null -w "%{http_code}" https://mapmystandards-prod-production.up.railway.app/docs)
    
    if [ "$response" = "200" ]; then
        echo ""
        echo "✅ FastAPI is running! Checking endpoints..."
        
        # Test key endpoints
        echo "   FastAPI Docs: $(curl -s -o /dev/null -w "%{http_code}" https://mapmystandards-prod-production.up.railway.app/docs)"
        echo "   Health Check: $(curl -s -o /dev/null -w "%{http_code}" https://mapmystandards-prod-production.up.railway.app/health)"
        echo "   Trial Signup: $(curl -s -o /dev/null -w "%{http_code}" https://mapmystandards-prod-production.up.railway.app/api/trial/signup)"
        
        echo ""
        echo "🎉 Deployment successful! API is ready."
        echo "   Documentation: https://mapmystandards-prod-production.up.railway.app/docs"
        echo "   Total wait time: $elapsed seconds"
        exit 0
    else
        printf "\r⏳ Waiting... (%ds) - Status: %s" "$elapsed" "$response"
    fi
    
    sleep 5
done
