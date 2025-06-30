#!/bin/bash

# Quick Docker setup script without nginx
# Use this when you already have a reverse proxy (npm, traefik, etc.)

set -e

echo "🐳 Digital Signage Docker Setup (No Nginx)"
echo "=========================================="

# Stop any existing containers
if [ -f docker-compose.yml ]; then
    echo "Stopping existing containers..."
    docker-compose down
fi

# Use the simplified compose file
cp docker-compose.simple.yml docker-compose.yml

# Create environment file
echo "📝 Creating environment configuration..."
cat > .env << 'EOF'
# Database credentials
POSTGRES_DB=signage_db
POSTGRES_USER=signage_user
POSTGRES_PASSWORD=signage_secure_password_123

# Application settings
SESSION_SECRET=$(openssl rand -hex 32)
FLASK_ENV=production

# Auto-create admin user
ADMIN_USER=admin
ADMIN_EMAIL=admin@signage.local
ADMIN_PASSWORD=admin123456789

# Upload settings
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=104857600
EOF

echo "✅ Environment file created"

# Create required directories
mkdir -p uploads logs ssl
chmod 755 uploads logs

echo "📁 Directories created"

# Start the services
echo "🚀 Starting Docker services..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check status
echo "📊 Service status:"
docker-compose ps

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Your signage server is running on:"
echo "   http://localhost:5000"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "🔑 Admin login:"
echo "   Username: admin"
echo "   Password: admin123456789"
echo ""
echo "📋 Next steps:"
echo "   1. Point your npm reverse proxy to port 5000"
echo "   2. Access the web dashboard to verify login"
echo "   3. Change the admin password in settings"
echo "   4. Add devices and upload media"
echo ""
echo "🔧 Management commands:"
echo "   Logs:    docker-compose logs -f"
echo "   Stop:    docker-compose down"
echo "   Restart: docker-compose restart"
echo ""