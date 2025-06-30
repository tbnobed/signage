# Ubuntu Server Setup Guide
## Digital Signage Management System

This guide will help you deploy the digital signage server on Ubuntu Server.

## 🚀 Quick Start

**One-line installation:**
```bash
curl -L https://raw.githubusercontent.com/tbnobed/signage/main/install_server.sh | bash
```

## 📋 Prerequisites

- Ubuntu Server 20.04 LTS or newer
- 2GB+ RAM recommended
- 10GB+ disk space
- Network connectivity
- sudo access

## 🛠️ Manual Installation

### Step 1: Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Required Packages
```bash
# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv git nginx postgresql postgresql-contrib

# Install build tools for Python packages
sudo apt install -y build-essential python3-dev libpq-dev
```

### Step 3: Setup PostgreSQL Database
```bash
# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE signage_db;"
sudo -u postgres psql -c "CREATE USER signage_user WITH PASSWORD 'secure_password_here';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE signage_db TO signage_user;"
sudo -u postgres psql -c "ALTER USER signage_user CREATEDB;"
```

### Step 4: Download Application
```bash
# Create application directory
sudo mkdir -p /opt/signage
cd /opt/signage

# Download from GitHub
sudo git clone https://github.com/tbnobed/signage.git .

# Set ownership
sudo chown -R $USER:$USER /opt/signage
```

### Step 5: Setup Python Environment
```bash
cd /opt/signage

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 6: Configure Environment
```bash
# Create environment file
cat > .env << 'EOF'
DATABASE_URL=postgresql://signage_user:secure_password_here@localhost/signage_db
SESSION_SECRET=$(openssl rand -hex 32)
FLASK_ENV=production
UPLOAD_FOLDER=/opt/signage/uploads
EOF

# Create uploads directory
mkdir -p uploads
chmod 755 uploads
```

### Step 7: Initialize Database
```bash
# Activate virtual environment
source venv/bin/activate

# Create admin user
python3 create_admin.py admin admin@yourdomain.com your_secure_password
```

### Step 8: Create Systemd Service
```bash
sudo tee /etc/systemd/system/signage.service > /dev/null << 'EOF'
[Unit]
Description=Digital Signage Management System
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/signage
Environment=PATH=/opt/signage/venv/bin
EnvironmentFile=/opt/signage/.env
ExecStart=/opt/signage/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

### Step 9: Configure Nginx
```bash
sudo tee /etc/nginx/sites-available/signage > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or IP
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
    
    location /uploads/ {
        alias /opt/signage/uploads/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/signage /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t
```

### Step 10: Start Services
```bash
# Start and enable services
sudo systemctl daemon-reload
sudo systemctl start signage
sudo systemctl enable signage
sudo systemctl restart nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status signage
sudo systemctl status nginx
```

## 🔐 SSL/HTTPS Setup (Recommended)

### Using Let's Encrypt (Free SSL)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

### Manual SSL Certificate
```bash
# Edit nginx config for HTTPS
sudo nano /etc/nginx/sites-available/signage

# Add SSL server block:
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 🔧 Configuration Options

### Environment Variables (.env file)
```bash
# Database connection
DATABASE_URL=postgresql://user:password@localhost/database

# Security
SESSION_SECRET=your-secret-key-here

# File uploads
UPLOAD_FOLDER=/opt/signage/uploads
MAX_CONTENT_LENGTH=104857600  # 100MB in bytes

# Application settings
FLASK_ENV=production
```

### Firewall Setup
```bash
# Enable UFW
sudo ufw enable

# Allow SSH, HTTP, and HTTPS
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Check status
sudo ufw status
```

## 📊 Monitoring and Maintenance

### Service Management
```bash
# Check service status
sudo systemctl status signage
sudo systemctl status nginx
sudo systemctl status postgresql

# View logs
sudo journalctl -u signage -f
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo systemctl restart signage
sudo systemctl restart nginx
```

### Database Backup
```bash
# Create backup
sudo -u postgres pg_dump signage_db > backup_$(date +%Y%m%d).sql

# Restore backup
sudo -u postgres psql signage_db < backup_20240630.sql
```

### Application Updates
```bash
cd /opt/signage

# Backup current version
sudo cp -r /opt/signage /opt/signage_backup_$(date +%Y%m%d)

# Update from GitHub
sudo git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart signage
```

## 🔍 Troubleshooting

### Service Won't Start
```bash
# Check service logs
sudo journalctl -u signage -n 50

# Check Python path and environment
sudo systemctl show signage --property=Environment

# Test application manually
cd /opt/signage
source venv/bin/activate
python3 main.py
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
sudo -u postgres psql -d signage_db -c "SELECT version();"

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log

# Reset database password
sudo -u postgres psql -c "ALTER USER signage_user PASSWORD 'new_password';"
```

### Permission Issues
```bash
# Fix file permissions
sudo chown -R ubuntu:ubuntu /opt/signage
sudo chmod -R 755 /opt/signage
sudo chmod 644 /opt/signage/.env
```

### Nginx Issues
```bash
# Test nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log

# Reload nginx configuration
sudo systemctl reload nginx
```

## 📈 Performance Optimization

### Gunicorn Configuration
```bash
# Edit systemd service for more workers
sudo systemctl edit signage

# Add:
[Service]
ExecStart=
ExecStart=/opt/signage/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --worker-class gevent --timeout 120 main:app
```

### PostgreSQL Tuning
```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/*/main/postgresql.conf

# Key settings:
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

## 🚦 Server Access

After setup, access your server at:
- **HTTP**: `http://your-server-ip`
- **HTTPS**: `https://your-domain.com`

Default admin login created during setup.

## 📱 Client Connection

Once the server is running, clients can connect using:
```bash
curl -L https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh | sudo bash
```

When prompted, use your server URL:
- `http://your-server-ip` (if no SSL)
- `https://your-domain.com` (if SSL configured)

## 🆘 Support

For issues:
1. Check service logs: `sudo journalctl -u signage -f`
2. Verify nginx: `sudo nginx -t`
3. Test database: `sudo -u postgres psql signage_db`
4. Check firewall: `sudo ufw status`

---

**Server Repository**: https://github.com/tbnobed/signage.git