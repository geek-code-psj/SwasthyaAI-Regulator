# SwasthyaAI Regulator - Deployment Guide

**Production & Development Deployment Instructions**

---

## 📋 Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Database Setup](#database-setup)
5. [Troubleshooting](#troubleshooting)
6. [Performance Tuning](#performance-tuning)

---

## 🏠 Local Development

### Prerequisites
```
✅ Python 3.9+
✅ Node.js 18+
✅ Git
✅ Windows/macOS/Linux
```

### Step 1: Clone Repository
```bash
git clone https://github.com/geek-code-psj/SwasthyaAI-Regulator.git
cd SwasthyaAI-Regulator
```

### Step 2: Backend Setup
```bash
# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install minimal dependencies
pip install -r requirements-minimal.txt

# Verify Flask installation
python -c "import flask; print(f'Flask {flask.__version__}')"
```

### Step 3: Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install --legacy-peer-deps

# Verify Vite installation
npm --version

cd ..
```

### Step 4: Start Services
```bash
# Terminal 1: Backend
python backend/real_app.py
# Output: 🚀 SwasthyaAI Regulator - REAL Backend with File Processing
#         ✅ API running on http://localhost:5000

# Terminal 2: Frontend
cd frontend
npm run dev
# Output: ➜  Local:   http://localhost:3000/
```

### Step 5: Test Application
```bash
# Open browser
http://localhost:3000

# Test steps:
1. Click "Login" (any email/password)
2. Go to "Upload"
3. Upload test document with personal info
4. View "Results" - See PII anonymization
```

**✅ Local Development Complete!**

---

## 🐳 Docker Deployment

### Prerequisites
```
✅ Docker Desktop installed
✅ docker-compose available
✅ 2GB RAM available
```

### Step 1: Build Docker Images
```bash
docker-compose build

# Output:
# Building swasthya-backend
# Building swasthya-frontend
# Successfully tagged...
```

### Step 2: Start Containers
```bash
docker-compose up -d

# Verify all running:
docker-compose ps

# Output:
# NAME                 STATUS           PORTS
# swasthya-backend     Up 2 minutes     0.0.0.0:5000->5000/tcp
# swasthya-frontend    Up 2 minutes     0.0.0.0:3000->3000/tcp
```

### Step 3: View Logs
```bash
# Backend logs
docker-compose logs backend -f

# Frontend logs
docker-compose logs frontend -f

# All logs
docker-compose logs -f
```

### Step 4: Stop Services
```bash
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

### Docker Environment Variables
Create `.env` in project root:
```env
# Backend
FLASK_ENV=production
FLASK_DEBUG=0
FLASK_SECRET_KEY=your-secret-key-min-32-chars-long
JWT_SECRET_KEY=your-jwt-secret-key-min-32-chars-long

# Database
DATABASE_URL=sqlite:///submissions.db

# Frontend  
VITE_API_URL=http://localhost:5000
```

**✅ Docker Deployment Complete!**

---

## ☁️ Production Deployment

### Option A: AWS EC2 (Recommended)

#### 1. Create EC2 Instance
```bash
# Launch Ubuntu 22.04 LTS instance
# t3.small (1GB RAM, 20GB SSD)
# Security group: Allow ports 3000, 5000, 80, 443
```

#### 2. SSH into Instance
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

#### 3. Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.9 python3-pip python3-venv git -y

# Install Node
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Verify installations
python3 --version  # 3.9+
node --version     # 18+
npm --version      # 9+
```

#### 4. Clone Repository
```bash
cd /home/ubuntu
git clone https://github.com/geek-code-psj/SwasthyaAI-Regulator.git
cd SwasthyaAI-Regulator
```

#### 5. Setup Backend
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-minimal.txt gunicorn
```

#### 6. Setup Frontend
```bash
cd frontend
npm install --legacy-peer-deps
npm run build
cd ..
```

#### 7. Create Systemd Service
```bash
# Backend service
sudo tee /etc/systemd/system/swasthya-backend.service > /dev/null <<EOF
[Unit]
Description=SwasthyaAI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/SwasthyaAI-Regulator
ExecStart=/home/ubuntu/SwasthyaAI-Regulator/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 backend.real_app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable swasthya-backend
sudo systemctl start swasthya-backend
```

#### 8. Setup Nginx (Reverse Proxy)
```bash
sudo apt install nginx -y

# Create config
sudo tee /etc/nginx/sites-available/swasthya > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/swasthya /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

#### 9. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

**✅ AWS EC2 Production Ready!**

---

### Option B: Railway.app (Quick Deploy)

#### 1. Connect GitHub Repository
- Go to [Railway.app](https://railway.app)
- Click "New Project" → "Deploy from GitHub"
- Select your repo

#### 2. Configure Environment
```env
FLASK_ENV=production
FLASK_SECRET_KEY=generate-random-key
JWT_SECRET_KEY=generate-random-key
DATABASE_URL=sqlite:///submissions.db
```

#### 3. Configure Build
```bash
# Add railway.json
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "startCommand": "gunicorn backend.real_app:app"
  }
}
```

#### 4. Deploy
Push to GitHub → Railway auto-deploys

**✅ Railway Deployment Complete!**

---

### Option C: Docker Swarm / Kubernetes

#### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml swasthya

# Verify
docker stack services swasthya
```

