#!/bin/bash

# A³E Production Deployment Script
# Deploys the Autonomous Accreditation & Audit Engine to production
# NO MOCK DATA - Only real user data processing

set -e

echo "🚀 A³E Production Deployment - Real Data Processing Only"
echo "========================================================"

# Configuration
A3E_PORT=${A3E_PORT:-8001}
A3E_ENV=${A3E_ENV:-"a3e_env"}
A3E_APP="a3e_production_real_data.py"
SERVICE_NAME="a3e-production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running from correct directory
if [ ! -f "$A3E_APP" ]; then
    print_error "A³E application file '$A3E_APP' not found!"
    print_info "Please run this script from the MapMyStandards directory"
    exit 1
fi

print_info "Starting A³E Production Deployment..."

# Step 1: Create/activate virtual environment
print_info "Setting up Python environment..."
if [ ! -d "$A3E_ENV" ]; then
    print_info "Creating virtual environment: $A3E_ENV"
    python3 -m venv "$A3E_ENV"
fi

source "$A3E_ENV/bin/activate"
print_status "Virtual environment activated"

# Step 2: Install dependencies
print_info "Installing production dependencies..."
pip install --upgrade pip
pip install fastapi uvicorn aiofiles python-multipart

print_status "Dependencies installed"

# Step 3: Validate A3E application
print_info "Validating A³E production application..."
if python -c "import sys; exec(open('$A3E_APP').read().split('if __name__')[0]); print('✅ A³E app validation: PASSED')"; then
    print_status "A³E application validation successful"
else
    print_error "A³E application validation failed!"
    exit 1
fi

# Step 4: Check for existing A3E processes
print_info "Checking for existing A³E processes..."
if pgrep -f "$A3E_APP" > /dev/null; then
    print_warning "Existing A³E process found. Stopping..."
    pkill -f "$A3E_APP" || true
    sleep 2
fi

# Step 5: Start A3E production service
print_info "Starting A³E Production Service..."
print_info "Port: $A3E_PORT"
print_info "Mode: PRODUCTION (Real data only)"

# Create log directory
mkdir -p logs

# Start the A3E service
nohup python "$A3E_APP" > logs/a3e_production.log 2>&1 &
A3E_PID=$!

# Wait for service to start
sleep 3

# Step 6: Health check
print_info "Performing health check..."
if curl -f -s "http://localhost:$A3E_PORT/health" > /dev/null; then
    print_status "A³E Production Service is running!"
    
    # Get service status
    STATUS=$(curl -s "http://localhost:$A3E_PORT/health" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"Service: {data.get('service', 'unknown')}\")
    print(f\"Status: {data.get('status', 'unknown')}\")
    print(f\"Version: {data.get('version', 'unknown')}\")
    print(f\"Mock Data: {data.get('mock_data', 'unknown')}\")
    print(f\"Data Type: {data.get('data_type', 'unknown')}\")
except:
    print('Status check failed')
")
    
    echo ""
    print_status "A³E Service Status:"
    echo "$STATUS"
    
    # Verify no mock data
    MOCK_DATA=$(curl -s "http://localhost:$A3E_PORT/health" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(str(data.get('mock_data', True)).lower())
except:
    print('true')
")
    
    if [ "$MOCK_DATA" = "false" ]; then
        print_status "✅ VERIFIED: No mock data - Real user data processing only"
    else
        print_error "❌ WARNING: Mock data detected! Production system should not use mock data"
        exit 1
    fi
    
else
    print_error "A³E service failed to start or health check failed!"
    print_info "Check logs: tail -f logs/a3e_production.log"
    exit 1
fi

# Step 7: Display service information
echo ""
echo "========================================================"
print_status "A³E Production Deployment Complete!"
echo "========================================================"
echo ""
print_info "Service Information:"
echo "  🌐 Service URL: http://localhost:$A3E_PORT"
echo "  📄 Document Upload: http://localhost:$A3E_PORT/upload"
echo "  📚 API Documentation: http://localhost:$A3E_PORT/docs"
echo "  🏥 Health Check: http://localhost:$A3E_PORT/health"
echo "  📋 Process ID: $A3E_PID"
echo "  📁 Log File: logs/a3e_production.log"
echo ""
print_info "Production Features:"
echo "  ✅ Real document processing (PDF, DOCX, TXT)"
echo "  ✅ AI-powered compliance analysis"
echo "  ✅ SACSCOC, HLC, Cognia standards support"
echo "  ✅ No mock data - User uploads only"
echo "  ✅ Secure document storage"
echo ""
print_info "Management Commands:"
echo "  📊 View logs: tail -f logs/a3e_production.log"
echo "  🔄 Restart: ./deploy_a3e_production.sh"
echo "  🛑 Stop: pkill -f $A3E_APP"
echo "  🩺 Health: curl http://localhost:$A3E_PORT/health"
echo ""
print_status "A³E Production System Ready for Use!"
echo "🎯 Upload real institutional documents for AI-powered compliance analysis"
