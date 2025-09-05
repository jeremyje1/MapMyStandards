#!/usr/bin/env python3
"""Test script to simulate Stripe webhook for debugging user creation"""

import json
import requests
from datetime import datetime

# Simulate a checkout.session.completed event
webhook_payload = {
    "type": "checkout.session.completed",
    "data": {
        "object": {
            "id": "cs_test_12345",
            "customer": "cus_test_12345",
            "customer_details": {
                "email": "testwebhook@example.com",
                "name": "Test Webhook User"
            },
            "subscription": "sub_test_12345",
            "amount_total": 19900,  # $199 in cents
            "metadata": {
                "plan_name": "Professional",
                "institution_name": "Test University",
                "institution_type": "college",
                "role": "Administrator"
            }
        }
    }
}

# Send to the correct backend endpoint
url = "https://api.mapmystandards.ai/api/billing/webhook/stripe"

print(f"Testing webhook at: {url}")
print(f"Payload: {json.dumps(webhook_payload, indent=2)}")

try:
    response = requests.post(url, json=webhook_payload)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response body: {response.text}")
except Exception as e:
    print(f"Error: {e}")