#### Kubernetes
```bash
# Create deployment
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml

# Scale backend
kubectl scale deployment swasthya-backend --replicas=3

# Monitor
kubectl get pods -w
```

---

## 🗄️ Database Setup

### SQLite (Default - No Setup Needed)
```bash
# Database auto-creates at: submissions.db
# Already configured in real_app.py

# Verify
python -c "
import sqlite3
conn = sqlite3.connect('submissions.db')
c = conn.cursor()
c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
print(c.fetchall())
conn.close()
"
```

### PostgreSQL (Optional - Better for Production)

#### Install PostgreSQL
```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql

# Windows
# Download: https://www.postgresql.org/download/windows/
```

#### Create Database
```bash
psql -U postgres
CREATE DATABASE swasthya;
CREATE USER regulator WITH PASSWORD 'secure-password';
ALTER ROLE regulator SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE swasthya TO regulator;
\q
```

#### Update Backend Config
```python
# backend/config.py
DATABASE_URI = 'postgresql://regulator:secure-password@localhost:5432/swasthya'
```

#### Create Tables
```bash
python -c "
from backend.real_app import app
with app.app_context():
    db.create_all()
    print('✅ Tables created')
"
```

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Find process on port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
python backend/real_app.py --port 8000
```

### CORS Errors
```bash
# Error: "Access to XMLHttpRequest blocked by CORS policy"
# Fix: Check CORS configuration in real_app.py

# Verify CORS is enabled:
python -c "from flask_cors import CORS; print('✅ CORS available')"
```

### Database Lock
```bash
# Error: "database is locked"
# Fix: Stop backend, remove submissions.db, restart

rm submissions.db
python backend/real_app.py
```

### Node Modules Issues
```bash
# Error: "Cannot find module 'react'"
# Fix: Reinstall dependencies

cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### Memory Issues on VM
```bash
# If running out of memory:
# Reduce Gunicorn workers from 4 to 2
gunicorn -w 2 -b 0.0.0.0:5000 backend.real_app:app
```

---

## ⚡ Performance Tuning

### Backend Optimization
```python
# config.py
SQLALCHEMY_ECHO = False          # Disable SQL logging
SQLALCHEMY_TRACK_MODIFICATIONS = False
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # Limit upload size
```

### Gunicorn Configuration
```bash
# Production
gunicorn -w 4 \
  -b 0.0.0.0:5000 \
  --timeout 300 \
  --access-logfile - \
  backend.real_app:app
```

### Frontend Optimization
```bash
# Build for production
npm run build

# Analyze bundle size
npm install -g vite-plugin-visualizer
npm run build  # Will generate stats.html
```

### Nginx Caching
```nginx
location /api/ {
    # Cache API responses for 5 minutes
    proxy_cache_valid 200 10m;
    proxy_cache_use_stale_error_timeout;
    proxy_pass http://localhost:5000;
}
```

### Database Indexes
```sql
-- Create indexes for faster queries
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_created_at ON submissions(created_at DESC);
```

---

## 📊 Monitoring

### Application Health Check
```bash
# Backend endpoint
curl http://localhost:5000/
# Response: { "status": "operational", ... }

# Frontend endpoint
curl http://localhost:3000/
# Response: HTML (React app)
```

### Docker Monitoring
```bash
# CPU/Memory usage
docker stats

# Container logs
docker logs -f swasthya-backend

# Inspect container
docker inspect swasthya-backend
```

### System Monitoring
```bash
# CPU/Memory (Linux)
top
htop

# Disk usage
df -h

# Network
netstat -tulpn
```

---

## 🚀 Deployment Checklist

- [ ] Environment variables configured (.env file)
- [ ] Database initialized (SQLite or PostgreSQL)
- [ ] CORS configured for frontend domain
- [ ] SSL certificate installed (production)
- [ ] Firewall rules configured (ports 80, 443)
- [ ] Backup strategy planned
- [ ] Monitoring/logging configured
- [ ] Error handling tested
- [ ] Load testing completed
- [ ] Security audit done

---

## 📞 Support

### Common Issues Repository
See [GitHub Issues](https://github.com/geek-code-psj/SwasthyaAI-Regulator/issues)

### Quick Debug
```bash
# Check logs
docker-compose logs -f

# Check ports
netstat -tulpn | grep LISTEN

# Test API
curl -s http://localhost:5000/ | python -m json.tool

# Test database
sqlite3 submissions.db ".tables"
```

---

**Last Updated**: March 2026  
**Version**: 1.0.0  
**Status**: ✅ Production Ready
