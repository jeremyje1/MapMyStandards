# 🚀 DEPLOYMENT GUIDE - MAPMY STANDARDS

## 🎯 **DEPLOYMENT OVERVIEW:**

### **Frontend (Vercel):**
- Clean pricing page with correct pricing
- Professional signup flow
- Static files served via CDN

### **Backend (Your Server):**
- Flask API for user management
- Stripe integration with webhooks
- Database and session management

---

## 📋 **STEP 1: DEPLOY FRONTEND TO VERCEL**

```bash
# Install Vercel CLI if needed
npm i -g vercel

# Deploy frontend
vercel --prod

# Your frontend will be available at:
# https://your-project.vercel.app
```

**Frontend URLs:**
- `https://your-project.vercel.app/pricing` - Pricing page
- `https://your-project.vercel.app/signup` - Customer signup
- `https://your-project.vercel.app/contact` - Contact form

---

## 🖥️ **STEP 2: DEPLOY BACKEND TO PRODUCTION**

### **Option A: DigitalOcean Droplet**
```bash
# 1. Create droplet (Ubuntu 20.04)
# 2. SSH into server
ssh root@your-server-ip

# 3. Install dependencies
apt update && apt install python3 python3-pip python3-venv nginx -y

# 4. Clone your repository
git clone https://github.com/jeremyje1/MapMyStandards.git
cd MapMyStandards

# 5. Set up environment
python3 -m venv backend_env
source backend_env/bin/activate
pip install flask flask-cors stripe gunicorn

# 6. Set environment variables
export STRIPE_SECRET_KEY="your_secret_key"
export STRIPE_PUBLISHABLE_KEY="your_publishable_key"
export MONTHLY_PRICE_ID="price_1RtXF3K8PKpLCKDZJNfi3Rvi"
export ANNUAL_PRICE_ID="price_1RtXF3K8PKpLCKDZAMb4rM8U"

# 7. Start with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 subscription_backend:app
```

### **Option B: Railway/Render**
```bash
# 1. Create requirements.txt
echo "flask
flask-cors
stripe
gunicorn" > requirements.txt

# 2. Create Procfile
echo "web: gunicorn subscription_backend:app" > Procfile

# 3. Deploy to Railway/Render with environment variables
```

---

## 🔗 **STEP 3: CONFIGURE STRIPE WEBHOOKS**

### **Webhook Endpoint:**
```
https://your-backend-domain.com/webhook
```

### **Events to Select:**
- `customer.subscription.created`
- `invoice.payment_succeeded` 
- `customer.subscription.trial_will_end`
- `customer.subscription.deleted`

### **Get Webhook Secret:**
1. Copy webhook signing secret from Stripe dashboard
2. Add to environment variables: `STRIPE_WEBHOOK_SECRET=whsec_...`

---

## ⚙️ **STEP 4: UPDATE FRONTEND URLs**

Update `signup.html` line ~95:
```javascript
const BACKEND_URL = 'https://your-backend-domain.com';
```

Redeploy frontend:
```bash
vercel --prod
```

---

## 🧪 **STEP 5: TEST COMPLETE FLOW**

### **End-to-End Test:**
1. Visit: `https://your-frontend.vercel.app/pricing`
2. Click "Start Free Trial"
3. Complete signup form
4. Add test payment method
5. Verify trial activation
6. Check welcome email
7. Test login/dashboard

### **Test Cards (Stripe):**
- Success: `4242 4242 4242 4242`
- Declined: `4000 0000 0000 0002`

---

## 📊 **MONITORING & MAINTENANCE**

### **Check Health:**
```bash
curl https://your-backend.com/health
```

### **Monitor Logs:**
```bash
tail -f /var/log/mapmystandards.log
```

### **Database Backup:**
```bash
cp mapmystandards.db backup_$(date +%Y%m%d).db
```

---

## 🔒 **SECURITY CHECKLIST**

- ✅ Environment variables (no hardcoded keys)
- ✅ HTTPS enabled for backend
- ✅ Stripe webhook signature verification
- ✅ Session security
- ✅ Database access controls
- ✅ Regular backups

---

## 🎉 **YOU'RE LIVE!**

**Frontend:** Professional pricing and signup
**Backend:** Complete user management and billing
**Integration:** Seamless Stripe trial flow

**Your customers now have a world-class experience!** 🚀
