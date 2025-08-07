#!/usr/bin/env python3
"""
MapMyStandards Backend API with Stripe Subscriptions and User Management
Handles trials, payments, user accounts, and webhooks
"""

import os
import sqlite3
import hashlib
import secrets
import stripe
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
from flask_cors import CORS
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
CORS(app)

# Load environment variables
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
MONTHLY_PRICE_ID = os.getenv('MONTHLY_PRICE_ID', 'price_1RtXF3K8PKpLCKDZJNfi3Rvi')
ANNUAL_PRICE_ID = os.getenv('ANNUAL_PRICE_ID', 'price_1RtXF3K8PKpLCKDZAMb4rM8U')

stripe.api_key = STRIPE_SECRET_KEY

# Database setup
def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect('mapmystandards.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            institution TEXT,
            username TEXT UNIQUE,
            is_active BOOLEAN DEFAULT FALSE,
            trial_status TEXT DEFAULT 'pending',
            stripe_customer_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            stripe_subscription_id TEXT UNIQUE,
            status TEXT,
            current_period_start TIMESTAMP,
            current_period_end TIMESTAMP,
            trial_start TIMESTAMP,
            trial_end TIMESTAMP,
            plan_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # API keys table (for platform access)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            api_key TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_trial_id():
    """Generate a unique trial ID"""
    return f"trial_{secrets.token_urlsafe(12)}"

def generate_api_key():
    """Generate a unique API key"""
    return f"a3e_{secrets.token_urlsafe(32)}"

def send_email(to_email, subject, body):
    """Send email notification"""
    try:
        # Configure your SMTP settings here
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_email = "support@mapmystandards.ai"  # Replace with your email
        smtp_password = "your_app_password"  # Replace with your app password
        
        msg = MIMEMultipart()
        msg['From'] = smtp_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_email, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

@app.route('/')
def home():
    """Home page"""
    return redirect('https://platform.mapmystandards.ai')

@app.route('/create-trial-account', methods=['POST'])
def create_trial_account():
    """Create user account and Stripe checkout session for trial"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'email', 'institution', 'username', 'password', 'plan']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate email format
        if '@' not in data['email']:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password length
        if len(data['password']) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Get price ID based on plan
        price_id = MONTHLY_PRICE_ID if data['plan'] == 'monthly' else ANNUAL_PRICE_ID
        
        conn = sqlite3.connect('mapmystandards.db')
        cursor = conn.cursor()
        
        # Check if email or username already exists
        cursor.execute('SELECT id FROM users WHERE email = ? OR username = ?', 
                      (data['email'], data['username']))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Email or username already exists'}), 400
        
        # Create user account (initially inactive until trial starts)
        password_hash = hash_password(data['password'])
        
        cursor.execute('''
            INSERT INTO users (email, password_hash, first_name, last_name, 
                             institution, username, is_active, trial_status)
            VALUES (?, ?, ?, ?, ?, ?, FALSE, 'pending')
        ''', (data['email'], password_hash, data['firstName'], data['lastName'], 
              data['institution'], data['username']))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=data['email'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{request.host_url}trial-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{request.host_url}signup?cancelled=true",
            metadata={
                'user_id': str(user_id),
                'plan_type': data['plan'],
                'username': data['username']
            },
            subscription_data={
                'trial_period_days': 7,
                'metadata': {
                    'user_id': str(user_id),
                    'username': data['username']
                }
            }
        )
        
        return jsonify({
            'success': True,
            'checkout_url': checkout_session.url,
            'user_id': user_id
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create_trial_account: {e}")
        return jsonify({'error': 'Payment system error. Please try again.'}), 500
    except Exception as e:
        logger.error(f"Error in create_trial_account: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    try:
        data = request.get_json()
        price_id = data.get('price_id')
        email = data.get('email')
        
        if not price_id or not email:
            return jsonify({'error': 'Missing price_id or email'}), 400
        
        # Create or get customer
        customer = stripe.Customer.create(
            email=email,
            metadata={'platform': 'mapmystandards'}
        )
        
        # Create checkout session with trial
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer=customer.id,
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://platform.mapmystandards.ai/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://platform.mapmystandards.ai/pricing?canceled=true',
            subscription_data={
                'trial_period_days': 7,
                'metadata': {
                    'platform': 'mapmystandards',
                    'email': email
                }
            },
            metadata={
                'platform': 'mapmystandards',
                'email': email
            }
        )
        
        return jsonify({'checkout_url': checkout_session.url})
        
    except Exception as e:
        logger.error(f"Checkout session error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = "whsec_YOUR_WEBHOOK_SECRET"  # You'll need to set this up
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        logger.error("Invalid payload")
        return '', 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        return '', 400
    
    # Handle the event
    if event['type'] == 'customer.subscription.created':
        # Trial started
        subscription = event['data']['object']
        handle_trial_started(subscription)
    
    elif event['type'] == 'customer.subscription.trial_will_end':
        # Trial ending soon (3 days before)
        subscription = event['data']['object']
        handle_trial_ending_soon(subscription)
    
    elif event['type'] == 'invoice.payment_succeeded':
        # Payment succeeded (trial converted or regular billing)
        invoice = event['data']['object']
        if invoice['billing_reason'] == 'subscription_cycle':
            handle_subscription_payment(invoice)
    
    elif event['type'] == 'customer.subscription.deleted':
        # Subscription canceled
        subscription = event['data']['object']
        handle_subscription_canceled(subscription)
    
    return '', 200

def handle_trial_started(subscription):
    """Handle when a trial starts"""
    try:
        customer_id = subscription['customer']
        customer = stripe.Customer.retrieve(customer_id)
        email = customer['email']
        
        # Create user account
        conn = sqlite3.connect('mapmystandards.db')
        cursor = conn.cursor()
        
        # Generate trial ID and API key
        trial_id = generate_trial_id()
        api_key = generate_api_key()
        
        # Create user
        cursor.execute('''
            INSERT OR IGNORE INTO users (email, password_hash, stripe_customer_id, trial_id)
            VALUES (?, ?, ?, ?)
        ''', (email, hash_password(secrets.token_urlsafe(16)), customer_id, trial_id))
        
        user_id = cursor.lastrowid or cursor.execute(
            'SELECT id FROM users WHERE email = ?', (email,)
        ).fetchone()[0]
        
        # Create subscription record
        trial_start = datetime.fromtimestamp(subscription['trial_start'])
        trial_end = datetime.fromtimestamp(subscription['trial_end'])
        
        cursor.execute('''
            INSERT INTO subscriptions 
            (user_id, stripe_subscription_id, status, trial_start, trial_end, plan_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, subscription['id'], 'trialing', trial_start, trial_end, 'monthly'))
        
        # Create API key
        cursor.execute('''
            INSERT INTO api_keys (user_id, api_key)
            VALUES (?, ?)
        ''', (user_id, api_key))
        
        conn.commit()
        conn.close()
        
        # Send welcome email
        send_trial_welcome_email(email, trial_id, api_key)
        
        logger.info(f"Trial started for {email}")
        
    except Exception as e:
        logger.error(f"Error handling trial start: {e}")

def send_trial_welcome_email(email, trial_id, api_key):
    """Send welcome email with trial access"""
    subject = "🎉 Your A³E Platform 7-Day Trial Has Started!"
    
    body = f"""
    <html>
    <body>
        <h2>Welcome to MapMyStandards A³E Platform!</h2>
        
        <p>Your 7-day free trial has officially started. Here's everything you need to get started:</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🔑 Your Access Credentials:</h3>
            <p><strong>Trial ID:</strong> {trial_id}</p>
            <p><strong>API Key:</strong> {api_key}</p>
            <p><strong>Login URL:</strong> https://platform.mapmystandards.ai/login</p>
        </div>
        
        <h3>🚀 Getting Started:</h3>
        <ol>
            <li>Visit the <a href="https://platform.mapmystandards.ai/login">login page</a></li>
            <li>Enter your Trial ID: <code>{trial_id}</code></li>
            <li>Start exploring the A³E platform features</li>
        </ol>
        
        <h3>📋 Your Trial Details:</h3>
        <ul>
            <li><strong>Trial Period:</strong> 7 days (ends automatically)</li>
            <li><strong>Full Access:</strong> All A³E platform features included</li>
            <li><strong>No Charges:</strong> Completely free for 7 days</li>
            <li><strong>Auto-billing:</strong> $49.99/month after trial (cancel anytime)</li>
        </ul>
        
        <h3>🛟 Need Help?</h3>
        <p>Contact our support team: <a href="mailto:support@mapmystandards.ai">support@mapmystandards.ai</a></p>
        
        <p>Thank you for choosing MapMyStandards!</p>
        
        <p><em>The MapMyStandards Team</em></p>
    </body>
    </html>
    """
    
    send_email(email, subject, body)

def handle_trial_ending_soon(subscription):
    """Handle trial ending notification"""
    customer_id = subscription['customer']
    customer = stripe.Customer.retrieve(customer_id)
    email = customer['email']
    
    subject = "⏰ Your A³E Trial Ends in 3 Days"
    body = f"""
    <html>
    <body>
        <h2>Your trial is ending soon!</h2>
        <p>Your 7-day trial of the A³E Platform ends in 3 days.</p>
        <p>If you'd like to continue, no action is needed - your subscription will automatically begin.</p>
        <p>To cancel, visit your <a href="https://platform.mapmystandards.ai/account">account page</a>.</p>
    </body>
    </html>
    """
    
    send_email(email, subject, body)

def handle_subscription_payment(invoice):
    """Handle successful subscription payment"""
    # Update subscription status in database
    pass

def handle_subscription_canceled(subscription):
    """Handle subscription cancellation"""
    # Deactivate user account
    pass

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        logger.error("Invalid payload in webhook")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return jsonify({'error': 'Invalid signature'}), 400
    
    try:
        # Handle the event
        if event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            handle_subscription_created(subscription)
            
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            handle_payment_succeeded(invoice)
            
        elif event['type'] == 'customer.subscription.trial_will_end':
            subscription = event['data']['object']
            handle_trial_ending(subscription)
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            handle_subscription_cancelled(subscription)
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({'error': 'Webhook handling failed'}), 500

def handle_subscription_created(subscription):
    """Handle new subscription creation (trial started)"""
    user_id = subscription['metadata'].get('user_id')
    if not user_id:
        logger.error("No user_id in subscription metadata")
        return
    
    conn = sqlite3.connect('mapmystandards.db')
    cursor = conn.cursor()
    
    try:
        # Update user status to active trial
        cursor.execute('''
            UPDATE users 
            SET is_active = TRUE, trial_status = 'active', stripe_customer_id = ?
            WHERE id = ?
        ''', (subscription['customer'], user_id))
        
        # Create subscription record
        trial_end = datetime.fromtimestamp(subscription['trial_end']) if subscription['trial_end'] else None
        
        cursor.execute('''
            INSERT INTO subscriptions 
            (user_id, stripe_subscription_id, stripe_customer_id, status, trial_end, plan_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, subscription['id'], subscription['customer'], 
              subscription['status'], trial_end, subscription['metadata'].get('plan_type', 'monthly')))
        
        # Generate API key for platform access
        api_key = generate_api_key()
        cursor.execute('''
            INSERT INTO api_keys (user_id, api_key)
            VALUES (?, ?)
        ''', (user_id, api_key))
        
        conn.commit()
        
        # Get user details for welcome email
        cursor.execute('SELECT email, first_name, username FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user:
            send_trial_welcome_email_updated(user[0], user[1], user[2], api_key)
        
    finally:
        conn.close()

def handle_payment_succeeded(invoice):
    """Handle successful payment (trial converted or renewal)"""
    subscription_id = invoice['subscription']
    
    conn = sqlite3.connect('mapmystandards.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE subscriptions 
            SET status = 'active', trial_status = 'converted'
            WHERE stripe_subscription_id = ?
        ''', (subscription_id,))
        
        conn.commit()
        
    finally:
        conn.close()

def handle_trial_ending(subscription):
    """Handle trial ending reminder"""
    user_id = subscription['metadata'].get('user_id')
    if user_id:
        conn = sqlite3.connect('mapmystandards.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT email, first_name FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if user:
                send_trial_reminder_email(user[0], user[1])
        finally:
            conn.close()

def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    conn = sqlite3.connect('mapmystandards.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE subscriptions 
            SET status = 'cancelled'
            WHERE stripe_subscription_id = ?
        ''', (subscription['id'],))
        
        # Deactivate user
        cursor.execute('''
            UPDATE users 
            SET is_active = FALSE, trial_status = 'cancelled'
            WHERE stripe_customer_id = ?
        ''', (subscription['customer'],))
        
        conn.commit()
        
    finally:
        conn.close()

def send_trial_welcome_email_updated(email, first_name, username, api_key):
    """Send welcome email with login credentials"""
    try:
        subject = "Welcome to MapMyStandards - Your 7-Day Trial Started!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">Welcome to MapMyStandards, {first_name}! 🎉</h2>
            
            <p>Your 7-day free trial has started successfully! You now have full access to the A³E Platform.</p>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1f2937;">Your Login Credentials:</h3>
                <p><strong>Login URL:</strong> <a href="https://platform.mapmystandards.ai/login">https://platform.mapmystandards.ai/login</a></p>
                <p><strong>Username:</strong> {username}</p>
                <p><strong>Password:</strong> (The password you created during signup)</p>
            </div>
            
            <div style="background: #ecfdf5; border: 1px solid #a7f3d0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4 style="margin-top: 0; color: #065f46;">🎯 Your Trial Details:</h4>
                <ul style="color: #047857;">
                    <li>✅ 7 days of free access</li>
                    <li>✅ No charge until trial ends</li>
                    <li>✅ Cancel anytime during trial</li>
                    <li>✅ Full platform features included</li>
                </ul>
            </div>
            
            <h3 style="color: #1f2937;">What's Next?</h3>
            <ol>
                <li><strong>Login to your dashboard:</strong> Use the credentials above to access your platform</li>
                <li><strong>Explore the features:</strong> Upload your accreditation data and start mapping standards</li>
                <li><strong>Get support:</strong> Email us at support@mapmystandards.ai if you need help</li>
            </ol>
            
            <p style="margin-top: 30px;">
                <a href="https://platform.mapmystandards.ai/login" 
                   style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                    Access Your Dashboard →
                </a>
            </p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
            
            <p style="color: #6b7280; font-size: 14px;">
                Questions? Reply to this email or contact our support team at 
                <a href="mailto:support@mapmystandards.ai">support@mapmystandards.ai</a>
            </p>
            
            <p style="color: #6b7280; font-size: 12px;">
                MapMyStandards - Accreditation Analytics Engine<br>
                © 2025 All rights reserved
            </p>
        </body>
        </html>
        """
        
        # Use your email service here (SendGrid, AWS SES, etc.)
        # For now, just log the email content
        logger.info(f"Welcome email for {email}: {html_content}")
        
    except Exception as e:
        logger.error(f"Error sending welcome email: {e}")

def send_trial_reminder_email(email, first_name):
    """Send trial ending reminder"""
    try:
        subject = "Your MapMyStandards trial ends in 3 days"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2563eb;">Hi {first_name},</h2>
            
            <p>Your 7-day free trial of MapMyStandards will end in 3 days.</p>
            
            <p>To continue using the platform after your trial:</p>
            <ul>
                <li>✅ No action needed - you'll automatically continue with your selected plan</li>
                <li>❌ Want to cancel? <a href="https://platform.mapmystandards.ai/cancel">Cancel here</a></li>
            </ul>
            
            <p>
                <a href="https://platform.mapmystandards.ai/login" 
                   style="background: #2563eb; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                    Continue Using Platform →
                </a>
            </p>
        </body>
        </html>
        """
        
        logger.info(f"Trial reminder email for {email}: {html_content}")
        
    except Exception as e:
        logger.error(f"Error sending trial reminder: {e}")

@app.route('/trial-success')
def trial_success():
    """Success page after trial signup"""
    session_id = request.args.get('session_id')
    
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to MapMyStandards!</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>body { font-family: 'Inter', sans-serif; }</style>
    </head>
    <body class="bg-gray-50">
        <div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
            <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl shadow-lg">
                <div class="text-center">
                    <div class="mx-auto h-16 w-16 bg-green-100 rounded-full flex items-center justify-center">
                        <span class="text-green-600 text-2xl">🎉</span>
                    </div>
                    <h2 class="mt-6 text-3xl font-bold text-gray-900">Welcome to MapMyStandards!</h2>
                    <p class="mt-2 text-sm text-gray-600">Your 7-day free trial has started successfully</p>
                </div>
                
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 class="text-lg font-semibold text-blue-900 mb-2">✅ What happens next:</h3>
                    <ul class="text-sm text-blue-800 space-y-1">
                        <li>📧 Check your email for login credentials</li>
                        <li>🔑 Use your username/password to login</li>
                        <li>🚀 Start exploring the A³E Platform</li>
                        <li>💳 No charge for 7 days</li>
                    </ul>
                </div>
                
                <div class="space-y-4">
                    <a href="https://platform.mapmystandards.ai/login" 
                       class="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                        Go to Login Dashboard →
                    </a>
                    
                    <p class="text-center text-sm text-gray-500">
                        Need help? Email us at 
                        <a href="mailto:support@mapmystandards.ai" class="text-blue-600 hover:text-blue-500">support@mapmystandards.ai</a>
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint"""
    if request.method == 'GET':
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login | MapMyStandards</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>body { font-family: 'Inter', sans-serif; }</style>
        </head>
        <body class="bg-gray-50">
            <div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
                <div class="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl shadow-lg">
                    <div class="text-center">
                        <img src="https://mapmystandards.ai/wp-content/uploads/2025/07/Original-Logo.png" alt="MapMyStandards" class="mx-auto h-12 w-auto">
                        <h2 class="mt-6 text-3xl font-bold text-gray-900">Sign in to your account</h2>
                        <p class="mt-2 text-sm text-gray-600">Access your A³E Platform dashboard</p>
                    </div>
                    
                    <form class="mt-8 space-y-6" action="/login" method="POST">
                        <div class="space-y-4">
                            <div>
                                <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
                                <input id="username" name="username" type="text" required 
                                       class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 rounded-lg placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                                       placeholder="Enter your username">
                            </div>
                            <div>
                                <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
                                <input id="password" name="password" type="password" required 
                                       class="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 rounded-lg placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                                       placeholder="Enter your password">
                            </div>
                        </div>
                        
                        <div>
                            <button type="submit" 
                                    class="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                                Sign in
                            </button>
                        </div>
                        
                        <div class="text-center">
                            <p class="text-sm text-gray-600">
                                Don't have an account? 
                                <a href="/signup" class="font-medium text-blue-600 hover:text-blue-500">Start your free trial</a>
                            </p>
                        </div>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """
    
    # Handle POST request (login form submission)
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return redirect('/login?error=missing_credentials')
        
        # Hash the provided password
        password_hash = hash_password(password)
        
        conn = sqlite3.connect('mapmystandards.db')
        cursor = conn.cursor()
        
        # Check credentials and user status
        cursor.execute('''
            SELECT id, email, first_name, is_active, trial_status 
            FROM users 
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if user and user[3]:  # User exists and is active
            # Create session
            session['user_id'] = user[0]
            session['username'] = username
            session['email'] = user[1]
            session['first_name'] = user[2]
            
            # Redirect to dashboard
            return redirect('/dashboard')
        else:
            return redirect('/login?error=invalid_credentials')
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return redirect('/login?error=system_error')

@app.route('/dashboard')
def dashboard():
    """User dashboard - requires login"""
    if 'user_id' not in session:
        return redirect('/login')
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard | MapMyStandards</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>body {{ font-family: 'Inter', sans-serif; }}</style>
    </head>
    <body class="bg-gray-50">
        <nav class="bg-white shadow">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex justify-between h-16">
                    <div class="flex items-center">
                        <img src="https://mapmystandards.ai/wp-content/uploads/2025/07/Original-Logo.png" alt="MapMyStandards" class="h-8 w-auto">
                        <span class="ml-2 text-xl font-bold text-gray-900">MapMyStandards</span>
                    </div>
                    <div class="flex items-center space-x-4">
                        <span class="text-gray-700">Welcome, {session.get('first_name', 'User')}!</span>
                        <a href="/logout" class="text-gray-500 hover:text-gray-700">Logout</a>
                    </div>
                </div>
            </div>
        </nav>
        
        <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div class="px-4 py-6 sm:px-0">
                <div class="border-4 border-dashed border-gray-200 rounded-lg h-96 flex items-center justify-center">
                    <div class="text-center">
                        <h1 class="text-3xl font-bold text-gray-900 mb-4">Welcome to Your A³E Platform!</h1>
                        <p class="text-gray-600 mb-6">Your accreditation analytics dashboard is ready.</p>
                        <div class="space-y-4">
                            <button class="bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700">
                                Upload Data
                            </button>
                            <button class="bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 ml-4">
                                View Reports
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health_check():
    """Health check endpoint for deployment"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'mapmystandards-backend'
    })

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
