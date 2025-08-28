"""
Enhanced Email Service with Postmark Support

Provides email sending via Postmark (preferred), SendGrid, or SMTP fallback.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import email providers
try:
    from postmarker.core import PostmarkClient
    POSTMARK_AVAILABLE = True
except ImportError:
    POSTMARK_AVAILABLE = False
    logger.warning("Postmark not available - install postmarker package")

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logger.warning("SendGrid not available")

class EmailServiceEnhanced:
    """Enhanced email service with multiple provider support"""
    
    def __init__(self):
        self.provider = None
        self.client = None
        
        # Email settings
        self.from_email = os.getenv('EMAIL_FROM', 'support@mapmystandards.ai')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'MapMyStandards A³E')
        self.admin_email = os.getenv('ADMIN_NOTIFICATION_EMAIL', 'admin@mapmystandards.ai')
        
        # Try Postmark first (preferred)
        postmark_token = os.getenv('POSTMARK_SERVER_TOKEN')
        if POSTMARK_AVAILABLE and postmark_token:
            try:
                self.client = PostmarkClient(server_token=postmark_token)
                self.provider = 'postmark'
                self.message_stream = os.getenv('POSTMARK_MESSAGE_STREAM', 'outbound')
                logger.info("✅ Email service initialized with Postmark")
            except Exception as e:
                logger.error(f"Failed to initialize Postmark: {e}")
        
        # Try SendGrid as fallback
        if not self.provider:
            sendgrid_key = os.getenv('SENDGRID_API_KEY')
            if SENDGRID_AVAILABLE and sendgrid_key:
                try:
                    self.client = SendGridAPIClient(api_key=sendgrid_key)
                    self.provider = 'sendgrid'
                    logger.info("✅ Email service initialized with SendGrid")
                except Exception as e:
                    logger.error(f"Failed to initialize SendGrid: {e}")
        
        if not self.provider:
            logger.warning("⚠️ No email provider configured")
    
    def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        tag: Optional[str] = None
    ) -> bool:
        """Send an email using the configured provider"""
        
        if not self.provider:
            logger.warning(f"Cannot send email - no provider configured. Subject: {subject}")
            return False
        
        try:
            if self.provider == 'postmark':
                return self._send_postmark(to, subject, html_body, text_body, cc, bcc, reply_to, tag)
            elif self.provider == 'sendgrid':
                return self._send_sendgrid(to, subject, html_body, text_body)
            return False
        except Exception as e:
            logger.error(f"Failed to send email via {self.provider}: {e}")
            return False
    
    def _send_postmark(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        reply_to: Optional[str] = None,
        tag: Optional[str] = None
    ) -> bool:
        """Send email via Postmark"""
        
        email_data = {
            'From': f"{self.from_name} <{self.from_email}>",
            'To': to,
            'Subject': subject,
            'HtmlBody': html_body,
            'MessageStream': self.message_stream
        }
        
        if text_body:
            email_data['TextBody'] = text_body
        if cc:
            email_data['Cc'] = ', '.join(cc)
        if bcc:
            email_data['Bcc'] = ', '.join(bcc)
        if reply_to:
            email_data['ReplyTo'] = reply_to
        if tag:
            email_data['Tag'] = tag
        
        response = self.client.emails.send(**email_data)
        
        if response.get('ErrorCode') == 0:
            logger.info(f"✅ Email sent via Postmark: {subject} to {to}")
            return True
        else:
            logger.error(f"Postmark error: {response.get('Message')}")
            return False
    
    def _send_sendgrid(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Send email via SendGrid"""
        
        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to,
            subject=subject,
            html_content=html_body
        )
        
        if text_body:
            message.plain_text_content = text_body
        
        response = self.client.send(message)
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"✅ Email sent via SendGrid: {subject} to {to}")
            return True
        else:
            logger.error(f"SendGrid error: {response.status_code}")
            return False
    
    # Convenience methods for common emails
    
    def send_trial_welcome(self, user_email: str, user_name: str) -> bool:
        """Send welcome email for trial signup"""
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1e3c72;">Welcome to MapMyStandards A³E, {user_name}!</h2>
                
                <p>Thank you for starting your 7-day free trial. You now have access to:</p>
                
                <ul style="color: #555;">
                    <li>✨ AI-powered evidence mapping with 95% accuracy</li>
                    <li>📊 Real-time compliance tracking and analytics</li>
                    <li>📈 Comprehensive accreditation reports</li>
                    <li>🎯 Gap analysis and recommendations</li>
                </ul>
                
                <p><strong>Getting Started:</strong></p>
                <ol>
                    <li>Upload your first evidence document</li>
                    <li>Select your accreditor and standards</li>
                    <li>Let our AI map your evidence automatically</li>
                    <li>Review your compliance dashboard</li>
                </ol>
                
                <div style="margin: 30px 0;">
                    <a href="https://platform.mapmystandards.ai/dashboard" 
                       style="background: #10b981; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        Access Your Dashboard
                    </a>
                </div>
                
                <p style="color: #777; font-size: 14px;">
                    Your trial expires in 7 days. Upgrade anytime to continue using all features.
                </p>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                
                <p style="color: #999; font-size: 12px;">
                    MapMyStandards A³E | Autonomous Accreditation & Audit Engine<br>
                    Questions? Reply to this email or visit our <a href="https://mapmystandards.ai/contact">support page</a>.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to MapMyStandards A³E, {user_name}!
        
        Thank you for starting your 7-day free trial.
        
        Access your dashboard: https://platform.mapmystandards.ai/dashboard
        
        Your trial expires in 7 days. Upgrade anytime to continue using all features.
        
        Questions? Visit https://mapmystandards.ai/contact
        """
        
        return self.send_email(
            to=user_email,
            subject="Welcome to MapMyStandards A³E - Your Trial is Active!",
            html_body=html_body,
            text_body=text_body,
            tag="trial-welcome"
        )
    
    def send_document_processed(
        self, 
        user_email: str, 
        document_name: str,
        standards_mapped: int,
        confidence_score: float
    ) -> bool:
        """Send notification when document processing is complete"""
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1e3c72;">Document Processing Complete</h2>
                
                <p>Your document has been successfully analyzed:</p>
                
                <div style="background: #f9fafb; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Document:</strong> {document_name}</p>
                    <p style="margin: 5px 0;"><strong>Standards Mapped:</strong> {standards_mapped}</p>
                    <p style="margin: 5px 0;"><strong>Confidence Score:</strong> {confidence_score:.1f}%</p>
                </div>
                
                <div style="margin: 30px 0;">
                    <a href="https://platform.mapmystandards.ai/evidence-mapping" 
                       style="background: #6366f1; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 6px; display: inline-block;">
                        View Evidence Mapping
                    </a>
                </div>
                
                <p style="color: #999; font-size: 12px;">
                    MapMyStandards A³E | AI-Powered Accreditation Management
                </p>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to=user_email,
            subject=f"✅ Document Processed: {document_name}",
            html_body=html_body,
            tag="document-processed"
        )
    
    def test_email_configuration(self) -> Dict[str, Any]:
        """Test email configuration by sending a test email"""
        
        test_result = {
            'provider': self.provider,
            'configured': self.provider is not None,
            'from_email': self.from_email,
            'test_sent': False,
            'error': None
        }
        
        if self.provider:
            try:
                success = self.send_email(
                    to=self.admin_email,
                    subject="Test Email - MapMyStandards Configuration",
                    html_body="<p>This is a test email to verify email configuration.</p>",
                    text_body="This is a test email to verify email configuration.",
                    tag="test"
                )
                test_result['test_sent'] = success
            except Exception as e:
                test_result['error'] = str(e)
        
        return test_result

# Singleton instance
_email_service = None

def get_email_service() -> EmailServiceEnhanced:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailServiceEnhanced()
    return _email_service