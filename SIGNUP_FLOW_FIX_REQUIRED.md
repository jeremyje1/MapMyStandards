# Signup Flow Fix Required

## Current Issue
The Houston College (and likely all new users) signup is failing because of a disconnect between the Stripe Checkout flow and user account creation.

## Current Flow (BROKEN)
1. User fills signup form → Redirected to Stripe Checkout
2. User completes payment in Stripe Checkout
3. User redirected to trial-success.html
4. trial-success.html tries to create user account with `payment_method_id: 'from_checkout_session'`
5. **Backend rejects this because it's not a valid Stripe payment method ID**
6. User account is never created in database

## Root Cause
The trial signup endpoint expects a real Stripe payment method ID but the frontend is sending a placeholder string.

## Solutions

### Solution 1: Fix Frontend Integration (Recommended)
Modify trial-success.html to properly handle the Stripe Checkout session:

```javascript
// In trial-success.html, after getting session data:
const sessionResponse = await fetch(`/api/checkout/session/${sessionId}`);
const sessionData = await sessionResponse.json();

// The backend should return the payment_method from the checkout session
const accountResponse = await fetch('/api/trial/signup', {
    method: 'POST',
    body: JSON.stringify({
        ...signupData,
        payment_method_id: sessionData.payment_method, // Use actual payment method
        stripe_customer_id: sessionData.customer,
        stripe_subscription_id: sessionData.subscription
    })
});
```

### Solution 2: Modify Backend to Handle Post-Checkout Signups
Create a separate endpoint that creates users after checkout without requiring payment_method_id:

```python
@router.post("/trial/create-after-checkout")
async def create_user_after_checkout(
    request: CreateAfterCheckoutRequest,
    db: AsyncSession = Depends(get_db)
):
    # Since payment is already collected via Checkout,
    # we can create the user with just customer/subscription IDs
    # No need for payment_method_id
```

### Solution 3: Use Stripe Webhooks (Best Practice)
Handle user creation via Stripe webhook when 'checkout.session.completed' event is received:
1. Stripe sends webhook when checkout completes
2. Webhook handler creates user in database
3. Frontend just needs to poll/wait for user creation

## Immediate Fix Needed
For Houston College and other signups to work:

1. **Check if Stripe webhook is configured** - This might already be handling user creation
2. **Verify the checkout session endpoint** exists and returns proper data
3. **Update trial-success.html** to use proper payment method ID or use a different endpoint

## Testing
To verify the fix works:
1. Complete a full signup flow with test card 4242 4242 4242 4242
2. Check Railway logs: `railway logs | grep -i "trial"`
3. Verify user in database: `railway run python3 check_railway_users.py`

## Why Authentication Works But Signup Doesn't
The authentication fix we implemented works because existing users can login. The issue is that NEW users can't be created due to the Stripe integration problem.