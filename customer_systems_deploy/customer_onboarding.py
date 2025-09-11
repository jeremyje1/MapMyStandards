#!/usr/bin/env python3
"""
Customer Onboarding Script for MapMyStandards
Generates secure, customer-specific JWT tokens for dashboard access
"""

import jwt
import os
import sys
import hashlib
from datetime import datetime, timedelta

def create_customer_access():
    """Interactive customer token creation"""
    print("🚀 MapMyStandards Customer Onboarding")
    print("=" * 50)
    print()
    
    # Collect customer information
    print("📋 Customer Information:")
    customer_email = input("Customer Email: ").strip()
    customer_org = input("Organization/Institution: ").strip()
    
    # Validate inputs
    if not customer_email or "@" not in customer_email:
        print("❌ Error: Please provide a valid email address")
        return
    
    if not customer_org:
        print("❌ Error: Please provide an organization name")
        return
    
    print()
    print("📊 Access Tier Selection:")
    print("1. Trial (7 days) - Limited features")
    print("2. Standard (30 days) - Full dashboard access")
    print("3. Premium (90 days) - Advanced analytics")
    print("4. Enterprise (365 days) - All features + API access")
    
    choice = input("Select tier (1-4): ").strip()
    
    tier_options = {
        "1": {"days": 7, "tier": "trial", "name": "Trial"},
        "2": {"days": 30, "tier": "standard", "name": "Standard"},
        "3": {"days": 90, "tier": "premium", "name": "Premium"},
        "4": {"days": 365, "tier": "enterprise", "name": "Enterprise"}
    }
    
    if choice not in tier_options:
        print("❌ Invalid selection. Using Standard (30 days)")
        tier_info = tier_options["2"]
    else:
        tier_info = tier_options[choice]
    
    # Generate customer-specific token
    secret_key = "BzKxm0pmrXyEyJditsbVDnngbvyhD512-xo0ei5G_l-si4m4B4dsE7DQeF9zYduD1-AtYvvIK-v1fAXS7QjFWQ"
    customer_id = hashlib.sha256(f"{customer_email}:{customer_org}".encode()).hexdigest()[:16]
    
    payload = {
        "sub": customer_email,
        "email": customer_email,
        "user_id": f"customer-{customer_id}",
        "organization": customer_org,
        "tier": tier_info["tier"],
        "exp": datetime.utcnow() + timedelta(days=tier_info["days"]),
        "iat": datetime.utcnow(),
        "environment": "production",
        "features": get_tier_features(tier_info["tier"])
    }
    
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    
    # Display results
    print()
    print("✅ Customer Access Created Successfully!")
    print("=" * 60)
    print(f"📧 Customer: {customer_email}")
    print(f"🏢 Organization: {customer_org}")
    print(f"🎯 Tier: {tier_info['name']} ({tier_info['days']} days)")
    print(f"📅 Expires: {(datetime.utcnow() + timedelta(days=tier_info['days'])).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()
    
    # Customer setup instructions
    print("📋 CUSTOMER SETUP INSTRUCTIONS")
    print("=" * 40)
    print("Send these instructions to your customer:")
    print()
    print("🌐 Dashboard Access Setup:")
    print("1. Open your web browser")
    print("2. Navigate to: https://your-dashboard-url.com")
    print("3. Press F12 to open Developer Tools")
    print("4. Click on the 'Console' tab")
    print("5. Copy and paste this EXACT command:")
    print()
    print(f"localStorage.setItem('jwt_token', '{token}');")
    print()
    print("6. Press Enter to execute the command")
    print("7. Close Developer Tools (F12 again)")
    print("8. Refresh the page or navigate to the dashboard")
    print()
    print("✨ The dashboard will now load with full access!")
    print()
    
    # Features summary
    print("🎯 AVAILABLE FEATURES:")
    features = get_tier_features(tier_info["tier"])
    for feature in features:
        print(f"   ✅ {feature}")
    print()
    
    # Support information
    print("📞 SUPPORT INFORMATION:")
    print("   • Token expires automatically after the trial period")
    print("   • Customer can contact support for extension")
    print("   • All data is secure and customer-specific")
    print(f"   • Customer ID: {customer_id}")
    print()
    
    # Save customer record
    save_customer_record(customer_email, customer_org, tier_info, customer_id, token)

def get_tier_features(tier):
    """Get features available for each tier"""
    features = {
        "trial": [
            "Basic Dashboard View",
            "Standards Overview",
            "Sample Evidence Upload"
        ],
        "standard": [
            "Full AI Dashboard",
            "StandardsGraph™ Analysis", 
            "EvidenceMapper™",
            "Compliance Scoring",
            "Document Upload & Analysis"
        ],
        "premium": [
            "Full AI Dashboard",
            "StandardsGraph™ Analysis",
            "EvidenceMapper™", 
            "Advanced Analytics",
            "Gap Risk Prediction",
            "Compliance Reporting",
            "Multi-accreditor Support"
        ],
        "enterprise": [
            "All Premium Features",
            "API Access",
            "Bulk Document Processing",
            "Custom Integrations",
            "Priority Support",
            "White-label Options"
        ]
    }
    return features.get(tier, features["standard"])

def save_customer_record(email, org, tier_info, customer_id, token):
    """Save customer record for tracking"""
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "email": email,
        "organization": org,
        "tier": tier_info["tier"],
        "days": tier_info["days"],
        "customer_id": customer_id,
        "token_preview": token[:20] + "...",
        "expires": (datetime.utcnow() + timedelta(days=tier_info["days"])).isoformat()
    }
    
    # Append to customer log
    import json
    try:
        with open("customer_access_log.json", "a") as f:
            f.write(json.dumps(record) + "\n")
        print(f"📝 Customer record saved to customer_access_log.json")
    except Exception as e:
        print(f"⚠️  Could not save customer record: {e}")

if __name__ == "__main__":
    create_customer_access()
