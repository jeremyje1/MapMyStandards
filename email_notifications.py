"""
Email notification system for A³E subscriptions and user management
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
from typing import Dict, Any

class EmailNotificationService:
    """Handles email notifications for A³E platform"""
    
    def __init__(self):
        # Configure with environment variables or fallback to defaults
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'support@mapmystandards.ai')
        
    def send_welcome_email(self, user_email: str, user_name: str, plan: str, api_key: str) -> bool:
        """Send welcome email to new subscribers"""
        try:
            subject = "Welcome to A³E - Your AI Accreditation Team is Ready!"
            
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
                        <h1>🎯 Welcome to A³E!</h1>
                        <p>Your AI Accreditation & Audit Engine is ready to transform your compliance process</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hello {user_name}!</h2>
                        
                        <p>Thank you for subscribing to the <strong>{plan}</strong> plan. Your A³E system is now active and ready to handle your accreditation needs.</p>
                        
                        <div class="feature">
                            <h3>🚀 Your Account Details</h3>
                            <p><strong>Plan:</strong> {plan}</p>
                            <p><strong>Email:</strong> {user_email}</p>
                            <p><strong>API Key:</strong></p>
                            <div class="api-key">{api_key}</div>
                            <p><small>Keep this API key secure - you'll need it to access the A³E engine programmatically.</small></p>
                        </div>
                        
                        <div class="feature">
                            <h3>🎓 What's Included</h3>
                            <ul>
                                <li>✅ Dual-mode support (Higher Education & K-12)</li>
                                <li>✅ 18+ accreditor standards (SACSCOC, HLC, Cognia, etc.)</li>
                                <li>✅ FERPA/COPPA compliant processing</li>
                                <li>✅ Multi-agent AI pipeline (Mapper, GapFinder, Narrator, Verifier)</li>
                                <li>✅ Real-time compliance dashboards</li>
                                <li>✅ Complete audit traceability</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://mapmystandards.ai/engine" class="button">Launch A³E Engine</a>
                            <a href="https://mapmystandards.ai/dashboard.html" class="button" style="background: #059669; margin-left: 10px;">View Dashboard</a>
                        </div>
                        
                        <div class="feature">
                            <h3>📞 Need Help?</h3>
                            <p>Our team is here to ensure your success:</p>
                            <ul>
                                <li>📧 <strong>Email Support:</strong> support@mapmystandards.ai</li>
                                <li>📚 <strong>Documentation:</strong> <a href="https://mapmystandards.ai/docs">Quick Start Guide</a></li>
                                <li>🎥 <strong>Training:</strong> <a href="https://mapmystandards.ai/training">Video Tutorials</a></li>
                            </ul>
                        </div>
                        
                        <p><strong>Pro Tip:</strong> Start with our sample documents to see A³E in action, then upload your own institutional evidence for comprehensive analysis.</p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 MapMyStandards.ai - Autonomous Accreditation & Audit Engine</p>
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
            subject = f"A³E Trial - {days_left} Days Remaining"
            
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
                        <p>Your A³E trial expires in {days_left} days</p>
                    </div>
                    
                    <div class="content">
                        <h2>Hi {user_name}!</h2>
                        
                        <div class="urgency">
                            <h3>🚨 Action Required</h3>
                            <p>Your A³E trial will expire in <strong>{days_left} days</strong>. Don't lose access to your AI accreditation team!</p>
                        </div>
                        
                        <h3>What You'll Lose:</h3>
                        <ul>
                            <li>❌ Access to the A³E analysis engine</li>
                            <li>❌ Your saved analysis sessions</li>
                            <li>❌ Compliance dashboard and reports</li>
                            <li>❌ API access and integrations</li>
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://mapmystandards.ai/checkout.html" class="button">Upgrade Now - Save 20%</a>
                        </div>
                        
                        <p>Use code <strong>TRIAL20</strong> at checkout for 20% off your first year!</p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 MapMyStandards.ai</p>
                        <p>Questions? Reply to this email or contact support@mapmystandards.ai</p>
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
            subject = "A³E Subscription Confirmed - Thank You!"
            
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
                        <p>Welcome to the A³E family</p>
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
                            <li>✅ Complete multi-agent AI pipeline</li>
                            <li>✅ Real-time compliance monitoring</li>
                            <li>✅ Priority support</li>
                            <li>✅ API access and integrations</li>
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="https://mapmystandards.ai/dashboard.html" class="button">Access Your Dashboard</a>
                        </div>
                        
                        <p><strong>Need help getting started?</strong> Our team offers free onboarding sessions to ensure you get maximum value from A³E.</p>
                    </div>
                    
                    <div class="footer">
                        <p>© 2025 MapMyStandards.ai</p>
                        <p>Manage your subscription: <a href="https://mapmystandards.ai/account">Account Settings</a></p>
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
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add HTML content
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            server.send_message(msg)
            server.quit()
            
            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False

# Initialize email service
email_service = EmailNotificationService()
