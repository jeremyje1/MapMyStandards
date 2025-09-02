"""
Professional Email Service for MapMyStandards
Provides email notifications for customer signups and admin alerts
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import requests

logger = logging.getLogger(__name__)


class ProfessionalEmailService:
    """Professional email service for customer and admin notifications"""
    
    def __init__(self):
        self.api_key = os.getenv('POSTMARK_SERVER_TOKEN') or os.getenv('POSTMARK_API_KEY')
        self.from_email = os.getenv('EMAIL_FROM', 'noreply@mapmystandards.ai')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'MapMyStandards')
        self.admin_email = os.getenv('ADMIN_NOTIFICATION_EMAIL', 'admin@mapmystandards.ai')
        self.api_url = "https://api.postmarkapp.com"
        
        if not self.api_key:
            logger.warning("Postmark API key not configured. Emails will be logged only.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Professional email service initialized")
    
    def _send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        tag: Optional[str] = None
    ) -> bool:
        """Send email via Postmark API"""
        
        if not self.enabled:
            logger.info(f"[MOCK EMAIL] To: {to} | Subject: {subject}")
            return True
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Postmark-Server-Token": self.api_key
        }
        
        payload = {
            "From": f"{self.from_name} <{self.from_email}>",
            "To": to,
            "Subject": subject,
            "HtmlBody": html_body,
            "TextBody": text_body or self._html_to_text(html_body),
            "Tag": tag or "general"
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/email",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Email sent to {to} (MessageID: {result.get('MessageID')})")
                return True
            else:
                logger.error(f"Postmark error {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        import re
        text = re.sub(r'<[^>]+>', '', html)
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
        text = text.replace('&lt;', '<').replace('&gt;', '>')
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def send_customer_welcome_email(
        self,
        email: str,
        name: str,
        institution: Optional[str] = None,
        trial_days: int = 14
    ) -> bool:
        """Send professional welcome email to new customer"""
        
        subject = "Welcome to MapMyStandards - Your Account is Active"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                }}
                .header {{
                    background-color: #1e40af;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    color: #ffffff;
                    font-size: 28px;
                    margin: 0;
                    font-weight: 300;
                    letter-spacing: 1px;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 20px;
                    color: #1e40af;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #1e40af;
                    color: #ffffff;
                    padding: 14px 28px;
                    text-decoration: none;
                    border-radius: 4px;
                    font-weight: 500;
                    margin: 20px 0;
                }}
                .features {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 25px 0;
                }}
                .feature-item {{
                    padding: 8px 0;
                    border-bottom: 1px solid #e9ecef;
                }}
                .feature-item:last-child {{
                    border-bottom: none;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 30px;
                    text-align: center;
                    font-size: 14px;
                    color: #6c757d;
                }}
                .footer a {{
                    color: #6c757d;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>MapMyStandards</h1>
                </div>
                
                <div class="content">
                    <div class="greeting">
                        Dear {name},
                    </div>
                    
                    <p>
                        Thank you for signing up for MapMyStandards. Your account has been successfully created and is now active.
                        {f' Your {trial_days}-day trial period has begun, giving you full access to all platform features.' if trial_days else ''}
                    </p>
                    
                    {f'''
                    <p>
                        <strong>Institution:</strong> {institution}<br>
                        <strong>Account Email:</strong> {email}
                    </p>
                    ''' if institution else ''}
                    
                    <div class="features">
                        <h3 style="margin-top: 0; color: #1e40af;">Your Account Includes:</h3>
                        <div class="feature-item">
                            <strong>Document Analysis:</strong> Upload and analyze compliance documents
                        </div>
                        <div class="feature-item">
                            <strong>Standards Mapping:</strong> Automatic mapping to accreditation standards
                        </div>
                        <div class="feature-item">
                            <strong>Compliance Reports:</strong> Generate comprehensive compliance reports
                        </div>
                        <div class="feature-item">
                            <strong>Gap Analysis:</strong> Identify areas needing attention
                        </div>
                        <div class="feature-item">
                            <strong>Progress Tracking:</strong> Monitor your accreditation readiness
                        </div>
                    </div>
                    
                    <p style="text-align: center;">
                        <a href="https://platform.mapmystandards.ai/dashboard" class="button">
                            Access Your Dashboard
                        </a>
                    </p>
                    
                    <h3 style="color: #1e40af; margin-top: 30px;">Getting Started</h3>
                    <ol style="color: #555555;">
                        <li>Log in to your dashboard using this email address</li>
                        <li>Complete your institution profile</li>
                        <li>Upload your first compliance document</li>
                        <li>Review the automated analysis and standards mapping</li>
                        <li>Generate your first compliance report</li>
                    </ol>
                    
                    <p style="margin-top: 30px;">
                        If you have any questions or need assistance, our support team is available at 
                        <a href="mailto:support@mapmystandards.ai" style="color: #1e40af;">support@mapmystandards.ai</a>.
                    </p>
                    
                    <p>
                        Best regards,<br>
                        The MapMyStandards Team
                    </p>
                </div>
                
                <div class="footer">
                    <p style="margin: 0;">
                        MapMyStandards - Accreditation Compliance Platform<br>
                        <a href="https://mapmystandards.ai">mapmystandards.ai</a> | 
                        <a href="mailto:support@mapmystandards.ai">Support</a> | 
                        <a href="https://mapmystandards.ai/privacy">Privacy Policy</a>
                    </p>
                    <p style="margin-top: 15px; font-size: 12px;">
                        You received this email because you signed up for MapMyStandards.
                        <a href="https://platform.mapmystandards.ai/unsubscribe">Unsubscribe</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(
            to=email,
            subject=subject,
            html_body=html_body,
            tag="welcome"
        )
    
    def send_admin_notification(
        self,
        customer_email: str,
        customer_name: str,
        institution: Optional[str] = None,
        signup_type: str = "trial",
        additional_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send professional notification to admin about new signup"""
        
        subject = f"New {signup_type.title()} Signup: {customer_name}"
        
        signup_time = datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                }}
                .header {{
                    background-color: #059669;
                    padding: 20px 30px;
                }}
                .header h1 {{
                    color: #ffffff;
                    font-size: 24px;
                    margin: 0;
                    font-weight: 400;
                }}
                .content {{
                    padding: 30px;
                }}
                .info-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .info-table td {{
                    padding: 10px;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .info-table td:first-child {{
                    font-weight: 600;
                    width: 150px;
                    color: #6b7280;
                }}
                .alert-box {{
                    background-color: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 20px 0;
                }}
                .action-buttons {{
                    margin: 25px 0;
                    text-align: center;
                }}
                .action-button {{
                    display: inline-block;
                    padding: 10px 20px;
                    margin: 0 10px;
                    background-color: #1e40af;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 4px;
                }}
                .footer {{
                    background-color: #f9fafb;
                    padding: 20px 30px;
                    text-align: center;
                    font-size: 13px;
                    color: #6b7280;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Customer Signup</h1>
                </div>
                
                <div class="content">
                    <p style="font-size: 16px;">
                        A new customer has signed up for MapMyStandards.
                    </p>
                    
                    <table class="info-table">
                        <tr>
                            <td>Name</td>
                            <td>{customer_name}</td>
                        </tr>
                        <tr>
                            <td>Email</td>
                            <td><a href="mailto:{customer_email}" style="color: #1e40af; text-decoration: none;">{customer_email}</a></td>
                        </tr>
                        <tr>
                            <td>Institution</td>
                            <td>{institution or 'Not provided'}</td>
                        </tr>
                        <tr>
                            <td>Signup Type</td>
                            <td>{signup_type.upper()}</td>
                        </tr>
                        <tr>
                            <td>Signup Time</td>
                            <td>{signup_time}</td>
                        </tr>
                        {self._format_additional_info(additional_info)}
                    </table>
                    
                    <div class="alert-box">
                        <strong>Recommended Actions:</strong>
                        <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                            <li>Review customer profile for completeness</li>
                            <li>Monitor initial platform usage</li>
                            <li>Schedule follow-up for day 3 of trial</li>
                            <li>Prepare personalized onboarding if high-value prospect</li>
                        </ul>
                    </div>
                    
                    <div class="action-buttons">
                        <a href="https://platform.mapmystandards.ai/admin/users" class="action-button">
                            View in Admin Panel
                        </a>
                        <a href="mailto:{customer_email}" class="action-button" style="background-color: #059669;">
                            Contact Customer
                        </a>
                    </div>
                    
                    <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 14px; color: #6b7280;">
                        <strong>Note:</strong> This is an automated notification. The customer has received a welcome email with 
                        instructions for accessing their account.
                    </p>
                </div>
                
                <div class="footer">
                    <p style="margin: 0;">
                        MapMyStandards Admin Notification System<br>
                        This is an automated message - do not reply directly to this email
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
            tag="admin-notification"
        )
    
    def _format_additional_info(self, info: Optional[Dict[str, Any]]) -> str:
        """Format additional information for admin email"""
        if not info:
            return ""
        
        rows = []
        for key, value in info.items():
            formatted_key = key.replace('_', ' ').title()
            rows.append(f"<tr><td>{formatted_key}</td><td>{value}</td></tr>")
        
        return "".join(rows)


# Global instance
email_service = ProfessionalEmailService()