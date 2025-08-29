#!/bin/bash

# Railway Environment Variables Setup Script
# This script helps you configure all required environment variables for Railway deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚂 Railway Environment Variables Setup${NC}"
echo -e "${YELLOW}This script will help you set up environment variables for Railway deployment${NC}\n"

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}Railway CLI is not installed!${NC}"
    echo "Install it with: npm install -g @railway/cli"
    exit 1
fi

# Check if logged in to Railway
echo -e "${BLUE}Checking Railway authentication...${NC}"
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Railway. Logging in...${NC}"
    railway login
fi

echo -e "${GREEN}✅ Railway CLI ready${NC}\n"

# Function to set Railway environment variable
set_railway_var() {
    local key=$1
    local value=$2
    local description=$3
    
    echo -e "${BLUE}Setting ${key}...${NC}"
    if [[ -n "$value" ]]; then
        railway variables set "$key=$value" --yes
        echo -e "${GREEN}✅ ${key} set${NC}"
    else
        echo -e "${YELLOW}⚠️  ${key} skipped (no value)${NC}"
    fi
}

# Load existing .env file if present
if [ -f ".env" ]; then
    echo -e "${GREEN}Found local .env file. Loading values...${NC}\n"
    source .env
else
    echo -e "${YELLOW}No .env file found. You'll need to provide values manually.${NC}\n"
fi

echo -e "${BLUE}Setting up Railway environment variables...${NC}\n"

# ============================================
# SECURITY VARIABLES
# ============================================
echo -e "${YELLOW}=== Security Configuration ===${NC}"

# Generate new production secrets if not provided
if [[ -z "$SECRET_KEY" ]]; then
    echo -e "${YELLOW}Generating new SECRET_KEY for production...${NC}"
    SECRET_KEY=$(openssl rand -base64 48)
fi

if [[ -z "$JWT_SECRET_KEY" ]]; then
    echo -e "${YELLOW}Generating new JWT_SECRET_KEY for production...${NC}"
    JWT_SECRET_KEY=$(openssl rand -base64 32)
fi

if [[ -z "$NEXTAUTH_SECRET" ]]; then
    echo -e "${YELLOW}Generating new NEXTAUTH_SECRET for production...${NC}"
    NEXTAUTH_SECRET=$(openssl rand -base64 32)
fi

if [[ -z "$DATABASE_ENCRYPTION_KEY" ]]; then
    echo -e "${YELLOW}Generating new DATABASE_ENCRYPTION_KEY for production...${NC}"
    DATABASE_ENCRYPTION_KEY=$(openssl rand -hex 32)
fi

set_railway_var "SECRET_KEY" "$SECRET_KEY" "Application secret key"
set_railway_var "JWT_SECRET_KEY" "$JWT_SECRET_KEY" "JWT signing key"
set_railway_var "NEXTAUTH_SECRET" "$NEXTAUTH_SECRET" "NextAuth secret"
set_railway_var "DATABASE_ENCRYPTION_KEY" "$DATABASE_ENCRYPTION_KEY" "Database encryption key"

# ============================================
# APPLICATION VARIABLES
# ============================================
echo -e "\n${YELLOW}=== Application Configuration ===${NC}"

set_railway_var "NODE_ENV" "production" "Node environment"
set_railway_var "RAILWAY_ENVIRONMENT" "production" "Railway environment"
set_railway_var "PORT" "8000" "Application port"
set_railway_var "API_PORT" "8000" "API port"
set_railway_var "API_HOST" "0.0.0.0" "API host"

# Get Railway public domain
echo -e "${BLUE}Getting Railway domain...${NC}"
RAILWAY_DOMAIN=$(railway domain --json 2>/dev/null | grep -o '"domain":"[^"]*' | cut -d'"' -f4 || echo "")

if [[ -n "$RAILWAY_DOMAIN" ]]; then
    set_railway_var "API_BASE_URL" "https://$RAILWAY_DOMAIN" "API base URL"
    set_railway_var "NEXT_PUBLIC_APP_URL" "https://$RAILWAY_DOMAIN" "Public app URL"
    set_railway_var "NEXTAUTH_URL" "https://$RAILWAY_DOMAIN" "NextAuth URL"
else
    echo -e "${YELLOW}Could not get Railway domain. Set these manually after deployment:${NC}"
    echo "  - API_BASE_URL"
    echo "  - NEXT_PUBLIC_APP_URL"
    echo "  - NEXTAUTH_URL"
fi

# ============================================
# DATABASE CONFIGURATION
# ============================================
echo -e "\n${YELLOW}=== Database Configuration ===${NC}"

# Railway provides DATABASE_URL automatically if you provision a PostgreSQL database
echo -e "${BLUE}Railway will provide DATABASE_URL when you provision PostgreSQL${NC}"
echo -e "${YELLOW}To add PostgreSQL: railway add postgresql${NC}"

set_railway_var "DATABASE_POOL_SIZE" "20" "Database connection pool size"
set_railway_var "DATABASE_MAX_OVERFLOW" "30" "Database max overflow"

