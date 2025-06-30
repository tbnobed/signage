#!/bin/bash

# Digital Signage Server Installation Script for Ubuntu
# This script automates the complete server setup process

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration variables
INSTALL_DIR="/opt/signage"
SERVICE_USER="signage"
DB_NAME="signage_db"
DB_USER="signage_user"
NGINX_SITE="signage"

print_header() {
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}     Digital Signage Server Installation${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo
}

print_step() {
    echo -e "${BLUE}🔹 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_ubuntu() {
    if ! grep -q "Ubuntu" /etc/os-release; then
        print_error "This script is designed for Ubuntu Server"
        exit 1
    fi
    print_success "Ubuntu detected"
}

update_system() {
    print_step "Updating system packages..."
    apt update -y && apt upgrade -y
    print_success "System updated"
}

install_dependencies() {
    print_step "Installing required packages..."
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        nginx \
        postgresql \
        postgresql-contrib \
        build-essential \
        libpq-dev \
        curl \
        wget \
        ufw \
        openssl
    print_success "Dependencies installed"
}

setup_user() {
    print_step "Creating service user..."
    if ! id "$SERVICE_USER" &>/dev/null; then
        useradd -r -s /bin/bash -d "$INSTALL_DIR" "$SERVICE_USER"
        print_success "User $SERVICE_USER created"
    else
        print_success "User $SERVICE_USER already exists"
    fi
}

setup_postgresql() {
    print_step "Configuring PostgreSQL..."
    
    # Start and enable PostgreSQL
    systemctl start postgresql
    systemctl enable postgresql
    
    # Generate secure password
    DB_PASSWORD=$(openssl rand -base64 32)
    
    # Create database and user
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;"
    sudo -u postgres psql -c "DROP USER IF EXISTS $DB_USER;"
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;"
    sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    sudo -u postgres psql -c "ALTER USER $DB_USER CREATEDB;"
    
    print_success "PostgreSQL configured"
    echo "Database: $DB_NAME"
    echo "User: $DB_USER"
    echo "Password: $DB_PASSWORD"
}

download_application() {
    print_step "Downloading application..."
    
    # Create directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Download application files from GitHub
    echo "Downloading from GitHub repository..."
    
    # Core application files
    wget -O app.py "https://raw.githubusercontent.com/tbnobed/signage/main/app.py"
    wget -O main.py "https://raw.githubusercontent.com/tbnobed/signage/main/main.py"
    wget -O routes.py "https://raw.githubusercontent.com/tbnobed/signage/main/routes.py"
    wget -O models.py "https://raw.githubusercontent.com/tbnobed/signage/main/models.py"
    wget -O auth.py "https://raw.githubusercontent.com/tbnobed/signage/main/auth.py"
    wget -O create_admin.py "https://raw.githubusercontent.com/tbnobed/signage/main/create_admin.py"
    
    # Create directories
    mkdir -p templates static uploads
    
    # Download templates (basic structure)
    mkdir -p templates
    cat > templates/base.html << 'EOF'
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Digital Signage{% endblock %}</title>
    <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">
                <i class="fas fa-tv me-2"></i>Digital Signage
            </a>
            {% if current_user.is_authenticated %}
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('dashboard') }}">Dashboard</a>
                <a class="nav-link" href="{{ url_for('devices') }}">Devices</a>
                <a class="nav-link" href="{{ url_for('media') }}">Media</a>
                <a class="nav-link" href="{{ url_for('playlists') }}">Playlists</a>
                <a class="nav-link" href="{{ url_for('logout') }}">Logout</a>
            </div>
            {% endif %}
        </div>
    </nav>
    
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
EOF
    
    print_success "Application downloaded"
}

setup_python_env() {
    print_step "Setting up Python environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv venv
    
    # Create requirements file
    cat > requirements.txt << 'EOF'
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Werkzeug==3.0.1
SQLAlchemy==2.0.23
psycopg2-binary==2.9.9
gunicorn==21.2.0
email-validator==2.1.0
Pillow==10.1.0
requests==2.31.0
PyJWT==2.8.0
EOF
    
    # Install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Python environment ready"
}

