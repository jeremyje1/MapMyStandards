# Stripe Product Creation Script
# Run this in your Stripe dashboard or via API

import os
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Stripe with secret key
stripe_key = os.getenv('STRIPE_SECRET_KEY')

if not stripe_key or stripe_key == 'sk_test_your_stripe_secret_key_here':
    print("❌ Stripe API key not configured!")
    print("\n📋 Setup Instructions:")
    print("1. Go to https://dashboard.stripe.com/apikeys")
    print("2. Copy your 'Secret key' (starts with sk_test_ or sk_)")
    print("3. Update STRIPE_SECRET_KEY in your .env file")
    print("4. Run this script again: python stripe_products_setup.py")
    print("\n💡 Need a Stripe account?")
    print("   → Sign up at https://stripe.com")
    print("   → Verification usually takes 1-2 business days")
    exit(1)

stripe.api_key = stripe_key

# 1. Create Products (matches stripe_trial_setup.md exactly)
products = [
    {
        "name": "A³E College Plan",
        "description": "Complete accreditation automation for colleges and their accreditation teams",
        "metadata": {
            "plan_type": "college",
            "target_audience": "colleges_and_accreditation_directors",
            "features": "unlimited_docs,3_institutions,full_ai_pipeline,canvas_integration"
        }
    },
    {
        "name": "A³E Multi-Campus Plan", 
        "description": "Enterprise accreditation management for multi-campus colleges",
        "metadata": {
            "plan_type": "multicampus",
            "target_audience": "university_systems_and_enterprise_directors",
            "features": "unlimited_everything,api_access,dedicated_support,white_label"
        }
    }
]

# 2. Create Pricing Plans (exact prices from stripe_trial_setup.md)
pricing_plans = [
    # College Plan Monthly
    {
        "product": "A³E College Plan",
        "unit_amount": 29700,  # $297.00
        "currency": "usd",
        "recurring": {"interval": "month"},
        "nickname": "price_college_monthly"
    },
    # College Plan Yearly  
    {
        "product": "A³E College Plan",
        "unit_amount": 297000,  # $2,970.00 (annual)
        "currency": "usd",
        "recurring": {"interval": "year"},
        "nickname": "price_college_yearly"
    },
    # Multi-Campus Plan Monthly
    {
        "product": "A³E Multi-Campus Plan",
        "unit_amount": 89700,  # $897.00
        "currency": "usd",
        "recurring": {"interval": "month"},
        "nickname": "price_multicampus_monthly"
    },
    # Multi-Campus Plan Yearly
    {
        "product": "A³E Multi-Campus Plan",
        "unit_amount": 807300,  # $8,073.00 (annual)
        "currency": "usd", 
        "recurring": {"interval": "year"},
        "nickname": "price_multicampus_yearly"
    }
]

# Execute creation with proper error handling and output
def create_products_and_prices():
    """Create Stripe products and prices according to stripe_trial_setup.md"""
    
    print("\n🚀 Creating Stripe Products for A³E (MapMyStandards.ai)")
    print("=" * 60)
    
    created_products = {}
    created_prices = {}
    
    try:
        # Create Products
        print("\n📦 Creating Products...")
        for product_data in products:
            print(f"   → Creating: {product_data['name']}")
            product = stripe.Product.create(**product_data)
            created_products[product_data['name']] = product.id
            print(f"     ✅ Product ID: {product.id}")
        
        # Create Prices
        print("\n💰 Creating Price Plans...")
        for price_data in pricing_plans:
            product_name = price_data.pop('product')
            product_id = created_products[product_name]
            price_data['product'] = product_id
            
            print(f"   → Creating: {price_data['nickname']}")
            price = stripe.Price.create(**price_data)
            created_prices[price_data['nickname']] = price.id
            
            # Display price info
            amount = price_data['unit_amount'] / 100
            interval = price_data['recurring']['interval']
            print(f"     ✅ Price ID: {price.id}")
            print(f"     💵 Amount: ${amount:,.2f} per {interval}")
            print(f"     🆓 Trial: 7 days (set on subscription)")
        
        # Success Summary
        print("\n" + "=" * 60)
        print("✅ SUCCESS: All Stripe products created!")
        print("\n📋 Update your .env file with these Price IDs:")
        print("-" * 50)
        for nickname, price_id in created_prices.items():
            env_var = f"STRIPE_{nickname.upper()}"
            print(f"{env_var}={price_id}")
        
        print(f"\n🔑 Next Steps:")
        print("1. Copy the Price IDs above to your .env file")
        print("2. Update your Stripe API keys in .env")
        print("3. Set up webhooks in Stripe Dashboard")
        print("4. Test the checkout flow")
        
        return True
        
    except stripe.error.StripeError as e:
        print(f"\n❌ Stripe Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    create_products_and_prices()
