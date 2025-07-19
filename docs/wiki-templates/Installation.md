# 🔧 Installation Guide

This guide will help you install and set up Kuroibara on your system. Choose the installation method that best fits your needs.

---

## 🎯 **Installation Methods**

### 🐳 **Method 1: Docker (Recommended)**
- ✅ **Easiest setup** - Everything included
- ✅ **Cross-platform** - Works on Windows, macOS, Linux
- ✅ **Isolated environment** - No conflicts with other software
- ✅ **Easy updates** - Simple container management

### 🔧 **Method 2: Manual Installation**
- ✅ **Full control** - Customize every component
- ✅ **Development setup** - For contributors and developers
- ⚠️ **More complex** - Requires technical knowledge

---

## 🐳 **Docker Installation (Recommended)**

### **Prerequisites**
- Docker Engine 20.10+ and Docker Compose 2.0+
- 4GB+ RAM available
- 10GB+ free disk space

### **Step 1: Quick Start with Docker Hub**
```bash
# Download and start with Docker Compose
curl -O https://raw.githubusercontent.com/Futs/kuroibara/main/docker-compose.yml
docker compose up -d
```

### **Step 1 Alternative: From Source**
```bash
# Clone the repository
git clone https://github.com/Futs/kuroibara.git
cd kuroibara
```

### **Step 2: Configure Environment**
```bash
# Copy the example environment file
cp .env.example .env

# Edit the configuration (optional)
nano .env  # or use your preferred editor
```

### **Step 3: Start Kuroibara**
```bash
# Start all services
docker compose up -d

# Check status
docker compose ps
```

### **Step 4: Access Kuroibara**
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Email Testing**: http://localhost:8025 (MailHog)

### **Step 5: Create Admin Account**
1. Open http://localhost:3000 in your browser
2. Click "Register" to create your first account
3. This first account will have admin privileges

---

## 🔧 **Manual Installation**

### **Prerequisites**
- Python 3.13+
- Node.js 22+
- PostgreSQL 16+
- Redis/Valkey
- Git

### **Step 1: Clone Repository**
```bash
git clone https://github.com/Futs/kuroibara.git
cd kuroibara
```

### **Step 2: Backend Setup**
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb kuroibara
alembic upgrade head

# Configure environment
cp .env.example .env
# Edit .env with your database and Redis settings
```

### **Step 3: Frontend Setup**
```bash
# Navigate to frontend (new terminal)
cd frontend/app

# Install dependencies
npm install

# Build for production
npm run build
```

### **Step 4: Start Services**
```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend (development)
cd frontend/app
npm run dev

# Or serve built frontend with nginx/apache
```

---

## ⚙️ **Configuration Options**

### **Environment Variables**
Key settings you can customize in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/kuroibara

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Features
ENABLE_REGISTRATION=true
ENABLE_EMAIL_VERIFICATION=false
```

### **Docker Compose Customization**
Modify `docker-compose.yml` for:
- Port changes
- Volume mounts
- Resource limits
- Additional services

---

## 🔄 **Post-Installation Setup**

### **1. Create Your Account**
- Visit the web interface
- Register your first account (becomes admin)
- Configure your profile and preferences

### **2. Configure Providers**
- Go to Settings → Provider Preferences
- Enable/disable manga providers
- Set favorites for better performance

### **3. Test the Installation**
- Search for a popular manga
- Add it to your library
- Try reading a chapter
- Check that downloads work (if enabled)

---

## 🔧 **Troubleshooting Installation**

### **Docker Issues**

**Problem**: `docker compose up` fails
```bash
# Check Docker is running
docker --version
docker compose --version

# Check logs
docker compose logs

# Reset and try again
docker compose down -v
docker compose up -d
```

**Problem**: Port conflicts
```bash
# Check what's using the ports
netstat -tulpn | grep :3000
netstat -tulpn | grep :8000

# Change ports in docker-compose.yml
```

### **Manual Installation Issues**

**Problem**: Database connection fails
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure database exists: `createdb kuroibara`

**Problem**: Python dependencies fail
- Ensure Python 3.12+ is installed
- Try upgrading pip: `pip install --upgrade pip`
- Install system dependencies if needed

**Problem**: Node.js build fails
- Ensure Node.js 22+ is installed
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall

---

## 🚀 **Performance Optimization**

### **For Docker**
```yaml
# Add to docker-compose.yml services
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

### **For Manual Installation**
- Use nginx for frontend serving
- Configure PostgreSQL for your workload
- Set up Redis persistence
- Enable gzip compression

---

## 🔄 **Updates & Maintenance**

### **Docker Updates**
```bash
# Pull latest changes
git pull origin main

# Update containers
docker compose pull
docker compose up -d

# Clean up old images
docker image prune
```

### **Manual Updates**
```bash
# Update code
git pull origin main

# Update backend
cd backend
pip install -r requirements.txt
alembic upgrade head

# Update frontend
cd frontend/app
npm install
npm run build
```

---

## 🆘 **Getting Help**

If you encounter issues during installation:

1. **Check [Common Issues](Common-Issues)** for known problems
2. **Review [Troubleshooting](Troubleshooting)** for detailed solutions
3. **Search existing [Issues](https://github.com/Futs/kuroibara/issues)**
4. **Ask in [Discussions](https://github.com/Futs/kuroibara/discussions)**
5. **Create a new issue** with your system details and error logs

---

## ✅ **Installation Complete!**

Once installed, continue with:
- **[🚀 Getting Started](Getting-Started)** - Your first steps
- **[📱 User Guide](User-Guide)** - Complete feature overview
- **[⚙️ Configuration](Configuration)** - Advanced settings

---

*For technical details, see the [Technical Documentation](https://github.com/Futs/kuroibara/tree/main/docs).*
