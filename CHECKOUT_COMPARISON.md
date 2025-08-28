# Checkout System Comparison

## Two Checkout Pages Available

### 1. `/trial-signup.html` - **Robust Multi-Step Checkout** (RECOMMENDED)

This is the more polished, production-ready checkout system with:

#### Features:
- ✅ **Multi-step form** with progress indicator
- ✅ **Professional UI** with smooth transitions
- ✅ **Proper payment collection** via Stripe Elements
- ✅ **Form validation** at each step
- ✅ **Password creation** during signup
- ✅ **Plan selection** with visual cards
- ✅ **Summary review** before submission
- ✅ **Newsletter opt-in** option
- ✅ **Pre-fill support** from URL parameters

#### Form Steps:
1. **Institution Details** - Name, email, institution, role, password
2. **Payment Information** - Card details via Stripe Elements
3. **Plan Selection** - Choose between monthly/yearly plans
4. **Confirmation** - Review all details before submitting

#### API Endpoint:
- Posts to: `/api/trial/signup`
- Creates user account AND Stripe subscription in one flow

#### URL Parameters Supported:
```
/trial-signup.html?plan=professional_monthly&email=user@example.com&institution_name=My%20College
```

### 2. `/checkout.html` - **Simple Single-Page Checkout** (BASIC)

The simpler checkout page that I just fixed with:

#### Features:
- ✅ **Single page form** (now with payment collection)
- ✅ **Stripe Elements** integration (just added)
- ✅ **Basic validation**
- ✅ **Plan details display**
- ❌ No password creation (separate flow needed)
- ❌ No multi-step progression
- ❌ Less polished UI

#### API Endpoint:
- Posts to: `/api/v1/billing/trial/signup`
- Requires payment method but no password

## Recommendation: Use `/trial-signup.html`

The `/trial-signup.html` page is the superior choice because:

1. **Better UX** - Multi-step form reduces cognitive load
2. **Complete signup** - Creates user account with password
3. **Professional appearance** - Polished UI with animations
4. **Better conversion** - Progress indicator keeps users engaged
5. **Form validation** - Step-by-step validation reduces errors

## Live Mode Configuration

### Current Status:
- **Mode**: LIVE (real charges will occur)
- **Publishable Key**: `pk_live_51Rxag5RMpSG47vNmE0GkLZ6x...`
- **Secret Key**: Needs to be added from Stripe Dashboard

### To Complete Live Setup:

1. **Get your live secret key**:
   - Go to: https://dashboard.stripe.com/apikeys
   - Copy your live secret key (starts with `sk_live_`)
   - Replace `sk_live_YOUR_LIVE_SECRET_KEY_HERE` in `.env`

2. **Verify prices are in live mode**:
   ```bash
   stripe prices list --live-mode | grep price_1RyV
   ```

3. **Test with a real card** (will charge!):
   - Navigate to: `/trial-signup.html?plan=college_monthly`
   - Complete the multi-step form
   - Use a real credit card
   - Verify in Stripe Dashboard (live mode)

## Quick Start URLs

### For Testing (Recommended Page):
```
# College Monthly Plan ($297/mo)
https://yourdomain.com/trial-signup.html?plan=college_monthly

# College Yearly Plan ($2,970/yr)
https://yourdomain.com/trial-signup.html?plan=college_yearly

# Multi-Campus Monthly ($897/mo)
https://yourdomain.com/trial-signup.html?plan=multicampus_monthly

# Multi-Campus Yearly ($8,073/yr)
https://yourdomain.com/trial-signup.html?plan=multicampus_yearly
```

### Plan Mappings:
The system accepts multiple plan name formats:
- `professional_monthly` → College Monthly ($297)
- `professional_yearly` → College Yearly ($2,970)
- `college_monthly` → College Monthly ($297)
- `college_yearly` → College Yearly ($2,970)
- `multicampus_monthly` → Multi-Campus Monthly ($897)
- `multicampus_yearly` → Multi-Campus Yearly ($8,073)

## API Endpoint Differences

### `/api/trial/signup` (trial-signup.html)
- Creates full user account
- Requires password
- Sends welcome email
- More comprehensive user data

### `/api/v1/billing/trial/signup` (checkout.html)
- Creates Stripe subscription only
- No password required
- Minimal user data
- Returns API key

## Migration Path

To fully switch to the robust system:

1. **Update marketing links** to point to `/trial-signup.html`
2. **Add redirects** from `/checkout.html` to `/trial-signup.html`
3. **Monitor conversion rates** to ensure improvement
4. **Eventually deprecate** the simple checkout page

## Security Notes

⚠️ **LIVE MODE ACTIVE** - Real charges will occur!
- All transactions are real
- Refunds must be processed manually
- Test carefully before going to production
- Consider using staging environment first