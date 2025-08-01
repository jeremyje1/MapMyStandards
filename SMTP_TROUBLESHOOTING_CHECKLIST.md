# Titan Email SMTP Setup Checklist

## 🎯 **Current Status**
✅ Email account exists: support@mapmystandards.ai  
✅ Webmail access working  
✅ SMTP server responding: smtp.titan.email:587/465  
❌ SMTP authentication failing (Error 535)  

## 🔍 **Error 535 Diagnosis**

**Error 535 = Authentication Failure**

Since your webmail works but SMTP fails, this typically means:
1. **App-specific password required** (most common)
2. **Two-factor authentication enabled** 
3. **SMTP access needs special activation**

## 📋 **Step-by-Step Solution**

### Step 1: Check for Two-Factor Authentication
1. **Login to your Titan webmail**
2. **Look for**: Security settings or Account settings
3. **Check if 2FA is enabled** - if YES, you need an app password

### Step 2: Generate App-Specific Password
**In your Titan Email dashboard, look for:**
- "App Passwords" or "Application Passwords"
- "Security" → "App-specific passwords"
- "Account" → "Third-party apps"
- "Settings" → "Mail client access"

**If found:**
1. Click "Generate new password" or "Create app password"
2. Name it: "MapMyStandards SMTP"
3. **Copy the generated password** (it's different from your webmail password)
4. Use this password for SMTP

### Step 3: Verify SMTP Settings
**Use these exact settings:**
```
SMTP Server: smtp.titan.email
Port: 587 (preferred) or 465
Security: STARTTLS (for 587) or SSL (for 465)
Username: support@mapmystandards.ai
Password: [your app-specific password]
```

### Step 4: Test Configuration
```bash
# Run this test with your app password
python test_app_password.py
```

## 🚨 **If App Passwords Not Available**

### Option A: Contact Namecheap Support
**Live Chat**: https://www.namecheap.com/help-center/live-chat/

**Say exactly this:**
> "I have Titan Email for mapmystandards.ai. Webmail works but SMTP gives error 535. Do I need to generate an app-specific password for SMTP access? If so, where do I find this in my dashboard?"

### Option B: Try Password Reset
1. **Reset your email password** in Titan Email settings
2. **Use the new password** for both webmail and SMTP
3. **Test immediately** after reset

### Option C: Check SMTP Authentication Method
Make sure your application uses:
- **Authentication**: Normal password (not OAuth)
- **Security**: STARTTLS or SSL (not None)
- **Username**: Full email address

## ✅ **Success Indicators**

When it works, you'll see:
- ✅ SMTP connection successful
- ✅ Authentication successful  
- ✅ Your contact forms will send emails
- ✅ Welcome emails will be delivered

## 📞 **Support Resources**

**Namecheap Support:**
- Live Chat: https://www.namecheap.com/help-center/live-chat/
- Phone: +1 646-535-0457
- Ticket: https://support.namecheap.com/

**What to ask:**
- "How do I set up SMTP for my Titan Email account?"
- "Do I need an app-specific password for SMTP?"
- "Where do I find app password settings in Titan Email?"

## 🎯 **Most Likely Solution**

Based on Error 535 with working webmail, **99% chance you need an app-specific password**. Look for this option in your Titan Email security settings first!
