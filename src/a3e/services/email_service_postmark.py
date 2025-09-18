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
        self.from_email = os.getenv('FROM_EMAIL') or os.getenv('EMAIL_FROM', 'support@mapmystandards.ai')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'MapMyStandards A³E')
        self.admin_email = os.getenv('ADMIN_EMAIL') or os.getenv('ADMIN_NOTIFICATION_EMAIL', 'admin@mapmystandards.ai')
        
        # Try Postmark first (preferred)
        postmark_token = os.getenv('POSTMARK_SERVER_TOKEN') or os.getenv('POSTMARK_API_TOKEN')
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
        <head>
            <style>
                .container {{ max-width: 650px; margin: 0 auto; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
                .header {{ background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; background: #ffffff; }}
                .section {{ margin-bottom: 25px; }}
                .step {{ background: #f8fafc; border-left: 4px solid #3b82f6; padding: 15px; margin: 10px 0; }}
                .feature {{ background: #f0f9ff; padding: 15px; margin: 10px 0; border-radius: 6px; }}
                .cta-button {{ background: #3b82f6; color: white; padding: 15px 30px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: 600; }}
                .footer {{ background: #f8fafc; padding: 20px; text-align: center; color: #64748b; font-size: 14px; }}
                .resource-link {{ color: #3b82f6; text-decoration: none; font-weight: 500; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0; font-size: 28px;">Welcome to MapMyStandards</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your AI-Powered Accreditation Management Platform</p>
                </div>
                
                <div class="content">
                    <div class="section">
                        <h2 style="color: #1e293b; margin-bottom: 15px;">Hello {user_name},</h2>
                        <p style="color: #475569; line-height: 1.6;">Thank you for starting your 7-day free trial with MapMyStandards. You now have access to our comprehensive accreditation management platform designed to streamline your compliance process and maximize your institutional effectiveness.</p>
                    </div>
                    
                    <div class="section">
                        <h3 style="color: #1e293b; margin-bottom: 15px;">Your Platform Includes:</h3>
                        <div class="feature">
                            <strong>AI-Powered Evidence Mapping</strong><br>
                            Advanced algorithms automatically map your documents to accreditation standards with 95% accuracy, saving hours of manual work.
                        </div>
                        <div class="feature">
                            <strong>Real-Time Compliance Dashboard</strong><br>
                            Monitor your accreditation readiness with live analytics, progress tracking, and comprehensive reporting tools.
                        </div>
                        <div class="feature">
                            <strong>Gap Analysis & Recommendations</strong><br>
                            Identify compliance gaps and receive actionable recommendations to strengthen your accreditation portfolio.
                        </div>
                        <div class="feature">
                            <strong>Multi-Accreditor Support</strong><br>
                            Work with multiple accrediting bodies simultaneously with standards from HLC, SACSCOC, MSCHE, and more.
                        </div>
                    </div>
                    
                    <div class="section">
                        <h3 style="color: #1e293b; margin-bottom: 15px;">Getting Started - Your 4-Step Onboarding:</h3>
                        <div class="step">
                            <strong>Step 1: Complete Your Profile</strong><br>
                            Set up your institution details and select your primary accrediting body to customize your experience.
                        </div>
                        <div class="step">
                            <strong>Step 2: Upload Your First Documents</strong><br>
                            Begin with key documents like strategic plans, assessment reports, or syllabi to see our AI in action.
                        </div>
                        <div class="step">
                            <strong>Step 3: Review AI Mappings</strong><br>
                            Examine how our system maps your evidence to standards and make any necessary adjustments.
                        </div>
                        <div class="step">
                            <strong>Step 4: Explore Your Dashboard</strong><br>
                            Familiarize yourself with compliance tracking, reporting tools, and analytics features.
                        </div>
                    </div>
                    
                    <div class="section" style="text-align: center; margin: 30px 0;">
                        <a href="https://platform.mapmystandards.ai/dashboard-modern.html" class="cta-button">Access Your Dashboard</a>
                    </div>
                    
                    <div class="section">
                        <h3 style="color: #1e293b; margin-bottom: 15px;">Resources to Maximize Your Success:</h3>
                        <ul style="color: #475569; line-height: 1.8;">
                            <li><a href="https://mapmystandards.ai/quick-start" class="resource-link">Quick Start Guide</a> - Get up and running in under 30 minutes</li>
                            <li><a href="https://mapmystandards.ai/best-practices" class="resource-link">Best Practices</a> - Tips from successful accreditation teams</li>
                            <li><a href="https://mapmystandards.ai/video-tutorials" class="resource-link">Video Tutorials</a> - Step-by-step walkthroughs of key features</li>
                            <li><a href="https://mapmystandards.ai/support" class="resource-link">Help Center</a> - Comprehensive documentation and FAQs</li>
                        </ul>
                    </div>
                    
                    <div class="section">
                        <h3 style="color: #1e293b; margin-bottom: 15px;">Need Assistance?</h3>
                        <p style="color: #475569; line-height: 1.6;">Our team is here to help you succeed. Feel free to reach out with any questions about using the platform, best practices for evidence organization, or guidance on accreditation processes.</p>
                        <p style="color: #475569;"><strong>Support:</strong> <a href="mailto:support@northpathstrategies.org" class="resource-link">support@northpathstrategies.org</a></p>
                    </div>
                    
                    <div class="section" style="background: #fef3c7; padding: 15px; border-radius: 6px; border-left: 4px solid #f59e0b;">
                        <p style="margin: 0; color: #92400e;"><strong>Your Trial Details:</strong> Your 7-day free trial gives you full access to all platform features. You can upgrade to a paid plan at any time to continue using MapMyStandards beyond your trial period.</p>
                    </div>
                </div>
                
                <div class="footer">
                    <p style="margin: 0 0 10px 0;"><strong>MapMyStandards</strong></p>
                    <p style="margin: 0;">AI-Powered Accreditation Management Platform</p>
                    <p style="margin: 10px 0 0 0; font-size: 12px;">
                        This email was sent to {user_email}. 
                        <a href="https://mapmystandards.ai/unsubscribe" style="color: #64748b;">Unsubscribe</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Welcome to MapMyStandards, {user_name}!
        
        Thank you for starting your 7-day free trial with our AI-powered accreditation management platform.
        
        YOUR PLATFORM INCLUDES:
        
        • AI-Powered Evidence Mapping - Advanced algorithms automatically map your documents to accreditation standards with 95% accuracy
        • Real-Time Compliance Dashboard - Monitor your accreditation readiness with live analytics and comprehensive reporting
        • Gap Analysis & Recommendations - Identify compliance gaps and receive actionable recommendations
        • Multi-Accreditor Support - Work with multiple accrediting bodies simultaneously
        
        GETTING STARTED - YOUR 4-STEP ONBOARDING:
        
        1. Complete Your Profile - Set up your institution details and select your primary accrediting body
        2. Upload Your First Documents - Begin with key documents like strategic plans or assessment reports
        3. Review AI Mappings - Examine how our system maps your evidence to standards
        4. Explore Your Dashboard - Familiarize yourself with compliance tracking and reporting tools
        
    Access your dashboard: https://platform.mapmystandards.ai/dashboard-modern.html
        
        HELPFUL RESOURCES:
        • Quick Start Guide: https://mapmystandards.ai/quick-start
        • Best Practices: https://mapmystandards.ai/best-practices
        • Video Tutorials: https://mapmystandards.ai/video-tutorials
        • Help Center: https://mapmystandards.ai/support
        
        Need assistance? Contact our support team at support@northpathstrategies.org
        
        Your 7-day trial gives you full access to all platform features. You can upgrade at any time to continue using MapMyStandards.
        
        Best regards,
        The MapMyStandards Team
        
        ---
        MapMyStandards - AI-Powered Accreditation Management Platform
        This email was sent to {user_email}
        """
        
        return self.send_email(
            to=user_email,
            subject="Welcome to MapMyStandards - Your Trial is Active!",
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

