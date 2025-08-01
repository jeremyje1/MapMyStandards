# 🔐 Generate Titan Email App Password for SMTP

## The Issue
Your SMTP authentication is failing because Titan Email requires **app-specific passwords** for SMTP access, not your regular login password.

## ✅ Solution: Generate App Password

### Step 1: Access Titan Email Dashboard
1. 🌐 Go to: https://cp.titan.email
2. 🔐 Login with: `support@mapmystandards.ai` and password `MapMyStandardsSMTP1*`

### Step 2: Generate App Password
1. 📧 Once logged in, look for **"Security"** or **"App Passwords"** section
2. 🔑 Click **"Generate App Password"** or **"Create App Password"**
3. 📝 Name it: `MapMyStandards SMTP`
4. 💾 **SAVE THE GENERATED PASSWORD** - you won't see it again!

### Step 3: Update Configuration
Replace your current password in `.env` with the app password:

```bash
# In your .env file:
SMTP_PASSWORD=your_new_app_password_here
```

### Step 4: Test Again
Run the test script:
```bash
python test_comprehensive_smtp.py
```

## 🚨 Can't Find App Passwords?

If you can't find the app password option in Titan Email:

### Alternative 1: Check Account Settings
- Look in: **Account Settings** → **Security** → **App Passwords**
- Or: **Mail Settings** → **SMTP/IMAP Access**

### Alternative 2: Enable IMAP/SMTP Access
Some Titan accounts have IMAP/SMTP disabled by default:
1. Go to **Mail Settings**
2. Look for **"IMAP/SMTP Access"** or **"External Access"**
3. Enable it
4. Try your regular password again

### Alternative 3: Contact Namecheap Support
If app passwords aren't available:
1. 📞 Contact Namecheap support
2. 📝 Tell them: "I need to enable SMTP authentication for support@mapmystandards.ai"
3. 🎯 Ask specifically about app passwords or SMTP access

## 🔄 Quick Alternative: Use Gmail SMTP

If Titan continues to be problematic, you can temporarily use Gmail:

1. Create a Gmail account: `mapmystandardsai@gmail.com`
2. Enable 2-factor authentication
3. Generate an app password
4. Update your `.env`:
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=mapmystandardsai@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_USE_TLS=true
```

## 📞 Need Help?

**Namecheap Titan Email Support:**
- 📧 Email: support@namecheap.com
- 💬 Live chat via Namecheap dashboard
- 📞 Phone: Available in your account dashboard

**What to tell them:**
> "I need to set up SMTP authentication for my Titan Email account support@mapmystandards.ai. The regular password isn't working for SMTP. I need either an app-specific password or to enable SMTP access."

---

## 🎯 Expected Result

Once you have the correct app password, your test should show:

```
✅ AUTHENTICATION SUCCESSFUL!
🎉 Working configuration found: Titan Email Standard
📧 Testing email send...
✅ Test email sent successfully!
```

Then your MapMyStandards.ai contact forms and email notifications will work perfectly!
