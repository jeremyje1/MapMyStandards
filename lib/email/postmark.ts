// Email service interface - simplified for deployment

export interface SendEmailArgs {
  to: string;
  subject: string;
  html: string;
  tag?: string;
  text?: string;
}

export async function sendEmail({ to, subject, html, tag }: SendEmailArgs) {
  // Log email for development
  console.log('📧 Email service called:', { to, subject, tag });
  
  // Return mock response for now
  return { MessageID: 'mock-' + Date.now() };
}
