#!/usr/bin/env python3
"""
Create proper Stripe subscription products with 7-day trials
This replaces the payment links with real subscription products
"""

import stripe
import os

# Set your Stripe secret key from environment variable
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


def create_subscription_products():
    """Create Stripe products and prices with 7-day trials"""

    print("🚀 Creating MapMyStandards subscription products...")

    try:
        # Create the main product
        product = stripe.Product.create(
            name="A³E Platform - MapMyStandards",
            description=("Accreditation Analytics Engine for educational "
                         "institutions"),
            images=["https://mapmystandards.ai/wp-content/uploads/2025/07/"
                    "Original-Logo.png"],
            metadata={
                "platform": "mapmystandards",
                "version": "v1.0"
            }
        )

        print(f"✅ Product created: {product.id}")

        # Create monthly price with 7-day trial
        monthly_price = stripe.Price.create(
            product=product.id,
            unit_amount=4999,  # $49.99
            currency="usd",
            recurring={
                "interval": "month",
                "trial_period_days": 7
            },
            metadata={
                "plan_type": "monthly",
                "trial_days": "7"
            }
        )

        print(f"✅ Monthly price created: {monthly_price.id}")

        # Create annual price with 7-day trial (and discount)
        annual_price = stripe.Price.create(
            product=product.id,
            unit_amount=49999,  # $499.99 (save $100 per year)
            currency="usd",
            recurring={
                "interval": "year",
                "trial_period_days": 7
            },
            metadata={
                "plan_type": "annual",
                "trial_days": "7"
            }
        )

        print(f"✅ Annual price created: {annual_price.id}")

        # Create configuration file for the application
        config = f"""# MapMyStandards Stripe Configuration
# Generated on {stripe.util.get_timestamp()}

# Product IDs
PRODUCT_ID={product.id}

# Price IDs (with 7-day trials)
MONTHLY_PRICE_ID={monthly_price.id}
ANNUAL_PRICE_ID={annual_price.id}

# Stripe Keys (set these in your environment)
STRIPE_PUBLISHABLE_KEY=your_live_publishable_key_here
STRIPE_SECRET_KEY=your_live_secret_key_here

# Webhook Configuration
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# Application Settings
TRIAL_PERIOD_DAYS=7
SUPPORT_EMAIL=support@mapmystandards.ai
PLATFORM_URL=https://platform.mapmystandards.ai
"""

        with open('stripe_config.env', 'w') as f:
            f.write(config)

        print("✅ Configuration saved to stripe_config.env")

        # Create summary report
        summary = f"""
🎉 SUCCESS! Stripe subscription products created:

📦 PRODUCT:
   ID: {product.id}
   Name: A³E Platform - MapMyStandards

💰 MONTHLY PLAN:
   Price ID: {monthly_price.id}
   Amount: $49.99/month
   Trial: 7 days free

💰 ANNUAL PLAN:
   Price ID: {annual_price.id}
   Amount: $499.99/year (save $100!)
   Trial: 7 days free

🔧 NEXT STEPS:
1. Update your application with these price IDs
2. Set up webhook endpoint for subscription events
3. Configure customer portal for cancellations
4. Test the trial flow before going live

📝 WEBHOOK EVENTS TO HANDLE:
- customer.subscription.created (trial started)
- customer.subscription.trial_will_end (3 days before trial ends)
- invoice.payment_succeeded (trial converted to paid)
- customer.subscription.deleted (cancellation)

🎯 TRIAL FLOW:
1. Customer signs up → 7-day trial starts
2. No charge for 7 days
3. After 7 days → automatic billing begins
4. Customer can cancel anytime during trial (no charge)
"""

        print(summary)

        with open('stripe_setup_summary.txt', 'w') as f:
            f.write(summary)

        return {
            'product_id': product.id,
            'monthly_price_id': monthly_price.id,
            'annual_price_id': annual_price.id
        }

    except stripe.error.StripeError as e:
        print(f"❌ Stripe error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    result = create_subscription_products()
    if result:
        print("\n🎉 All done! Check stripe_config.env for your configuration.")
    else:
        print("\n❌ Failed to create products. Check your Stripe keys "
              "and try again.")
