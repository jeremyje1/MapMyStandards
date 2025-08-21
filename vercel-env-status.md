# Vercel Environment Variables Status

## Stripe Price IDs (Production & Preview)

### Default Prices (Professional Tier)
- `STRIPE_MONTHLY_PRICE_ID`: price_1RyVQ4K8PKpLCKDZON0IMe3F ($299/month)
- `STRIPE_ANNUAL_PRICE_ID`: Already set (Professional annual - $2,999/year)

### Tier-Specific Prices
All successfully added to Production and Preview environments:

#### Starter Tier
- `STRIPE_PRICE_ID_STARTER_MONTHLY`: price_1RyVPPK8PKpLCKDZFbwkFdqq ($99/month)
- `STRIPE_PRICE_ID_STARTER_ANNUAL`: price_1RyVPgK8PKpLCKDZe8nu4ium ($999/year)

#### Professional Tier
- `STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY`: price_1RyVQ4K8PKpLCKDZON0IMe3F ($299/month)
- `STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL`: price_1RyVQFK8PKpLCKDZ7KxYraxk ($2,999/year)

#### Institution Tier
- `STRIPE_PRICE_ID_INSTITUTION_MONTHLY`: price_1RyVQgK8PKpLCKDZTais3Tyx ($599/month)
- `STRIPE_PRICE_ID_INSTITUTION_ANNUAL`: price_1RyVQrK8PKpLCKDZUshqaOvZ ($5,999/year)

## Other Key Variables Set
- `STRIPE_SECRET_KEY`: Set for Production
- `STRIPE_PUBLISHABLE_KEY`: Set for Production & Preview
- `STRIPE_WEBHOOK_SECRET`: Set for Preview

## Notes
- Professional tier is set as the default for backwards compatibility
- All price IDs are for live Stripe products
- Development environment may still have old test price IDs
