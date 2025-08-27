# 📧 Email System Deployment Guide

Complete guide for deploying the Postmark email notification system for MapMyStandards A³E platform.

## ✅ What's Been Implemented

### Email Notifications
- **Welcome Emails**: Sent to new trial users with API key and onboarding information
- **Assessment Complete**: Notifies users when document analysis finishes
- **Report Generation**: Alerts users when reports are ready for download
- **Admin Notifications**: Alerts admins about signups and milestone completions

### Email Types Supported
1. **Customer Welcome** (`send_welcome_email`)
2. **Assessment Complete** (`send_assessment_complete_notification`) 
3. **Admin Signup Alert** (`send_admin_signup_notification`)
4. **Admin Milestone Alerts** (analysis complete, report generated)

## 🔧 Environment Variables Required

Add these to your production environment (Railway, Heroku, etc.):

```bash
# Postmark Configuration
POSTMARK_SERVER_TOKEN=your_server_token_here
EMAIL_FROM=support@mapmystandards.ai
EMAIL_FROM_NAME=MapMyStandards A³E
ADMIN_NOTIFICATION_EMAIL=admin@mapmystandards.ai

# Public URLs (used in email links)
PUBLIC_APP_URL=https://platform.mapmystandards.ai
PUBLIC_API_URL=https://api.mapmystandards.ai
```

## 🚀 Deployment Steps

### 1. Configure Postmark Account
1. Login to [Postmark](https://postmarkapp.com)
2. Create/select your server
3. Copy the Server Token from the API tab
4. Verify sender signatures for:
   - `support@mapmystandards.ai` 
   - `admin@mapmystandards.ai`

### 2. Set Environment Variables

#### Railway Deployment
```bash
railway variables set POSTMARK_SERVER_TOKEN=your_token_here
railway variables set EMAIL_FROM=support@mapmystandards.ai
railway variables set EMAIL_FROM_NAME="MapMyStandards A³E"
railway variables set ADMIN_NOTIFICATION_EMAIL=admin@mapmystandards.ai
```

#### Docker/Local
```bash
export POSTMARK_SERVER_TOKEN=your_token_here
export EMAIL_FROM=support@mapmystandards.ai
export EMAIL_FROM_NAME="MapMyStandards A³E" 
export ADMIN_NOTIFICATION_EMAIL=admin@mapmystandards.ai
```

### 3. Test Email System

Run the test script to verify everything works:

```bash
python test_email_system.py
```

Expected output:
```
🧪 Testing MapMyStandards Email Notification System
============================================================
✅ Postmark API Key: ********12345678
📧 From Email: support@mapmystandards.ai
👑 Admin Email: admin@mapmystandards.ai

📬 Testing Email Notifications:
----------------------------------------
1. Testing welcome email...
   ✅ SUCCESS
2. Testing admin signup notification...
   ✅ SUCCESS
...
🎉 ALL TESTS PASSED! Email system is working correctly.
```

### 4. Deploy Application

Deploy your application with the new email system:

```bash
# Railway
railway up

# Or manual deployment
git add .
git commit -m "Add Postmark email notification system"
git push
```

## 📁 Files Modified/Created

### Core Email Service
- `src/a3e/services/postmark_service.py` - Main email service
- `src/a3e/core/config.py` - Added Postmark configuration

### Integration Points
- `src/a3e/api/routes/trial.py` - Trial signup emails
- `src/a3e/api/routes/uploads_db.py` - Analysis complete notifications  
- `src/a3e/api/routes/reports.py` - Report generation notifications

### Testing & Documentation
- `test_email_system.py` - Email system test script
- `EMAIL_DEPLOYMENT_GUIDE.md` - This deployment guide

## 🔍 Email Flow Overview

### Trial Signup Flow
1. User signs up → `trial.py:signup_trial`
2. Background task calls `send_welcome_email` → Customer receives welcome
3. Background task calls `send_admin_signup_notification` → Admin receives alert

### Document Analysis Flow  
1. User uploads file → `uploads_db.py:upload_file`
2. Analysis completes → `process_analysis_job`
3. Calls `send_analysis_complete_notification` → Customer receives results
4. Calls `send_admin_signup_notification` (milestone) → Admin receives activity alert

### Report Generation Flow
1. User requests report → `reports.py:generate_report`
2. Report completes → `generate_report_background`
3. Calls `send_report_complete_notification` → Customer receives download link
4. Calls `send_admin_signup_notification` (milestone) → Admin receives activity alert

## 🎨 Email Templates

All emails feature:
- **Professional Design**: Modern, responsive HTML templates
- **Branding**: MapMyStandards A³E colors and styling
- **Clear CTAs**: Prominent action buttons
- **Mobile Friendly**: Responsive design for all devices
- **Rich Content**: Progress metrics, compliance scores, action items

### Template Types
- **Welcome Email**: Onboarding flow with API key and getting started guide
- **Assessment Complete**: Results summary with compliance scores
- **Report Ready**: Download links with report previews
- **Admin Alerts**: User activity summaries with recommended actions

## 🛠️ Troubleshooting

### Common Issues

**No emails sent:**
- Check `POSTMARK_SERVER_TOKEN` is set correctly
- Verify sender signatures in Postmark dashboard
- Check application logs for error messages

**Emails in spam:**
- Add SPF/DKIM records as shown in Postmark
- Use verified sending domains
- Monitor reputation in Postmark dashboard  

**Template formatting issues:**
- Test emails across different clients (Gmail, Outlook, Apple Mail)
- Use Postmark's email preview tools
- Check HTML/CSS validation

### Debug Commands

Check configuration:
```bash
python -c "from src.a3e.core.config import get_settings; s=get_settings(); print(f'Postmark: {bool(s.POSTMARK_SERVER_TOKEN)}, From: {s.EMAIL_FROM}')"
```

Test single email:
```bash
python -c "
from src.a3e.services.postmark_service import postmark_service
result = postmark_service.send_welcome_email('test@example.com', 'Test User', 'api_123')
print('SUCCESS' if result else 'FAILED')
"
```

## 📊 Monitoring & Analytics

### Postmark Dashboard
- Track delivery rates and bounce rates
- Monitor email opens and clicks  
- View detailed sending statistics
- Set up webhook notifications for bounces

### Application Logs
Email events are logged with emojis for easy identification:
- `📧` = Email sent successfully
- `⚠️` = Email failed to send  
- `❌` = Email system error

### Recommended Alerts
Set up monitoring for:
- Email delivery failures > 5%
- Bounce rates > 2%
- Admin notification delays > 5 minutes

## 🔐 Security Considerations

- **API Key Security**: Store Postmark tokens in environment variables only
- **Email Content**: Never include sensitive data in email bodies
- **Rate Limiting**: Postmark handles rate limiting automatically
- **Sender Reputation**: Monitor for spam complaints and bounces

## 📈 Future Enhancements

Planned improvements:
- **Email Templates**: Postmark template integration for easier management
- **Unsubscribe Handling**: User preference management
- **Email Scheduling**: Delayed and recurring notifications
- **A/B Testing**: Template and subject line testing
- **Advanced Analytics**: Custom email event tracking

---

## 🆘 Support

For issues with this email system:

1. Check the test script results: `python test_email_system.py`
2. Review application logs for email-related errors
3. Verify Postmark dashboard for delivery issues
4. Contact dev team with specific error messages

**System Status**: ✅ **READY FOR PRODUCTION**

The email notification system is fully implemented and tested, providing comprehensive customer communication and admin activity monitoring for the MapMyStandards A³E platform.