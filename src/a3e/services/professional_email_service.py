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
                response = self.postmark.emails.send(
                    From=f"{self.from_name} <{self.from_email}>",
                    To=to_email,
                    Subject=subject,
                    HtmlBody=html_content,
                    TextBody=text_content or self._html_to_text(html_content)
                )
                logger.info(f"✅ Email sent via Postmark to {to_email}")
                return True
                
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
        subject = "Welcome to MapMyStandards!"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h1 style="color: #2563eb;">Welcome to MapMyStandards!</h1>
                    
                    <p>Hello {user_name},</p>
                    
                    <p>Thank you for joining MapMyStandards. We're excited to help you streamline 
                    your accreditation compliance process.</p>
                    
                    <h3>Getting Started</h3>
                    <ul>
                        <li>Complete your institution profile</li>
                        <li>Upload your first evidence document</li>
                        <li>View your compliance dashboard</li>
                        <li>Generate your first compliance report</li>
                    </ul>
                    
                    <div style="margin: 30px 0;">
                        <a href="https://platform.mapmystandards.ai/dashboard" 
                           style="background-color: #2563eb; 
                                  color: white; 
                                  padding: 12px 30px; 
                                  text-decoration: none; 
                                  border-radius: 5px;
                                  display: inline-block;">
                            Go to Dashboard
                        </a>
                    </div>
                    
                    <p>If you have any questions, feel free to contact our support team.</p>
                    
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


# Create singleton instance
email_service = ProfessionalEmailService()

# Export for backward compatibility
__all__ = ['email_service', 'ProfessionalEmailService']