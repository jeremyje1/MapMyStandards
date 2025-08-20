#!/usr/bin/env python3
"""
Setup environment for MapMyStandards A3E platform
Pulls from Vercel and generates missing variables
"""

import os
import sys
import secrets
import subprocess
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load existing .env.local from Vercel
load_dotenv('.env.local')

def generate_secure_key(length=32):
    """Generate a secure random key"""
    return secrets.token_urlsafe(length)

def setup_environment():
    """Setup complete environment with all required variables"""
    
    env_file = '.env.local'
    
    print("🔧 Setting up MapMyStandards A3E environment...")
    print(f"📄 Using environment file: {env_file}")
    
    # Check existing variables from Vercel
    print("\n✅ Found from Vercel:")
    vercel_vars = [
        'POSTMARK_API_TOKEN',
        'POSTMARK_MESSAGE_STREAM',
        'STRIPE_MONTHLY_PRICE_ID',
        'STRIPE_ANNUAL_PRICE_ID',
        'ADMIN_EMAIL',
        'FROM_EMAIL',
        'REPLY_TO_EMAIL'
    ]
    
    for var in vercel_vars:
        value = os.getenv(var)
        if value:
            print(f"  - {var}: {'*' * 10}{value[-4:]}" if len(value) > 4 else "***")
    
    # Generate missing critical variables
    print("\n🔑 Generating missing variables:")
    
    # JWT Secret Key
    if not os.getenv('JWT_SECRET_KEY'):
        jwt_secret = generate_secure_key(64)
        set_key(env_file, 'JWT_SECRET_KEY', jwt_secret)
        print(f"  - JWT_SECRET_KEY: Generated secure key")
    
    # Database URL (using SQLite for local dev)
    if not os.getenv('DATABASE_URL'):
        # For production, this should be PostgreSQL
        # For local dev, we'll use SQLite
        db_path = Path.cwd() / 'data' / 'a3e_dev.db'
        db_path.parent.mkdir(exist_ok=True)
        database_url = f"sqlite:///{db_path}"
        set_key(env_file, 'DATABASE_URL', database_url)
        print(f"  - DATABASE_URL: {database_url}")
    
    # API URLs
    if not os.getenv('API_BASE_URL'):
        set_key(env_file, 'API_BASE_URL', 'http://localhost:8000')
        print(f"  - API_BASE_URL: http://localhost:8000")
    
    # Data directory
    if not os.getenv('DATA_DIR'):
        data_dir = str(Path.cwd() / 'data')
        set_key(env_file, 'DATA_DIR', data_dir)
        print(f"  - DATA_DIR: {data_dir}")
    
    # Stripe webhook secret (placeholder - needs real value)
    if not os.getenv('STRIPE_WEBHOOK_SECRET'):
        print("\n⚠️  WARNING: STRIPE_WEBHOOK_SECRET not found!")
        print("  You'll need to get this from your Stripe dashboard:")
        print("  1. Go to https://dashboard.stripe.com/webhooks")
        print("  2. Find your webhook endpoint")
        print("  3. Copy the signing secret (starts with 'whsec_')")
        set_key(env_file, 'STRIPE_WEBHOOK_SECRET', 'whsec_PLACEHOLDER_REPLACE_ME')
    
    # Stripe API key (placeholder - needs real value)
    if not os.getenv('STRIPE_API_KEY'):
        print("\n⚠️  WARNING: STRIPE_API_KEY not found!")
        print("  You'll need to get this from your Stripe dashboard:")
        print("  1. Go to https://dashboard.stripe.com/apikeys")
        print("  2. Copy your secret key (starts with 'sk_')")
        set_key(env_file, 'STRIPE_API_KEY', 'sk_test_PLACEHOLDER_REPLACE_ME')
    
    print("\n📝 Creating .env.example for documentation...")
    create_env_example()
    
    print("\n✅ Environment setup complete!")
    print(f"\n📋 Next steps:")
    print(f"  1. Review {env_file} and update any PLACEHOLDER values")
    print(f"  2. Get your Stripe API key and webhook secret")
    print(f"  3. For production, set up a PostgreSQL database")
    print(f"  4. Run: python setup_database.py --with-test-user")
    
    return True

def create_env_example():
    """Create an example environment file for documentation"""
    example_content = """# MapMyStandards A3E Environment Variables

# Database (PostgreSQL for production, SQLite for dev)
DATABASE_URL=sqlite:///./data/a3e_dev.db
# DATABASE_URL=postgresql://user:password@localhost:5432/mapmystandards

# Security
JWT_SECRET_KEY=your-secure-jwt-secret-key-here

# API Configuration  
API_BASE_URL=http://localhost:8000
DATA_DIR=./data

# Stripe (Get from https://dashboard.stripe.com)
STRIPE_API_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_signing_secret
STRIPE_MONTHLY_PRICE_ID=price_your_monthly_price_id
STRIPE_ANNUAL_PRICE_ID=price_your_annual_price_id

# Email (Postmark)
POSTMARK_API_TOKEN=your-postmark-api-token
POSTMARK_MESSAGE_STREAM=your-message-stream
FROM_EMAIL=noreply@yourdomain.com
REPLY_TO_EMAIL=support@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com

# Optional: MailerSend (alternative email provider)
MAILER_SEND_API_KEY=your-mailersend-api-key

# Frontend URL
NEXT_PUBLIC_APP_URL=https://app.mapmystandards.ai
"""
    
    with open('.env.example', 'w') as f:
        f.write(example_content)

if __name__ == "__main__":
    try:
        setup_environment()
        
        # Now run the database setup
        print("\n🗄️  Setting up database...")
        result = subprocess.run([
            sys.executable, 
            'setup_database.py', 
            '--with-test-user'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database setup complete!")
            print(result.stdout)
        else:
            print("❌ Database setup failed!")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
