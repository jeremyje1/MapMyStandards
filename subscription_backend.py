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
import time
from datetime import datetime
from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
from functools import wraps
import logging

# Try to import passlib, fallback if not available
try:
    from passlib.context import CryptContext  # type: ignore
    CryptContext_available = True
except ImportError:
    CryptContext = None
    CryptContext_available = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
CORS(app)

# Load environment variables
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
MONTHLY_PRICE_ID = os.getenv("MONTHLY_PRICE_ID", "price_1RtXF3K8PKpLCKDZJNfi3Rvi")
ANNUAL_PRICE_ID = os.getenv("ANNUAL_PRICE_ID", "price_1RtXF3K8PKpLCKDZAMb4rM8U")

stripe.api_key = STRIPE_SECRET_KEY


# Ensure CryptContext only defined once  
CryptContext = CryptContext if CryptContext_available else None

# Password hashing context (bcrypt) with legacy SHA-256 support
if CryptContext:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:  # fallback (will use legacy SHA-256 only)
    pwd_context = None

def hash_password(password: str) -> str:
    """Hash password using bcrypt or fallback to SHA-256"""
    if pwd_context:
        return pwd_context.hash(password)
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, stored: str) -> bool:
    """Verify password using bcrypt or fallback to SHA-256"""
    try:
        if len(stored) == 64 and all(c in "0123456789abcdef" for c in stored.lower()):
            return hashlib.sha256(plain.encode()).hexdigest() == stored
        if pwd_context:
            return pwd_context.verify(plain, stored)
        return False
    except Exception:
        return False


# Define subscription helper utilities early
if '_update_subscription_period_fields' not in globals():
    def _update_subscription_period_fields(cursor, subscription_obj, user_id):
        try:
            cps = subscription_obj.get("current_period_start")
            cpe = subscription_obj.get("current_period_end")
            if cps and cpe:
                cursor.execute(
                    """
                    UPDATE subscriptions
                    SET current_period_start = ?, current_period_end = ?
                    WHERE user_id = ? AND stripe_subscription_id = ?
                    """,
                    (
                        datetime.fromtimestamp(cps),
                        datetime.fromtimestamp(cpe),
                        user_id,
                        subscription_obj.get("id"),
                    ),
                )
        except Exception as e:  # pragma: no cover
            logger.warning(f"Failed to update period fields: {e}")

if 'expire_trials' not in globals():
    def expire_trials():
        try:
            conn = sqlite3.connect("mapmystandards.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE users
                SET trial_status = 'ended', is_active = FALSE
                WHERE trial_status = 'active' AND id IN (
                    SELECT user_id FROM subscriptions
                    WHERE trial_end IS NOT NULL AND trial_end < CURRENT_TIMESTAMP AND (status IS NULL OR status != 'active')
                )
                """
            )
            conn.commit()
            conn.close()
        except Exception as e:  # pragma: no cover
            logger.warning(f"expire_trials error: {e}")


# Database setup
def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect("mapmystandards.db")
    cursor = conn.cursor()

    # Users table
    cursor.execute(
        """
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
    """
    )

    # Subscriptions table
    cursor.execute(
        """
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
    """
    )

    # API keys table (for platform access)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            api_key TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """
    )

    conn.commit()
    conn.close()


# Initialize database on app startup
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")


def generate_trial_id():
    """Generate a unique trial ID"""
    return f"trial_{secrets.token_urlsafe(12)}"


def generate_api_key():
    """Generate a unique API key"""
    return f"a3e_{secrets.token_urlsafe(32)}"


@app.route("/")
def home():
    """Home page"""
    return redirect("https://platform.mapmystandards.ai")