configure_application() {
    print_step "Configuring application..."
    
    cd "$INSTALL_DIR"
    
    # Generate session secret
    SESSION_SECRET=$(openssl rand -hex 32)
    
    # Create environment file
    cat > .env << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
SESSION_SECRET=$SESSION_SECRET
FLASK_ENV=production
UPLOAD_FOLDER=$INSTALL_DIR/uploads
MAX_CONTENT_LENGTH=104857600
EOF
    
    # Set proper permissions
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chmod 600 .env
    chmod 755 uploads
    
    print_success "Application configured"
}

create_admin_user() {
    print_step "Creating admin user..."
    
    cd "$INSTALL_DIR"
    
    echo "Please enter admin user details:"
    read -p "Admin username: " ADMIN_USER
    read -p "Admin email: " ADMIN_EMAIL
    
    while true; do
        read -s -p "Admin password (min 12 chars): " ADMIN_PASS
        echo
        if [ ${#ADMIN_PASS} -ge 12 ]; then
            break
        else
            echo "Password must be at least 12 characters long"
        fi
    done
    
    # Create admin user
    source venv/bin/activate
    python3 create_admin.py "$ADMIN_USER" "$ADMIN_EMAIL" "$ADMIN_PASS"
    
    print_success "Admin user created"
}

create_systemd_service() {
    print_step "Creating systemd service..."
    
    cat > /etc/systemd/system/signage.service << EOF
[Unit]
Description=Digital Signage Management System
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=exec
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
    
    print_success "Systemd service created"
}

configure_nginx() {
    print_step "Configuring Nginx..."
    
    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    cat > /etc/nginx/sites-available/$NGINX_SITE << EOF
server {
    listen 80;
    server_name $SERVER_IP _;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }
    
    location /uploads/ {
        alias $INSTALL_DIR/uploads/;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    
    # Enable site
    ln -sf /etc/nginx/sites-available/$NGINX_SITE /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    nginx -t
    
    print_success "Nginx configured"
}

setup_firewall() {
    print_step "Configuring firewall..."
    
    # Enable UFW
    ufw --force enable
    
    # Allow SSH, HTTP, and HTTPS
    ufw allow ssh
    ufw allow 'Nginx Full'
    
    print_success "Firewall configured"
}

start_services() {
    print_step "Starting services..."
    
    # Reload systemd
    systemctl daemon-reload
    
    # Start and enable services
    systemctl start signage
    systemctl enable signage
    systemctl restart nginx
    systemctl enable nginx
    
    print_success "Services started"
}

print_completion_info() {
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    echo
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}     Installation Complete!${NC}"
    echo -e "${GREEN}============================================================${NC}"
    echo
    echo -e "${CYAN}🌐 Server Access:${NC}"
    echo "   Web Dashboard: http://$SERVER_IP"
    echo "   Admin Login: Use credentials created during setup"
    echo
    echo -e "${CYAN}📱 Client Installation:${NC}"
    echo "   Run on client devices:"
    echo "   curl -L https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh | sudo bash"
    echo "   Use server URL: http://$SERVER_IP"
    echo
    echo -e "${CYAN}🔧 Service Management:${NC}"
    echo "   Status: sudo systemctl status signage"
    echo "   Logs:   sudo journalctl -u signage -f"
    echo "   Restart: sudo systemctl restart signage"
    echo
    echo -e "${CYAN}🔐 Security:${NC}"
    echo "   Database: $DB_NAME (user: $DB_USER)"
    echo "   Config: $INSTALL_DIR/.env"
    echo "   Uploads: $INSTALL_DIR/uploads"
    echo
    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo "   1. Access web dashboard and verify login"
    echo "   2. Add devices in the dashboard"
    echo "   3. Upload media files"
    echo "   4. Create playlists"
    echo "   5. Install clients on display devices"
    echo
    echo -e "${YELLOW}🔒 For HTTPS/SSL:${NC}"
    echo "   sudo apt install certbot python3-certbot-nginx"
    echo "   sudo certbot --nginx -d your-domain.com"
    echo
}

# Main installation process
main() {
    print_header
    
    check_root
    check_ubuntu
    update_system
    install_dependencies
    setup_user
    setup_postgresql
    download_application
    setup_python_env
    configure_application
    create_admin_user
    create_systemd_service
    configure_nginx
    setup_firewall
    start_services
    print_completion_info
}

# Run main function
main "$@"