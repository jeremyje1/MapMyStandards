import { NextResponse } from 'next/server';
import { sendEmail } from '@/lib/email/postmark';

export async function POST(req: Request) {
  try {
    const { to } = await req.json();
    if (!to) return NextResponse.json({ error: 'Missing to' }, { status: 400 });

    const result = await sendEmail({
      to,
      subject: 'Test Email from Dev Endpoint',
      html: '<p>This is a test email sent via Postmark helper.</p>',
      tag: 'dev-test'
    });

    return NextResponse.json({ ok: true, result });
  } catch (e: any) {
    return NextResponse.json({ ok: false, error: e.message }, { status: 500 });
  }
}

export const dynamic = 'force-dynamic';
