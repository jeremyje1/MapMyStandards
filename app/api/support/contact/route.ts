import { NextResponse } from 'next/server';
import { sendEmail } from '@/lib/email/postmark';

interface ContactPayload {
  name?: string;
  email?: string;
  message?: string;
}

function sanitize(input: string | undefined): string {
  if (!input) return '';
  return input.replace(/[<>]/g, '');
}

export async function POST(req: Request) {
  try {
    const body: ContactPayload = await req.json();
    const name = sanitize(body.name);
    const email = sanitize(body.email);
    const message = sanitize(body.message);

    if (!email || !message) {
      return NextResponse.json({ error: 'Email and message required' }, { status: 400 });
    }

    // Auto receipt to user
    await sendEmail({
      to: email,
      subject: 'We received your message',
      html: `<p>Thanks ${name || 'there'}, we received your request and will get back shortly.</p>`,
      tag: 'support-auto',
    });

    // Internal notification
    const teamInbox = process.env.FROM_EMAIL;
    if (teamInbox) {
      await sendEmail({
        to: teamInbox,
        subject: 'New support request',
        html: `<p><b>From:</b> ${name || 'Unknown'} (${email})</p><p>${message}</p>`,
        tag: 'support-internal',
      });
    }

    return NextResponse.json({ ok: true });
  } catch (err: any) {
    console.error('Support contact error', err);
    return NextResponse.json({ error: 'Server error' }, { status: 500 });
  }
}

export const dynamic = 'force-dynamic';
