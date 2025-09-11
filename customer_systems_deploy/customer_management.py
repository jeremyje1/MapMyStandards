#!/usr/bin/env python3
"""
Customer Management Dashboard
View and manage customer access tokens
"""

import json
import os
from datetime import datetime
import jwt

def load_customer_records():
    """Load customer records from log file"""
    try:
        with open("customer_access_log.json", "r") as f:
            records = []
            for line in f:
                if line.strip():
                    records.append(json.loads(line.strip()))
            return records
    except FileNotFoundError:
        return []

def view_customers():
    """Display all customer records"""
    records = load_customer_records()
    
    if not records:
        print("📭 No customer records found.")
        return
    
    print("👥 CUSTOMER ACCESS DASHBOARD")
    print("=" * 80)
    print(f"{'Email':<30} {'Organization':<25} {'Tier':<12} {'Status':<10} {'Expires':<12}")
    print("-" * 80)
    
    now = datetime.utcnow()
    
    for record in records:
        expires = datetime.fromisoformat(record['expires'].replace('Z', '+00:00').replace('+00:00', ''))
        status = "🟢 Active" if expires > now else "🔴 Expired"
        expires_str = expires.strftime('%Y-%m-%d')
        
        print(f"{record['email']:<30} {record['organization']:<25} {record['tier']:<12} {status:<10} {expires_str:<12}")
    
    print("-" * 80)
    print(f"Total customers: {len(records)}")
    
    # Summary stats
    active = sum(1 for r in records if datetime.fromisoformat(r['expires'].replace('Z', '+00:00').replace('+00:00', '')) > now)
    expired = len(records) - active
    
    print(f"Active: 🟢 {active} | Expired: 🔴 {expired}")

def validate_customer_token():
    """Validate a specific customer token"""
    token = input("Enter customer token: ").strip()
    
    try:
        secret_key = "BzKxm0pmrXyEyJditsbVDnngbvyhD512-xo0ei5G_l-si4m4B4dsE7DQeF9zYduD1-AtYvvIK-v1fAXS7QjFWQ"
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        print("\n✅ Token is VALID")
        print("-" * 40)
        print(f"Customer: {payload.get('email')}")
        print(f"Organization: {payload.get('organization')}")
        print(f"Tier: {payload.get('tier')}")
        print(f"Customer ID: {payload.get('user_id')}")
        print(f"Expires: {datetime.fromtimestamp(payload.get('exp')).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # Check if expired
        if datetime.fromtimestamp(payload.get('exp')) < datetime.utcnow():
            print("⚠️  Status: EXPIRED")
        else:
            print("🟢 Status: ACTIVE")
            
    except jwt.ExpiredSignatureError:
        print("\n🔴 Token is EXPIRED")
    except jwt.InvalidTokenError:
        print("\n❌ Token is INVALID")

def main():
    """Main menu for customer management"""
    while True:
        print("\n🔧 MapMyStandards Customer Management")
        print("=" * 40)
        print("1. View All Customers")
        print("2. Validate Customer Token")
        print("3. Create New Customer Access")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            print()
            view_customers()
        elif choice == "2":
            print()
            validate_customer_token()
        elif choice == "3":
            print("\nLaunching customer onboarding...")
            os.system("python3 customer_onboarding.py")
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please select 1-4.")

if __name__ == "__main__":
    main()
