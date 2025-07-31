# 🔧 A³E Troubleshooting Guide

## 🚀 **Quick Start**

### **Option 1: Use the Startup Script**
```bash
cd /Users/jeremyestrella/Desktop/MapMyStandards
./start_a3e.sh
```

### **Option 2: Manual Start**
```bash
cd /Users/jeremyestrella/Desktop/MapMyStandards
PYTHONPATH=/Users/jeremyestrella/Desktop/MapMyStandards/src \
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python \
-m uvicorn a3e.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🩺 **Common Issues & Solutions**

### **❌ "Connection Refused" or "Not launching"**

**Check if server is running:**
```bash
ps aux | grep uvicorn
```

**Check if port 8000 is in use:**
```bash
lsof -i :8000
```

**Kill existing processes:**
```bash
pkill -f uvicorn
```

### **❌ "ModuleNotFoundError: No module named 'a3e'"**

**Solution: Set PYTHONPATH correctly**
```bash
export PYTHONPATH=/Users/jeremyestrella/Desktop/MapMyStandards/src
```

### **❌ "Database connection failed"**

**Check PostgreSQL status:**
```bash
brew services list | grep postgresql
```

**Start PostgreSQL:**
```bash
brew services start postgresql@14
```

**Test database connection:**
```bash
psql -h localhost -p 5432 -U a3e -d a3e
```

### **❌ "Address already in use"**

**Kill processes using port 8000:**
```bash
lsof -ti:8000 | xargs kill -9
```

---

## 🌐 **Access Points**

Once the server is running, you can access:

- **Main API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Admin Interface**: http://localhost:8000/admin (if available)

---

## 📊 **Verify System Status**

```bash
# Test if server is responding
curl http://localhost:8000/health

# Test main endpoint
curl http://localhost:8000/

# Test proprietary capabilities
curl http://localhost:8000/api/v1/proprietary/capabilities
```

---

## 🔍 **Debug Mode**

If you need to see detailed logs:

```bash
cd /Users/jeremyestrella/Desktop/MapMyStandards
PYTHONPATH=/Users/jeremyestrella/Desktop/MapMyStandards/src \
/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python \
-m uvicorn a3e.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

---

## 🆘 **Still Having Issues?**

1. **Check the terminal output** for specific error messages
2. **Verify all dependencies** are installed:
   ```bash
   pip3 list | grep -E "(fastapi|uvicorn|sqlalchemy|psycopg2)"
   ```
3. **Check the .env file** exists and has proper values
4. **Restart PostgreSQL** if database issues persist
5. **Try a different port** if 8000 is busy:
   ```bash
   --port 8001
   ```

---

## ✅ **Expected Startup Output**

When working correctly, you should see:
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
2025-XX-XX XX:XX:XX,XXX - a3e.main - INFO - 🚀 Starting A3E Application...
...
2025-XX-XX XX:XX:XX,XXX - a3e.main - INFO - ✅ Database service initialized
...
2025-XX-XX XX:XX:XX,XXX - a3e.main - INFO - 🎉 A3E Application startup complete!
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```
