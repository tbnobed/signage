# Docker Deployment Guide
## Digital Signage Management System

This guide explains how to deploy the digital signage server using Docker and Docker Compose.

## 🚀 Quick Start

**One-command deployment:**
```bash
# Clone the repository
git clone https://github.com/tbnobed/signage.git
cd signage

# Start the services
docker-compose up -d

# Create admin user
docker-compose exec app python3 create_admin.py admin admin@yourdomain.com your_secure_password
```

Your server will be available at `http://localhost` or `http://your-server-ip`

## 📋 Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- 4GB+ RAM available
- 20GB+ disk space
- Network connectivity

## 🏗️ Architecture

The Docker setup includes:
- **App Container**: Flask application with Gunicorn
- **Database Container**: PostgreSQL 15
- **Reverse Proxy**: Nginx for load balancing and SSL
- **Persistent Storage**: Docker volumes for data and uploads

## 🛠️ Installation

### Step 1: Get the Code
```bash
# Option 1: Clone from GitHub
git clone https://github.com/tbnobed/signage.git
cd signage

# Option 2: Download files individually
wget https://raw.githubusercontent.com/tbnobed/signage/main/docker-compose.yml
wget https://raw.githubusercontent.com/tbnobed/signage/main/Dockerfile
wget https://raw.githubusercontent.com/tbnobed/signage/main/nginx.conf
# ... download other files as needed
```

### Step 2: Configure Environment (Optional)
```bash
# Create environment file for custom settings
cat > .env << 'EOF'
# Database settings
POSTGRES_DB=signage_db
POSTGRES_USER=signage_user
POSTGRES_PASSWORD=change_this_secure_password

# Application settings
SESSION_SECRET=your_very_long_random_session_secret_here
FLASK_ENV=production

# Admin user (auto-created on first run)
ADMIN_USER=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your_admin_password_here

# Upload settings
MAX_CONTENT_LENGTH=104857600
EOF
```

### Step 3: Start the Services
```bash
# Start in background
docker-compose up -d

# Watch logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Step 4: Create Admin User (if not using .env)
```bash
# Interactive admin creation
docker-compose exec app python3 create_admin.py

# Or directly via command line
docker-compose exec app python3 create_admin.py admin admin@example.com mypassword123
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
POSTGRES_DB=signage_db
POSTGRES_USER=signage_user
POSTGRES_PASSWORD=secure_database_password

# Application Security
SESSION_SECRET=your_very_long_random_session_secret_at_least_32_chars
FLASK_ENV=production

# Auto-Admin Creation (optional)
ADMIN_USER=admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=admin_password_min_12_chars

# File Upload Settings
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=104857600  # 100MB

# Logging
LOG_LEVEL=INFO
```

### Custom Nginx Configuration

Edit `nginx.conf` for custom domains or SSL:

```nginx
# For custom domain
server_name your-domain.com;

# For SSL (Let's Encrypt)
listen 443 ssl http2;
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
```

### Volume Mounts

The docker-compose.yml creates these persistent volumes:
- `./uploads:/app/uploads` - Media file storage
- `./logs:/app/logs` - Application logs
- `postgres_data:/var/lib/postgresql/data` - Database data
- `./ssl:/etc/nginx/ssl` - SSL certificates

## 🔐 SSL/HTTPS Setup

### Option 1: Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem
sudo chown $(id -u):$(id -g) ./ssl/*.pem

# Restart nginx
docker-compose restart nginx
```

### Option 2: Self-Signed Certificate
```bash
# Create SSL directory
mkdir -p ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/key.pem \
    -out ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"

# Restart nginx
docker-compose restart nginx
```

## 📊 Management Commands

### Service Management
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart specific service
docker-compose restart app

# View logs
docker-compose logs -f app
docker-compose logs -f db
docker-compose logs -f nginx

# Check service status
docker-compose ps
```

### Database Management
```bash
# Access database shell
docker-compose exec db psql -U signage_user -d signage_db

