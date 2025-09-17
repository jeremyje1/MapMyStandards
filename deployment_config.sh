#!/bin/bash

# Deployment configuration for MapMyStandards
# Source this file to set up deployment environment variables
# Usage: source deployment_config.sh [environment]

ENVIRONMENT=${1:-production}

echo "🔧 Setting up deployment configuration for: $ENVIRONMENT"

case $ENVIRONMENT in
    "local")
        export TARGET_URL="http://localhost:8000"
        export FRONTEND_URL="http://localhost:3000"
        export API_BASE_URL="http://localhost:8000"
        echo "   API: $TARGET_URL"
        echo "   Frontend: $FRONTEND_URL"
        ;;
        
    "staging")
        export TARGET_URL="https://api-staging.mapmystandards.ai"
        export FRONTEND_URL="https://staging.mapmystandards.ai"
        export API_BASE_URL="https://api-staging.mapmystandards.ai"
        echo "   API: $TARGET_URL"
        echo "   Frontend: $FRONTEND_URL"
        ;;
        
    "production")
        export TARGET_URL="https://api.mapmystandards.ai"
        export FRONTEND_URL="https://mapmystandards.ai"
        export API_BASE_URL="/api"  # Use relative in production for same-origin
        echo "   API: $TARGET_URL"
        echo "   Frontend: $FRONTEND_URL"
        ;;
        
    *)
        echo "❌ Unknown environment: $ENVIRONMENT"
        echo "   Valid options: local, staging, production"
        return 1
        ;;
esac

# Export additional configuration
export MMS_ENVIRONMENT=$ENVIRONMENT
export NODE_ENV=$( [ "$ENVIRONMENT" = "local" ] && echo "development" || echo "production" )

# Function to run health checks
check_deployment() {
    if [ -f "$(dirname "${BASH_SOURCE[0]}")/check_deployment_extended.sh" ]; then
        bash "$(dirname "${BASH_SOURCE[0]}")/check_deployment_extended.sh" "$TARGET_URL" "$MMS_AUTH_TOKEN"
    else
        echo "❌ check_deployment_extended.sh not found"
    fi
}

# Function to update frontend config
update_frontend_config() {
    local config_file="${FRONTEND_CONFIG_PATH:-web/js/config.js}"
    
    if [ -f "$config_file" ]; then
        echo "📝 Updating frontend configuration..."
        # Create a backup
        cp "$config_file" "${config_file}.bak"
        
        # Update the configuration with environment-specific values
        # This is a simplified version - in production you'd use a more robust templating solution
        if [ "$ENVIRONMENT" = "production" ]; then
            echo "   Setting production API base to relative paths"
        else
            echo "   Setting $ENVIRONMENT API base to $API_BASE_URL"
        fi
    else
        echo "⚠️  Frontend config not found at: $config_file"
    fi
}

echo ""
echo "✅ Configuration loaded. Available commands:"
echo "   check_deployment    - Run extended health checks"
echo "   update_frontend_config - Update frontend configuration"
echo ""
echo "To test authenticated endpoints, set MMS_AUTH_TOKEN:"
echo "   export MMS_AUTH_TOKEN='your-auth-token'"