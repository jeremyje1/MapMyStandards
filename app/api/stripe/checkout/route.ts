import { NextResponse } from 'next/server';
import Stripe from 'stripe';

const stripeSecret = process.env.STRIPE_SECRET_KEY;
const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
const stripe = stripeSecret ? new Stripe(stripeSecret, { apiVersion: '2024-06-20' }) : null;

function resolvePriceId(priceEnvKey: string | null): { priceId: string | null; mode: 'subscription' | 'payment'; } {
  if (!priceEnvKey) return { priceId: null, mode: 'subscription' };
  const mode: 'subscription' | 'payment' = priceEnvKey === 'STRIPE_PRICE_PILOT' ? 'payment' : 'subscription';
  const priceId = (process.env as any)[priceEnvKey];
  return { priceId: priceId || null, mode };
}

export async function POST(req: Request) {
  if (!stripe) {
    return NextResponse.json({ error: 'Stripe not configured' }, { status: 500 });
  }
  try {
    const body = await req.json().catch(() => ({}));
    const priceEnvKey: string | null = body.priceEnvKey || null;
    if (!priceEnvKey) {
      return NextResponse.json({ error: 'Missing priceEnvKey' }, { status: 400 });
    }
    const allowed = new Set([
      'STRIPE_PRICE_DEPARTMENT_ANNUAL',
      'STRIPE_PRICE_CAMPUS_ANNUAL',
      'STRIPE_PRICE_SYSTEM_ANNUAL',
      'STRIPE_PRICE_PILOT',
    ]);
    if (!allowed.has(priceEnvKey)) {
      return NextResponse.json({ error: 'Unsupported price key' }, { status: 400 });
    }
    const { priceId, mode } = resolvePriceId(priceEnvKey);
    if (!priceId) {
      return NextResponse.json({ error: 'Price ID not set' }, { status: 500 });
    }
    const successUrl = `${appUrl}/success?session_id={CHECKOUT_SESSION_ID}`;
    const cancelUrl = `${appUrl}/pricing?canceled=1`;
    const params: Stripe.Checkout.SessionCreateParams = mode === 'subscription' ? {
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: successUrl,
      cancel_url: cancelUrl,
      metadata: { priceEnvKey },
      allow_promotion_codes: true,
    } : {
      mode: 'payment',
      payment_method_types: ['card'],
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: successUrl,
      cancel_url: cancelUrl,
      metadata: { priceEnvKey },
      allow_promotion_codes: false,
    };
    const session = await stripe.checkout.sessions.create(params);
    return NextResponse.json({ url: session.url });
  } catch (e) {
    console.error('Checkout create error', e);
    return NextResponse.json({ error: 'Checkout session error' }, { status: 500 });
  }
}

export const dynamic = 'force-dynamic';
