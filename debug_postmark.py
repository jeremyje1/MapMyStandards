#!/usr/bin/env python3
"""
Debug Postmark Token

This script debugs the Postmark token to see what's happening.
"""

import os
from dotenv import load_dotenv
load_dotenv()

def debug_postmark_token():
    """Debug the Postmark token configuration"""
    print("🔍 Debugging Postmark token...")
    
    # Check both possible environment variable names
    server_token = os.getenv('POSTMARK_SERVER_TOKEN')
    api_token = os.getenv('POSTMARK_API_TOKEN')
    
    print(f"POSTMARK_SERVER_TOKEN: {'Set' if server_token else 'Not set'}")
    if server_token:
        print(f"  Value: {server_token[:8]}...{server_token[-4:]} (length: {len(server_token)})")
    
    print(f"POSTMARK_API_TOKEN: {'Set' if api_token else 'Not set'}")
    if api_token:
        print(f"  Value: {api_token[:8]}...{api_token[-4:]} (length: {len(api_token)})")
    
    # The token being used
    token_to_use = server_token or api_token
    print(f"\nToken that will be used: {token_to_use[:8]}...{token_to_use[-4:]} (length: {len(token_to_use)})")
    
    # Check if it looks like a valid Postmark server token
    # Postmark server tokens are typically 36 characters and contain hyphens
    if token_to_use:
        if len(token_to_use) == 36 and token_to_use.count('-') == 4:
            print("✅ Token format looks like a valid Postmark server token")
        else:
            print("⚠️  Token format doesn't look like a typical Postmark server token")
            print("   Expected: 36 characters with 4 hyphens (UUID format)")
            print(f"   Got: {len(token_to_use)} characters with {token_to_use.count('-')} hyphens")
    
    # Test with the postmarker library directly
    try:
        from postmarker.core import PostmarkClient
        print("\n🧪 Testing direct Postmark client connection...")
        
        client = PostmarkClient(server_token=token_to_use)
        
        # Try to send a simple test email to validate the token
        try:
            # Create a test email (we won't actually send it, just validate the token)
            from postmarker.models.emails import EmailBatch
            
            # Just test the client initialization by accessing its properties
            if hasattr(client, '_server_token'):
                print("✅ Postmark client initialized with token")
            
            # Try a simple API call that validates the token
            # We'll try to get account info (this requires valid token)
            response = client.account.get()
            print("✅ Postmark token is valid and API is accessible!")
            print(f"Account Name: {response.get('Name', 'Unknown')}")
            
        except Exception as e:
            print(f"❌ Postmark API validation failed: {e}")
            if "Server token" in str(e) or "Unauthorized" in str(e):
                print("💡 The token appears to be invalid or expired")
                print("💡 Please check your Postmark account and regenerate the server token if needed")
            else:
                print("💡 There might be a network issue or API problem")
                
    except ImportError:
        print("❌ postmarker library not available")
    except Exception as e:
        print(f"❌ Error creating Postmark client: {e}")

if __name__ == "__main__":
    debug_postmark_token()
