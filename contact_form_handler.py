#!/usr/bin/env python3
"""
Simple contact form handler using Python and SMTP
This script handles contact form submissions and sends emails
"""

import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs


class ContactFormHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """Handle contact form submissions"""
        try:
            # Get the content length
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Parse the form data
            form_data = parse_qs(post_data.decode('utf-8'))

            # Extract form fields
            first_name = form_data.get('firstName', [''])[0]
            last_name = form_data.get('lastName', [''])[0]
            email = form_data.get('email', [''])[0]
            institution = form_data.get('institution', [''])[0]
            subject = form_data.get('subject', [''])[0]
            message = form_data.get('message', [''])[0]

            # Validate required fields
            if not all([first_name, last_name, email, subject, message]):
                self.send_error_response('Missing required fields')
                return

            # Send email
            success = self.send_email(first_name, last_name, email,
                                      institution, subject, message)

            if success:
                self.send_success_response()
            else:
                self.send_error_response('Failed to send email')

        except Exception as e:
            print(f"Error processing form: {e}")
            self.send_error_response('Server error')

    def send_email(self, first_name, last_name, email, institution,
                   subject, message):
        """Send email using SMTP"""
        try:
            # Email configuration
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_email = os.getenv('SMTP_EMAIL', 'support@mapmystandards.ai')
            smtp_password = os.getenv('SMTP_PASSWORD', '')

            if not smtp_password:
                print("SMTP_PASSWORD not set")
                return False

            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = 'support@mapmystandards.ai'
            msg['Subject'] = f"Contact Form: {subject}"

            # Create email body
            body = f"""
New contact form submission:

Name: {first_name} {last_name}
Email: {email}
Institution: {institution}
Subject: {subject}

Message:
{message}

Submitted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """

            msg.attach(MIMEText(body, 'plain'))

            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
            server.quit()

            print(f"Email sent successfully for {first_name} {last_name}")
            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def send_success_response(self):
        """Send success response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {'success': True, 'message': 'Message sent successfully'}
        self.wfile.write(json.dumps(response).encode())

    def send_error_response(self, error_message):
        """Send error response"""
        self.send_response(400)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = {'success': False, 'message': error_message}
        self.wfile.write(json.dumps(response).encode())


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    server = HTTPServer(('', port), ContactFormHandler)
    print(f"Contact form server running on port {port}")
    server.serve_forever()
