import postmark from 'postmark';

// Wrapper around the Postmark client providing a consistent way to send
// transactional emails. Configuration entirely via environment variables.

const token = process.env.POSTMARK_API_TOKEN!; // Must be present
const stream = process.env.POSTMARK_MESSAGE_STREAM || 'outbound';
const from = process.env.FROM_EMAIL!; // Required
const replyTo = process.env.REPLY_TO_EMAIL || from;

const client = new postmark.ServerClient(token);

export interface SendEmailArgs {
  to: string;
  subject: string;
  html: string;
  tag?: string;
}

export async function sendEmail({ to, subject, html, tag }: SendEmailArgs) {
  return client.sendEmail({
    From: from,
    To: to,
    Subject: subject,
    HtmlBody: html,
    MessageStream: stream,
    Tag: tag,
    ReplyTo: replyTo,
  });
}
