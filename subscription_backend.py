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


# Initialize database on app startup
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")


def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_trial_id():
    """Generate a unique trial ID"""
    return f"trial_{secrets.token_urlsafe(12)}"

def generate_api_key():
    """Generate a unique API key"""
    return f"a3e_{secrets.token_urlsafe(32)}"

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
            success_url=f"https://platform.mapmystandards.ai/trial-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"https://platform.mapmystandards.ai/signup?cancelled=true",
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

@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_test_secret')
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
            (user_id, stripe_subscription_id, status, trial_end, plan_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, subscription['id'], subscription['status'], trial_end, 
              subscription['metadata'].get('plan_type', 'monthly')))
        
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
            logger.info(f"Trial started for user {user[0]} (ID: {user_id})")
        
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
            SET status = 'active'
            WHERE stripe_subscription_id = ?
        ''', (subscription_id,))
        
        conn.commit()
        logger.info(f"Payment succeeded for subscription {subscription_id}")
        
    finally:
        conn.close()

def handle_trial_ending(subscription):
    """Handle trial ending reminder"""
    user_id = subscription['metadata'].get('user_id')
    if user_id:
        logger.info(f"Trial ending soon for user ID {user_id}")

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
        logger.info(f"Subscription cancelled: {subscription['id']}")
        
    finally:
        conn.close()

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
                    <a href="https://api.mapmystandards.ai/login" 
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
                                <a href="https://platform.mapmystandards.ai" class="font-medium text-blue-600 hover:text-blue-500">Start your free trial</a>
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
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
