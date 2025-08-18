#!/bin/bash

# Canvas Personal Account Setup Helper
# Helps configure Canvas integration for personal accounts

echo "🎨 Canvas Personal Account Setup"
echo "================================"
echo ""

echo "Step 1: Find your Canvas URL"
echo "----------------------------"
echo "Please provide your Canvas URL (e.g., https://canvas.instructure.com)"
read -p "Canvas URL: " CANVAS_URL

# Clean up URL
CANVAS_URL=$(echo "$CANVAS_URL" | sed 's:/*$::')
API_BASE="$CANVAS_URL/api/v1"

echo ""
echo "Step 2: Get Access Token"
echo "------------------------"
echo "1. Log into Canvas: $CANVAS_URL"
echo "2. Go to Account → Settings"
echo "3. Scroll down to 'Approved Integrations'"
echo "4. Click '+ New Access Token'"
echo "5. Purpose: 'A3E Integration'"
echo "6. Expiry: Leave blank (never expires) or set to 1 year"
echo "7. Copy the generated token"
echo ""
read -p "Paste your access token here: " CANVAS_TOKEN

echo ""
echo "Step 3: Test Connection"
echo "----------------------"

# Test the connection
echo "Testing Canvas API connection..."
USER_INFO=$(curl -s -H "Authorization: Bearer $CANVAS_TOKEN" "$API_BASE/users/self" 2>/dev/null)

if echo "$USER_INFO" | grep -q '"id"'; then
    echo "✅ Canvas connection successful!"
    
    # Extract user info
    USER_ID=$(echo "$USER_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('id', 'N/A'))" 2>/dev/null || echo "N/A")
    USER_NAME=$(echo "$USER_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('name', 'N/A'))" 2>/dev/null || echo "N/A")
    
    echo "   User ID: $USER_ID"
    echo "   Name: $USER_NAME"
    
    # Test courses access
    echo ""
    echo "Testing courses access..."
    COURSES=$(curl -s -H "Authorization: Bearer $CANVAS_TOKEN" "$API_BASE/courses" 2>/dev/null)
    
    if echo "$COURSES" | grep -q '\['; then
        COURSE_COUNT=$(echo "$COURSES" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        echo "✅ Found $COURSE_COUNT courses"
    else
        echo "⚠️  Limited course access (normal for personal accounts)"
    fi
    
else
    echo "❌ Canvas connection failed. Please check:"
    echo "   - Canvas URL is correct"
    echo "   - Access token is valid"
    echo "   - Token has API access permissions"
    exit 1
fi

echo ""
echo "Step 4: Update Configuration"
echo "----------------------------"

# Update .env file
if [ -f ".env" ]; then
    echo "Updating .env file..."
    
    # Remove old Canvas config
    sed -i.bak '/^CANVAS_/d' .env
    
    # Add new Canvas config
    cat >> .env << EOF

# Canvas LMS Configuration (Personal Account)
CANVAS_API_BASE=$API_BASE
CANVAS_ACCESS_TOKEN=$CANVAS_TOKEN
CANVAS_USER_ID=$USER_ID
CANVAS_BASE_URL=$CANVAS_URL
EOF
    
    echo "✅ .env file updated!"
else
    echo "⚠️  .env file not found. Please create it with:"
    echo ""
    echo "CANVAS_API_BASE=$API_BASE"
    echo "CANVAS_ACCESS_TOKEN=$CANVAS_TOKEN"
    echo "CANVAS_USER_ID=$USER_ID"
    echo "CANVAS_BASE_URL=$CANVAS_URL"
fi

echo ""
echo "Step 5: Test Integration"
echo "------------------------"
echo "Run this command to test the Canvas integration:"
echo ""
echo "  ./scripts/test_canvas.sh"
echo ""
echo "Or start the API server and visit:"
echo "  http://localhost:8000/api/v1/integrations/canvas/test"
echo ""
echo "🎉 Canvas setup complete!"
