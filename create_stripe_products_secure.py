#!/usr/bin/env python3
"""
A³E MapMyStandards.ai - Secure Stripe Products Setup
Using environment variables for Stripe API keys

New Pricing Model: $49.99/month, $499/year, Consultative
"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set the Stripe API key from environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def create_a3e_products():
    """Create A³E products and pricing in Stripe"""
    
    if not stripe.api_key:
        print("❌ Error: STRIPE_SECRET_KEY not found in environment variables")
        print("Please set your Stripe secret key in .env file")
        return None
        
    print("🚀 Creating A³E Stripe Products")
    print("=" * 50)
    
    try:
        # Create the main A³E product
        product = stripe.Product.create(
            name="A³E Accreditation Analytics Engine",
            description="Complete accreditation management and analytics platform for educational institutions",
            metadata={
                "platform": "a3e",
                "version": "1.0"
            }
        )
        
        print(f"✅ Product created: {product.name}")
        print(f"   Product ID: {product.id}")
        
        # Create monthly pricing
        monthly_price = stripe.Price.create(
            product=product.id,
            unit_amount=4999,  # $49.99
            currency='usd',
            recurring={'interval': 'month'},
            nickname='A³E Monthly'
        )
        
        print(f"✅ Monthly price created: ${monthly_price.unit_amount/100}/month")
        print(f"   Price ID: {monthly_price.id}")
        
        # Create yearly pricing (with discount)
        yearly_price = stripe.Price.create(
            product=product.id,
            unit_amount=49900,  # $499 (17% discount)
            currency='usd',
            recurring={'interval': 'year'},
            nickname='A³E Yearly'
        )
        
        print(f"✅ Yearly price created: ${yearly_price.unit_amount/100}/year")
        print(f"   Price ID: {yearly_price.id}")
        
        return {
            'product_id': product.id,
            'monthly_price_id': monthly_price.id,
            'yearly_price_id': yearly_price.id
        }
        
    except Exception as e:
        print(f"❌ Error creating products: {str(e)}")
        return None

if __name__ == "__main__":
    result = create_a3e_products()
    if result:
        print("\n🎉 Stripe products created successfully!")
        print("\nProduct IDs to use in your environment:")
        print(f"STRIPE_PRODUCT_ID={result['product_id']}")
        print(f"STRIPE_MONTHLY_PRICE_ID={result['monthly_price_id']}")
        print(f"STRIPE_YEARLY_PRICE_ID={result['yearly_price_id']}")
    else:
        print("\n❌ Failed to create Stripe products")
