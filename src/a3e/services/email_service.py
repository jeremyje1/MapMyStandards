"""
Email service for MapMyStandards.ai
Handles email sending via SendGrid API
"""

import os
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Try SendGrid first, fallback to SMTP
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, From, To, Subject, Content, Attachment, FileContent, FileName, FileType, Disposition
    import base64
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("SendGrid not available - email functionality limited")

# Fallback SMTP imports
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders

class EmailService:
    def __init__(self):
        # SendGrid configuration (preferred)
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.use_sendgrid = SENDGRID_AVAILABLE and self.sendgrid_api_key
        
        # Common settings
        self.default_from = os.getenv('EMAIL_FROM', 'support@mapmystandards.ai')
        self.default_from_name = os.getenv('EMAIL_FROM_NAME', 'MapMyStandards Support')
        
        # SMTP fallback configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'mx1.titan.email')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.use_tls = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
        self.smtp_username = os.getenv('SMTP_USERNAME', 'support@mapmystandards.ai')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Initialize SendGrid client if available
        if self.use_sendgrid:
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
        if self.use_sendgrid:
            return self._send_via_sendgrid(to_emails, subject, body, from_email, html_body, attachments)
        else:
            return self._send_via_smtp(to_emails, subject, body, from_email, html_body, attachments)
    
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
                to_emails=[To(email) for email in to_emails],
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
            msg = MimeMultipart('alternative')
            msg['From'] = from_email or self.default_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text body
            text_part = MimeText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MimeText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MimeBase('application', 'octet-stream')
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
        try:
            # Create message
            msg = MimeMultipart('alternative')
            msg['From'] = from_email or self.default_from
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Add text body
            text_part = MimeText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML body if provided
            if html_body:
                html_part = MimeText(html_body, 'html')
                msg.attach(html_part)
            
            # Add attachments if provided
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MimeBase('application', 'octet-stream')
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
            
            server.login(self.username, self.password)
            server.send_message(msg, to_addrs=to_emails)
            server.quit()
            
            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_contact_form_email(self, name: str, email: str, message: str) -> bool:
        """Send contact form submission email"""
        subject = f"New Contact Form Submission from {name}"
        
        body = f"""
New contact form submission received:

Name: {name}
Email: {email}

Message:
{message}

---
Sent from MapMyStandards.ai contact form
        """
        
        html_body = f"""
        <h2>New Contact Form Submission</h2>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
        <p><strong>Message:</strong></p>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
            {message.replace('\n', '<br>')}
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
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email to new users"""
        subject = "Welcome to MapMyStandards.ai!"
        
        body = f"""
Dear {user_name},

Welcome to MapMyStandards.ai! We're excited to help you streamline your accreditation process.

Your account has been successfully created. Here's what you can do next:

1. Complete your institutional profile
2. Upload your first accreditation documents
3. Start using our A³E Engine for intelligent analysis

If you have any questions, please don't hesitate to reach out to our support team.

Best regards,
The MapMyStandards.ai Team

---
support@mapmystandards.ai
NorthPath Strategies
        """
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1e3c72;">Welcome to MapMyStandards.ai!</h2>
            
            <p>Dear {user_name},</p>
            
            <p>Welcome to MapMyStandards.ai! We're excited to help you streamline your accreditation process.</p>
            
            <p>Your account has been successfully created. Here's what you can do next:</p>
            
            <ol>
                <li>Complete your institutional profile</li>
                <li>Upload your first accreditation documents</li>
                <li>Start using our A³E Engine for intelligent analysis</li>
            </ol>
            
            <p>If you have any questions, please don't hesitate to reach out to our support team.</p>
            
            <p>Best regards,<br>The MapMyStandards.ai Team</p>
            
            <hr style="border: 1px solid #eee;">
            <p style="color: #6c757d; font-size: 12px;">
                <a href="mailto:support@mapmystandards.ai">support@mapmystandards.ai</a><br>
                NorthPath Strategies
            </p>
        </div>
        """
        
        return self.send_email(
            to_emails=[user_email],
            subject=subject,
            body=body,
            html_body=html_body
        )
    
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
    
    async def send_password_reset_email(self, email: str, reset_link: str, user_name: str) -> bool:
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
            to_emails=[email],
            subject=subject,
            body=body,
            html_body=html_body
        )

# Create global email service instance
email_service = EmailService()
