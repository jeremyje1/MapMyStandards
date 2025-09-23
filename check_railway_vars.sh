#!/bin/bash

echo "🔍 Checking Railway environment variables..."
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not installed. Installing..."
    curl -fsSL https://railway.app/install.sh | sh
fi

# Check Railway project variables
echo "📋 Fetching Railway environment variables..."
echo ""

# List all variables (without showing values for security)
railway variables --json 2>/dev/null | jq -r 'keys[]' 2>/dev/null | while read var; do
    if [[ "$var" == "AWS_"* ]] || [[ "$var" == "S3_"* ]]; then
        echo "✅ Found: $var"
    fi
done

echo ""
echo "🔍 Checking for required S3 variables..."
echo ""

# Check specific required variables
required_vars=("AWS_ACCESS_KEY_ID" "AWS_SECRET_ACCESS_KEY" "AWS_REGION" "S3_BUCKET_NAME")
missing_vars=()

for var in "${required_vars[@]}"; do
    if railway variables --json 2>/dev/null | jq -e "has(\"$var\")" > /dev/null 2>&1; then
        echo "✅ $var is set"
    else
        echo "❌ $var is MISSING"
        missing_vars+=("$var")
    fi
done

echo ""
if [ ${#missing_vars[@]} -eq 0 ]; then
    echo "✅ All required AWS S3 variables are configured!"
    echo ""
    echo "📝 S3 Configuration detected:"
    railway variables --json 2>/dev/null | jq -r 'to_entries | .[] | select(.key | startswith("AWS_") or startswith("S3_")) | "\(.key)=***"' 2>/dev/null
else
    echo "⚠️  Missing variables: ${missing_vars[*]}"
    echo ""
    echo "To add missing variables, use:"
    for var in "${missing_vars[@]}"; do
        echo "  railway variables set $var=your-value"
    done
fi

echo ""
echo "🔗 To view all variables: railway variables"
echo "🔗 To add a variable: railway variables set KEY=value"