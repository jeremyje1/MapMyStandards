#!/usr/bin/env node
const required = [
  'STRIPE_SECRET_KEY',
  'STRIPE_PRICE_DEPARTMENT_ANNUAL',
  'STRIPE_PRICE_CAMPUS_ANNUAL',
  'STRIPE_PRICE_SYSTEM_ANNUAL',
  'STRIPE_PRICE_PILOT'
];
const missing = required.filter(k => !process.env[k]);
if (missing.length) {
  console.warn('[stripe-env] Missing vars:', missing.join(', '));
  process.exitCode = 0;
} else {
  console.log('[stripe-env] All Stripe env vars present');
}
