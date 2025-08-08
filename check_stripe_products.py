#!/usr/bin/env python3
"""
Check existing Stripe products and prices for A³E
"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# Set the Stripe API key from environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


def list_existing_products():
    """List all existing products and their prices"""

    if not stripe.api_key:
        print("❌ Error: STRIPE_SECRET_KEY not found in environment variables")
        return None

    print("🔍 Checking existing Stripe products...")
    print("=" * 50)

    try:
        # List all products
        products = stripe.Product.list(active=True, limit=10)

        if not products.data:
            print("No products found. Creating new ones...")
            return None

        for product in products.data:
            print(f"\n📦 Product: {product.name}")
            print(f"   ID: {product.id}")
            print(f"   Description: {product.description}")

            # Get prices for this product
            prices = stripe.Price.list(product=product.id, active=True)

            for price in prices.data:
                interval = (price.recurring.interval if price.recurring
                            else 'one-time')
                amount = price.unit_amount / 100
                print(f"   💰 Price: ${amount}/{interval} (ID: {price.id})")

        return products.data

    except Exception as e:
        print(f"❌ Error checking products: {str(e)}")
        return None


if __name__ == "__main__":
    products = list_existing_products()
    if products:
        print(f"\n✅ Found {len(products)} existing products")
    else:
        print("\n❌ No products found or error occurred")