# Backup database
docker-compose exec db pg_dump -U signage_user signage_db > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T db psql -U signage_user -d signage_db < backup_20240630.sql

# Reset database (DESTRUCTIVE)
docker-compose down -v
docker-compose up -d
```

### Application Management
```bash
# Create admin user
docker-compose exec app python3 create_admin.py

# Access application shell
docker-compose exec app bash

# Update application (if using Git)
git pull
docker-compose build --no-cache app
docker-compose up -d app

# View uploaded media
ls -la uploads/

# Clear application logs
docker-compose exec app truncate -s 0 logs/app.log
```

## 🔍 Monitoring and Troubleshooting

### Health Checks
```bash
# Check container health
docker-compose ps

# Test application endpoint
curl -f http://localhost/

# Check database connection
docker-compose exec app python3 -c "
from app import db
try:
    db.engine.execute('SELECT 1')
    print('Database connection: OK')
except Exception as e:
    print(f'Database error: {e}')
"
```

### Common Issues

#### Database Connection Failed
```bash
# Check database container
docker-compose logs db

# Verify database credentials
docker-compose exec db psql -U signage_user -d signage_db -c "SELECT version();"

# Reset database password
docker-compose exec db psql -U postgres -c "ALTER USER signage_user PASSWORD 'new_password';"
```

#### Nginx Not Starting
```bash
# Test nginx configuration
docker-compose exec nginx nginx -t

# Check nginx logs
docker-compose logs nginx

# Reload nginx config
docker-compose exec nginx nginx -s reload
```

#### Upload Issues
```bash
# Check upload directory permissions
docker-compose exec app ls -la uploads/

# Fix permissions
docker-compose exec app chown -R signage:signage uploads/
```

### Performance Tuning

#### Scale Application Containers
```yaml
# In docker-compose.yml
services:
  app:
    deploy:
      replicas: 3
    # ... rest of config
```

#### Optimize Database
```bash
# Tune PostgreSQL settings
docker-compose exec db psql -U signage_user -d signage_db -c "
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();
"
```

## 🚦 Production Deployment

### Recommended Production Setup
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build: .
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
  
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    shm_size: 256mb
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

### Security Hardening
```bash
# Create dedicated network
docker network create signage_network

# Use secrets for passwords
echo "secure_db_password" | docker secret create db_password -

# Enable firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Backup Strategy
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U signage_user signage_db | gzip > backup_${DATE}.sql.gz
tar -czf uploads_${DATE}.tar.gz uploads/
echo "Backup created: backup_${DATE}.sql.gz, uploads_${DATE}.tar.gz"
EOF

# Make executable and run
chmod +x backup.sh
./backup.sh

# Schedule daily backups
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

## 📱 Client Connection

Once deployed, clients connect using:
```bash
curl -L https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh | sudo bash
```

When prompted for server URL, use:
- **Production Server**: `https://display.obtv.io` (default)
- **Local Development**: `http://localhost:5000`
- **Custom Server**: Your own domain/IP

## 🔄 Updates and Maintenance

### Update Application
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# Check deployment
docker-compose ps
docker-compose logs -f app
```

### Regular Maintenance
```bash
# Clean unused images and containers
docker system prune -f

# Update base images
docker-compose pull
docker-compose up -d

# Rotate logs
docker-compose exec app logrotate /etc/logrotate.conf
```

---

## 📄 File Structure for Docker Deployment

Required files in your project directory:
```
signage/
├── docker-compose.yml     # Service orchestration
├── Dockerfile            # Application container
├── docker-entrypoint.sh  # Startup script
├── nginx.conf            # Reverse proxy config
├── init-db.sql           # Database initialization
├── .env                  # Environment variables (optional)
├── uploads/              # Media storage (created automatically)
├── logs/                 # Application logs (created automatically)
├── ssl/                  # SSL certificates (for HTTPS)
└── [application files]   # Flask app, models, templates, etc.
```

**Repository**: https://github.com/tbnobed/signage.git