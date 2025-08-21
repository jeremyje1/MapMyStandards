#!/usr/bin/env python3
"""
Test script to verify new Stripe pricing configuration
"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('.env.pricing')

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def test_pricing():
    """Test that all new price IDs exist and are correct"""
    
    pricing_config = {
        "Starter Monthly": os.getenv('STRIPE_PRICE_ID_STARTER_MONTHLY', 'price_1RyVDtRMpSG47vNmDPNdcTbm'),
        "Starter Annual": os.getenv('STRIPE_PRICE_ID_STARTER_ANNUAL', 'price_1RyVE2RMpSG47vNmVjOIvF0a'),
        "Professional Monthly": os.getenv('STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY', 'price_1RyVEORMpSG47vNmYL4DWCYF'),
        "Professional Annual": os.getenv('STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL', 'price_1RyVEWRMpSG47vNmiQjLhvqt'),
        "Institution Monthly": os.getenv('STRIPE_PRICE_ID_INSTITUTION_MONTHLY', 'price_1RyVElRMpSG47vNmWNWcxCEB'),
        "Institution Annual": os.getenv('STRIPE_PRICE_ID_INSTITUTION_ANNUAL', 'price_1RyVEtRMpSG47vNmyZDQcjUm'),
    }
    
    print("Testing Stripe Pricing Configuration")
    print("=" * 50)
    
    for name, price_id in pricing_config.items():
        try:
            price = stripe.Price.retrieve(price_id)
            product = stripe.Product.retrieve(price.product)
            
            amount = price.unit_amount / 100
            interval = price.recurring.interval if price.recurring else "one-time"
            
            print(f"\n✅ {name}")
            print(f"   Price ID: {price_id}")
            print(f"   Product: {product.name}")
            print(f"   Amount: ${amount:,.2f} / {interval}")
            print(f"   Active: {price.active}")
            
        except stripe.error.StripeError as e:
            print(f"\n❌ {name}")
            print(f"   Price ID: {price_id}")
            print(f"   Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("\nPricing Structure Summary:")
    print("\nStarter Tier:")
    print("  - Monthly: $99/month")
    print("  - Annual: $999/year (Save $189)")
    
    print("\nProfessional Tier (Most Popular):")
    print("  - Monthly: $299/month")
    print("  - Annual: $2,999/year (Save $589)")
    
    print("\nInstitution Tier:")
    print("  - Monthly: $599/month")
    print("  - Annual: $5,999/year (Save $1,189)")
    
    print("\nEnterprise Tier:")
    print("  - Custom pricing - Contact sales")

if __name__ == "__main__":
    test_pricing()
