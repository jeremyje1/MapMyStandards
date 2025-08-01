# How to Get SMTP Configuration Details for Titan Email

## 🎯 **Quick Action Steps**

### Option 1: Live Chat with Namecheap (FASTEST)
1. **Go to**: https://www.namecheap.com/help-center/live-chat/
2. **Say**: "I need SMTP settings for my Titan Email account on mapmystandards.ai for application integration"
3. **They should provide**:
   - Exact SMTP server hostname
   - Port number
   - Security settings
   - Authentication requirements

### Option 2: Check Your Namecheap Account
1. **Login to**: https://ap.www.namecheap.com/
2. **Navigate to**: Domain List → Manage (mapmystandards.ai)
3. **Look for**: 
   - "Professional Email" or "Titan Email" section
   - "Email Client Setup" or "Mail Settings"
   - "SMTP Configuration" link

### Option 3: Check Titan Webmail Settings
Since you already have webmail access:
1. **Login** to your Titan webmail interface
2. **Look for**: Settings ⚙️ or Account
3. **Find**: "Email Client Setup" or "SMTP Settings"
4. **Common locations**:
   - Settings → Mail Client Configuration
   - Account → SMTP/IMAP Settings
   - Help → Email Client Setup

## 📋 **Standard Titan Email SMTP Settings**

Based on common Titan configurations, try these:

### Configuration A (Most Common):
```
SMTP Server: smtp.titan.email
Port: 587
Security: STARTTLS
Username: support@mapmystandards.ai
Password: Ipo4Eva45*
```

### Configuration B (Alternative):
```
SMTP Server: mail.mapmystandards.ai
Port: 587
Security: STARTTLS
Username: support@mapmystandards.ai
Password: Ipo4Eva45*
```

### Configuration C (SSL):
```
SMTP Server: smtp.titan.email
Port: 465
Security: SSL/TLS
Username: support@mapmystandards.ai
Password: Ipo4Eva45*
```

## 🔧 **Testing Each Configuration**

Let me create a test script for you:

```python
# Test script to try different configurations
python test_multiple_smtp_configs.py
```

## 📞 **Contact Information**

### Namecheap Support:
- **Live Chat**: https://www.namecheap.com/help-center/live-chat/
- **Phone**: +1 646-535-0457 (US)
- **Ticket**: https://support.namecheap.com/

### What to Ask:
> "Hi, I have a Titan Email account for mapmystandards.ai and need the SMTP server configuration for sending emails from my application. Can you provide the server, port, and authentication settings?"

## 🚨 **Common Issues & Solutions**

### Issue: Error 535 "Authentication failed" (MOST COMMON)
**Root Cause**: App-specific password required for SMTP access

**Solutions**:
1. **Check for 2FA**: If two-factor authentication is enabled, you MUST use an app-specific password
2. **Generate App Password**: Look in Titan Email dashboard for "App Passwords" or "Application Passwords"
3. **Verify exact credentials**: Ensure no extra spaces or characters in username/password
4. **Try password reset**: Reset your email password and try again

### Issue: "AUTH not supported"
- **Solution**: Try different server (smtp.titan.email vs mail.mapmystandards.ai)

### Issue: "Connection refused"
- **Solution**: Try different port (587 vs 465)

## 🔑 **App-Specific Password Setup**

Since Error 535 usually indicates need for app-specific password:

### Step 1: Check Your Titan Email Dashboard
1. **Login to webmail** (your current working interface)
2. **Look for**:
   - "Security" or "Account Security"
   - "App Passwords" or "Application Passwords" 
   - "Two-Factor Authentication" settings
   - "Third-Party Apps" or "Mail Client Access"

### Step 2: Generate App Password
1. **Find**: "Generate App Password" or "Create Application Password"
2. **Name it**: "MapMyStandards SMTP" or similar
3. **Copy the generated password** (usually different from your webmail password)
4. **Use this password** instead of your regular password

### Step 3: Test with App Password
```bash
# Update your .env file with the app-specific password
SMTP_PASSWORD=your_app_specific_password_here
```

## 🎯 **Next Steps**

1. **Try live chat first** - fastest way to get exact settings
2. **Test each configuration** using our test script
3. **Document working settings** for future use

The exact settings depend on how Namecheap has configured your specific Titan Email service!
