#!/bin/bash

echo "🚀 DEPLOYING MAPMY STANDARDS PLATFORM..."

# Navigate to project directory
cd /Users/jeremyestrella/Desktop/MapMyStandards

# Check if environment variables are set
if [ -z "$STRIPE_SECRET_KEY" ] || [ -z "$STRIPE_PUBLISHABLE_KEY" ]; then
    echo "❌ Please set environment variables first:"
    echo "export STRIPE_SECRET_KEY='your_secret_key'"
    echo "export STRIPE_PUBLISHABLE_KEY='your_publishable_key'"
    echo "export MONTHLY_PRICE_ID='price_1RtXF3K8PKpLCKDZJNfi3Rvi'"
    echo "export ANNUAL_PRICE_ID='price_1RtXF3K8PKpLCKDZAMb4rM8U'"
    exit 1
fi

echo "✅ Environment variables configured"

# Activate virtual environment
if [ -d "backend_env" ]; then
    source backend_env/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv backend_env
    source backend_env/bin/activate
    pip install flask flask-cors stripe
    echo "✅ Virtual environment created and activated"
fi

# Initialize database
echo "🗄️ Initializing database..."
python3 -c "
from subscription_backend import init_db
init_db()
print('✅ Database initialized')
"

# Start the backend server
echo "🔧 Starting backend server..."
echo "Backend will be available at: http://localhost:5000"
echo ""
echo "📋 Available endpoints:"
echo "  - http://localhost:5000/signup (Customer signup)"
echo "  - http://localhost:5000/pricing_clean.html (Clean pricing page)"
echo "  - http://localhost:5000/login (Customer login)"
echo "  - http://localhost:5000/dashboard (Customer dashboard)"
echo "  - http://localhost:5000/webhook (Stripe webhooks)"
echo ""
echo "🎯 Next steps after backend starts:"
echo "  1. Configure Stripe webhook: http://localhost:5000/webhook"
echo "  2. Test signup flow: http://localhost:5000/signup"
echo "  3. Deploy to production server"
echo ""

# Start the Flask backend
python3 subscription_backend.py
