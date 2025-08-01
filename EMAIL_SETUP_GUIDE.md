# Email Account Setup Guide for MapMyStandards.ai

## Current Status
❌ **Email account `support@mapmystandards.ai` needs to be created**

The SMTP servers are accessible but not accepting authentication, which indicates the email account hasn't been created yet.

## Step-by-Step Setup Instructions

### 1. Access Your Hosting Control Panel
- Log into your WordPress hosting provider's control panel
- Look for "Email" or "Email Management" section
- Some providers call it "Titan Email" or "Professional Email"

### 2. Create the Email Account
- Navigate to "Create New Email Account" or similar
- **Email Address**: `support@mapmystandards.ai`
- **Password**: `Ipo4Eva45*`
- **Mailbox Size**: Choose appropriate size (usually 5GB+ recommended)

### 3. Alternative SMTP Settings to Try
Different hosting providers may use different SMTP configurations:

**Option A - Titan Email (Current)**
```
SMTP Server: mx1.titan.email
Port: 587
Security: STARTTLS
Username: support@mapmystandards.ai
Password: Ipo4Eva45*
```

**Option B - WordPress.com Business Email**
```
SMTP Server: smtp.titan.email
Port: 587
Security: STARTTLS
Username: support@mapmystandards.ai
Password: Ipo4Eva45*
```

**Option C - Alternative Settings**
```
SMTP Server: mail.mapmystandards.ai
Port: 587 or 465
Security: STARTTLS or SSL/TLS
Username: support@mapmystandards.ai
Password: Ipo4Eva45*
```

### 4. Verify Email Account Creation
After creating the account, you should be able to:
- Log into webmail (usually at mail.mapmystandards.ai or via hosting panel)
- Send and receive test emails
- See the account listed in your hosting panel

### 5. Test Configuration
Once the account is created, run this test:
```bash
python comprehensive_email_test.py
```

## Common Hosting Provider Instructions

### WordPress.com Business
1. Go to My Sites → Settings → Email
2. Click "Add Email Address"
3. Follow the setup wizard

### Bluehost/HostGator/Similar
1. cPanel → Email Accounts
2. Create Account
3. Enter details and create

### GoDaddy
1. My Products → Email & Office
2. Manage → Create Account

### Namecheap
1. Domain List → Manage → Email
2. Add Email Account

## What to Do Next
1. **Create the email account** using your hosting provider's panel
2. **Verify the account works** by logging into webmail
3. **Test our email system** again
4. **Update SMTP settings** if needed based on your provider's recommendations

## Need Help?
- Check your hosting provider's email setup documentation
- Contact their support if you can't find the email management section
- Some providers have specific SMTP server addresses for their email service

The email infrastructure (DNS records) is perfect - we just need the actual email account to exist!
