#!/usr/bin/env python3
"""
Stripe Cleanup Script - Remove duplicate products and prices
"""

import os
import stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def cleanup_duplicate_products():
    """Remove duplicate A³E products keeping only the latest ones"""
    
    print("🧹 Cleaning up duplicate Stripe products...")
    
    # Get all products
    products = stripe.Product.list(limit=100)
    a3e_products = [p for p in products.data if 'A³E' in p.name]
    
    print(f"Found {len(a3e_products)} A³E products")
    
    # Group by name
    college_products = [p for p in a3e_products if 'College Plan' in p.name]
    multicampus_products = [p for p in a3e_products if 'Multi-Campus Plan' in p.name]
    
    # Keep newest, delete others
    def cleanup_product_group(products, name):
        if len(products) > 1:
            # Sort by creation date (newest first)
            products.sort(key=lambda x: x.created, reverse=True)
            keep = products[0]
            delete_list = products[1:]
            
            print(f"\n{name}:")
            print(f"  Keeping: {keep.id} (created: {keep.created})")
            
            for product in delete_list:
                try:
                    # First, get and delete all prices for this product
                    prices = stripe.Price.list(product=product.id)
                    for price in prices.data:
                        print(f"  Deleting price: {price.id}")
                        # Stripe doesn't allow deleting prices, but we can deactivate them
                        stripe.Price.modify(price.id, active=False)
                    
                    # Then delete the product
                    print(f"  Deleting product: {product.id}")
                    stripe.Product.modify(product.id, active=False)
                    
                except Exception as e:
                    print(f"  Error deleting {product.id}: {e}")
    
    cleanup_product_group(college_products, "College Plan")
    cleanup_product_group(multicampus_products, "Multi-Campus Plan")
    
    print("\n✅ Cleanup complete!")

if __name__ == "__main__":
    cleanup_duplicate_products()
