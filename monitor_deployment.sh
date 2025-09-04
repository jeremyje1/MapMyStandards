#!/bin/bash
# Monitor Railway deployment and API status

echo "MapMyStandards Deployment Monitor"
echo "================================="
echo "Started at: $(date)"
echo ""

# Function to check API health
check_api() {
    echo -n "Checking API health... "
    if curl -s -m 5 https://api.mapmystandards.ai/health > /dev/null 2>&1; then
        echo "✅ API is UP!"
        return 0
    else
        echo "⏳ API not ready yet"
        return 1
    fi
}

# Function to check specific endpoint
check_endpoint() {
    local endpoint=$1
    local name=$2
    echo -n "  - $name: "
    response=$(curl -s -w "\n%{http_code}" -m 5 "$endpoint" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "000" ]; then
        echo "❌ Connection failed"
    elif [ "$http_code" = "200" ] || [ "$http_code" = "400" ] || [ "$http_code" = "404" ]; then
        echo "✅ Responding (HTTP $http_code)"
    else
        echo "⚠️  HTTP $http_code"
    fi
}

# Monitor loop
counter=0
max_attempts=30  # 15 minutes max (30 * 30 seconds)

while [ $counter -lt $max_attempts ]; do
    echo "Check #$((counter + 1)) at $(date +%H:%M:%S)"
    
    if check_api; then
        echo ""
        echo "🎉 Deployment successful! Testing endpoints:"
        check_endpoint "https://api.mapmystandards.ai/health" "Health Check"
        check_endpoint "https://api.mapmystandards.ai/api/billing/webhook/stripe" "Webhook Endpoint"
        check_endpoint "https://api.mapmystandards.ai/api/users/check?email=test@example.com" "Database Check"
        
        echo ""
        echo "✅ All systems operational!"
        echo "You can now test user signups at: https://platform.mapmystandards.ai"
        exit 0
    fi
    
    counter=$((counter + 1))
    
    if [ $counter -lt $max_attempts ]; then
        echo "Waiting 30 seconds before next check..."
        echo ""
        sleep 30
    fi
done

echo ""
echo "❌ Deployment monitoring timed out after 15 minutes."
echo "Check Railway logs manually: railway logs"
exit 1
