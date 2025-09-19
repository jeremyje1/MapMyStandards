"""
Postmark Email Service for MapMyStandards.ai

Provides email sending capabilities using the Postmark API with comprehensive
templates for customer and admin notifications.
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PostmarkConfig(BaseModel):
    """Postmark configuration settings"""
    api_key: str
    from_email: str = "support@mapmystandards.ai"
    from_name: str = "MapMyStandards A³E"
    admin_email: str = "admin@mapmystandards.ai"
    api_url: str = "https://api.postmarkapp.com"


class PostmarkEmailService:
    """Postmark-based email service for A³E platform"""
    
    def __init__(self):
        self.api_key = os.getenv('POSTMARK_SERVER_TOKEN') or os.getenv('POSTMARK_API_KEY')
        self.from_email = os.getenv('EMAIL_FROM', 'support@mapmystandards.ai')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'MapMyStandards A³E')
        self.admin_email = os.getenv('ADMIN_NOTIFICATION_EMAIL', 'info@northpathstrategies.org')
        self.api_url = "https://api.postmarkapp.com"
        self.reply_to = os.getenv('EMAIL_REPLY_TO', os.getenv('ADMIN_NOTIFICATION_EMAIL', 'info@northpathstrategies.org'))
        self.message_stream = os.getenv('POSTMARK_MESSAGE_STREAM', 'outbound')
        
        if not self.api_key:
            logger.warning("No Postmark API key found. Email notifications will be logged only.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Postmark email service initialized successfully")
    
    def _send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        tag: Optional[str] = None,
        template_id: Optional[str] = None,
        template_model: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send email via Postmark API
        
        Args:
            to: Recipient email address
            subject: Email subject
            html_body: HTML email content
            text_body: Plain text email content
            tag: Email tag for tracking
            template_id: Postmark template ID (if using template)
            template_model: Template variables (if using template)
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            logger.info(f"📧 [MOCK] Email to {to}: {subject}")
            logger.debug(f"HTML Body: {html_body}")
            return True
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.api_key
        }
        
        if template_id and template_model:
            # Use template-based email
            payload = {
                "From": f"{self.from_name} <{self.from_email}>",
                "To": to,
                "TemplateId": template_id,
                "TemplateModel": template_model,
                "Tag": tag or "general"
            }
            endpoint = f"{self.api_url}/email/withTemplate"
        else:
            # Use content-based email
            payload = {
                "From": f"{self.from_name} <{self.from_email}>",
                "To": to,
                "Subject": subject,
                "HtmlBody": html_body,
                "TextBody": text_body or self._html_to_text(html_body),
                "Tag": tag or "general"
            }
            endpoint = f"{self.api_url}/email"

        # Optional headers
        if self.reply_to:
            payload["ReplyTo"] = self.reply_to
        if self.message_stream:
            payload["MessageStream"] = self.message_stream
        
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Email sent successfully to {to} (MessageID: {result.get('MessageID')})")
                return True
            else:
                error_data = response.json() if response.content else {}
                logger.error(f"❌ Postmark API error {response.status_code}: {error_data}")
                # Retry logic: try removing MessageStream, then fallback From
                try:
                    # Retry without MessageStream
                    payload.pop("MessageStream", None)
                    response2 = requests.post(endpoint, headers=headers, json=payload, timeout=10)
                    if response2.status_code == 200:
                        result2 = response2.json()
                        logger.info(f"✅ Email sent to {to} after removing MessageStream (MessageID: {result2.get('MessageID')})")
                        return True
                except Exception as re1:
                    logger.warning(f"Postmark retry without MessageStream failed: {re1}")

                try:
                    # Retry with fallback From
                    fallback_from = os.getenv('EMAIL_FROM_FALLBACK', 'support@mapmystandards.ai')
                    if fallback_from and (self.from_email != fallback_from):
                        payload["From"] = f"{self.from_name} <{fallback_from}>"
                        response3 = requests.post(endpoint, headers=headers, json=payload, timeout=10)
                        if response3.status_code == 200:
                            result3 = response3.json()
                            logger.info(f"✅ Email sent to {to} using fallback From (MessageID: {result3.get('MessageID')})")
                            return True
                except Exception as re2:
                    logger.warning(f"Postmark retry with fallback From failed: {re2}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to send email via Postmark: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {e}")
            return False
    
    def _html_to_text(self, html: str) -> str:
        """Simple HTML to text conversion"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Replace HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def send_welcome_email(self, user_email: str, user_name: str, api_key: Optional[str] = None) -> bool:
        """Send welcome email to new trial users"""
        subject = "🎯 Welcome to MapMyStandards A³E - Your Trial is Ready!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Welcome to MapMyStandards A³E</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f8fafc;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 2rem; text-align: center;">
                    <h1 style="color: #ffffff; font-size: 28px; font-weight: 800; margin: 0; display: flex; align-items: center; justify-content: center; gap: 10px;">
                        🎯 MapMyStandards A³E
                    </h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Autonomous Accreditation & Audit Engine</p>
                </div>
                
                <!-- Main Content -->
                <div style="padding: 2rem;">
                    <h2 style="color: #1e40af; font-size: 24px; font-weight: 700; margin: 0 0 20px 0;">
                        Welcome aboard, {user_name}! 🚀
                    </h2>
                    
                    <p style="color: #374151; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                        Your <strong>14-day free trial</strong> is now active and ready to transform your accreditation process. 
                        No credit card required!
                    </p>
                    
                    <!-- Key Features -->
                    <div style="background: #f0f9ff; border-left: 4px solid #10b981; padding: 20px; margin: 20px 0; border-radius: 6px;">
                        <h3 style="color: #1e40af; font-size: 18px; font-weight: 600; margin: 0 0 15px 0;">What you can do right now:</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #374151;">
                            <li style="margin-bottom: 8px;">📤 <strong>Upload Documents:</strong> Start with policies, handbooks, or evidence files</li>
                            <li style="margin-bottom: 8px;">🔍 <strong>AI Analysis:</strong> Get instant standards mapping and compliance insights</li>
                            <li style="margin-bottom: 8px;">📊 <strong>Generate Reports:</strong> Create professional compliance reports</li>
                            <li style="margin-bottom: 8px;">📈 <strong>Track Progress:</strong> Monitor your accreditation readiness in real-time</li>
                        </ul>
                    </div>
                    
                    <!-- CTA Button -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://platform.mapmystandards.ai/dashboard-modern" 
                           style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #34d399 100%); color: #ffffff; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            🎯 Access Your Dashboard
                        </a>
                    </div>
                    
                    {f'''
                    <!-- API Key Section -->
                    <div style="background: #f9fafb; border: 1px solid #e5e7eb; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="color: #374151; font-size: 16px; font-weight: 600; margin: 0 0 10px 0;">🔑 Your API Key</h4>
                        <p style="color: #6b7280; font-size: 14px; margin: 0 0 10px 0;">For developers and advanced integrations:</p>
                        <code style="background: #1f2937; color: #10b981; padding: 8px 12px; border-radius: 4px; font-size: 14px; display: block; font-family: 'Monaco', 'Menlo', monospace; word-break: break-all;">
                            {api_key}
                        </code>
                        <p style="color: #6b7280; font-size: 12px; margin: 10px 0 0 0;">Keep this secure - treat it like a password!</p>
                    </div>
                    ''' if api_key else ''}
                    
                    <!-- Next Steps -->
                    <h3 style="color: #1e40af; font-size: 18px; font-weight: 600; margin: 30px 0 15px 0;">Quick Start Guide:</h3>
                    <ol style="color: #374151; padding-left: 20px; line-height: 1.6;">
                        <li style="margin-bottom: 8px;"><strong>Log in</strong> to your dashboard using this email address</li>
                        <li style="margin-bottom: 8px;"><strong>Upload</strong> your first document (policy, handbook, etc.)</li>
                        <li style="margin-bottom: 8px;"><strong>Review</strong> the AI-generated standards mapping</li>
                        <li style="margin-bottom: 8px;"><strong>Generate</strong> your first compliance report</li>
                    </ol>
                    
                    <!-- Support -->
                    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 30px 0; border-radius: 6px;">
                        <h4 style="color: #92400e; font-size: 16px; font-weight: 600; margin: 0 0 10px 0;">🤝 Need Help?</h4>
                        <p style="color: #92400e; font-size: 14px; margin: 0;">
                            Our team is here to help! Email us at 
                            <a href="mailto:support@mapmystandards.ai" style="color: #92400e; font-weight: 600;">support@mapmystandards.ai</a> 
                            or reply to this email.
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #f3f4f6; padding: 2rem; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 14px; margin: 0 0 10px 0;">
                        Ready to transform your accreditation process?
                    </p>
                    <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                        MapMyStandards A³E | 
                        <a href="mailto:support@mapmystandards.ai" style="color: #9ca3af;">Support</a> | 
                        <a href="https://platform.mapmystandards.ai/unsubscribe" style="color: #9ca3af;">Unsubscribe</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to=user_email,
            subject=subject,
            html_body=html_body,
            tag="welcome"
        )
    
    def send_admin_signup_notification(
        self, 
        email: str, 
        name: str, 
        institution: Optional[str] = None,
        role: Optional[str] = None,
        trial: bool = True,
        milestone_type: Optional[str] = None,
        additional_info: Optional[str] = None
    ) -> bool:
        """Send admin notification about new signup or milestone"""
        
        # Determine notification type and subject
        if milestone_type == "report_generated":
            subject = f"📊 Report Generated: {name}"
            notification_title = "Report Generated"
            notification_icon = "📊"
            notification_description = f"User generated a new report"
        elif milestone_type == "analysis_complete":
            subject = f"🔍 Analysis Complete: {name}"
            notification_title = "Analysis Complete"
            notification_icon = "🔍"
            notification_description = f"Document analysis completed"
        else:
            subject = f"🎯 New {'Trial ' if trial else ''}Signup: {name}"
            notification_title = f"New {'Trial ' if trial else ''}Signup Alert"
            notification_icon = "📈"
            notification_description = "New user signed up!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>New Signup Notification</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f8fafc;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #10b981 0%, #34d399 100%); padding: 2rem; text-align: center;">
                    <h1 style="color: #ffffff; font-size: 24px; font-weight: 800; margin: 0;">
                        {notification_icon} {notification_title}
                    </h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">MapMyStandards A³E Platform</p>
                </div>
                
                <!-- Main Content -->
                <div style="padding: 2rem;">
                    <h2 style="color: #1e40af; font-size: 20px; font-weight: 700; margin: 0 0 20px 0;">
                        {notification_description} 🎉
                    </h2>
                    
                    <!-- User Details -->
                    <div style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #374151; width: 140px;">👤 Name:</td>
                                <td style="padding: 8px 0; color: #1f2937;">{name}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #374151;">📧 Email:</td>
                                <td style="padding: 8px 0;">
                                    <a href="mailto:{email}" style="color: #1e40af; text-decoration: none; font-weight: 500;">{email}</a>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #374151;">🏛️ Institution:</td>
                                <td style="padding: 8px 0; color: #1f2937;">{institution or '(Not provided)'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #374151;">💼 Role:</td>
                                <td style="padding: 8px 0; color: #1f2937;">{role or '(Not provided)'}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #374151;">🆓 Trial:</td>
                                <td style="padding: 8px 0;">
                                    <span style="background: {'#d1fae5' if trial else '#fee2e2'}; color: {'#065f46' if trial else '#991b1b'}; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600;">
                                        {'✅ YES' if trial else '❌ NO'}
                                    </span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #374151;">⏰ {"Signed up:" if not milestone_type else "Activity:"}</td>
                                <td style="padding: 8px 0; color: #1f2937;">{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</td>
                            </tr>
                            {f'''
                            <tr>
                                <td style="padding: 8px 0; font-weight: 600; color: #374151;">ℹ️ Details:</td>
                                <td style="padding: 8px 0; color: #1f2937;">{additional_info}</td>
                            </tr>
                            ''' if additional_info else ''}
                        </table>
                    </div>
                    
                    <!-- Action Items -->
                    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 20px 0; border-radius: 6px;">
                        <h3 style="color: #92400e; font-size: 16px; font-weight: 600; margin: 0 0 10px 0;">📋 Recommended Actions:</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #92400e;">
                            {f'''
                            <li style="margin-bottom: 5px;">Review generated report for quality</li>
                            <li style="margin-bottom: 5px;">Follow up on user satisfaction</li>
                            <li style="margin-bottom: 5px;">Consider converting trial to paid plan</li>
                            ''' if milestone_type == "report_generated" else f'''
                            <li style="margin-bottom: 5px;">Check analysis results quality</li>
                            <li style="margin-bottom: 5px;">Ensure user received results</li>
                            <li style="margin-bottom: 5px;">Monitor for next user action</li>
                            ''' if milestone_type == "analysis_complete" else f'''
                            <li style="margin-bottom: 5px;">Monitor trial usage and engagement</li>
                            <li style="margin-bottom: 5px;">Send personalized onboarding if high-value prospect</li>
                            <li style="margin-bottom: 5px;">Add to nurture email sequence</li>
                            '''}
                        </ul>
                    </div>
                    
                    <!-- Quick Actions -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="https://platform.mapmystandards.ai/admin/users" 
                           style="display: inline-block; background: #1e40af; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px; margin-right: 10px;">
                            👥 View in Admin Panel
                        </a>
                        <a href="mailto:{email}" 
                           style="display: inline-block; background: #10b981; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px;">
                            📧 Contact User
                        </a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #f3f4f6; padding: 1.5rem; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 12px; margin: 0;">
                        Automated notification from MapMyStandards A³E Platform
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to=self.admin_email,
            subject=subject,
            html_body=html_body,
            tag="admin-signup"
        )
    
    def send_assessment_complete_notification(
        self,
        user_email: str,
        user_name: str,
        assessment_type: str,  # "upload_analysis", "report_generated", "standards_mapped"
        document_name: Optional[str] = None,
        standards_mapped: Optional[int] = None,
        compliance_score: Optional[float] = None,
        report_url: Optional[str] = None
    ) -> bool:
        """Send notification when assessment milestone is completed"""
        
        # Customer notification
        customer_subject = f"🎯 Your {assessment_type.replace('_', ' ').title()} is Complete!"
        
        milestone_details = {
            "upload_analysis": {
                "icon": "📤",
                "title": "Document Analysis Complete",
                "description": f"We've finished analyzing your document: <strong>{document_name or 'Unknown Document'}</strong>",
                "action_text": "View Analysis Results",
                "action_url": "https://platform.mapmystandards.ai/dashboard-modern"
            },
            "report_generated": {
                "icon": "📊", 
                "title": "Compliance Report Generated",
                "description": f"Your comprehensive compliance report is ready for download.",
                "action_text": "Download Report",
                "action_url": report_url or "https://platform.mapmystandards.ai/reports-modern"
            },
            "standards_mapped": {
                "icon": "🗺️",
                "title": "Standards Mapping Complete", 
                "description": f"We've mapped {standards_mapped or 0} standards to your institutional evidence.",
                "action_text": "View Standards Mapping",
                "action_url": "https://platform.mapmystandards.ai/dashboard-modern#standards"
            }
        }
        
        milestone = milestone_details.get(assessment_type, milestone_details["upload_analysis"])
        
        customer_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Assessment Complete</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f8fafc;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff;">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #10b981 0%, #34d399 100%); padding: 2rem; text-align: center;">
                    <h1 style="color: #ffffff; font-size: 28px; font-weight: 800; margin: 0;">
                        {milestone['icon']} Great Progress, {user_name}!
                    </h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">MapMyStandards A³E</p>
                </div>
                
                <!-- Main Content -->
                <div style="padding: 2rem;">
                    <h2 style="color: #1e40af; font-size: 24px; font-weight: 700; margin: 0 0 20px 0;">
                        {milestone['title']} ✅
                    </h2>
                    
                    <p style="color: #374151; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                        {milestone['description']}
                    </p>
                    
                    {f'''
                    <!-- Results Summary -->
                    <div style="background: #f0f9ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <h3 style="color: #1e40af; font-size: 18px; font-weight: 600; margin: 0 0 15px 0;">📊 Key Results:</h3>
                        <ul style="margin: 0; padding-left: 20px; color: #374151; line-height: 1.6;">
                            {f"<li><strong>Standards Mapped:</strong> {standards_mapped}</li>" if standards_mapped else ""}
                            {f"<li><strong>Compliance Score:</strong> {compliance_score:.1f}%</li>" if compliance_score else ""}
                            {f"<li><strong>Document:</strong> {document_name}</li>" if document_name else ""}
                        </ul>
                    </div>
                    ''' if any([standards_mapped, compliance_score, document_name]) else ''}
                    
                    <!-- CTA Button -->
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{milestone['action_url']}" 
                           style="display: inline-block; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: #ffffff; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            {milestone['action_text']} →
                        </a>
                    </div>
                    
                    <!-- Next Steps -->
                    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 30px 0; border-radius: 6px;">
                        <h4 style="color: #92400e; font-size: 16px; font-weight: 600; margin: 0 0 10px 0;">🎯 What's Next?</h4>
                        <p style="color: #92400e; font-size: 14px; margin: 0;">
                            Continue building your compliance portfolio by uploading more documents or generating additional reports. 
                            Your accreditation readiness improves with each analysis!
                        </p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div style="background: #f3f4f6; padding: 2rem; text-align: center; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 14px; margin: 0 0 10px 0;">
                        Questions? We're here to help!
                    </p>
                    <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                        MapMyStandards A³E | 
                        <a href="mailto:support@mapmystandards.ai" style="color: #9ca3af;">Support</a> | 
                        <a href="https://platform.mapmystandards.ai/unsubscribe" style="color: #9ca3af;">Unsubscribe</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send customer notification
        customer_success = self._send_email(
            to=user_email,
            subject=customer_subject,
            html_body=customer_html,
            tag="assessment-complete"
        )
        
        # Admin notification
        admin_subject = f"📊 Assessment Complete: {user_name} - {assessment_type.replace('_', ' ').title()}"
        
        admin_html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #1e40af; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">📊 Assessment Milestone Reached</h1>
            </div>
            
            <div style="padding: 20px;">
                <h2 style="color: #1e40af;">User Activity Alert</h2>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr><td style="font-weight: 600; padding: 8px 0;">User:</td><td>{user_name} ({user_email})</td></tr>
                    <tr><td style="font-weight: 600; padding: 8px 0;">Milestone:</td><td>{milestone['title']}</td></tr>
                    <tr><td style="font-weight: 600; padding: 8px 0;">Document:</td><td>{document_name or 'N/A'}</td></tr>
                    <tr><td style="font-weight: 600; padding: 8px 0;">Standards Mapped:</td><td>{standards_mapped or 'N/A'}</td></tr>
                    <tr><td style="font-weight: 600; padding: 8px 0;">Compliance Score:</td><td>{f'{compliance_score:.1f}%' if compliance_score else 'N/A'}</td></tr>
                    <tr><td style="font-weight: 600; padding: 8px 0;">Timestamp:</td><td>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</td></tr>
                </table>
                
                <div style="background: #f0f9ff; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <strong>💡 Engagement Opportunity:</strong><br>
                    This user is actively using the platform. Consider reaching out with personalized support or upgrade suggestions.
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send admin notification
        admin_success = self._send_email(
            to=self.admin_email,
            subject=admin_subject,
            html_body=admin_html,
            tag="admin-milestone"
        )
        
        return customer_success and admin_success


# Global service instance
postmark_service = PostmarkEmailService()
