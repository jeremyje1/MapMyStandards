"""
Professional Email Service for MapMyStandards
Handles all email communications with fallback support
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import email service implementations
EMAIL_SERVICE_AVAILABLE = False
POSTMARK_AVAILABLE = False
SENDGRID_AVAILABLE = False

try:
    from postmarker.core import PostmarkClient
    POSTMARK_AVAILABLE = True
except ImportError:
    logger.warning("Postmark not available")

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    logger.warning("SendGrid not available")


class ProfessionalEmailService:
    """Professional email service with multiple provider support"""
    
    def __init__(self):
        """Initialize email service with available provider"""
        self.provider = None
        self.from_email = os.getenv('EMAIL_FROM', 'noreply@mapmystandards.ai')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'MapMyStandards')
        self.reply_to = os.getenv('EMAIL_REPLY_TO', os.getenv('ADMIN_NOTIFICATION_EMAIL', 'info@northpathstrategies.org'))
        self.message_stream = os.getenv('POSTMARK_MESSAGE_STREAM', 'outbound')
        
        # Try Postmark first
        if POSTMARK_AVAILABLE:
            postmark_token = os.getenv('POSTMARK_API_TOKEN') or os.getenv('POSTMARK_SERVER_TOKEN')
            if postmark_token:
                try:
                    self.postmark = PostmarkClient(server_token=postmark_token)
                    self.provider = 'postmark'
                    logger.info("✅ Using Postmark for email")
                except Exception as e:
                    logger.error(f"Failed to initialize Postmark: {e}")
        
        # Fallback to SendGrid
        if not self.provider and SENDGRID_AVAILABLE:
            sendgrid_key = os.getenv('SENDGRID_API_KEY')
            if sendgrid_key:
                try:
                    self.sendgrid = SendGridAPIClient(sendgrid_key)
                    self.provider = 'sendgrid'
                    logger.info("✅ Using SendGrid for email")
                except Exception as e:
                    logger.error(f"Failed to initialize SendGrid: {e}")
        
        if not self.provider:
            logger.warning("⚠️ No email provider available - emails will not be sent")
    
    async def send_password_reset_email(
        self, 
        to_email: str, 
        reset_link: str,
        user_name: Optional[str] = None
    ) -> bool:
        """Send password reset email"""
        subject = "Reset Your MapMyStandards Password"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Reset Your Password</h2>
                    
                    <p>Hello {user_name or 'there'},</p>
                    
                    <p>You recently requested to reset your password for your MapMyStandards account.</p>
                    
                    <p>Click the link below to reset your password:</p>
                    
                    <div style="margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background-color: #2563eb; 
                                  color: white; 
                                  padding: 12px 30px; 
                                  text-decoration: none; 
                                  border-radius: 5px;
                                  display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #2563eb;">
                        {reset_link}
                    </p>
                    
                    <p>This link will expire in 1 hour for security reasons.</p>
                    
                    <p>If you didn't request a password reset, please ignore this email.</p>
                    
                    <hr style="margin-top: 40px; border: none; border-top: 1px solid #ddd;">
                    <p style="font-size: 12px; color: #666;">
                        This email was sent by MapMyStandards<br>
                        © 2025 MapMyStandards. All rights reserved.
                    </p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content
        )
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Send email using available provider"""
        
        if not self.provider:
            logger.warning(f"No email provider available - would send to {to_email}: {subject}")
            return False
        
        try:
            if self.provider == 'postmark':
                # Build initial payload
                kwargs = dict(
                    From=f"{self.from_name} <{self.from_email}>",
                    To=to_email,
                    Subject=subject,
                    HtmlBody=html_content,
                    TextBody=text_content or self._html_to_text(html_content),
                    ReplyTo=self.reply_to
                )
                if self.message_stream:
                    kwargs["MessageStream"] = self.message_stream

                def _send_and_check(payload: Dict[str, Any]) -> bool:
                    resp = self.postmark.emails.send(**payload)
                    # postmarker returns dict with ErrorCode/Message
                    try:
                        error_code = resp.get('ErrorCode', 0)
                    except AttributeError:
                        error_code = 0
                    if error_code and error_code != 0:
                        raise Exception(f"Postmark error {error_code}: {resp.get('Message')}")
                    return True

                # Attempt 1: as-configured
                try:
                    if _send_and_check(kwargs):
                        logger.info(f"✅ Email sent via Postmark to {to_email}")
                        return True
                except Exception as e1:
                    logger.warning(f"Postmark send failed (stream={kwargs.get('MessageStream')}): {e1}")

                # Attempt 2: force 'outbound' stream if different
                try:
                    if kwargs.get('MessageStream') != 'outbound':
                        k2 = dict(kwargs)
                        k2['MessageStream'] = 'outbound'
                        if _send_and_check(k2):
                            logger.info(f"✅ Email sent via Postmark to {to_email} on retry with 'outbound' stream")
                            return True
                except Exception as e2:
                    logger.warning(f"Postmark retry with 'outbound' failed: {e2}")

                # Attempt 3: remove MessageStream entirely
                try:
                    k3 = dict(kwargs)
                    k3.pop('MessageStream', None)
                    if _send_and_check(k3):
                        logger.info(f"✅ Email sent via Postmark to {to_email} after removing MessageStream")
                        return True
                except Exception as e3:
                    logger.warning(f"Postmark retry without MessageStream failed: {e3}")

                # Attempt 4: fallback From to a verified sender
                try:
                    fallback_from = os.getenv('EMAIL_FROM_FALLBACK', 'support@mapmystandards.ai')
                    if fallback_from and (self.from_email != fallback_from):
                        k4 = dict(k3 if 'k3' in locals() else kwargs)
                        k4['From'] = f"{self.from_name} <{fallback_from}>"
                        k4.pop('MessageStream', None)
                        if _send_and_check(k4):
                            logger.info(f"✅ Email sent via Postmark to {to_email} using fallback From {fallback_from}")
                            return True
                except Exception as e4:
                    logger.error(f"Postmark retry with fallback From failed: {e4}")
                    # let it fall through to overall exception handler
                # All retries failed
                raise Exception("All Postmark send attempts failed")
                
            elif self.provider == 'sendgrid':
                message = Mail(
                    from_email=(self.from_email, self.from_name),
                    to_emails=to_email,
                    subject=subject,
                    html_content=html_content
                )
                
                if text_content:
                    message.plain_text_content = text_content
                
                response = self.sendgrid.send(message)
                logger.info(f"✅ Email sent via SendGrid to {to_email}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
        
        return False
    
    def _html_to_text(self, html: str) -> str:
        """Simple HTML to text conversion"""
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', html)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    async def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email to new users"""
        subject = "Welcome to MapMyStandards — Let’s get you set up"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #2563eb;">Welcome to MapMyStandards</h1>
                    
                    <p>Hello {user_name},</p>
                    
                    <p>Thanks for joining! We’ve personalized your experience based on onboarding and made it easy to get value fast.</p>
                    
                    <h3>Quick Start</h3>
                    <ol>
                        <li><strong>Choose your accreditor</strong> on the Standards page — we’ll preselect from onboarding when possible.</li>
                        <li><strong>Upload documents</strong> on the Upload page — narratives and Evidence Mapping unlock with mapped evidence.</li>
                        <li><strong>Review your Dashboard</strong> for coverage and gaps tailored to your institution.</li>
                        <li><strong>Generate a narrative</strong> in Reports with inline citations from your evidence.</li>
                    </ol>
                    
                    <div style="margin: 30px 0;">
                        <a href="https://platform.mapmystandards.ai/dashboard-modern" 
                           style="background-color: #2563eb; 
                                  color: white; 
                                  padding: 12px 30px; 
                                  text-decoration: none; 
                                  border-radius: 5px;
                                  display: inline-block;">
                            Go to Dashboard
                        </a>
                    </div>
                    
                    <p>Need a hand? Reply to this email or reach us at support@mapmystandards.ai.</p>
                    
                    <p>Best regards,<br>
                    The MapMyStandards Team</p>
                </div>
            </body>
        </html>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content
        )

    # Compatibility helpers used by API routes
    def send_customer_welcome_email(self, email: str, name: str, institution: Optional[str] = None, trial_days: int = 7) -> bool:
        """Send a richer welcome email; synchronous wrapper for background tasks."""
        try:
            import asyncio
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            coro = self.send_welcome_email(email, name)
            if loop and loop.is_running():
                loop.create_task(coro)
                return True
            else:
                return asyncio.run(coro)
        except Exception as e:
            logger.error(f"Failed to dispatch customer welcome email: {e}")
            return False

    def send_admin_notification(
        self,
        customer_email: str,
        customer_name: str,
        institution: Optional[str] = None,
        signup_type: str = "trial",
        additional_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Notify admin of new signup or subscription."""
        try:
            admin_to = os.getenv('ADMIN_NOTIFICATION_EMAIL', 'info@northpathstrategies.org')
            subject = f"New {signup_type.capitalize()} Signup: {customer_name} <{customer_email}>"
            details = {
                'customer_email': customer_email,
                'customer_name': customer_name,
                'institution': institution or '(not provided)',
                'signup_type': signup_type,
            }
            if additional_info:
                details.update(additional_info)
            # Simple HTML summary
            rows = ''.join([f"<tr><td style='padding:6px 8px;background:#f9fafb'><strong>{k}</strong></td><td style='padding:6px 8px'>{v}</td></tr>" for k, v in details.items()])
            html = f"""
            <div style="font-family:Arial,sans-serif">
                <h2 style="margin:0 0 10px 0;color:#111827">New {signup_type.capitalize()} Signup</h2>
                <table style="border-collapse:collapse">{rows}</table>
            </div>
            """
            return self.send_email(
                to_email=admin_to,
                subject=subject,
                html_content=html
            ) or False
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
            return False


# Create singleton instance
email_service = ProfessionalEmailService()

# Export for backward compatibility
__all__ = ['email_service', 'ProfessionalEmailService']
