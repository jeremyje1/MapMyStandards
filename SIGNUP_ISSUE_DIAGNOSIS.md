# Signup Issue Diagnosis - Houston College

## Issue
Houston College signup is not creating accounts in the Railway PostgreSQL database.

## Root Cause Identified
The signup is failing at the Stripe payment validation step. The error message shows:
```
Payment setup failed: Request req_1LYxTmiMWT6NVl: You cannot use the test ID 'pm_card_visa' in livemode. 
If you are testing your integration, please use your testmode API keys instead.
```

## Why This Happens
1. The production environment is using **live Stripe API keys**
2. The trial signup endpoint (`/api/trial/signup`) requires a valid payment method ID
3. When a test payment method is used (or no valid payment method is provided), Stripe rejects the request
4. The user creation fails before it reaches the database insertion step

## The Signup Flow
1. User submits signup form → 
2. API validates data → 
3. **Stripe creates trial subscription (FAILS HERE)** → 
4. User record created in database → 
5. Welcome email sent

Since step 3 fails, steps 4 and 5 never execute.

## Solution Options

### Option 1: Use Valid Payment Method (Production)
- During signup through the web interface, ensure users complete the Stripe Checkout flow
- Stripe Checkout will collect a valid payment method and return a `payment_method_id`
- This ID should be included in the signup API request

### Option 2: Trial Without Payment (Development)
- Modify the trial signup to allow trials without immediate payment collection
- Collect payment information later (before trial expires)
- This requires backend code changes

### Option 3: Fix the Frontend Flow
The issue might be that after Stripe Checkout, the payment method ID is not being properly passed to the signup endpoint.

## Immediate Actions Needed

1. **Check the frontend signup flow**: Verify that after Stripe Checkout completion, the payment_method_id is being captured and sent to the API

2. **Review recent signups**: Check if ANY users have been created successfully in production

3. **Verify Stripe webhook**: Ensure Stripe webhooks are properly configured to handle checkout.session.completed events

## Testing a Proper Signup
To test if the signup works with proper payment:
1. Go through the actual signup flow on the website
2. Complete Stripe Checkout with a real test card (4242 4242 4242 4242)
3. Check if the user is created after successful payment

## Database Verification Commands
```bash
# Check all users in Railway database
railway run python3 check_railway_users.py

# Check Railway logs for signup attempts
railway logs

# Search for Houston-specific signups in logs
railway logs | grep -i houston
```