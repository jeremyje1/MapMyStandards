"""
Email notification system for MapMyStandards with SendGrid (primary) and MailerSend (backup)
"""

import os
from typing import Dict, Any
from datetime import datetime, timedelta

class EmailNotificationService:
    """Handles email notifications for MapMyStandards platform with dual provider support"""
    
    def __init__(self):
        # Load additional environment if available
        self._load_mailersend_config()
        
        # Configure SendGrid (primary)
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        
        # Configure MailerSend API (backup)
        self.mailersend_api_key = os.getenv('MAILERSEND_API_TOKEN')
        
        # Configure MailerSend SMTP (tertiary)
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.mailersend.net')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # Email settings
        self.from_email = os.getenv('EMAIL_FROM', 'support@mapmystandards.ai')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'MapMyStandards')
        self.admin_email = os.getenv('ADMIN_EMAIL', 'info@northpathstrategies.org')
        
        # Service priority
        self.primary_service = os.getenv('EMAIL_SERVICE_PRIMARY', 'sendgrid')
        self.backup_service = os.getenv('EMAIL_SERVICE_BACKUP', 'mailersend')
        self.tertiary_service = os.getenv('EMAIL_SERVICE_TERTIARY', 'smtp')
        
        # Check if we have working email configuration
        self.configured = bool(
            self.sendgrid_api_key or 
            self.mailersend_api_key or 
            (self.smtp_username and self.smtp_password)
        )
        
    def _load_mailersend_config(self):
        """Load MailerSend configuration from secure file if available"""
        try:
            if os.path.exists('mailersend_api.env'):
                with open('mailersend_api.env', 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.strip().split('=', 1)
                                os.environ[key] = value
        except Exception as e:
            print(f"Note: Could not load MailerSend config: {e}")
        
    def send_welcome_email(self, user_email: str, user_name: str, plan: str, api_key: str) -> bool:
        """Send welcome email to new subscribers"""
        try:
            subject = "Welcome to MapMyStandards - Your AI Accreditation Team is Ready!"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: white; padding: 30px; border: 1px solid #e5e7eb; }}
                    .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; color: #6b7280; }}
                    .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }}
                    .api-key {{ background: #f3f4f6; padding: 15px; border-radius: 6px; font-family: monospace; word-break: break-all; }}
                    .feature {{ margin: 15px 0; padding: 15px; background: #f0f9ff; border-left: 4px solid #0ea5e9; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎉 Welcome to MapMyStandards!</h1>
                        <p>Your AI Accreditation Analysis Team is Ready</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hi {user_name}!</h2>
                        
                        <p>Welcome to MapMyStandards! Your <strong>{plan}</strong> subscription is now active and your AI accreditation team is ready to help you excel.</p>
                        
                        <div class="feature">
                            <h3>🤖 Your A³E AI Engine Access</h3>
                            <p><strong>API Key:</strong></p>
                            <div class="api-key">{api_key}</div>
                        </div>
                        
                        <h3>🚀 What You Can Do Now:</h3>
                        <ul>
                            <li>✅ Upload accreditation documents for instant analysis</li>
                            <li>✅ Get comprehensive compliance reports across 5 major accreditation bodies</li>
                            <li>✅ Access real-time analytics and performance metrics</li>
                            <li>✅ Receive AI-powered compliance recommendations</li>
                            <li>✅ Track progress across 72+ accreditation standards</li>
                        </ul>
                        
                        <h3>🎯 Your Accreditation Coverage:</h3>
                        <ul>
                            <li><strong>SACSCOC</strong> - Southern Association of Colleges and Schools</li>
                            <li><strong>HLC</strong> - Higher Learning Commission</li>
                            <li><strong>COGNIA</strong> - Cognia Accreditation</li>
                            <li><strong>WASC</strong> - Western Association of Schools and Colleges</li>
                            <li><strong>NEASC</strong> - New England Association of Schools and Colleges</li>
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://platform.mapmystandards.ai" class="button">Access Your Dashboard</a>
                        </div>
                        
                        <p><strong>Need help getting started?</strong> Our support team is here to help you maximize your accreditation success.</p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 MapMyStandards.ai - AI-Powered Accreditation Excellence</p>
                        <p><a href="https://mapmystandards.ai/privacy">Privacy Policy</a> | <a href="https://mapmystandards.ai/terms">Terms of Service</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(user_email, subject, html_body)
            
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
            return False
    
    def send_trial_reminder(self, user_email: str, user_name: str, days_left: int) -> bool:
        """Send trial reminder email"""
        try:
            subject = f"MapMyStandards Trial - {days_left} Days Remaining"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: white; padding: 30px; border: 1px solid #e5e7eb; }}
                    .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; color: #6b7280; }}
                    .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }}
                    .urgency {{ background: #fef3c7; padding: 15px; border-radius: 6px; border-left: 4px solid #f59e0b; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>⏰ Trial Reminder</h1>
                        <p>Your MapMyStandards trial expires in {days_left} days</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hi {user_name}!</h2>
                        
                        <div class="urgency">
                            <h3>🚨 Action Required</h3>
                            <p>Your MapMyStandards trial will expire in <strong>{days_left} days</strong>. Don't lose access to your AI accreditation team!</p>
                        </div>
                        
                        <h3>What You'll Lose:</h3>
                        <ul>
                            <li>❌ Access to the A³E analysis engine</li>
                            <li>❌ Comprehensive compliance reports</li>
                            <li>❌ Real-time analytics dashboard</li>
                            <li>❌ AI-powered recommendations</li>
                            <li>❌ Multi-accreditor support</li>
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://mapmystandards.ai/pricing" class="button">Upgrade Now</a>
                        </div>
                        
                        <p><strong>Questions?</strong> Our team is here to help you choose the right plan for your institution.</p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 MapMyStandards.ai</p>
                        <p><a href="https://mapmystandards.ai/account">Manage Account</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(user_email, subject, html_body)
            
        except Exception as e:
            print(f"Failed to send trial reminder: {e}")
            return False
    
    def send_subscription_confirmation(self, user_email: str, user_name: str, plan: str, amount: float) -> bool:
        """Send subscription confirmation email"""
        try:
            subject = "MapMyStandards - Subscription Confirmed!"
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: white; padding: 30px; border: 1px solid #e5e7eb; }}
                    .footer {{ background: #f9fafb; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; color: #6b7280; }}
                    .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; }}
                    .confirmation {{ background: #d1fae5; padding: 15px; border-radius: 6px; border-left: 4px solid #10b981; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>✅ Subscription Confirmed!</h1>
                        <p>Welcome to the MapMyStandards family</p>
                    </div>
                    
                    <div class="content">
                        <h2>Thank you, {user_name}!</h2>
                        
                        <div class="confirmation">
                            <h3>🎉 Payment Successful</h3>
                            <p><strong>Plan:</strong> {plan}</p>
                            <p><strong>Amount:</strong> ${amount:.2f}/month</p>
                            <p><strong>Status:</strong> Active</p>
                            <p><strong>Next Billing:</strong> {(datetime.now() + timedelta(days=30)).strftime('%B %d, %Y')}</p>
                        </div>
                        
                        <h3>🚀 You Now Have Full Access To:</h3>
                        <ul>
                            <li>✅ Unlimited document analysis</li>
                            <li>✅ Complete AI accreditation pipeline</li>
                            <li>✅ Real-time compliance monitoring</li>
                            <li>✅ Advanced analytics dashboard</li>
                            <li>✅ Priority support</li>
                            <li>✅ API access and integrations</li>
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://platform.mapmystandards.ai" class="button">Access Your Dashboard</a>
                        </div>
                        
                        <p><strong>Need help getting started?</strong> Our team offers free onboarding sessions to ensure you get maximum value from MapMyStandards.</p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 MapMyStandards.ai</p>
                        <p>Manage your subscription: <a href="https://platform.mapmystandards.ai/account">Account Settings</a></p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            return self._send_email(user_email, subject, html_body)
            
        except Exception as e:
            print(f"Failed to send subscription confirmation: {e}")
            return False
    
    def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email using triple redundancy: SendGrid → MailerSend API → MailerSend SMTP"""
        try:
            if not self.configured:
                print("❌ Email service not configured - No methods available")
                return False
            
            # Try primary service first (SendGrid)
            if self.primary_service == 'sendgrid' and self.sendgrid_api_key:
                result = self._send_via_sendgrid(to_email, subject, html_body)
                if result:
                    return True
                print("⚠️ SendGrid failed, trying MailerSend API...")
            
            # Try backup service (MailerSend API)
            if self.backup_service == 'mailersend' and self.mailersend_api_key:
                result = self._send_via_mailersend(to_email, subject, html_body)
                if result:
                    return True
                print("⚠️ MailerSend API failed, trying SMTP...")
            
            # Try tertiary service (MailerSend SMTP)
            if self.tertiary_service == 'smtp' and self.smtp_username and self.smtp_password:
                result = self._send_via_smtp(to_email, subject, html_body)
                if result:
                    return True
                print("❌ All email services failed")
            
            return False
            
        except Exception as e:
            print(f"❌ Email service error: {e}")
            return False
    
    def _send_via_sendgrid(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via SendGrid"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            message = Mail(
                from_email=f"{self.from_name} <{self.from_email}>",
                to_emails=to_email,
                subject=subject,
                html_content=html_body
            )
            
            response = sg.send(message)
            
            if response.status_code in [200, 202]:
                print(f"✅ Email sent via SendGrid to {to_email} (Status: {response.status_code})")
                return True
            else:
                print(f"❌ SendGrid failed - Status: {response.status_code}")
                return False
            
        except ImportError:
            print("❌ SendGrid library not installed")
            return False
        except Exception as e:
            print(f"❌ SendGrid error: {e}")
            return False
    
    def _send_via_mailersend(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via MailerSend API"""
        try:
            import requests
            
            url = "https://api.mailersend.com/v1/email"
            
            headers = {
                "Authorization": f"Bearer {self.mailersend_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "from": {
                    "email": self.from_email,
                    "name": self.from_name
                },
                "to": [
                    {
                        "email": to_email
                    }
                ],
                "subject": subject,
                "html": html_body
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code in [200, 202]:
                print(f"✅ Email sent via MailerSend to {to_email} (Status: {response.status_code})")
                return True
            else:
                print(f"❌ MailerSend failed - Status: {response.status_code}, Response: {response.text}")
                return False
            
        except ImportError:
            print("❌ Requests library not available for MailerSend")
            return False
        except Exception as e:
            print(f"❌ MailerSend error: {e}")
            return False
    
    def _send_via_smtp(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via MailerSend SMTP (tertiary fallback)"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add plain text version for better compatibility
            plain_text = f"""
{subject}

This email was sent from MapMyStandards platform.
View in a web browser for the best experience.
"""
            text_part = MIMEText(plain_text, 'plain')
            msg.attach(text_part)
            
            # Add HTML content
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email using MailerSend SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.smtp_use_tls:
                server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent via MailerSend SMTP to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ MailerSend SMTP error: {e}")
            return False

# Initialize email service
email_service = EmailNotificationService()
