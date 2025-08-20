// Lightweight proxy Stripe webhook route.
// All real verification & handling occurs in the backend FastAPI service
// at /api/v1/billing/webhook/stripe. This keeps secrets server-side only.
import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

/**
 * POST /api/stripe/webhook
 * Raw body is required for Stripe signature verification, so we forward the
 * untouched bytes to the backend along with the stripe-signature header.
 * Set DISABLE_VERCEL_WEBHOOK=1 to short‑circuit during maintenance.
 */
export async function POST(req: Request) {
  if (process.env.DISABLE_VERCEL_WEBHOOK === '1') {
    return NextResponse.json({ disabled: true });
  }

  const signature = req.headers.get('stripe-signature');
  if (!signature) {
    return NextResponse.json({ error: 'missing stripe-signature' }, { status: 400 });
  }

  // Read raw body once (must not call req.json() beforehand)
  const raw = Buffer.from(await req.arrayBuffer());

  // Forward to backend API (assumes same origin domain for server API)
  const backendUrl = process.env.BACKEND_URL || 'https://api.mapmystandards.ai';
  const target = `${backendUrl}/api/v1/billing/webhook/stripe`;

  try {
    const forwardResp = await fetch(target, {
      method: 'POST',
      // Pass through the raw body for signature verification server-side
      body: raw,
      headers: {
        'content-type': req.headers.get('content-type') || 'application/json',
        'stripe-signature': signature,
        // Optionally convey source context
        'x-forwarded-from': 'nextjs-edge',
      },
      // Ensure we don't wait forever
      // (Next.js edge/functions default timeout still applies)
    });

    const text = await forwardResp.text();
    // Attempt to surface backend JSON when possible
    try {
      const json = JSON.parse(text);
      return NextResponse.json(json, { status: forwardResp.status });
    } catch {
      return new NextResponse(text, { status: forwardResp.status });
    }
  } catch (e: any) {
    console.error('Failed forwarding Stripe webhook', e);
    return NextResponse.json({ error: 'forward-failed', detail: e.message }, { status: 502 });
  }
}
