import { NextResponse } from 'next/server';
import Stripe from 'stripe';

const stripeSecret = process.env.STRIPE_SECRET_KEY;
const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
const stripe = stripeSecret ? new Stripe(stripeSecret, { apiVersion: '2024-06-20' }) : null;

// Single pricing tier - $199/month
const MONTHLY_PRICE_ID = 'price_1S2yYNK8PKpLCKDZ6zgFu2ay';

export async function POST(req: Request) {
  if (!stripe) {
    return NextResponse.json({ error: 'Stripe not configured' }, { status: 500 });
  }
  try {
    const successUrl = `${appUrl}/success?session_id={CHECKOUT_SESSION_ID}`;
    const cancelUrl = `${appUrl}/pricing?canceled=1`;
    
    // Create checkout session for $199/month subscription
    const params: Stripe.Checkout.SessionCreateParams = {
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [{ 
        price: MONTHLY_PRICE_ID, 
        quantity: 1 
      }],
      success_url: successUrl,
      cancel_url: cancelUrl,
      metadata: { 
        plan: 'monthly',
        price: '199'
      },
      allow_promotion_codes: true,
    };
    
    const session = await stripe.checkout.sessions.create(params);
    return NextResponse.json({ url: session.url });
  } catch (e) {
    console.error('Checkout create error', e);
    return NextResponse.json({ error: 'Checkout session error' }, { status: 500 });
  }
}

export const dynamic = 'force-dynamic';
