#!/usr/bin/env python3
"""
Manual trial recovery script for lost trial data due to server restarts.
This script can recreate a trial entry in the persistent storage.
"""

import json
import os
from datetime import datetime, timedelta

def recover_trial(trial_id, name, email, organization="Unknown"):
    """Recover a trial by manually adding it to the persistent storage"""
    
    TRIAL_DATA_FILE = "data/trial_users.json"
    
    # Load existing trial data
    trial_users = {}
    if os.path.exists(TRIAL_DATA_FILE):
        try:
            with open(TRIAL_DATA_FILE, 'r') as f:
                trial_users = json.load(f)
            print(f"✅ Loaded existing trial data with {len(trial_users)} trials")
        except Exception as e:
            print(f"❌ Error loading existing data: {e}")
    
    # Check if trial already exists
    if trial_id in trial_users:
        print(f"✅ Trial {trial_id} already exists in storage")
        print(f"   User: {trial_users[trial_id].get('name', 'Unknown')}")
        print(f"   Email: {trial_users[trial_id].get('email', 'Unknown')}")
        return True
    
    # Create trial entry
    trial_data = {
        'name': name,
        'email': email,
        'organization': organization,
        'use_case': 'stripe_trial_recovered',
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
        'status': 'active',
        'recovered': True,
        'recovery_date': datetime.now().isoformat()
    }
    
    # Add to trial users
    trial_users[trial_id] = trial_data
    
    # Save to persistent storage
    try:
        os.makedirs(os.path.dirname(TRIAL_DATA_FILE), exist_ok=True)
        with open(TRIAL_DATA_FILE, 'w') as f:
            json.dump(trial_users, f, indent=2, default=str)
        
        print(f"✅ Successfully recovered trial {trial_id}")
        print(f"   Name: {name}")
        print(f"   Email: {email}")
        print(f"   Organization: {organization}")
        print(f"   Expires: {trial_data['expires_at'][:10]}")
        print(f"   Dashboard URL: https://api.mapmystandards.ai/dashboard/{trial_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving trial data: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Trial Recovery Tool")
    print("=" * 50)
    
    # Recover the specific trial that was lost
    trial_id = "ALuvYpNhGklwcZqLnd5yIw"
    name = "Trial User"  # We can update this if you provide your actual name
    email = "user@example.com"  # We can update this if you provide your actual email
    organization = "Test Organization"
    
    print(f"Recovering trial: {trial_id}")
    success = recover_trial(trial_id, name, email, organization)
    
    if success:
        print("\n🎉 Recovery complete!")
        print(f"Your dashboard should now be accessible at:")
        print(f"https://api.mapmystandards.ai/dashboard/{trial_id}")
    else:
        print("\n❌ Recovery failed. Please check the error messages above.")