# ============================================
# EMAIL CONFIGURATION (Postmark)
# ============================================
echo -e "\n${YELLOW}=== Email Configuration (Postmark) ===${NC}"

set_railway_var "POSTMARK_API_TOKEN" "$POSTMARK_API_TOKEN" "Postmark API token"
set_railway_var "POSTMARK_MESSAGE_STREAM" "${POSTMARK_MESSAGE_STREAM:-outbound}" "Postmark message stream"
set_railway_var "FROM_EMAIL" "${FROM_EMAIL:-noreply@mapmystandards.ai}" "From email address"
set_railway_var "REPLY_TO_EMAIL" "${REPLY_TO_EMAIL:-support@mapmystandards.ai}" "Reply-to email"
set_railway_var "ADMIN_EMAIL" "${ADMIN_EMAIL:-admin@mapmystandards.ai}" "Admin email"

# ============================================
# STRIPE CONFIGURATION
# ============================================
echo -e "\n${YELLOW}=== Stripe Configuration ===${NC}"

if [[ -n "$STRIPE_SECRET_KEY" ]]; then
    set_railway_var "STRIPE_SECRET_KEY" "$STRIPE_SECRET_KEY" "Stripe secret key"
else
    echo -e "${RED}⚠️  STRIPE_SECRET_KEY not found. Add it manually for payments to work.${NC}"
fi

set_railway_var "STRIPE_PUBLISHABLE_KEY" "$STRIPE_PUBLISHABLE_KEY" "Stripe publishable key"
set_railway_var "STRIPE_WEBHOOK_SECRET" "$STRIPE_WEBHOOK_SECRET" "Stripe webhook secret"

# Price IDs
set_railway_var "STRIPE_PRICE_COLLEGE_MONTHLY" "$STRIPE_PRICE_COLLEGE_MONTHLY" "College monthly price"
set_railway_var "STRIPE_PRICE_COLLEGE_YEARLY" "$STRIPE_PRICE_COLLEGE_YEARLY" "College yearly price"
set_railway_var "STRIPE_PRICE_MULTI_CAMPUS_MONTHLY" "$STRIPE_PRICE_MULTI_CAMPUS_MONTHLY" "Multi-campus monthly"
set_railway_var "STRIPE_PRICE_MULTI_CAMPUS_YEARLY" "$STRIPE_PRICE_MULTI_CAMPUS_YEARLY" "Multi-campus yearly"

# ============================================
# AI SERVICES (Optional)
# ============================================
echo -e "\n${YELLOW}=== AI Services Configuration (Optional) ===${NC}"

if [[ -n "$OPENAI_API_KEY" ]]; then
    set_railway_var "OPENAI_API_KEY" "$OPENAI_API_KEY" "OpenAI API key"
fi

if [[ -n "$ANTHROPIC_API_KEY" ]]; then
    set_railway_var "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY" "Anthropic API key"
fi

# ============================================
# REDIS CONFIGURATION (Optional)
# ============================================
echo -e "\n${YELLOW}=== Redis Configuration (Optional) ===${NC}"

if [[ -n "$REDIS_URL" ]]; then
    set_railway_var "REDIS_URL" "$REDIS_URL" "Redis URL"
    set_railway_var "REDIS_TTL" "${REDIS_TTL:-3600}" "Redis TTL"
else
    echo -e "${BLUE}Redis not configured. Add 'railway add redis' if needed.${NC}"
fi

# ============================================
# OTHER CONFIGURATION
# ============================================
echo -e "\n${YELLOW}=== Other Configuration ===${NC}"

set_railway_var "LOG_LEVEL" "${LOG_LEVEL:-INFO}" "Log level"
set_railway_var "DEBUG" "false" "Debug mode"
set_railway_var "MAX_FILE_SIZE_MB" "${MAX_FILE_SIZE_MB:-100}" "Max file size"
set_railway_var "SUPPORTED_FILE_TYPES" "${SUPPORTED_FILE_TYPES:-pdf,docx,xlsx,csv,txt,md}" "Supported file types"
set_railway_var "DATA_DIR" "./data" "Data directory"

# ============================================
# SUMMARY
# ============================================
echo -e "\n${GREEN}✅ Railway environment variables setup complete!${NC}"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo "1. Review variables in Railway dashboard: railway open"
echo "2. Add PostgreSQL database: railway add postgresql"
echo "3. Add Redis (optional): railway add redis"
echo "4. Deploy your application: railway up"
echo ""
echo -e "${YELLOW}Important variables to verify/add manually:${NC}"
echo "  - STRIPE_SECRET_KEY (if not set)"
echo "  - STRIPE_WEBHOOK_SECRET (after setting up webhook)"
echo "  - Custom domain settings (after domain setup)"
echo ""
echo -e "${GREEN}To view all variables: railway variables${NC}"
echo -e "${GREEN}To deploy: railway up${NC}"