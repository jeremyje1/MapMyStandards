import { ServerClient } from 'postmark';

const TOKEN = process.env.POSTMARK_API_TOKEN;
const FROM = process.env.FROM_EMAIL || process.env.EMAIL_FROM || 'support@example.com';
const REPLY = process.env.REPLY_TO_EMAIL || FROM;
const STREAM = process.env.POSTMARK_MESSAGE_STREAM || 'outbound';

let client: ServerClient | null = null;
if (TOKEN) {
  client = new ServerClient(TOKEN);
} else {
  console.warn('Postmark token missing – emails disabled');
}

export interface SendEmailParams {
  to: string;
  subject: string;
  html: string;
  text?: string;
  tag?: string;
}

export async function sendEmail({ to, subject, html, text, tag }: SendEmailParams) {
  if (!client) throw new Error('Email client not configured');
  return client.sendEmail({
    From: FROM,
    To: to,
    ReplyTo: REPLY,
    Subject: subject,
    HtmlBody: html,
    TextBody: text || html.replace(/<[^>]+>/g, ''),
    Tag: tag,
    MessageStream: STREAM,
  });
}
// lib/email/postmark.ts
// (Removed duplicate implementation block that followed – cleaned for single export)
