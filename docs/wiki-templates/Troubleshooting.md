# 🐛 Troubleshooting Guide

This guide helps you diagnose and fix common issues with Kuroibara. Start with the most common problems below, then move to specific sections.

---

## 🚨 **Quick Fixes for Common Issues**

### **🔍 Search Not Working**
1. **Check provider status** in Settings → Provider Preferences
2. **Enable more providers** if only a few are selected
3. **Clear browser cache** and refresh the page
4. **Check internet connection** and try again

### **📚 Can't Add Manga to Library**
1. **Verify you're logged in** (check top-right corner)
2. **Try refreshing the page** and searching again
3. **Check if manga already exists** in your library
4. **Clear browser cache** if the issue persists

### **🖼️ Missing Cover Images**
1. **Wait a few seconds** for images to load
2. **Check your internet connection**
3. **Try a different provider** for the same manga
4. **Disable ad blockers** temporarily

### **🔐 Login Issues**
1. **Check username/password** for typos
2. **Clear browser cookies** for the site
3. **Try incognito/private browsing** mode
4. **Reset password** if needed

---

## 🔧 **Installation & Setup Issues**

### **Docker Problems**

#### **Container Won't Start**
```bash
# Check Docker status
docker --version
docker compose --version

# View container logs
docker compose logs

# Restart containers
docker compose down
docker compose up -d
```

#### **Port Already in Use**
```bash
# Find what's using the port
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Change ports in docker-compose.yml
ports:
  - "3001:3000"  # Change external port
```

#### **Database Connection Failed**
```bash
# Check database container
docker compose ps
docker compose logs postgres

# Reset database
docker compose down -v
docker compose up -d
```

### **Manual Installation Problems**

#### **Python Dependencies Fail**
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# Try with --no-cache-dir
pip install --no-cache-dir -r requirements.txt
```

#### **Node.js Build Fails**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules
rm -rf node_modules package-lock.json
npm install

# Try with different Node version
nvm use 22
npm install
```

#### **Database Migration Errors**
```bash
# Check database connection
psql -h localhost -U kuroibara -d kuroibara

# Reset migrations
alembic downgrade base
alembic upgrade head

# Create database if missing
createdb kuroibara
```

---

## 🌐 **Provider Issues**

### **No Search Results**
1. **Check provider status** in settings
2. **Try different search terms** (alternative spellings)
3. **Enable more providers** for better coverage
4. **Check provider-specific issues** below

### **Slow Search Performance**
1. **Disable slow providers** in preferences
2. **Limit concurrent searches** in settings
3. **Use favorite providers** for faster results
4. **Clear provider cache** if available

### **Provider-Specific Issues**

#### **MangaFox Issues**
- **Status**: Check if fanfox.net is accessible
- **Search**: Try exact manga titles
- **Images**: May load slowly, wait a few seconds

#### **MangaBat Issues**
- **URL**: Ensure using mangabats.com (not mangabat.com)
- **Search**: Use popular manga titles for testing
- **Access**: Check if site is blocked in your region

#### **Toonily Issues**
- **NSFW Content**: Enable NSFW in settings if needed
- **Search**: Try manhwa/manhua titles specifically
- **Loading**: May be slower due to site complexity

---

## 📱 **User Interface Issues**

### **Page Not Loading**
1. **Refresh the page** (Ctrl+F5 or Cmd+Shift+R)
2. **Clear browser cache** and cookies
3. **Try incognito/private mode**
4. **Check browser console** for errors (F12)

### **Buttons Not Working**
1. **Ensure JavaScript is enabled**
2. **Disable browser extensions** temporarily
3. **Try a different browser**
4. **Check for popup blockers**

### **Mobile Issues**
1. **Use supported browsers** (Chrome, Safari, Firefox)
2. **Enable JavaScript** on mobile
3. **Clear mobile browser cache**
4. **Try desktop version** if mobile fails

### **Dark Mode Problems**
1. **Check theme setting** in preferences
2. **Clear browser cache** after theme change
3. **Refresh page** to apply new theme
4. **Try system theme** if custom themes fail

---

## 🔐 **Authentication & Account Issues**

### **Can't Register**
1. **Check if registration is enabled** (admin setting)
2. **Use valid email format**
3. **Choose unique username**
4. **Check password requirements**

### **Email Verification**
1. **Check spam/junk folder**
2. **Wait up to 10 minutes** for email
3. **Request new verification** if needed
4. **Contact admin** if email never arrives

### **Password Reset**
1. **Use email associated with account**
2. **Check spam folder** for reset email
3. **Link expires in 1 hour** - request new one if needed
4. **Clear browser cache** before trying new password

### **Session Expires Quickly**
1. **Check "Remember Me"** when logging in
2. **Clear browser cookies** and log in again
3. **Check system time** is correct
4. **Contact admin** if issue persists

---

## 📊 **Performance Issues**

### **Slow Loading**
1. **Check internet connection** speed
2. **Close unnecessary browser tabs**
3. **Clear browser cache** regularly
4. **Disable browser extensions** temporarily

### **High Memory Usage**
1. **Close unused tabs**
2. **Restart browser** periodically
3. **Limit concurrent downloads**
4. **Check for memory leaks** in browser console

### **Search Takes Too Long**
1. **Reduce number of enabled providers**
2. **Use more specific search terms**
3. **Check provider response times** in settings
4. **Try searching during off-peak hours**

---

## 🔍 **Debugging Steps**

### **Browser Console Errors**
1. **Open Developer Tools** (F12)
2. **Check Console tab** for errors
3. **Look for red error messages**
4. **Copy error details** for support requests

### **Network Issues**
1. **Check Network tab** in Developer Tools
2. **Look for failed requests** (red entries)
3. **Check response codes** (404, 500, etc.)
4. **Verify API endpoints** are accessible

### **Server Logs**
```bash
# Docker logs
docker compose logs backend
docker compose logs frontend

# Manual installation logs
tail -f backend/logs/app.log
```

---

## 🆘 **Getting Additional Help**

### **Before Asking for Help**
1. **Try the solutions above** first
2. **Check [Common Issues](Common-Issues)** page
3. **Search existing [issues](https://github.com/Futs/kuroibara/issues)**
4. **Gather error details** and system information

### **Information to Include**
- **Operating System** and version
- **Browser** and version
- **Installation method** (Docker/Manual)
- **Error messages** (exact text)
- **Steps to reproduce** the issue
- **Screenshots** if helpful

### **Where to Get Help**
- **[GitHub Issues](https://github.com/Futs/kuroibara/issues)** - Bug reports
- **[GitHub Discussions](https://github.com/Futs/kuroibara/discussions)** - Questions
- **[Common Issues](Common-Issues)** - Quick solutions
- **[Installation Guide](Installation)** - Setup help

---

## 🔄 **Still Having Issues?**

If none of these solutions work:

1. **Create a detailed issue** on GitHub
2. **Include all relevant information** listed above
3. **Be patient** - maintainers will respond when available
4. **Check for updates** - your issue might be fixed in newer versions

---

## 🧭 **Navigation**

**🏠 Home**: [Wiki Home](Home)  
**← Previous**: [Common Issues](Common-Issues)  
**→ Next**: [Performance Optimization](Performance-Optimization)

---

*Last updated: December 2024 | Having trouble? [Create an issue](https://github.com/Futs/kuroibara/issues/new)*
