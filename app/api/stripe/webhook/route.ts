import { NextResponse } from 'next/server';
import Stripe from 'stripe';
import { headers } from 'next/headers';
import { sendEmail } from '@/lib/email/postmark';
import { tierFromPriceId } from '@/lib/tiers';
import { persistUserTier } from '@/lib/tierPersistence';
import { prisma } from '@/lib/prisma';
import { Prisma } from '@prisma/client';

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
            await persistUserTier({ email: customerEmail, tier: purchasedTier, source: session.id || 'unknown_session', stripeCustomerId: (session.customer as string) || null });
          } catch (e) {
            console.warn('Failed to persist user tier', e);
          }

          // Provision Org + Membership (idempotent)
            try {
              await prisma.$transaction(async (tx: Prisma.TransactionClient) => {
                const user = await tx.user.upsert({ where: { email: customerEmail }, update: {}, create: { email: customerEmail } });
                const existingMembership = await tx.membership.findFirst({ where: { userId: user.id } });
                if (!existingMembership) {
                  const orgName = session.customer_details?.name || customerEmail.split('@')[0];
                  const org = await tx.org.create({ data: { name: orgName } });
                  await tx.membership.create({ data: { orgId: org.id, userId: user.id, role: 'OWNER' } });
                }
              });
            } catch (e) {
              console.warn('Org provisioning skipped/failed', e);
            }

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
      case 'customer.subscription.created':
      case 'customer.subscription.updated': {
        const sub = event.data.object as Stripe.Subscription;
        const stripeCustomerId = sub.customer as string;
        let email: string | null = null;
        try {
          const cust = await stripe.customers.retrieve(stripeCustomerId);
          if (!cust || (cust as any).deleted) {
            console.warn('Customer deleted or missing for subscription', stripeCustomerId);
          } else {
            email = (cust as Stripe.Customer).email || null;
          }
        } catch (e) {
          console.warn('Failed fetching customer for subscription', e);
        }
        const priceId = (sub.items.data[0]?.price?.id) || null;
        const tier = tierFromPriceId(priceId) || 'unknown';

        // Derive env key name holding this price (for analytics/debug)
        let priceEnvKey: string | null = null;
        for (const k of Object.keys(process.env)) {
          if (k.startsWith('STRIPE_PRICE_') && process.env[k] === priceId) { priceEnvKey = k; break; }
        }
        try {
          if (email) {
            await persistUserTier({
              email,
              tier,
              source: sub.id,
              stripeCustomerId,
              stripeSubscriptionId: sub.id,
              priceId,
              priceEnvKey,
              status: sub.status,
              currentPeriodEnd: sub.current_period_end ? new Date(sub.current_period_end * 1000) : null,
            });
          }
        } catch (e) {
          console.warn('Failed to persist subscription update', e);
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
