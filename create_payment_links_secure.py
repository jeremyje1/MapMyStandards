#!/usr/bin/env python3
"""
A³E MapMyStandards.ai - Secure Stripe Payment Links Creator
Uses environment variables for API keys and configuration
"""

import stripe
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set the Stripe API key from environment
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


def create_payment_links():
    """Create Stripe Payment Links for easy checkout"""

    if not stripe.api_key:
        print("❌ Error: STRIPE_SECRET_KEY not found in environment variables")
        return None

    # Get price IDs from environment (try multiple variable names)
    monthly_price_id = (os.getenv('STRIPE_MONTHLY_PRICE_ID') or 
                       os.getenv('STRIPE_PRICE_ID_STARTER_MONTHLY') or
                       os.getenv('STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY'))
    yearly_price_id = (os.getenv('STRIPE_YEARLY_PRICE_ID') or 
                      os.getenv('STRIPE_PRICE_ID_STARTER_ANNUAL') or
                      os.getenv('STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL'))

    if not monthly_price_id or not yearly_price_id:
        print("❌ Error: Price IDs not found in environment variables")
        print("Please set STRIPE_MONTHLY_PRICE_ID and STRIPE_YEARLY_PRICE_ID")
        return None

    print("🔗 Creating Stripe Payment Links")
    print("=" * 40)

    try:
        # Create monthly payment link
        monthly_link = stripe.PaymentLink.create(
            line_items=[{
                'price': monthly_price_id,
                'quantity': 1,
            }],
            after_completion={
                "type": "redirect",
                "redirect": {
                    "url": ("https://platform.mapmystandards.ai/"
                            "dashboard?plan=monthly&success=true")
                }
            }
        )

        print(f"✅ Monthly payment link: {monthly_link.url}")

        # Create yearly payment link
        yearly_link = stripe.PaymentLink.create(
            line_items=[{
                'price': yearly_price_id,
                'quantity': 1,
            }],
            after_completion={
                "type": "redirect",
                "redirect": {
                    "url": ("https://platform.mapmystandards.ai/"
                            "dashboard?plan=yearly&success=true")
                }
            }
        )

        print(f"✅ Yearly payment link: {yearly_link.url}")

        return {
            'monthly_link': monthly_link.url,
            'yearly_link': yearly_link.url
        }

    except Exception as e:
        print(f"❌ Error creating payment links: {str(e)}")
        return None


if __name__ == "__main__":
    result = create_payment_links()
    if result:
        print("\n🎉 Payment links created successfully!")
        print("\nAdd these to your environment or use directly:")
        print(f"STRIPE_MONTHLY_CHECKOUT_URL={result['monthly_link']}")
        print(f"STRIPE_YEARLY_CHECKOUT_URL={result['yearly_link']}")
    else:
        print("\n❌ Failed to create payment links")
