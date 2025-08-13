import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { headers } from 'next/headers';
import { sendEmail } from '@/lib/email/postmark';
import { tierFromPriceId } from '@/lib/tiers';
import { persistUserTier } from '@/lib/tierPersistence';

// Expect these in env
const stripeSecret = process.env.STRIPE_SECRET_KEY;
const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET; // signing secret

const stripe = stripeSecret ? new Stripe(stripeSecret, { apiVersion: '2024-06-20' }) : null;

async function parseRawBody(req: Request): Promise<Buffer> {
  const arrayBuffer = await req.arrayBuffer();
  return Buffer.from(arrayBuffer);
}

export async function POST(req: Request) {
  if (!stripe) {
    console.error('Stripe not configured. Missing STRIPE_SECRET_KEY');
    return NextResponse.json({ error: 'Stripe not configured' }, { status: 500 });
  }
  if (!webhookSecret) {
    console.error('Missing STRIPE_WEBHOOK_SECRET');
    return NextResponse.json({ error: 'Webhook secret missing' }, { status: 500 });
  }

  const sig = headers().get('stripe-signature');
  if (!sig) {
    return NextResponse.json({ error: 'Missing stripe-signature header' }, { status: 400 });
  }

  let event: Stripe.Event;
  let rawBody: Buffer;
  try {
    rawBody = await parseRawBody(req);
    event = stripe.webhooks.constructEvent(rawBody, sig, webhookSecret);
  } catch (err: any) {
    console.error('Stripe webhook signature verification failed', err.message);
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session;
        const customerEmail = session.customer_details?.email;
        let purchasedTier = (session.metadata?.tier as string | undefined) || null;
        if (!purchasedTier) {
          try {
            if (session.id) {
              const lineItems = await stripe.checkout.sessions.listLineItems(session.id, { limit: 5 });
              const priceId = lineItems.data[0]?.price?.id;
              purchasedTier = tierFromPriceId(priceId);
            }
          } catch (e) {
            console.warn('Failed to resolve tier from line items', e);
          }
        }
        if (!purchasedTier) purchasedTier = 'unknown';

        // Persist tier (stub logs until real DB wired)
        if (customerEmail) {
          try {
            await persistUserTier({ email: customerEmail, tier: purchasedTier, source: session.id || 'unknown_session' });
          } catch (e) {
            console.warn('Failed to persist user tier', e);
          }
        }

        if (customerEmail) {
          const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
          const onboardingUrl = `${appUrl}/assessment/onboarding`;
          await sendEmail({
            to: customerEmail,
            subject: 'Welcome to NorthPath — Your next steps',
            html: `
              <h2>You're all set</h2>
              <p>Your subscribed tier: <strong>${purchasedTier}</strong>.</p>
              <p>Start here to complete your onboarding checklist and launch your assessment:</p>
              <p><a href="${onboardingUrl}" style="display:inline-block;padding:10px 16px;border-radius:6px;background:#2563eb;color:#fff;text-decoration:none;">Open onboarding</a></p>
              <hr/>
              <p>Need help? Reply to this email and we'll jump in.</p>
            `,
            tag: 'onboarding',
          });
        }
        break; }
      default: break;
    }

    return NextResponse.json({ received: true });
  } catch (err: any) {
    console.error('Webhook handler error', err);
    return NextResponse.json({ error: 'Webhook processing failed' }, { status: 500 });
  }
}

export const dynamic = 'force-dynamic'; // ensure edge caching not applied to webhook
