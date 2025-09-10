#!/usr/bin/env python3
"""Check Stripe webhook configuration"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# Set up Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

if not stripe.api_key:
    print("❌ STRIPE_SECRET_KEY not found in environment")
    exit(1)

print("Checking Stripe webhook endpoints...\n")

try:
    # List all webhook endpoints
    endpoints = stripe.WebhookEndpoint.list(limit=10)
    
    if not endpoints.data:
        print("❌ No webhook endpoints configured!")
        print("\n🔧 To fix this:")
        print("1. Go to https://dashboard.stripe.com/webhooks")
        print("2. Click 'Add endpoint'")
        print("3. Enter URL: https://api.mapmystandards.ai/api/v1/billing/webhook/stripe")
        print("4. Select events: checkout.session.completed")
        print("5. Copy the signing secret and set STRIPE_WEBHOOK_SECRET in Railway")
    else:
        for endpoint in endpoints.data:
            print(f"📌 Webhook: {endpoint.url}")
            print(f"   Status: {'✅ Enabled' if endpoint.status == 'enabled' else '❌ Disabled'}")
            print(f"   Events: {', '.join(endpoint.enabled_events[:3])}...")
            print(f"   Created: {endpoint.created}")
            print("")
            
            # Check if our endpoint is configured
            if 'api.mapmystandards.ai' in endpoint.url:
                print("✅ MapMyStandards webhook found!")
                if 'checkout.session.completed' in endpoint.enabled_events:
                    print("✅ checkout.session.completed event is enabled")
                else:
                    print("❌ checkout.session.completed event is NOT enabled!")
                    
except stripe.error.StripeError as e:
    print(f"❌ Stripe API error: {e}")
    print("\nMake sure you're using the correct Stripe API key")
    
print("\n📝 Note: After user signup, check Railway logs for webhook activity:")
print("   railway logs | grep webhook")
