# 🐛 Common Issues & Quick Fixes

Quick solutions to the most frequently encountered problems. For detailed troubleshooting, see the [Troubleshooting Guide](Troubleshooting).

---

## 🚨 **Most Common Issues**

### **🔍 1. Search Returns No Results**

**Symptoms**: Search box shows no manga results

**Quick Fixes**:

- ✅ **Check spelling** - Try alternative spellings or romanizations
- ✅ **Enable more providers** - Go to Settings → Provider Preferences
- ✅ **Try popular titles** - Search for "One Piece" or "Naruto" to test
- ✅ **Clear browser cache** - Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

**If still not working**: See [Provider Issues](Troubleshooting#provider-issues)

---

### **📚 2. Can't Add Manga to Library**

**Symptoms**: "+" button doesn't work or manga doesn't appear in library

**Quick Fixes**:

- ✅ **Check login status** - Look for username in top-right corner
- ✅ **Refresh the page** - F5 or reload button
- ✅ **Try different browser** - Test in incognito/private mode
- ✅ **Check if already added** - Search your library first

**If still not working**: See [Authentication Issues](Troubleshooting#authentication--account-issues)

---

### **🖼️ 3. Missing Cover Images**

**Symptoms**: Gray boxes instead of manga cover images

**Quick Fixes**:

- ✅ **Wait 10-15 seconds** - Images may load slowly
- ✅ **Disable ad blockers** - Temporarily disable for the site
- ✅ **Check internet connection** - Test other websites
- ✅ **Try different provider** - Some providers have better images

**If still not working**: See [Provider Issues](Troubleshooting#provider-issues)

---

### **🔐 4. Login Problems**

**Symptoms**: Can't log in or session expires quickly

**Quick Fixes**:

- ✅ **Check credentials** - Verify username and password
- ✅ **Clear browser cookies** - Delete site cookies and try again
- ✅ **Try incognito mode** - Test in private browsing
- ✅ **Reset password** - Use "Forgot Password" if needed

**If still not working**: See [Authentication Issues](Troubleshooting#authentication--account-issues)

---

### **⚡ 5. Slow Performance**

**Symptoms**: Pages load slowly or searches take too long

**Quick Fixes**:

- ✅ **Close other tabs** - Reduce browser memory usage
- ✅ **Disable slow providers** - Go to Settings → Provider Preferences
- ✅ **Clear browser cache** - Free up storage space
- ✅ **Restart browser** - Fresh start often helps

**If still not working**: See [Performance Issues](Troubleshooting#performance-issues)

---

## 🔧 **Installation Issues**

### **🐳 Docker Won't Start**

**Quick Fixes**:

```bash
# Check Docker is running
docker --version

# Restart Docker service
sudo systemctl restart docker  # Linux
# Or restart Docker Desktop on Windows/Mac

# Try starting again
docker compose up -d
```

### **🌐 Can't Access Web Interface**

**Quick Fixes**:

- ✅ **Check URL** - Try http://localhost:3000
- ✅ **Check ports** - Ensure 3000 and 8000 aren't in use
- ✅ **Wait for startup** - Give containers 2-3 minutes to start
- ✅ **Check logs** - `docker compose logs` for errors

### **💾 Database Connection Failed**

**Quick Fixes**:

```bash
# Reset database
docker compose down -v
docker compose up -d

# Check database logs
docker compose logs postgres
```

---

## 🌐 **Provider-Specific Issues**

### **MangaFox Problems**

- **No results**: Try exact manga titles
- **Slow loading**: Wait 10-15 seconds for images
- **Status unknown**: This is normal, status detection is limited

### **MangaBat Problems**

- **Site unreachable**: Check if mangabats.com is accessible
- **No images**: Try refreshing or different manga
- **Search fails**: Use popular manga titles for testing

### **Toonily Problems**

- **NSFW content**: Enable NSFW in settings if needed
- **Slow search**: This provider can be slower than others
- **Missing results**: Try manhwa/manhua specific titles

---

## 📱 **Browser-Specific Issues**

### **Chrome Issues**

- **Extensions blocking**: Disable ad blockers and privacy extensions
- **Cache problems**: Clear browsing data (Ctrl+Shift+Delete)
- **Memory issues**: Close unused tabs and restart browser

### **Firefox Issues**

- **Tracking protection**: Disable for the site temporarily
- **Cookie settings**: Allow cookies for the site
- **Private mode**: Test in regular browsing mode

### **Safari Issues**

- **JavaScript disabled**: Enable JavaScript in preferences
- **Cross-site tracking**: Allow for the site
- **Cache issues**: Clear website data in preferences

### **Mobile Browser Issues**

- **Touch controls**: Ensure touch events are working
- **Viewport issues**: Try desktop version if mobile fails
- **JavaScript**: Ensure JavaScript is enabled on mobile

---

## ⚙️ **Settings & Configuration**

### **Provider Preferences Not Saving**

- ✅ **Click "Save Changes"** - Don't forget to save
- ✅ **Check login status** - Must be logged in to save
- ✅ **Try different browser** - Test in incognito mode
- ✅ **Clear browser cache** - Reset and try again

### **Theme Not Changing**

- ✅ **Refresh page** - F5 after changing theme
- ✅ **Clear cache** - Browser may cache old styles
- ✅ **Check system theme** - "System" follows OS setting
- ✅ **Try different theme** - Test with Light/Dark manually

### **NSFW Settings Not Working**

- ✅ **Save settings** - Click save after changing
- ✅ **Refresh search** - Perform new search to see changes
- ✅ **Check provider support** - Not all providers have NSFW content
- ✅ **Clear search cache** - May show cached results

---

## 🔄 **Quick Diagnostic Steps**

### **When Something Doesn't Work**:

1. **🔄 Refresh the page** (F5)
2. **🧹 Clear browser cache** (Ctrl+Shift+Delete)
3. **🕵️ Try incognito mode** (Ctrl+Shift+N)
4. **🔍 Check browser console** (F12 → Console tab)
5. **🌐 Test different browser** (Chrome, Firefox, Safari)
6. **📱 Try on mobile** (Different device)
7. **⏰ Wait and try later** (Server might be busy)

### **Information to Gather for Support**:

- **Operating System** and version
- **Browser** and version
- **Error messages** (exact text)
- **Steps to reproduce** the issue
- **Screenshots** if helpful

---

## 🆘 **When to Seek Additional Help**

### **Try These Resources First**:

1. **[Troubleshooting Guide](Troubleshooting)** - Detailed solutions
2. **[Installation Guide](Installation)** - Setup problems
3. **[User Guide](User-Guide)** - Feature questions
4. **[Performance Optimization](Performance-Optimization)** - Speed issues

### **Still Need Help?**

- **[GitHub Issues](https://github.com/Futs/kuroibara/issues)** - Report bugs
- **[GitHub Discussions](https://github.com/Futs/kuroibara/discussions)** - Ask questions
- **Search existing issues** - Your problem might already be reported

---

## 💡 **Prevention Tips**

### **Avoid Common Issues**:

- **Keep browser updated** - Latest version for best compatibility
- **Regular cache clearing** - Prevents stale data issues
- **Bookmark the correct URL** - Avoid typos in address
- **Save settings changes** - Don't forget to click save
- **Test in incognito first** - Isolates extension conflicts

### **Best Practices**:

- **Use supported browsers** - Chrome, Firefox, Safari, Edge
- **Enable JavaScript** - Required for full functionality
- **Allow cookies** - Needed for login and preferences
- **Stable internet** - Better for provider searches
- **Regular updates** - Keep Kuroibara updated

---

## 🧭 **Navigation**

**🏠 Home**: [Wiki Home](Home)  
**← Previous**: [User Guide](User-Guide)  
**→ Next**: [Troubleshooting](Troubleshooting)

---

_Last updated: July 2025 | Quick fix didn't work? Try [Troubleshooting](Troubleshooting)_
