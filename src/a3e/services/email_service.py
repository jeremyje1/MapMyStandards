"""Email service for MapMyStandards.ai.

Provides unified email sending via SendGrid (preferred) with SMTP fallback.
Includes helper methods for common transactional emails. Keeps implementation
simple (synchronous) since volume is low and sending is usually off the main
request path via background task.
"""

from __future__ import annotations

import os
import logging
import smtplib
from datetime import datetime
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# Optional SendGrid
try:  # pragma: no cover - optional dependency
    from sendgrid import SendGridAPIClient  # type: ignore
    from sendgrid.helpers.mail import (
        Mail, From, To, Subject, Content,
        Attachment, FileContent, FileName, FileType, Disposition
    )
    import base64  # type: ignore
    SENDGRID_AVAILABLE = True
except Exception:  # pragma: no cover - absence is acceptable
    SENDGRID_AVAILABLE = False
    base64 = None  # type: ignore
    logging.getLogger(__name__).warning("SendGrid not available - falling back to SMTP if configured")

# Optional Postmark
try:
    from postmarker.core import PostmarkClient
    POSTMARK_AVAILABLE = True
except Exception:
    POSTMARK_AVAILABLE = False
    logging.getLogger(__name__).info("Postmark not available")

from ..core.url_helpers import build_unsubscribe_link

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        # Postmark configuration (preferred)
        self.postmark_api_key = os.getenv('POSTMARK_API_TOKEN')
        self.use_postmark = POSTMARK_AVAILABLE and self.postmark_api_key
        
        # SendGrid configuration (fallback)
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.use_sendgrid = SENDGRID_AVAILABLE and self.sendgrid_api_key and not self.use_postmark
        
        # Common settings
        self.default_from = os.getenv('FROM_EMAIL', os.getenv('EMAIL_FROM', 'info@northpathstrategies.org'))
        self.default_from_name = os.getenv('EMAIL_FROM_NAME', 'MapMyStandards Support')
        self.admin_email = os.getenv('ADMIN_EMAIL', 'info@northpathstrategies.org')
        
        # SMTP fallback configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'mx1.titan.email')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.use_tls = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
        self.smtp_username = os.getenv('SMTP_USERNAME', 'support@mapmystandards.ai')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Initialize Postmark client if available
        if self.use_postmark:
            self.postmark = PostmarkClient(server_token=self.postmark_api_key)
            logger.info("Email service initialized with Postmark")
        # Initialize SendGrid client if available
        elif self.use_sendgrid:
            self.sg = SendGridAPIClient(api_key=self.sendgrid_api_key)
            logger.info("Email service initialized with SendGrid")
        elif self.smtp_password:
            logger.info("Email service initialized with SMTP fallback")
        else:
            logger.warning("No email configuration found - emails will not be sent")
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """
        Send an email via SendGrid or SMTP fallback
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            body: Plain text email body
            from_email: Sender email (defaults to support@mapmystandards.ai)
            html_body: Optional HTML email body
            attachments: Optional list of file paths to attach
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if self.use_postmark:
            return self._send_via_postmark(to_emails, subject, body, from_email, html_body, attachments)
        elif self.use_sendgrid:
            return self._send_via_sendgrid(to_emails, subject, body, from_email, html_body, attachments)
        else:
            return self._send_via_smtp(to_emails, subject, body, from_email, html_body, attachments)
    
    def _send_via_postmark(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Send email via Postmark"""
        try:
            # Use default from email if not specified
            from_email = from_email or self.default_from
            
            # Prepare email data
            email_data = {
                'From': f"{self.default_from_name} <{from_email}>",
                'To': ', '.join(to_emails),
                'Subject': subject,
                'TextBody': body
            }
            
            if html_body:
                email_data['HtmlBody'] = html_body
            
            # Send email
            response = self.postmark.emails.send(**email_data)
            logger.info(f"Email sent successfully via Postmark to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via Postmark: {e}")
            return False
    
    def _send_via_sendgrid(
        self, 
        to_emails: List[str], 
        subject: str, 
        body: str, 
        from_email: Optional[str] = None,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Send email via SendGrid API"""
        try:
            # Create the email
            mail = Mail(
                from_email=From(from_email or self.default_from, self.default_from_name),
                subject=Subject(subject)
            )
            
            # Add content
            if html_body:
                mail.content = [
                    Content("text/plain", body),
                    Content("text/html", html_body)
                ]
            else:
                mail.content = Content("text/plain", body)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, 'rb') as f:
                            data = f.read()
                            encoded = base64.b64encode(data).decode()
                            
                        attachment = Attachment(
                            FileContent(encoded),
                            FileName(os.path.basename(file_path)),
                            FileType("application/octet-stream"),
                            Disposition("attachment")
                        )
                        mail.attachment = [attachment]
            
            # Send the email
            response = self.sg.send(mail)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully via SendGrid to {', '.join(to_emails)}")
                return True
            else:
                logger.error(f"SendGrid API returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email via SendGrid: {e}")
            return False
    
    def _send_via_smtp(
        self, 
        to_emails: List[str], 
        subject: str, 
        body: str, 
        from_email: Optional[str] = None,
        html_body: Optional[str] = None,
        attachments: Optional[List[str]] = None
    ) -> bool:
        """Send email via SMTP (fallback method)"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = from_email or self.default_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text body
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {os.path.basename(file_path)}'
                            )
                            msg.attach(part)
            
            # Connect to server and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg, to_addrs=to_emails)
            server.quit()
            
            logger.info(f"Email sent successfully via SMTP to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False
    # Removed duplicate legacy block using Mime* names (unreachable and undefined)
    
    def send_contact_form_email(self, name: str, user_email: str, message: str) -> bool:
        """Send contact form submission email"""
        subject = f"New Contact Form Submission from {name}"
        
        body = f"""
New contact form submission received:

Name: {name}
Email: {user_email}

Message:
{message}

---
Sent from MapMyStandards.ai contact form
        """
        
        safe_message_html = message.replace('\n', '<br>')
        html_body = f"""
        <h2>New Contact Form Submission</h2>
        <p><strong>Name:</strong> {name}</p>
    <p><strong>Email:</strong> <a href="mailto:{user_email}">{user_email}</a></p>
        <p><strong>Message:</strong></p>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
            {safe_message_html}
        </div>
        <hr>
        <p><em>Sent from MapMyStandards.ai contact form</em></p>
        """
        
        return self.send_email(
            to_emails=[os.getenv('CONTACT_FORM_RECIPIENT', 'support@mapmystandards.ai')],
            subject=subject,
            body=body,
            html_body=html_body
        )
    
    def send_welcome_email(self, user_email: str, user_name: str, plan_name: str = "Professional") -> bool:
        """Send welcome email to new subscription customers."""
        subject = "Welcome to MapMyStandards - Your Account is Ready"
        body = (
            f"Dear {user_name},\n\n"
            f"Thank you for subscribing to MapMyStandards {plan_name} plan. Your account has been successfully created.\n\n"
            "Getting Started:\n"
            "1. Upload Documents: Start by uploading your institutional documents for analysis\n"
            "2. Select Standards: Choose your accrediting body (SACSCOC, HLC, etc.)\n"
            "3. Review Mappings: See how your documents align with accreditation standards\n"
            "4. Generate Reports: Create compliance reports for your review\n\n"
            "Need Help?\n"
            "Email: support@mapmystandards.com\n"
            "Documentation: https://docs.mapmystandards.com\n\n"
            "Best regards,\n"
            "The MapMyStandards Team"
        )
        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:30px;border-radius:10px 10px 0 0;text-align:center;">
                <h1 style="margin:0;">Welcome to MapMyStandards</h1>
            </div>
            <div style="background:white;padding:30px;border:1px solid #e5e7eb;border-radius:0 0 10px 10px;">
                <h2 style="color:#1f2937;">Hello {user_name},</h2>
                <p style="color:#4b5563;">Thank you for subscribing to MapMyStandards <strong>{plan_name}</strong> plan. Your account has been successfully created and you're ready to streamline your accreditation compliance process.</p>
                
                <div style="background:#f9fafb;padding:15px;border-radius:5px;margin:15px 0;">
                    <p style="margin:5px 0;"><strong>Your Account Details:</strong></p>
                    <p style="margin:5px 0;">Email: {user_email}</p>
                    <p style="margin:5px 0;">Plan: {plan_name}</p>
                    <p style="margin:5px 0;">Status: Active</p>
                </div>
                
                <div style="text-align:center;margin:30px 0;">
                    <a href="https://app.mapmystandards.com/dashboard" style="display:inline-block;padding:12px 30px;background:#3b82f6;color:white;text-decoration:none;border-radius:5px;">Access Your Dashboard</a>
                </div>
                
                <h3 style="color:#1f2937;">Getting Started:</h3>
                <ol style="color:#4b5563;">
                    <li><strong>Upload Documents:</strong> Start by uploading your institutional documents for analysis</li>
                    <li><strong>Select Standards:</strong> Choose your accrediting body (SACSCOC, HLC, etc.)</li>
                    <li><strong>Review Mappings:</strong> See how your documents align with accreditation standards</li>
                    <li><strong>Generate Reports:</strong> Create compliance reports for your review</li>
                </ol>
                
                <h3 style="color:#1f2937;">Need Help?</h3>
                <p style="color:#4b5563;">Our support team is here to assist you:</p>
                <ul style="color:#4b5563;">
                    <li>Email: <a href="mailto:support@mapmystandards.com">support@mapmystandards.com</a></li>
                    <li>Documentation: <a href="https://docs.mapmystandards.com">docs.mapmystandards.com</a></li>
                    <li>Schedule a demo: <a href="https://calendly.com/mapmystandards">Book a call</a></li>
                </ul>
            </div>
            <div style="text-align:center;color:#6b7280;font-size:14px;margin-top:30px;">
                <p>This email was sent to {user_email}<br>
                MapMyStandards - Simplifying Accreditation Compliance<br>
                © 2025 MapMyStandards. All rights reserved.</p>
            </div>
        </div>
        """
        return self.send_email([user_email], subject, body, html_body=html_body)

    def send_admin_new_signup_notification(
        self, 
        user_email: str, 
        user_name: str, 
        institution: str | None = None, 
        trial: bool = False,
        plan_name: str | None = None,
        amount: float | None = None,
        stripe_customer_id: str | None = None,
        subscription_id: str | None = None
    ) -> bool:
        """Notify internal admin address of a new signup or subscription."""
        admin_recipient = os.getenv("ADMIN_NOTIFICATION_EMAIL", "info@northpathstrategies.org")
        
        if plan_name and amount:
            subject = f"New Customer: {user_name} - {plan_name} Plan (${amount:.2f})"
        else:
            subject = f"New {'Trial ' if trial else ''}Signup: {user_name} <{user_email}>"
        
        institution_line = f"Institution: {institution}" if institution else "Institution: (not provided)"
        
        body_lines = [
            f"New {'subscription' if plan_name else 'signup'} on MapMyStandards",
            f"",
            f"Name: {user_name}",
            f"Email: {user_email}",
            f"{institution_line}",
        ]
        
        if plan_name:
            body_lines.extend([
                f"Plan: {plan_name}",
                f"Amount: ${amount:.2f}" if amount else "Amount: N/A",
            ])
        
        if stripe_customer_id:
            body_lines.append(f"Stripe Customer: {stripe_customer_id}")
        
        if subscription_id:
            body_lines.append(f"Subscription ID: {subscription_id}")
        
        body_lines.append(f"Timestamp (UTC): {datetime.utcnow().isoformat()}")
        
        body = "\n".join(body_lines)
        
        html_body = f"""
        <div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;'>
            <div style='background:#10b981;color:white;padding:20px;border-radius:10px 10px 0 0;'>
                <h2 style='margin:0;'>{'New Customer Subscription' if plan_name else 'New Signup'}</h2>
            </div>
            <div style='background:white;padding:20px;border:1px solid #e5e7eb;border-radius:0 0 10px 10px;'>
                <table style='width:100%;border-collapse:collapse;'>
                    <tr><td style='padding:8px 0;font-weight:600;width:150px;'>Name:</td><td>{user_name}</td></tr>
                    <tr><td style='padding:8px 0;font-weight:600;'>Email:</td><td><a href='mailto:{user_email}'>{user_email}</a></td></tr>
                    <tr><td style='padding:8px 0;font-weight:600;'>Institution:</td><td>{institution or '(not provided)'}</td></tr>
        """
        
        if plan_name:
            amount_str = f"${amount:.2f}" if amount else "N/A"
            html_body += f"""
                    <tr><td style='padding:8px 0;font-weight:600;'>Plan:</td><td>{plan_name}</td></tr>
                    <tr><td style='padding:8px 0;font-weight:600;'>Amount:</td><td>{amount_str}</td></tr>
            """
        
        if stripe_customer_id:
            html_body += f"""
                    <tr><td style='padding:8px 0;font-weight:600;'>Stripe Customer:</td><td>{stripe_customer_id}</td></tr>
            """
        
        if subscription_id:
            html_body += f"""
                    <tr><td style='padding:8px 0;font-weight:600;'>Subscription ID:</td><td>{subscription_id}</td></tr>
            """
        
        html_body += f"""
                    <tr><td style='padding:8px 0;font-weight:600;'>Timestamp (UTC):</td><td>{datetime.utcnow().isoformat()}</td></tr>
                </table>
        """
        
        if stripe_customer_id:
            html_body += f"""
                <p style='margin-top:20px;'>
                    <a href='https://dashboard.stripe.com/customers/{stripe_customer_id}' 
                       style='background:#5469d4;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;display:inline-block;'>
                        View in Stripe Dashboard
                    </a>
                </p>
            """
        
        html_body += """
            </div>
            <p style='font-size:12px;color:#888;text-align:center;margin-top:20px;'>Automated notification • MapMyStandards</p>
        </div>
        """
        
        return self.send_email([admin_recipient], subject, body, html_body=html_body)

    def send_password_setup_email(self, user_email: str, user_name: str, setup_link: str, expires_hours: int = 48) -> bool:
        """Send initial password setup (or reset) email with secure link."""
        subject = "Set up your MapMyStandards password"
        body = (
            f"Dear {user_name},\n\n"
            "Welcome! Please set your password to complete your account setup.\n\n"
            f"Password setup link (valid {expires_hours} hours):\n{setup_link}\n\n"
            "If you did not request this, you can ignore the email.\n\n"
            "Best,\nMapMyStandards.ai Team"
        )
        html_body = f"""
        <div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;'>
            <h2 style='color:#1e3c72;margin-top:0;'>Set Your Password</h2>
            <p>Hi {user_name},</p>
            <p>Click the button below to create your password and finish setting up your account. This link is valid for <strong>{expires_hours} hours</strong>.</p>
            <p style='text-align:center;margin:30px 0;'>
                <a href='{setup_link}' style='background:#1e3c72;color:#fff;padding:12px 22px;border-radius:6px;text-decoration:none;font-weight:600;'>Set Password</a>
            </p>
            <p>If the button does not work, copy and paste this URL into your browser:</p>
            <code style='display:block;background:#f5f7fa;padding:10px;border-radius:4px;font-size:12px;word-break:break-all;'>{setup_link}</code>
            <p style='font-size:12px;color:#667;'>If you did not request this, you can safely ignore the email.</p>
            <hr style='border:1px solid #eee;'>
            <p style='font-size:12px;color:#999;'>support@mapmystandards.ai · <a href="{build_unsubscribe_link()}">Unsubscribe</a></p>
        </div>
        """
        return self.send_email([user_email], subject, body, html_body=html_body)
    
    def send_trial_expiration_notice(self, user_email: str, user_name: str, days_remaining: int) -> bool:
        """Send trial expiration notice"""
        subject = f"Your MapMyStandards.ai trial expires in {days_remaining} days"
        
        body = f"""
Dear {user_name},

Your 7-day free trial of MapMyStandards.ai expires in {days_remaining} days.

To continue using our platform without interruption, please upgrade to a paid plan:
- A³E College Plan: Ideal for single institutions
- A³E Multi-Campus Plan: Perfect for multi-campus systems

Visit your account dashboard to upgrade or contact our team for assistance.

Best regards,
The MapMyStandards.ai Team
        """
        
        return self.send_email(
            to_emails=[user_email],
            subject=subject,
            body=body
        )
    
    async def send_password_reset_email(self, recipient_email: str, reset_link: str, user_name: str) -> bool:
        """Send password reset email"""
        subject = "Reset Your MapMyStandards.ai Password"
        
        body = f"""
Dear {user_name},

You requested a password reset for your MapMyStandards.ai account.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
The MapMyStandards.ai Team
        """
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <img src="https://mapmystandards.ai/wp-content/uploads/2025/07/Original-Logo.png" alt="MapMyStandards.ai" style="height: 50px;">
                </div>
                
                <h2 style="color: #1e3c72;">Password Reset Request</h2>
                
                <p>Dear {user_name},</p>
                
                <p>You requested a password reset for your MapMyStandards.ai account.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="display: inline-block; background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">Reset Password</a>
                </div>
                
                <p style="color: #666; font-size: 14px;">This link will expire in 1 hour for security reasons.</p>
                
                <p style="color: #666; font-size: 14px;">If you didn't request this password reset, please ignore this email.</p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                <p style="color: #666; font-size: 12px; text-align: center;">
                    Best regards,<br>
                    The MapMyStandards.ai Team
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to_emails=[recipient_email],
            subject=subject,
            body=body,
            html_body=html_body
        )
    
    def send_trial_reminder_email(
        self, 
        recipient_email: str, 
        user_name: str,
        days_remaining: int,
        institution_name: str = "Your Institution",
        docs_analyzed: int = 0,
        hours_saved: int = 0,
        compliance_score: int = 0,
        estimated_savings: str = "500+",
        recommended_plan: str = "professional",
        discount_percent: int = 20
    ) -> bool:
        """Send trial reminder email with personalized stats"""
        try:
            # Load template
            template_path = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                "templates", 
                "email", 
                "trial_reminder.html"
            )
            
            with open(template_path, 'r') as f:
                template = f.read()
            
            # Calculate dynamic values
            recommended_plan_name = {
                "essential": "Essential Plan",
                "professional": "Professional Plan", 
                "enterprise": "Enterprise Plan"
            }.get(recommended_plan, "Professional Plan")
            
            recommended_plan_price = {
                "essential": "$497",
                "professional": "$997",
                "enterprise": "$1,997"
            }.get(recommended_plan, "$997")
            
            annual_savings = {
                "essential": "$1,194",
                "professional": "$2,394",
                "enterprise": "$4,794"
            }.get(recommended_plan, "$2,394")
            
            # Replace template variables
            html_body = template
            from src.a3e.core.config import settings
            base_app = settings.PUBLIC_APP_URL.rstrip('/')
            base_api = settings.PUBLIC_API_URL.rstrip('/')
            replacements = {
                "{{name}}": user_name,
                "{{email}}": recipient_email,
                "{{days_remaining}}": str(days_remaining),
                "{{institution_name}}": institution_name,
                "{{docs_analyzed}}": str(docs_analyzed),
                "{{hours_saved}}": str(hours_saved),
                "{{compliance_score}}": str(compliance_score),
                "{{estimated_savings}}": estimated_savings,
                "{{recommended_plan}}": recommended_plan,
                "{{recommended_plan_name}}": recommended_plan_name,
                "{{recommended_plan_price}}": recommended_plan_price,
                "{{annual_savings}}": annual_savings,
                "{{discount_percent}}": str(discount_percent),
                "{{unsubscribe_link}}": f"{base_api}/unsubscribe?email={recipient_email}"
            }
            
            for key, value in replacements.items():
                html_body = html_body.replace(key, value)
            
            # Handle conditional content based on days remaining
            if days_remaining == 7:
                subject = "Your A³E Trial - 7 Days to Transform Your Accreditation Process"
            elif days_remaining == 3:
                subject = "⚡ Only 3 Days Left in Your A³E Trial"
            else:
                subject = "🚨 Final Day - Your A³E Trial Expires Tomorrow"
            
            return self.send_email(
                to_emails=[recipient_email],
                subject=subject,
                body=f"Hi {user_name}, your A³E trial has {days_remaining} days remaining.",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send trial reminder email: {str(e)}")
            return False
    
    def send_trial_expired_email(
        self,
        recipient_email: str,
        user_name: str,
        expiration_date: str,
        institution_name: str = "Your Institution",
        docs_analyzed: int = 0,
        hours_saved: int = 0,
        money_saved: str = "500",
        compliance_score: int = 0,
        recommended_plan: str = "professional",
        offer_expiry_date: str = None
    ) -> bool:
        """Send trial expiration email with win-back offer"""
        try:
            # Load template
            template_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "templates",
                "email",
                "trial_expired.html"
            )
            
            with open(template_path, 'r') as f:
                template = f.read()
            
            # Calculate offer expiry if not provided
            if not offer_expiry_date:
                from datetime import datetime, timedelta
                offer_expiry = datetime.now() + timedelta(days=7)
                offer_expiry_date = offer_expiry.strftime("%B %d, %Y")
            
            # Replace template variables
            html_body = template
            from src.a3e.core.config import settings
            base_api = settings.PUBLIC_API_URL.rstrip('/')
            replacements = {
                "{{name}}": user_name,
                "{{email}}": recipient_email,
                "{{expiration_date}}": expiration_date,
                "{{institution_name}}": institution_name,
                "{{docs_analyzed}}": str(docs_analyzed),
                "{{hours_saved}}": str(hours_saved),
                "{{money_saved}}": money_saved,
                "{{compliance_score}}": str(compliance_score),
                "{{recommended_plan}}": recommended_plan,
                "{{offer_expiry_date}}": offer_expiry_date,
                "{{unsubscribe_link}}": f"{base_api}/unsubscribe?email={recipient_email}"
            }
            
            for key, value in replacements.items():
                html_body = html_body.replace(key, value)
            
            subject = "Your A³E Trial Has Expired - But There's Still Time!"
            
            return self.send_email(
                to_emails=[recipient_email],
                subject=subject,
                body=f"Hi {user_name}, your A³E trial has expired but we have a special offer for you.",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send trial expired email: {str(e)}")
            return False
    
    async def send_enhanced_password_reset_email(
        self,
        recipient_email: str,
        user_name: str,
        reset_link: str,
        reset_code: str,
        request_time: str,
        ip_address: str = "Unknown",
        location: str = "Unknown",
        device: str = "Unknown",
        request_id: str = None,
        expiry_hours: int = 24
    ) -> bool:
        """Send enhanced password reset email with security details"""
        try:
            # Load template
            template_path = os.path.join(
                os.path.dirname(__file__),
                "..",
                "templates",
                "email",
                "password_reset.html"
            )
            
            with open(template_path, 'r') as f:
                template = f.read()
            
            # Generate request ID if not provided
            if not request_id:
                import uuid
                request_id = str(uuid.uuid4())[:8]
            
            # Replace template variables
            html_body = template
            from src.a3e.core.config import settings
            base_api = settings.PUBLIC_API_URL.rstrip('/')
            replacements = {
                "{{name}}": user_name,
                "{{email}}": recipient_email,
                "{{reset_link}}": reset_link,
                "{{reset_code}}": reset_code,
                "{{request_time}}": request_time,
                "{{ip_address}}": ip_address,
                "{{location}}": location,
                "{{device}}": device,
                "{{request_id}}": request_id,
                "{{expiry_hours}}": str(expiry_hours),
                "{{unsubscribe_link}}": f"{base_api}/unsubscribe?email={recipient_email}"
            }
            
            for key, value in replacements.items():
                html_body = html_body.replace(key, value)
            
            subject = "Password Reset Request - MapMyStandards A³E"
            
            return self.send_email(
                to_emails=[recipient_email],
                subject=subject,
                body=f"Hi {user_name}, click here to reset your password: {reset_link}",
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send password reset email: {str(e)}")
            return False

# Create global email service instance
email_service = EmailService()
