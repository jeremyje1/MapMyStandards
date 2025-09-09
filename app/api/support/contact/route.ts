import { NextRequest, NextResponse } from 'next/server';

interface ContactFormData {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export async function POST(request: NextRequest) {
  try {
    const body: ContactFormData = await request.json();
    const { name, email, subject, message } = body;

    // Validate required fields
    if (!name || !email || !subject || !message) {
      return NextResponse.json(
        { error: 'All fields are required' },
        { status: 400 }
      );
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json(
        { error: 'Invalid email address' },
        { status: 400 }
      );
    }

    // Send email using Postmark
    if (process.env.POSTMARK_API_KEY) {
      const postmarkResponse = await fetch('https://api.postmarkapp.com/email', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-Postmark-Server-Token': process.env.POSTMARK_API_KEY,
        },
        body: JSON.stringify({
          From: process.env.POSTMARK_FROM_EMAIL || 'support@mapmystandards.ai',
          To: process.env.SUPPORT_EMAIL || 'support@mapmystandards.ai',
          ReplyTo: email,
          Subject: `[Contact Form] ${subject}`,
          TextBody: `
Name: ${name}
Email: ${email}
Subject: ${subject}

Message:
${message}
          `,
          HtmlBody: `
            <h3>New Contact Form Submission</h3>
            <p><strong>Name:</strong> ${name}</p>
            <p><strong>Email:</strong> ${email}</p>
            <p><strong>Subject:</strong> ${subject}</p>
            <h4>Message:</h4>
            <p>${message.replace(/\n/g, '<br>')}</p>
          `,
          MessageStream: 'outbound',
        }),
      });

      if (!postmarkResponse.ok) {
        const error = await postmarkResponse.json();
        console.error('Postmark error:', error);
        throw new Error('Failed to send email');
      }

      // Send confirmation email to user
      await fetch('https://api.postmarkapp.com/email', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'X-Postmark-Server-Token': process.env.POSTMARK_API_KEY,
        },
        body: JSON.stringify({
          From: process.env.POSTMARK_FROM_EMAIL || 'support@mapmystandards.ai',
          To: email,
          Subject: 'We received your message - MapMyStandards',
          TextBody: `
Hi ${name},

Thank you for contacting MapMyStandards. We've received your message and will get back to you within 24-48 hours.

Your message:
${message}

Best regards,
The MapMyStandards Team
          `,
          MessageStream: 'outbound',
        }),
      });
    } else {
      // Fallback: Log the contact form submission
      console.log('Contact form submission (no email service configured):', {
        name,
        email,
        subject,
        message,
        timestamp: new Date().toISOString(),
      });
    }

    return NextResponse.json({
      success: true,
      message: 'Thank you for your message. We will get back to you soon!',
    });
  } catch (error) {
    console.error('Contact form error:', error);
    return NextResponse.json(
      { error: 'Failed to process your request. Please try again later.' },
      { status: 500 }
    );
  }
}