@app.route("/health")
def health_check():
    """Health check endpoint for deployment verification"""
    from datetime import datetime
    return {
        "service": "mapmystandards-backend",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.route("/test-email")
def test_email_config():
    """Test endpoint to verify email configuration"""
    if not email_service:
        return jsonify({"error": "Email service not configured"}), 500
    
    try:
        # Send a test email to admin if configured
        if ADMIN_EMAIL:
            email_service._send_email(
                ADMIN_EMAIL,
                "MapMyStandards Backend Test",
                "This is a test email to verify SMTP configuration is working correctly."
            )
            return jsonify({"status": "success", "message": f"Test email sent to {ADMIN_EMAIL}"})
        else:
            return jsonify({"error": "ADMIN_EMAIL not configured"}), 400
    except Exception as e:
        return jsonify({"error": f"Email test failed: {str(e)}"}), 500


@app.route("/debug-config")
def debug_config():
    """Debug endpoint to check configuration"""
    return jsonify({
        "stripe_key_configured": bool(STRIPE_SECRET_KEY),
        "stripe_publishable_key_configured": bool(STRIPE_PUBLISHABLE_KEY),
        "monthly_price_id": MONTHLY_PRICE_ID,
        "annual_price_id": ANNUAL_PRICE_ID,
        "email_service_configured": bool(email_service),
        "admin_email_configured": bool(ADMIN_EMAIL)
    })


# Simple in-memory rate limiting (per-process). For clustered deployments use Redis.
RATE_LIMITS = {}


def check_rate_limit(key: str, limit: int, window: int) -> bool:
    now = time.time()
    bucket = RATE_LIMITS.setdefault(key, [])
    # prune
    RATE_LIMITS[key] = [t for t in bucket if now - t < window]
    if len(RATE_LIMITS[key]) >= limit:
        return False
    RATE_LIMITS[key].append(now)
    return True


def rate_limited(limit: int, window: int):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "unknown"
            key = f"{f.__name__}:{ip}"
            if not check_rate_limit(key, limit, window):
                return jsonify({"error": "Too many requests"}), 429
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/create-trial-account", methods=["POST"])
@rate_limited(limit=10, window=60)  # 10 attempts per minute per IP
def create_trial_account():
    """Create user account and Stripe checkout session for trial"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["firstName", "lastName", "email", "institution", "username", "password", "plan"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Validate email format (improved validation)
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data["email"]):
            return jsonify({"error": "Invalid email format"}), 400

        # Validate password length
        if len(data["password"]) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        # Validate plan selection
        if data["plan"] not in ["monthly", "annual"]:
            return jsonify({"error": f"Invalid plan selected. Must be 'monthly' or 'annual', received: '{data['plan']}'"}), 400

        # Get price ID based on plan
        price_id = MONTHLY_PRICE_ID if data["plan"] == "monthly" else ANNUAL_PRICE_ID

        conn = sqlite3.connect("mapmystandards.db")
        cursor = conn.cursor()

        # Check if email or username already exists
        cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (data["email"], data["username"]))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": "Email or username already exists"}), 400

        # Create user account (initially inactive until trial starts)
        password_hash = hash_password(data["password"])

        cursor.execute(
            """
            INSERT INTO users (email, password_hash, first_name, last_name, 
                             institution, username, is_active, trial_status)
            VALUES (?, ?, ?, ?, ?, ?, FALSE, 'pending')
        """,
            (data["email"], password_hash, data["firstName"], data["lastName"], data["institution"], data["username"]),
        )

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            customer_email=data["email"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            # Send users back to API domain so our success page + next steps show consistently
            success_url=(
                "https://api.mapmystandards.ai/trial-success?session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=(
                "https://platform.mapmystandards.ai/signup?cancelled=true"
            ),
            metadata={
                "user_id": str(user_id),
                "plan_type": data["plan"],
                "username": data["username"],
            },
            subscription_data={
                "trial_period_days": 7,
                "metadata": {"user_id": str(user_id), "username": data["username"]},
            },
        )

        return jsonify({"success": True, "checkout_url": checkout_session.url, "user_id": user_id})

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error in create_trial_account: {e}")
        logger.error(f"Stripe error type: {type(e)}")
        logger.error(f"Stripe error message: {str(e)}")
        return jsonify({"error": f"Payment system error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error in create_trial_account: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# Email notifications
try:
    from email_notifications import email_service
except Exception:  # pragma: no cover - fallback if module missing
    email_service = None

# Admin notification email (optional)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")


@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        # Verify webhook signature with trimmed secret to avoid whitespace issues
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret") or ""
        webhook_secret = webhook_secret.strip()
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        # Log basic event info for diagnostics
        try:
            logger.info(
                "Stripe event received: %s id=%s",
                event.get("type"),
                event.get("id"),
            )
        except Exception:
            pass
    except ValueError:
        logger.error("Invalid payload in webhook")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in webhook")
        return jsonify({"error": "Invalid signature"}), 400

    try:
        # Handle the event
        if event["type"] == "customer.subscription.created":
            subscription = event["data"]["object"]
            handle_subscription_created(subscription)

        elif event["type"] == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            handle_payment_succeeded(invoice)

        elif event["type"] == "customer.subscription.trial_will_end":
            subscription = event["data"]["object"]
            handle_trial_ending(subscription)

        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            handle_subscription_cancelled(subscription)

        elif event["type"] == "checkout.session.completed":
            session_obj = event["data"]["object"]
            logger.info(
                f"Checkout completed for customer {session_obj.get('customer')} subscription {session_obj.get('subscription')}"
            )

        return jsonify({"status": "success"})

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({"error": "Webhook handling failed"}), 500


def handle_subscription_created(subscription):
    """Handle new subscription creation (trial started)"""
    metadata = subscription.get("metadata") or {}
    user_id = metadata.get("user_id")
    if not user_id:
        logger.error("No user_id in subscription metadata")
        return

    conn = sqlite3.connect("mapmystandards.db")
    cursor = conn.cursor()

    try:
        # Update user status to active trial
        cursor.execute(
            """
            UPDATE users 
            SET is_active = TRUE, trial_status = 'active', stripe_customer_id = ?
            WHERE id = ?
        """,
            (subscription.get("customer"), user_id),
        )

        # Create subscription record
        trial_end = (
            datetime.fromtimestamp(subscription.get("trial_end"))
            if subscription.get("trial_end")
            else None
        )

        cursor.execute(
            """
            INSERT OR IGNORE INTO subscriptions 
            (user_id, stripe_subscription_id, status, trial_end, plan_type)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                user_id,
                subscription.get("id"),
                subscription.get("status", "trialing"),
                trial_end,
                metadata.get("plan_type", "monthly"),
            ),
        )

        _update_subscription_period_fields(cursor, subscription, user_id)

        # Generate API key for platform access
        api_key = generate_api_key()
        cursor.execute(
            """
            INSERT OR IGNORE INTO api_keys (user_id, api_key)
            VALUES (?, ?)
        """,
            (user_id, api_key),
        )

        conn.commit()

        # Get user details for welcome/admin email
        cursor.execute("SELECT email, first_name, username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            user_email = user[0]
            first_name_db = user[1]
            username_db = user[2]
            display_name = first_name_db or username_db
            logger.info(f"Trial started for user {user_email} (ID: {user_id})")

            # Send welcome email if configured
            if email_service:
                try:
                    email_service.send_welcome_email(
                        user_email=user_email,
                        user_name=display_name,
                        plan=metadata.get("plan_type", "monthly"),
                        api_key=api_key,
                    )
                except Exception as e:
                    logger.warning(f"Welcome email failed for {user_email}: {e}")

            # Notify admin (optional)
            if ADMIN_EMAIL and email_service:
                try:
                    subject = "New A³E trial started"
                    body = (
                        f"User: {user_email}<br>Username: {username_db}<br>"
                        f"Plan: {metadata.get('plan_type', 'monthly')}<br>"
                        f"Stripe Customer: {subscription.get('customer')}<br>"
                        f"Subscription: {subscription.get('id')}<br>"
                        f"Trial ends: {trial_end}"
                    )
                    email_service._send_email(ADMIN_EMAIL, subject, body)
                except Exception as e:
                    logger.warning(f"Admin notification failed: {e}")

    finally:
        conn.close()


def handle_payment_succeeded(invoice):
    """Handle successful payment (trial converted or renewal)"""
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        logger.warning(
            "invoice.payment_succeeded without subscription id. invoice_id=%s customer=%s",
            invoice.get("id"),
            invoice.get("customer"),
        )
        return

    conn = sqlite3.connect("mapmystandards.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE subscriptions 
            SET status = 'active'
            WHERE stripe_subscription_id = ?
        """,
            (subscription_id,),
        )

        # Period update
        try:
            sub_obj = stripe.Subscription.retrieve(subscription_id)
            if sub_obj:
                cursor.execute("SELECT user_id FROM subscriptions WHERE stripe_subscription_id = ? LIMIT 1", (subscription_id,))
                row_user = cursor.fetchone()
                if row_user:
                    _update_subscription_period_fields(cursor, sub_obj, row_user[0])
        except Exception as e:  # pragma: no cover
            logger.warning(f"Could not retrieve subscription for period update: {e}")

        # Fetch user for notifications
        cursor.execute(
            """
            SELECT u.email, COALESCE(u.first_name, u.username), s.plan_type
            FROM subscriptions s JOIN users u ON s.user_id = u.id
            WHERE s.stripe_subscription_id = ?
            LIMIT 1
            """,
            (subscription_id,),
        )
        row = cursor.fetchone()

        conn.commit()
        logger.info(f"Payment succeeded for subscription {subscription_id}")

        amount_cents = invoice.get("amount_paid") or invoice.get("total") or 0
        amount = (amount_cents or 0) / 100.0

        if row and email_service:
            user_email, user_name, plan_type = row
            try:
                email_service.send_subscription_confirmation(
                    user_email=user_email, user_name=user_name, plan=plan_type, amount=amount
                )
            except Exception as e:
                logger.warning(f"Subscription confirmation email failed for {user_email}: {e}")

        if ADMIN_EMAIL and email_service:
            try:
                subject = "A³E payment succeeded"
                body = (
                    f"Subscription: {subscription_id}\n"
                    f"Amount: ${amount:.2f}\n"
                    f"Invoice: {invoice.get('id')}\n"
                    f"Customer: {invoice.get('customer')}"
                )
                email_service._send_email(ADMIN_EMAIL, subject, body)
            except Exception as e:
                logger.warning(f"Admin payment notification failed: {e}")

    finally:
        conn.close()


def handle_trial_ending(subscription):
    """Handle trial ending reminder"""
    user_id = subscription["metadata"].get("user_id")
    if user_id:
        logger.info(f"Trial ending soon for user ID {user_id}")


def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    conn = sqlite3.connect("mapmystandards.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            UPDATE subscriptions 
            SET status = 'cancelled'
            WHERE stripe_subscription_id = ?
        """,
            (subscription["id"],),
        )

        # Deactivate user
        cursor.execute(
            """
            UPDATE users 
            SET is_active = FALSE, trial_status = 'cancelled'
            WHERE stripe_customer_id = ?
        """,
            (subscription["customer"],),
        )

        conn.commit()
        logger.info(f"Subscription cancelled: {subscription['id']}")

    finally:
        conn.close()


@app.route("/trial-success")
def trial_success():
    """Success page after trial signup.
    Also performs a defensive activation using the Stripe checkout session
    in case the webhook is delayed or blocked.
    """
    session_id = request.args.get("session_id")
    activation_done = False

    try:
        if session_id and stripe.api_key:
            # Retrieve the checkout session and related subscription
            checkout_sess = stripe.checkout.Session.retrieve(session_id)
            subscription_id = checkout_sess.get("subscription")
            customer_id = checkout_sess.get("customer")

            sub_obj = None
            if isinstance(subscription_id, dict):
                sub_obj = subscription_id
            elif subscription_id:
                try:
                    sub_obj = stripe.Subscription.retrieve(subscription_id)
                except Exception as e:  # pragma: no cover
                    logger.warning(f"Unable to retrieve subscription {subscription_id}: {e}")

            user_id = None
            plan_type = None
            trial_end_ts = None

            if sub_obj:
                metadata = sub_obj.get("metadata") or {}
                user_id = metadata.get("user_id")
                plan_type = metadata.get("plan_type", "monthly")
                trial_end_ts = sub_obj.get("trial_end")
            else:
                # Fallback to checkout session metadata if present
                metadata = checkout_sess.get("metadata") or {}
                user_id = metadata.get("user_id")
                plan_type = metadata.get("plan_type") or "monthly"

            if user_id:
                conn = sqlite3.connect("mapmystandards.db")
                cursor = conn.cursor()

                # Mark the user active and store stripe customer id
                cursor.execute(
                    """
                    UPDATE users 
                    SET is_active = TRUE, trial_status = 'active', stripe_customer_id = ?
                    WHERE id = ?
                    """,
                    (customer_id, user_id),
                )

                # Insert or update subscription
                sub_id_val = sub_obj.get("id") if isinstance(sub_obj, dict) else None
                sub_status = (sub_obj.get("status") if isinstance(sub_obj, dict) else "trialing")
                trial_end = datetime.fromtimestamp(trial_end_ts) if trial_end_ts else None

                cursor.execute(
                    """
                    INSERT OR IGNORE INTO subscriptions 
                    (user_id, stripe_subscription_id, status, trial_end, plan_type)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, sub_id_val, sub_status, trial_end, plan_type),
                )

                # Ensure API key exists
                cursor.execute("SELECT api_key FROM api_keys WHERE user_id = ? LIMIT 1", (user_id,))
                row = cursor.fetchone()
                if row:
                    api_key_val = row[0]
                else:
                    api_key_val = generate_api_key()
                    cursor.execute(
                        "INSERT INTO api_keys (user_id, api_key) VALUES (?, ?)",
                        (user_id, api_key_val),
                    )

                # Fetch user for emails
                cursor.execute(
                    "SELECT email, COALESCE(first_name, username) FROM users WHERE id = ?",
                    (user_id,),
                )
                u = cursor.fetchone()
                conn.commit()
                conn.close()

                # Send welcome/admin emails (best effort)
                if u and email_service:
                    try:
                        email_service.send_welcome_email(
                            user_email=u[0], user_name=u[1], plan=plan_type or "monthly", api_key=api_key_val
                        )
                    except Exception as e:  # pragma: no cover
                        logger.warning(f"Welcome email (success page) failed: {e}")
                if ADMIN_EMAIL and email_service:
                    try:
                        body = (
                            f"User: {u[0]}<br>Plan: {plan_type or 'monthly'}<br>"
                            f"Stripe Customer: {customer_id}<br>Subscription: {sub_id_val}"
                        )
                        email_service._send_email(ADMIN_EMAIL, "New A³E trial started (fallback)", body)
                    except Exception as e:  # pragma: no cover
                        logger.warning(f"Admin notification (success page) failed: {e}")

                activation_done = True
    except Exception as e:  # pragma: no cover
        logger.warning(f"Trial success activation fallback failed: {e}")

    status_html = (
        '<p class="mt-3 text-sm text-green-700">Account activated.</p>'
        if activation_done
        else '<p class="mt-3 text-sm text-yellow-700">If your account is not active yet, it will be in a few moments.</p>'
    )

    # Render success page with production CSS (no CDN)
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"> 
        <meta name="viewport" content="width=device-width, initial-scale=1.0"> 
        <title>Welcome to MapMyStandards!</title>
        <link rel="stylesheet" href="https://platform.mapmystandards.ai/assets/styles.css"> 
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet"> 
        <style>body {{ font-family: 'Inter', sans-serif; }}</style>
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
                        <li>📧 We've emailed your trial details</li> 
                        <li>🔑 Use your email or username and password to login</li> 
                        <li>🚀 Start exploring the A³E Platform</li> 
                        <li>💳 No charge for 7 days</li> 
                    </ul> 
                    {status_html} 
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


@app.route("/login", methods=["GET", "POST"])
@rate_limited(limit=15, window=300)  # 15 attempts per 5 minutes per IP
def login():
    """User login endpoint"""
    if request.method == "GET":
        # CSRF token generation
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        csrf = session["csrf_token"]
        return f"""
        <!DOCTYPE html>
        <html lang=\"en\">
        <head>
            <meta charset=\"UTF-8\">
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
            <title>Login | MapMyStandards</title>
            <link rel=\"stylesheet\" href=\"https://platform.mapmystandards.ai/assets/styles.css\"> 
            <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap\" rel=\"stylesheet\">
            <style>body {{ font-family: 'Inter', sans-serif; }}</style>
        </head>
        <body class=\"bg-gray-50\">
            <div class=\"min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8\">
                <div class=\"max-w-md w-full space-y-8 bg-white p-8 rounded-2xl shadow-lg\">
                    <div class=\"text-center\">
                        <img src=\"https://mapmystandards.ai/wp-content/uploads/2025/07/Original-Logo.png\" alt=\"MapMyStandards\" class=\"mx-auto h-12 w-auto\">
                        <h2 class=\"mt-6 text-3xl font-bold text-gray-900\">Sign in to your account</h2>
                        <p class=\"mt-2 text-sm text-gray-600\">Access your A³E Platform dashboard</p>
                    </div>
                    <form class=\"mt-8 space-y-6\" action=\"/login\" method=\"POST\">
                        <input type=\"hidden\" name=\"csrf_token\" value=\"{csrf}\">
                        <div class=\"space-y-4\">
                            <div>
                                <label for=\"username\" class=\"block text-sm font-medium text-gray-700\">Email or Username</label>
                                <input id=\"username\" name=\"username\" type=\"text\" required 
                                       class=\"mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 rounded-lg placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm\"
                                       placeholder=\"Enter your email or username\">
                            </div>
                            <div>
                                <label for=\"password\" class=\"block text-sm font-medium text-gray-700\">Password</label>
                                <input id=\"password\" name=\"password\" type=\"password\" required 
                                       class=\"mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 rounded-lg placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm\"
                                       placeholder=\"Enter your password\">
                            </div>
                        </div>
                        <div>
                            <button type=\"submit\" 
                                    class=\"group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500\">
                                Sign in
                            </button>
                        </div>
                        <div class=\"text-center\">
                            <p class=\"text-sm text-gray-600\">
                                Don't have an account? 
                                <a href=\"https://platform.mapmystandards.ai\" class=\"font-medium text-blue-600 hover:text-blue-500\">Start your free trial</a>
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
        if session.get("csrf_token") != request.form.get("csrf_token"):
            return redirect("/login?error=csrf")
        username_or_email = request.form.get("username")
        password = request.form.get("password")
        if not username_or_email or not password:
            return redirect("/login?error=missing_credentials")
        conn = sqlite3.connect("mapmystandards.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, email, first_name, is_active, trial_status, password_hash
            FROM users 
            WHERE (username = ? OR email = ?)
            LIMIT 1
            """,
            (username_or_email, username_or_email),
        )
        user = cursor.fetchone()
        conn.close()
        if user and verify_password(password, user[5]) and user[3]:
            session["user_id"] = user[0]
            session["username"] = username_or_email
            session["email"] = user[1]
            session["first_name"] = user[2]
            return redirect("/dashboard")
        else:
            return redirect("/login?error=invalid_credentials")
    except Exception as e:
        logger.error(f"Login error: {e}")
        return redirect("/login?error=system_error")


@app.route("/dashboard")
def dashboard():
    """User dashboard - requires login"""
    if "user_id" not in session:
        return redirect("/login")
    expire_trials()
    
    # Get user statistics for dashboard
    try:
        conn = sqlite3.connect("mapmystandards.db")
        cursor = conn.cursor()
        
        # Get upload count
        cursor.execute("SELECT COUNT(*) FROM uploads WHERE user_id = ?", (session['user_id'],))
        upload_count = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        conn.close()
    except:
        upload_count = 0
    
    return f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
        <meta charset=\"UTF-8\">
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
        <title>Dashboard | MapMyStandards</title>
        <link rel=\"stylesheet\" href=\"https://platform.mapmystandards.ai/assets/styles.css\"> 
        <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap\" rel=\"stylesheet\">
        <style>
            body {{ font-family: 'Inter', sans-serif; }}
            .status-card {{
                background: white;
                padding: 1.5rem;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
            }}
            .status-indicator {{
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                margin-right: 8px;
            }}
            .status-online {{ background-color: #10b981; }}
            .status-offline {{ background-color: #ef4444; }}
            .notification-item {{
                padding: 12px;
                border-left: 4px solid #3b82f6;
                background: #eff6ff;
                margin-bottom: 8px;
                border-radius: 4px;
            }}
        </style>
    </head>
    <body class=\"bg-gray-50\">
        <nav class=\"bg-white shadow\">
            <div class=\"max-w-7xl mx-auto px-4 sm:px-6 lg:px-8\">
                <div class=\"flex justify-between h-16\"> 
                    <div class=\"flex items-center\">
                        <img src=\"https://mapmystandards.ai/wp-content/uploads/2025/07/Original-Logo.png\" alt=\"MapMyStandards\" class=\"h-8 w-auto\"> 
                        <span class=\"ml-2 text-xl font-bold text-gray-900\">MapMyStandards</span>
                    </div>
                    <div class=\"flex items-center space-x-4\">
                        <a href=\"https://engine.mapmystandards.ai\" target=\"_blank\" class=\"text-indigo-600 hover:text-indigo-800 font-semibold\">🎯 A³E Engine</a>
                        <a href=\"/upload\" class=\"text-gray-700 hover:text-gray-900\">Upload</a>
                        <a href=\"/reports\" class=\"text-gray-700 hover:text-gray-900\">Reports</a>
                        <span class=\"text-gray-700\">Welcome, {session.get('first_name', 'User')}!</span>
                        <a href=\"/logout\" class=\"text-gray-500 hover:text-gray-700\">Logout</a>
                    </div>
                </div>
            </div>
        </nav>
        
        <div class=\"max-w-7xl mx-auto py-8 px-6\">
            <h1 class=\"text-3xl font-bold text-gray-900 mb-8\">Dashboard</h1>
            
            <!-- Quick Stats -->
            <div class=\"grid grid-cols-1 md:grid-cols-4 gap-6 mb-8\">
                <div class=\"status-card\">
                    <div class=\"text-2xl font-bold text-gray-900\">{upload_count}</div>
                    <div class=\"text-gray-600\">Documents Uploaded</div>
                </div>
                <div class=\"status-card\">
                    <div class=\"text-2xl font-bold text-green-600\" id=\"email-status-count\">✓</div>
                    <div class=\"text-gray-600\">Email System</div>
                </div>
                <div class=\"status-card\">
                    <div class=\"text-2xl font-bold text-blue-600\">Active</div>
                    <div class=\"text-gray-600\">Account Status</div>
                </div>
                <div class=\"status-card\">
                    <div class=\"text-2xl font-bold text-indigo-600\" id=\"a3e-status\">🎯</div>
                    <div class=\"text-gray-600\">A³E Engine</div>
                </div>
            </div>
            
            <!-- Main Content -->
            <div class=\"grid grid-cols-1 lg:grid-cols-3 gap-8\">
                <!-- Main Actions -->
                <div class=\"lg:col-span-2\">
                    <div class=\"status-card\">
                        <h2 class=\"text-xl font-semibold mb-6\">Quick Actions</h2>
                        <div class=\"grid grid-cols-1 md:grid-cols-2 gap-4\">
                            <a href=\"http://localhost:8002\" target=\"_blank\" class=\"block bg-indigo-600 text-white text-center px-6 py-4 rounded-lg font-semibold hover:bg-indigo-700 transition\">
                                🎯 Launch A³E Enhanced (5 Bodies)
                            </a>
                            <a href=\"http://localhost:8002/upload\" target=\"_blank\" class=\"block bg-blue-600 text-white text-center px-6 py-4 rounded-lg font-semibold hover:bg-blue-700 transition\">
                                📄 Upload Real Documents
                            </a>
                            <a href=\"/reports\" class=\"block bg-green-600 text-white text-center px-6 py-4 rounded-lg font-semibold hover:bg-green-700 transition\">
                                📊 View Reports
                            </a>
                            <button onclick=\"sendTestEmail()\" class=\"bg-purple-600 text-white px-6 py-4 rounded-lg font-semibold hover:bg-purple-700 transition\">
                                📧 Test Email System
                            </button>
                            <button onclick=\"refreshStatus()\" class=\"bg-gray-600 text-white px-6 py-4 rounded-lg font-semibold hover:bg-gray-700 transition\">
                                🔄 Refresh Status
                            </button>
                            <a href=\"http://localhost:8002/docs\" target=\"_blank\" class=\"block bg-yellow-600 text-white text-center px-6 py-4 rounded-lg font-semibold hover:bg-yellow-700 transition\">
                                📚 A³E Enhanced API Docs
                            </a>
                            <a href=\"http://localhost:8002/api/analytics\" target=\"_blank\" class=\"block bg-orange-600 text-white text-center px-6 py-4 rounded-lg font-semibold hover:bg-orange-700 transition\">
                                📊 A³E Analytics Dashboard
                            </a>
                        </div>
                    </div>
                </div>
                
                <!-- System Status & Notifications -->
                <div>
                    <!-- Email Status -->
                    <div class=\"status-card\">
                        <h3 class=\"text-lg font-semibold mb-4\">Email System Status</h3>
                        <div id=\"email-status-details\">
                            <div class=\"text-gray-500\">Loading...</div>
                        </div>
                        <button onclick=\"checkEmailStatus()\" class=\"mt-3 text-blue-600 hover:text-blue-800 text-sm\">
                            Check Status
                        </button>
                    </div>
                    
                    <!-- Notifications -->
                    <div class=\"status-card\">
                        <h3 class=\"text-lg font-semibold mb-4\">Recent Notifications</h3>
                        <div id=\"notifications-list\">
                            <div class=\"text-gray-500\">Loading...</div>
                        </div>
                        <button onclick=\"loadNotifications()\" class=\"mt-3 text-blue-600 hover:text-blue-800 text-sm\">
                            Refresh Notifications
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Load initial data
            document.addEventListener('DOMContentLoaded', function() {{
                checkEmailStatus();
                loadNotifications();
            }});
            
            function checkEmailStatus() {{
                fetch('/api/email-status')
                .then(response => response.json())
                .then(data => {{
                    const statusDiv = document.getElementById('email-status-details');
                    if (data.email_service_configured) {{
                        statusDiv.innerHTML = `
                            <div class="space-y-2">
                                <div><span class="status-indicator status-online"></span>Email Service: Online</div>
                                <div><span class="status-indicator status-online"></span>Admin Email: Configured</div>
                                <div class="text-sm text-gray-600">From: ${{data.from_email}}</div>
                                <div class="text-sm text-gray-600">Your Email: ${{data.user_email}}</div>
                            </div>
                        `;
                        document.getElementById('email-status-count').textContent = '✓';
                        document.getElementById('email-status-count').className = 'text-2xl font-bold text-green-600';
                    }} else {{
                        statusDiv.innerHTML = `
                            <div><span class="status-indicator status-offline"></span>Email Service: Offline</div>
                        `;
                        document.getElementById('email-status-count').textContent = '✗';
                        document.getElementById('email-status-count').className = 'text-2xl font-bold text-red-600';
                    }}
                }})
                .catch(error => {{
                    console.error('Error checking email status:', error);
                    document.getElementById('email-status-details').innerHTML = 
                        '<div class="text-red-500">Error checking status</div>';
                }});
            }}
            
            function loadNotifications() {{
                fetch('/api/notifications')
                .then(response => response.json())
                .then(data => {{
                    const notificationsList = document.getElementById('notifications-list');
                    const notifications = data.notifications || [];
                    
                    document.getElementById('notification-count').textContent = notifications.length;
                    
                    if (notifications.length > 0) {{
                        notificationsList.innerHTML = notifications.slice(0, 3).map(notification => `
                            <div class="notification-item">
                                <div class="font-medium text-sm">${{notification.title}}</div>
                                <div class="text-xs text-gray-600">${{notification.message}}</div>
                                <div class="text-xs text-gray-500 mt-1">${{new Date(notification.date).toLocaleDateString()}}</div>
                            </div>
                        `).join('');
                    }} else {{
                        notificationsList.innerHTML = '<div class="text-gray-500">No notifications</div>';
                    }}
                }})
                .catch(error => {{
                    console.error('Error loading notifications:', error);
                    document.getElementById('notifications-list').innerHTML = 
                        '<div class="text-red-500">Error loading notifications</div>';
                }});
            }}
            
            function sendTestEmail() {{
                const button = event.target;
                button.disabled = true;
                button.textContent = '📧 Sending...';
                
                fetch('/api/send-test-email', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }}
                }})
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        alert('✅ Test email sent successfully!\\n\\n' + data.message);
                    }} else {{
                        alert('❌ Failed to send test email:\\n\\n' + (data.error || 'Unknown error'));
                    }}
                }})
                .catch(error => {{
                    alert('❌ Error sending test email:\\n\\n' + error.message);
                }})
                .finally(() => {{
                    button.disabled = false;
                    button.textContent = '📧 Test Email System';
                }});
            }}
            
            function refreshStatus() {{
                checkEmailStatus();
                loadNotifications();
                alert('✅ Status refreshed!');
            }}
        </script>
    </body>
    </html>
    """


# New placeholder pages so buttons don't 404 and session stays on same subdomain
@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    if "user_id" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        # Handle file upload
        try:
            if 'file' not in request.files:
                return jsonify({"error": "No file provided"}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            # Save file and process
            import uuid
            file_id = str(uuid.uuid4())
            filename = file.filename
            
            # For now, just log the upload (in production, you'd save the file)
            conn = sqlite3.connect("mapmystandards.db")
            cursor = conn.cursor()
            
            # Create uploads table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    filename TEXT,
                    upload_date TEXT,
                    status TEXT DEFAULT 'processing'
                )
            """)
            
            cursor.execute("""
                INSERT INTO uploads (id, user_id, filename, upload_date, status)
                VALUES (?, ?, ?, ?, ?)
            """, (file_id, session['user_id'], filename, datetime.utcnow().isoformat(), 'completed'))
            
            conn.commit()
            conn.close()
            
            # Send notification email
            try:
                if email_service and ADMIN_EMAIL:
                    email_service._send_email(
                        ADMIN_EMAIL,
                        f"New File Upload - {filename}",
                        f"User {session.get('first_name', 'Unknown')} ({session.get('email', 'unknown')}) uploaded file: {filename}"
                    )
            except Exception as e:
                logger.error(f"Failed to send upload notification: {e}")
            
            return jsonify({"success": True, "file_id": file_id, "message": "File uploaded successfully"})
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return jsonify({"error": str(e)}), 500
    
    # GET request - show upload page
    return f"""
    <!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>Upload Data | MapMyStandards</title>
    <link rel='stylesheet' href='https://platform.mapmystandards.ai/assets/styles.css'>
    <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' rel='stylesheet'>
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .upload-zone {{
            border: 2px dashed #d1d5db;
            border-radius: 8px;
            padding: 3rem;
            text-align: center;
            transition: border-color 0.3s;
        }}
        .upload-zone:hover {{
            border-color: #3b82f6;
        }}
        .upload-zone.dragover {{
            border-color: #3b82f6;
            background-color: #eff6ff;
        }}
    </style></head>
    <body class='bg-gray-50 min-h-screen'>
    <nav class="bg-white shadow mb-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16"> 
                <div class="flex items-center">
                    <img src="https://mapmystandards.ai/wp-content/uploads/2025/07/Original-Logo.png" alt="MapMyStandards" class="h-8 w-auto"> 
                    <span class="ml-2 text-xl font-bold text-gray-900">MapMyStandards</span>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/dashboard" class="text-gray-700 hover:text-gray-900">Dashboard</a>
                    <a href="/reports" class="text-gray-700 hover:text-gray-900">Reports</a>
                    <span class="text-gray-700">Welcome, {session.get('first_name', 'User')}!</span>
                    <a href="/logout" class="text-gray-500 hover:text-gray-700">Logout</a>
                </div>
            </div>
        </div>
    </nav>
    
    <div class='max-w-4xl mx-auto py-8 px-6'>
        <h1 class='text-3xl font-bold mb-4 text-gray-900'>Upload Accreditation Data</h1>
        <p class='text-gray-700 mb-8'>Upload your accreditation documents for analysis and compliance tracking.</p>
        
        <div class="bg-white rounded-lg shadow p-6 mb-6">
            <div id="upload-zone" class="upload-zone">
                <svg class="mx-auto h-12 w-12 text-gray-400 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
                <p class="text-lg font-medium text-gray-900 mb-2">Drag and drop files here</p>
                <p class="text-gray-500 mb-4">or click to browse</p>
                <input type="file" id="file-input" class="hidden" multiple accept=".pdf,.doc,.docx,.xls,.xlsx,.csv">
                <button onclick="document.getElementById('file-input').click()" class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition">
                    Choose Files
                </button>
            </div>
        </div>
        
        <div id="upload-progress" class="hidden bg-white rounded-lg shadow p-6 mb-6">
            <h3 class="text-lg font-semibold mb-4">Upload Progress</h3>
            <div id="progress-list"></div>
        </div>
        
        <div id="upload-history" class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">Recent Uploads</h3>
            <div id="history-list">Loading...</div>
        </div>
        
        <div class="mt-6">
            <a href='/dashboard' class='inline-block bg-gray-800 text-white px-5 py-3 rounded-lg hover:bg-gray-900 transition'>&larr; Back to Dashboard</a>
        </div>
    </div>
    
    <script>
        const uploadZone = document.getElementById('upload-zone');
        const fileInput = document.getElementById('file-input');
        const progressDiv = document.getElementById('upload-progress');
        const progressList = document.getElementById('progress-list');
        
        // Drag and drop functionality
        uploadZone.addEventListener('dragover', (e) => {{
            e.preventDefault();
            uploadZone.classList.add('dragover');
        }});
        
        uploadZone.addEventListener('dragleave', () => {{
            uploadZone.classList.remove('dragover');
        }});
        
        uploadZone.addEventListener('drop', (e) => {{
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files);
            handleFiles(files);
        }});
        
        fileInput.addEventListener('change', (e) => {{
            const files = Array.from(e.target.files);
            handleFiles(files);
        }});
        
        function handleFiles(files) {{
            if (files.length === 0) return;
            
            progressDiv.classList.remove('hidden');
            progressList.innerHTML = '';
            
            files.forEach(file => uploadFile(file));
        }}
        
        function uploadFile(file) {{
            const formData = new FormData();
            formData.append('file', file);
            
            const progressItem = document.createElement('div');
            progressItem.className = 'mb-2 p-3 border rounded';
            progressItem.innerHTML = `
                <div class="flex justify-between items-center">
                    <span class="font-medium">${{file.name}}</span>
                    <span class="text-blue-600">Uploading...</span>
                </div>
            `;
            progressList.appendChild(progressItem);
            
            fetch('/upload', {{
                method: 'POST',
                body: formData
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    progressItem.innerHTML = `
                        <div class="flex justify-between items-center">
                            <span class="font-medium">${{file.name}}</span>
                            <span class="text-green-600">✓ Completed</span>
                        </div>
                    `;
                    loadUploadHistory();
                }} else {{
                    progressItem.innerHTML = `
                        <div class="flex justify-between items-center">
                            <span class="font-medium">${{file.name}}</span>
                            <span class="text-red-600">✗ Failed</span>
                        </div>
                    `;
                }}
            }})
            .catch(error => {{
                progressItem.innerHTML = `
                    <div class="flex justify-between items-center">
                        <span class="font-medium">${{file.name}}</span>
                        <span class="text-red-600">✗ Error</span>
                    </div>
                `;
            }});
        }}
        
        function loadUploadHistory() {{
            fetch('/api/uploads')
            .then(response => response.json())
            .then(data => {{
                const historyList = document.getElementById('history-list');
                if (data.uploads && data.uploads.length > 0) {{
                    historyList.innerHTML = data.uploads.map(upload => `
                        <div class="flex justify-between items-center py-2 border-b">
                            <div>
                                <span class="font-medium">${{upload.filename}}</span>
                                <br><small class="text-gray-500">${{new Date(upload.upload_date).toLocaleString()}}</small>
                            </div>
                            <span class="px-2 py-1 rounded text-sm bg-green-100 text-green-800">${{upload.status}}</span>
                        </div>
                    `).join('');
                }} else {{
                    historyList.innerHTML = '<p class="text-gray-500">No uploads yet</p>';
                }}
            }})
            .catch(error => {{
                document.getElementById('history-list').innerHTML = '<p class="text-red-500">Error loading history</p>';
            }});
        }}
        
        // Load upload history on page load
        loadUploadHistory();
    </script>
    </body></html>
    """


@app.route("/api/uploads")
def get_uploads():
    """Get user's upload history"""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        conn = sqlite3.connect("mapmystandards.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, filename, upload_date, status 
            FROM uploads 
            WHERE user_id = ? 
            ORDER BY upload_date DESC 
            LIMIT 20
        """, (session['user_id'],))
        
        uploads = []
        for row in cursor.fetchall():
            uploads.append({
                'id': row[0],
                'filename': row[1],
                'upload_date': row[2],
                'status': row[3]
            })
        
        conn.close()
        return jsonify({"uploads": uploads})
        
    except Exception as e:
        logger.error(f"Error fetching uploads: {e}")
        return jsonify({"error": "Failed to fetch uploads"}), 500


@app.route("/reports", methods=["GET"])
@app.route("/reports", methods=["GET"])
def reports_page():
    if "user_id" not in session:
        return redirect("/login")
    
    # Get user's data for reports
    try:
        conn = sqlite3.connect("mapmystandards.db")
        cursor = conn.cursor()
        
        # Get upload statistics
        cursor.execute("""
            SELECT COUNT(*) as total_uploads,
                   COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_uploads,
                   COUNT(CASE WHEN upload_date > datetime('now', '-7 days') THEN 1 END) as recent_uploads
            FROM uploads WHERE user_id = ?
        """, (session['user_id'],))
        
        stats = cursor.fetchone()
        total_uploads = stats[0] if stats else 0
        completed_uploads = stats[1] if stats else 0 
        recent_uploads = stats[2] if stats else 0
        
        # Get recent uploads for the activity feed
        cursor.execute("""
            SELECT filename, upload_date, status 
            FROM uploads 
            WHERE user_id = ? 
            ORDER BY upload_date DESC 
            LIMIT 5
        """, (session['user_id'],))
        
        recent_files = cursor.fetchall()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error fetching report data: {e}")
        total_uploads = completed_uploads = recent_uploads = 0
        recent_files = []
    
    return f"""
    <!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>Reports | MapMyStandards</title>
    <link rel='stylesheet' href='https://platform.mapmystandards.ai/assets/styles.css'>
    <link href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap' rel='stylesheet'>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #1f2937;
        }}
        .stat-label {{
            color: #6b7280;
            font-size: 0.875rem;
        }}
    </style></head>
    <body class='bg-gray-50 min-h-screen'>
    
    <nav class="bg-white shadow mb-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16"> 
                <div class="flex items-center">
                    <img src="https://mapmystandards.ai/wp-content/uploads/2025/07/Original-Logo.png" alt="MapMyStandards" class="h-8 w-auto"> 
                    <span class="ml-2 text-xl font-bold text-gray-900">MapMyStandards</span>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="/dashboard" class="text-gray-700 hover:text-gray-900">Dashboard</a>
                    <a href="/upload" class="text-gray-700 hover:text-gray-900">Upload</a>
                    <span class="text-gray-700">Welcome, {session.get('first_name', 'User')}!</span>
                    <a href="/logout" class="text-gray-500 hover:text-gray-700">Logout</a>
                </div>
            </div>
        </div>
    </nav>
    
    <div class='max-w-7xl mx-auto py-8 px-6'>
        <h1 class='text-3xl font-bold mb-8 text-gray-900'>Accreditation Analytics Dashboard</h1>
        
        <!-- Statistics Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="stat-card">
                <div class="stat-number">{total_uploads}</div>
                <div class="stat-label">Total Documents</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{completed_uploads}</div>
                <div class="stat-label">Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{recent_uploads}</div>
                <div class="stat-label">This Week</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{int((completed_uploads/total_uploads*100) if total_uploads > 0 else 0)}%</div>
                <div class="stat-label">Compliance Rate</div>
            </div>
        </div>
        
        <!-- Charts Row -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">Upload Trends</h3>
                <canvas id="uploadChart" width="400" height="200"></canvas>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">Compliance Status</h3>
                <canvas id="complianceChart" width="400" height="200"></canvas>
            </div>
        </div>
        
        <!-- Activity Feed -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">Recent Activity</h3>
                <div class="space-y-3">
                    {"".join([f'''
                    <div class="flex justify-between items-center py-2 border-b border-gray-100">
                        <div>
                            <span class="font-medium">{file[0]}</span>
                            <br><small class="text-gray-500">{file[1]}</small>
                        </div>
                        <span class="px-2 py-1 rounded text-xs bg-green-100 text-green-800">{file[2]}</span>
                    </div>
                    ''' for file in recent_files]) if recent_files else '<p class="text-gray-500">No recent activity</p>'}
                </div>
            </div>
            
            <div class="bg-white rounded-lg shadow p-6">
                <h3 class="text-lg font-semibold mb-4">Quick Actions</h3>
                <div class="space-y-3">
                    <a href="/upload" class="block w-full bg-blue-600 text-white text-center px-4 py-3 rounded-lg hover:bg-blue-700 transition">
                        📄 Upload New Documents
                    </a>
                    <button onclick="generateReport()" class="block w-full bg-green-600 text-white text-center px-4 py-3 rounded-lg hover:bg-green-700 transition">
                        📊 Generate Compliance Report
                    </button>
                    <button onclick="exportData()" class="block w-full bg-purple-600 text-white text-center px-4 py-3 rounded-lg hover:bg-purple-700 transition">
                        📤 Export Analytics Data
                    </button>
                </div>
            </div>
        </div>
        
        <div class="mt-8">
            <a href='/dashboard' class='inline-block bg-gray-800 text-white px-5 py-3 rounded-lg hover:bg-gray-900 transition'>&larr; Back to Dashboard</a>
        </div>
    </div>
    
    <script>
        // Upload Trends Chart
        const uploadCtx = document.getElementById('uploadChart').getContext('2d');
        new Chart(uploadCtx, {{
            type: 'line',
            data: {{
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug'],
                datasets: [{{
                    label: 'Documents Uploaded',
                    data: [2, 5, 3, 8, 12, 6, 9, {total_uploads}],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.1
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
        
        // Compliance Chart  
        const complianceCtx = document.getElementById('complianceChart').getContext('2d');
        new Chart(complianceCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Compliant', 'Needs Review', 'Non-Compliant'],
                datasets: [{{
                    data: [{completed_uploads}, {max(0, total_uploads - completed_uploads)}, 0],
                    backgroundColor: [
                        'rgb(34, 197, 94)',
                        'rgb(251, 191, 36)', 
                        'rgb(239, 68, 68)'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        function generateReport() {{
            alert('Generating compliance report... This feature will provide detailed PDF reports of your accreditation status.');
        }}
        
        function exportData() {{
            alert('Exporting analytics data... This feature will provide CSV/Excel exports of your compliance data.');
        }}
    </script>
    </body></html>
    """


@app.route("/api/email-status")
def email_status():
    """Check email system status for both admin and customer notifications"""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        status = {
            "email_service_configured": bool(email_service),
            "admin_email_configured": bool(ADMIN_EMAIL),
            "smtp_server": getattr(email_service, 'smtp_server', 'Not configured') if email_service else 'Not configured',
            "from_email": getattr(email_service, 'from_email', 'Not configured') if email_service else 'Not configured',
            "user_email": session.get('email', 'Unknown'),
            "notifications_enabled": True  # This would be user preference in production
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error checking email status: {e}")
        return jsonify({"error": "Failed to check email status"}), 500


@app.route("/api/send-test-email", methods=["POST"])
def send_test_email():
    """Send test email to customer"""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        user_email = session.get('email')
        user_name = session.get('first_name', 'User')
        
        if not user_email:
            return jsonify({"error": "User email not found"}), 400
        
        if not email_service:
            return jsonify({"error": "Email service not configured"}), 500
        
        # Send test email to customer
        subject = "MapMyStandards - Test Email Confirmation"
        message = f"""
        Hello {user_name},
        
        This is a test email to confirm that our email notification system is working correctly.
        
        Your MapMyStandards account details:
        - Email: {user_email}
        - Account Status: Active
        - Platform Access: Full access to upload and reporting features
        
        If you received this email, our notification system is working perfectly!
        
        Best regards,
        The MapMyStandards Team
        
        ---
        MapMyStandards - Accreditation Analytics Platform
        https://platform.mapmystandards.ai
        """
        
        email_service._send_email(user_email, subject, message)
        
        # Also notify admin about the test
        if ADMIN_EMAIL:
            admin_subject = f"Customer Test Email Sent - {user_name}"
            admin_message = f"Test email was successfully sent to customer {user_name} ({user_email})"
            email_service._send_email(ADMIN_EMAIL, admin_subject, admin_message)
        
        return jsonify({
            "success": True, 
            "message": f"Test email sent to {user_email}",
            "admin_notified": bool(ADMIN_EMAIL)
        })
        
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        return jsonify({"error": f"Failed to send test email: {str(e)}"}), 500


@app.route("/api/notifications")
def get_notifications():
    """Get user notifications and email activity"""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # In a production system, you'd have a notifications table
        # For now, we'll simulate some notifications based on user activity
        
        conn = sqlite3.connect("mapmystandards.db")
        cursor = conn.cursor()
        
        # Get recent uploads to create notifications
        cursor.execute("""
            SELECT filename, upload_date, status 
            FROM uploads 
            WHERE user_id = ? 
            ORDER BY upload_date DESC 
            LIMIT 10
        """, (session['user_id'],))
        
        uploads = cursor.fetchall()
        
        notifications = []
        for upload in uploads:
            notifications.append({
                "type": "upload",
                "title": f"File processed: {upload[0]}",
                "message": f"Your file {upload[0]} has been {upload[2]}",
                "date": upload[1],
                "status": "read" if upload[2] == "completed" else "unread"
            })
        
        # Add system notifications
        notifications.extend([
            {
                "type": "system",
                "title": "Welcome to MapMyStandards!",
                "message": "Your account is active and ready for accreditation analytics",
                "date": datetime.utcnow().isoformat(),
                "status": "read"
            },
            {
                "type": "feature", 
                "title": "New Features Available",
                "message": "Enhanced reporting and analytics now available in your dashboard",
                "date": datetime.utcnow().isoformat(),
                "status": "unread"
            }
        ])
        
        conn.close()
        return jsonify({"notifications": notifications})
        
    except Exception as e:
        logger.error(f"Error fetching notifications: {e}")
        return jsonify({"error": "Failed to fetch notifications"}), 500


@app.route("/subscriptions-debug")
def subs_debug():  # pragma: no cover
    try:
        conn = sqlite3.connect("mapmystandards.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, stripe_subscription_id, status, plan_type, trial_end FROM subscriptions ORDER BY id DESC LIMIT 20")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"count": len(rows), "subscriptions": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/logout")
def logout():
    """User logout"""
    session.clear()
    return redirect("/login")


@app.route("/favicon.ico")
def favicon_ico():
    # Prefer ico, fallback to svg, else 204-style empty response
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    ico_path = os.path.join(web_dir, 'favicon.ico')
    svg_path = os.path.join(web_dir, 'favicon.svg')
    if os.path.exists(ico_path):
        return app.send_static_file(os.path.relpath(ico_path, os.path.dirname(__file__)))  # may require static_folder config
    if os.path.exists(svg_path):
        try:
            with open(svg_path, 'r', encoding='utf-8') as f:
                return f.read(), 200, {"Content-Type": "image/svg+xml"}
        except Exception:
            pass
    return "", 204


@app.route("/landing")
def marketing_landing():
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    landing_path = os.path.join(web_dir, 'landing.html')
    if os.path.exists(landing_path):
        try:
            with open(landing_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Failed to read landing.html: {e}")
    return ("<h1>Landing page not found</h1>", 404)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
