# Stripe Free Trial Setup Guide

## Create These Exact Products in Stripe Dashboard:

### Product 1: A³E College Plan
```
Product Name: A³E College Plan
Description: Complete accreditation automation for colleges and their accreditation teams

Price 1 (Monthly):
- Amount: $297.00 USD
- Billing Period: Monthly  
- Trial Period: 21 days
- Price ID: price_college_monthly

Price 2 (Yearly):
- Amount: $2,970.00 USD
- Billing Period: Yearly
- Trial Period: 21 days  
- Price ID: price_college_yearly
```

### Product 2: A³E Multi-Campus Plan
```
Product Name: A³E Multi-Campus Plan
Description: Enterprise accreditation management for multi-campus colleges

Price 1 (Monthly):
- Amount: $897.00 USD
- Billing Period: Monthly
- Trial Period: 21 days
- Price ID: price_multicampus_monthly

Price 2 (Yearly):
- Amount: $8,073.00 USD  
- Billing Period: Yearly
- Trial Period: 21 days
- Price ID: price_multicampus_yearly
```

## How the Trial Works:

1. **Day 0:** Customer signs up with credit card
2. **Days 1-21:** Free access to full features
3. **Day 22:** Automatic billing begins
4. **Ongoing:** Regular monthly/yearly billing

## Important Stripe Settings:

### Subscription Settings:
- ✅ Collect payment method during trial: YES
- ✅ Prorate charges: YES  
- ✅ Cancel at period end: NO
- ✅ Trial period days: 21

### Webhook Events to Handle:
- customer.subscription.created (trial started)
- customer.subscription.trial_will_end (7 days before)
- invoice.payment_succeeded (first charge)
- invoice.payment_failed (handle failures)

## Code Implementation:

### Frontend (Checkout):
```javascript
// Create subscription with trial
const { error } = await stripe.redirectToCheckout({
  lineItems: [{
    price: 'price_college_monthly', // Your price ID
    quantity: 1,
  }],
  mode: 'subscription',
  successUrl: 'https://yourdomain.com/success',
  cancelUrl: 'https://yourdomain.com/cancel',
  allowPromotionCodes: true, // For discount codes
});
```

### Backend (Create Subscription):
```python
import stripe

stripe.api_key = "sk_test_..."

# Create subscription with trial
subscription = stripe.Subscription.create(
    customer=customer_id,
    items=[{
        'price': 'price_college_monthly',
    }],
    trial_period_days=21,
    payment_behavior='default_incomplete',
    expand=['latest_invoice.payment_intent'],
)
```

## Customer Experience:

1. **Signup:** "Start your 21-day free trial"
2. **Email Day 1:** "Welcome! Your trial has started"  
3. **Email Day 14:** "7 days left in your trial"
4. **Email Day 20:** "Your trial ends tomorrow"
5. **Email Day 22:** "Welcome to A³E! Your subscription is active"

## Trial Management:

### Extend Trial (if needed):
```python
# Extend trial by 7 days
stripe.Subscription.modify(
    subscription_id,
    trial_end=int(time.time()) + (7 * 24 * 60 * 60)  # 7 days from now
)
```

### Cancel During Trial:
```python
# Cancel subscription (ends at trial end)
stripe.Subscription.modify(
    subscription_id,
    cancel_at_period_end=True
)
```

## Key Benefits:

✅ **No upfront payment** - removes signup friction
✅ **Full feature access** - customers see complete value
✅ **Automatic conversion** - no manual upgrade needed
✅ **Credit card required** - reduces fake signups
✅ **Easy cancellation** - builds trust

## Trial Optimization Tips:

1. **Collect payment method upfront** - much higher conversion
2. **Send trial progress emails** - keep users engaged
3. **Show trial countdown** - create urgency
4. **Offer onboarding** - ensure users see value
5. **Track trial usage** - identify engaged users
