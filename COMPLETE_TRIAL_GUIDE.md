# Complete 21-Day Free Trial Setup Guide

## 🎯 **How It Works**

### Customer Journey:
1. **Sign Up** → Enters email + credit card info
2. **Day 0-21** → Full access to A³E, no charges
3. **Day 22** → Automatic billing begins at chosen plan rate
4. **Ongoing** → Regular monthly/yearly billing

### Why This Works:
✅ **Lower friction** - "free trial" vs "pay now"
✅ **Higher conversion** - customers experience full value
✅ **Automatic billing** - no manual upgrade needed
✅ **Credit card required** - reduces fake signups

## 💳 **Stripe Dashboard Setup**

### Step 1: Create Products
```
Product: A³E College Plan
├── Price 1: $297/month (21-day trial)
├── Price 2: $2,970/year (21-day trial)

Product: A³E Multi-Campus Plan  
├── Price 1: $897/month (21-day trial)
├── Price 2: $8,073/year (21-day trial)
```

### Step 2: Enable Trial Settings
For each price:
- ✅ Trial Period: 21 days
- ✅ Collect payment method: Yes
- ✅ Prorate charges: Yes

### Step 3: Set Up Webhooks
Required endpoints:
```
customer.subscription.created
customer.subscription.trial_will_end  
invoice.payment_succeeded
invoice.payment_failed
```

## 🛠️ **Implementation Details**

### Frontend (Checkout Form):
```javascript
// Customer enters:
// - Email
// - Name  
// - Credit card details
// - Selected plan

// Stripe creates:
// - Payment method
// - Customer
// - Subscription with 21-day trial
```

### Backend Flow:
```python
# 1. Create customer with payment method
customer = stripe.Customer.create(
    email=email,
    payment_method=payment_method_id
)

# 2. Create subscription with trial
subscription = stripe.Subscription.create(
    customer=customer.id,
    items=[{'price': price_id}],
    trial_period_days=21,
    payment_behavior='default_incomplete'
)

# 3. Grant immediate API access
api_key = generate_api_key()
store_trial_user(customer.id, api_key, trial_end)
```

### Database Schema:
```sql
CREATE TABLE trial_users (
    id UUID PRIMARY KEY,
    customer_id VARCHAR UNIQUE,
    subscription_id VARCHAR UNIQUE,
    email VARCHAR,
    api_key VARCHAR UNIQUE,
    plan VARCHAR,
    trial_start TIMESTAMP,
    trial_end TIMESTAMP,
    status VARCHAR DEFAULT 'trialing',
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 📧 **Email Automation**

### Trial Lifecycle Emails:
1. **Day 0:** "Welcome! Your 21-day trial has started"
2. **Day 7:** "How to get the most from your A³E trial"
3. **Day 14:** "1 week left in your trial" 
4. **Day 18:** "3 days left - questions about A³E?"
5. **Day 21:** "Your trial ends today - billing starts tomorrow"
6. **Day 22:** "Welcome to A³E! Your subscription is active"

### Email Templates:
```html
<!-- Day 0: Welcome -->
Subject: Your A³E trial has started! 🎉

Hi [Name],

Welcome to A³E! Your 21-day free trial is now active.

Your API Key: [API_KEY]
Trial Ends: [TRIAL_END_DATE]
Plan: [PLAN_NAME]

Getting Started:
1. Visit docs.mapmystandards.ai
2. Upload your first document
3. See instant standards mapping

Questions? Reply to this email.

Best,
The A³E Team
```

## 🔄 **Trial Management**

### Check Trial Status:
```python
def get_trial_status(customer_id):
    subscription = stripe.Subscription.retrieve(subscription_id)
    
    if subscription.status == 'trialing':
        days_left = (subscription.trial_end - time.time()) / 86400
        return {
            'status': 'trialing',
            'days_left': int(days_left),
            'trial_end': subscription.trial_end
        }
    elif subscription.status == 'active':
        return {'status': 'active', 'billing_started': True}
```

### Handle Trial End:
```python
# Webhook: customer.subscription.trial_will_end
def handle_trial_ending(subscription_id):
    # Send final reminder email
    send_trial_ending_email(subscription.customer)
    
    # Update user status  
    update_user_status(subscription.customer, 'trial_ending')
```

### Cancel During Trial:
```python
# Customer can cancel anytime during trial
def cancel_trial(subscription_id):
    stripe.Subscription.modify(
        subscription_id,
        cancel_at_period_end=True
    )
    # User keeps access until trial end
    # No billing occurs
```

## 📊 **Trial Analytics**

### Key Metrics to Track:
- **Trial signup rate** (visitors → trials)
- **Trial-to-paid conversion** (trials → paying customers)  
- **Trial engagement** (API usage during trial)
- **Cancellation reasons** (why trials don't convert)

### Dashboard Queries:
```sql
-- Trial conversion rate
SELECT 
    COUNT(*) as total_trials,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as conversions,
    (COUNT(CASE WHEN status = 'active' THEN 1 END) * 100.0 / COUNT(*)) as conversion_rate
FROM trial_users 
WHERE trial_start >= '2025-01-01';

-- Trial engagement
SELECT 
    customer_id,
    COUNT(*) as api_calls_during_trial
FROM api_usage_logs 
WHERE created_at BETWEEN trial_start AND trial_end
GROUP BY customer_id;
```

## 🎯 **Optimization Tips**

### Increase Trial Conversion:
1. **Require payment method** - 60%+ higher conversion
2. **Onboarding sequence** - guide users to "aha moment"
3. **Progress tracking** - show trial days remaining
4. **Usage-based emails** - target low-engagement users
5. **Exit surveys** - understand why trials don't convert

### Reduce Trial Abuse:
1. **Email verification** required
2. **Credit card verification** (small auth charge)
3. **One trial per email** domain
4. **Usage limits** during trial (if needed)

### Conversion Tactics:
```html
<!-- In-app trial countdown -->
<div class="trial-countdown">
    ⏰ 7 days left in your trial
    <a href="/billing">Upgrade now to continue</a>
</div>

<!-- Trial usage progress -->
<div class="trial-progress">
    📊 You've analyzed 23 documents during your trial
    <span>Upgrade to analyze unlimited documents</span>
</div>
```

This setup provides a smooth trial experience that maximizes conversions while minimizing friction and abuse!
