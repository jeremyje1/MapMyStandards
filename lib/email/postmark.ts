// Email service interface - simplified for deployment

export interface SendEmailArgs {
  to: string;
  subject: string;
  html: string;
  tag?: string;
  text?: string;
}

export async function sendEmail({ to, subject, html, tag, text }: SendEmailArgs) {
  // Log email for development
  console.log('📧 Email service called:', { to, subject, tag });
  
  // Return mock response for now
  return { MessageID: 'mock-' + Date.now() };
}

export async function sendMagicLinkEmail(email: string, url: string) {
  const html = `
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h2>Sign in to MapMyStandards</h2>
      <p>Click the link below to sign in to your account:</p>
      <a href="${url}" style="display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 5px;">Sign In</a>
      <p style="margin-top: 20px; color: #666;">If you didn't request this email, you can safely ignore it.</p>
      <p style="color: #666;">This link will expire in 24 hours.</p>
    </div>
  `;

  const text = `Sign in to MapMyStandards\n\nClick this link to sign in: ${url}\n\nIf you didn't request this email, you can safely ignore it.\n\nThis link will expire in 24 hours.`;

  return sendEmail({
    to: email,
    subject: 'Sign in to MapMyStandards',
    html,
    text,
  });
}
