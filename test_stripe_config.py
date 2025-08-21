"""Test script to verify Stripe configuration"""
import os
from src.a3e.core.config import get_settings

# Get settings
settings = get_settings()

print("=== Stripe Configuration Test ===")
print(f"STRIPE_SECRET_KEY exists: {bool(settings.STRIPE_SECRET_KEY)}")
print(f"STRIPE_SECRET_KEY length: {len(settings.STRIPE_SECRET_KEY) if settings.STRIPE_SECRET_KEY else 0}")
print(f"STRIPE_PUBLISHABLE_KEY exists: {bool(settings.STRIPE_PUBLISHABLE_KEY)}")
print(f"STRIPE_PUBLISHABLE_KEY starts with: {settings.STRIPE_PUBLISHABLE_KEY[:10] if settings.STRIPE_PUBLISHABLE_KEY else 'None'}")

print("\n=== Price IDs ===")
print(f"STRIPE_PRICE_COLLEGE_MONTHLY: {settings.STRIPE_PRICE_COLLEGE_MONTHLY}")
print(f"STRIPE_PRICE_COLLEGE_YEARLY: {settings.STRIPE_PRICE_COLLEGE_YEARLY}")
print(f"STRIPE_PRICE_MULTI_CAMPUS_MONTHLY: {settings.STRIPE_PRICE_MULTI_CAMPUS_MONTHLY}")
print(f"STRIPE_PRICE_MULTI_CAMPUS_YEARLY: {settings.STRIPE_PRICE_MULTI_CAMPUS_YEARLY}")

print("\n=== Environment Variables (Direct) ===")
print(f"STRIPE_SECRET_KEY from env: {bool(os.getenv('STRIPE_SECRET_KEY'))}")
print(f"STRIPE_PUBLISHABLE_KEY from env: {bool(os.getenv('STRIPE_PUBLISHABLE_KEY'))}")
print(f"STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY from env: {os.getenv('STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY', 'Not found')}")
print(f"STRIPE_PRICE_ID_INSTITUTION_MONTHLY from env: {os.getenv('STRIPE_PRICE_ID_INSTITUTION_MONTHLY', 'Not found')}")
