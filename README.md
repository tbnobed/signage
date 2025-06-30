# Digital Signage Management System

A comprehensive Flask-based digital signage management system for controlling displays across multiple remote locations. Features a centralized web admin dashboard and lightweight client agents that run on Raspberry Pi, Intel NUC, or any Linux device.

## 🚀 Quick Start

### Server Setup (Admin Dashboard)
1. **Deploy the server application** (web dashboard)
2. **Create admin user**: `python3 create_admin.py`
3. **Access dashboard** at `http://your-server-ip:5000`

### Client Setup (Display Devices)
**One-line installation on any Linux device:**
```bash
curl -L https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh | bash
```

The setup script will:
- Install Python 3 and dependencies automatically
- Install media players (omxplayer/VLC/FFmpeg)
- Ask for your server URL and device ID
- Set up auto-start service
- Test connection and start the client

## 📋 Features

### Admin Dashboard
- **Device Management**: Register and monitor remote display devices
- **Media Library**: Upload and organize images and videos
- **Playlist System**: Create timed content sequences 
- **Real-time Monitoring**: Device status, logs, and health monitoring
- **User Management**: Secure admin authentication

### Client Agents
- **Multi-platform Support**: Raspberry Pi, Intel NUC, any Linux device
- **Media Player Detection**: Automatic omxplayer/VLC/FFmpeg detection
- **Offline Capability**: Local media caching for network interruptions
- **Auto-recovery**: Handles crashes and connection issues
- **Remote Management**: Zero-touch content updates

## 🏗️ Architecture

### Server Components
- **Flask Web Application** with Bootstrap 5 dark theme
- **PostgreSQL Database** (SQLite for development)
- **RESTful API** for client communication
- **File Upload System** with media management

### Client Components  
- **Python Agent** (`client_agent.py`) for media playback
- **Systemd Service** for auto-start and crash recovery
- **HTTP Polling** for server communication
- **Local Caching** for offline operation

## 📱 Supported Devices

### Raspberry Pi
- **Recommended**: Raspberry Pi 4B+ with 2GB+ RAM
- **Media Player**: omxplayer (hardware accelerated)
- **OS**: Raspberry Pi OS Lite or Desktop

### Intel NUC / PC
- **Requirements**: Any Linux PC with video output
- **Media Players**: VLC or FFmpeg
- **OS**: Ubuntu, Debian, CentOS, Fedora

### Display Connection
- HDMI output to TV/Monitor
- Network connection (WiFi or Ethernet)
- Power supply appropriate for device

## 🛠️ Installation

### Prerequisites
- Linux-based device (Raspberry Pi, PC, etc.)
- Network connectivity
- sudo access for installation

### Automatic Installation
```bash
# Register device in web dashboard first, then run:
curl -L https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh | bash

# Follow the prompts for:
# - Server URL (e.g., http://192.168.1.100:5000)
# - Device ID (unique identifier)
# - Check interval (default: 60 seconds)
```

### Manual Installation
```bash
# Download setup script
wget https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh
chmod +x setup_client.sh

# Run setup
./setup_client.sh
```

## 📊 Management

### Device Registration
1. Open admin dashboard
2. Go to **Devices** → **Add Device**
3. Enter device name, unique ID, and location
4. Note the Device ID for client setup

### Content Management
1. **Upload Media**: Go to **Media** section, upload images/videos
2. **Create Playlists**: Go to **Playlists**, add media with timing
3. **Assign Content**: In **Devices**, assign playlists to specific devices

### Monitoring
- **Dashboard**: Real-time overview of all devices
- **Device Status**: Online/offline status and last check-in
- **Logs**: View device activity and error messages
- **Media Playback**: See what's currently playing on each device

## 🔧 Configuration

### Environment Variables (Client)
```bash
SIGNAGE_SERVER_URL=http://your-server:5000
DEVICE_ID=your-unique-device-id
CHECK_INTERVAL=60
MEDIA_DIR=/path/to/media/cache
LOG_FILE=/path/to/client.log
```

### Systemd Service
The setup script automatically creates a systemd service:
```bash
# Service management
sudo systemctl status signage-client
sudo systemctl restart signage-client
sudo systemctl stop signage-client
sudo systemctl start signage-client

# View logs
journalctl -u signage-client -f
```

## 🔍 Troubleshooting

### Client Not Connecting
```bash
# Check service status
sudo systemctl status signage-client

# Test network connectivity
ping your-server-ip
curl http://your-server-ip:5000

# Check configuration
cat ~/signage/.env
```

### Media Not Playing
```bash
# Test media player manually
omxplayer /path/to/test/video.mp4
vlc /path/to/test/video.mp4

# Check client logs
tail -f ~/signage_agent.log

# Verify media downloads
ls -la ~/signage_media/
```

### Performance Issues
- **Raspberry Pi**: Use omxplayer for hardware acceleration
- **Power Supply**: Ensure adequate power (2.5A+ for Pi 4)
- **SD Card**: Use Class 10 or better for Raspberry Pi
- **Network**: Check bandwidth for media downloads

## 🚦 API Endpoints

### Client Communication
- `POST /api/devices/{device_id}/checkin` - Device heartbeat
- `GET /api/devices/{device_id}/playlist` - Get assigned playlist
- `POST /api/devices/{device_id}/log` - Send log messages

### Web Dashboard  
- `GET /` - Dashboard overview
- `GET /devices` - Device management
- `GET /media` - Media library
- `GET /playlists` - Playlist management

## 📁 Project Structure

```
signage/
├── app.py                 # Flask application setup
├── routes.py              # Web routes and API endpoints
├── models.py              # Database models
├── auth.py                # Authentication system
├── client_agent.py        # Client software for devices
├── setup_client.sh        # Shell setup script
├── setup_client.py        # Python setup script
├── create_admin.py        # Admin user creation
├── templates/             # HTML templates
├── static/               # CSS, JS, images
└── uploads/              # Media file storage
```

## 🔐 Security

### Server Security
- Session-based authentication
- Secure password hashing
- CSRF protection
- Input validation and sanitization

### Client Security
- Outbound-only connections
- No inbound ports required
- Secure file handling
- Automatic updates from server

### Network Security
- Use HTTPS in production
- VPN recommended for remote devices
- Firewall configuration
- Regular security updates

## 🚀 Deployment

### Development
```bash
python3 create_admin.py
python3 main.py
```

### Production
- Use reverse proxy (nginx)
- SSL/TLS certificates
- PostgreSQL database
- Container deployment
- Monitoring and logging

## 📈 Scaling

### Multiple Locations
- Central server can manage hundreds of devices
- Geographic distribution supported
- Bandwidth optimization with local caching
- Staggered update scheduling

### Load Balancing
- Multiple server instances
- Database clustering
- CDN for media distribution
- Monitoring and alerting

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes and test
4. Submit pull request

## 📄 License

This project is open source. See LICENSE file for details.

## 🆘 Support

For technical support and documentation:
- Check the [CLIENT_SETUP.md](CLIENT_SETUP.md) for detailed setup instructions
- Review logs for troubleshooting
- Create GitHub issues for bugs or feature requests

---

**Repository**: https://github.com/tbnobed/signage.git

## File List for GitHub Repository

To set up the GitHub repository, you'll need to upload these files:

**Core Application:**
- `app.py` - Flask application setup
- `main.py` - Application entry point
- `routes.py` - Web routes and API endpoints
- `models.py` - Database models
- `auth.py` - Authentication system
- `pyproject.toml` - Python dependencies

**Client Setup:**
- `setup_client.sh` - Shell script for automatic client installation
- `setup_client.py` - Python setup script for client configuration
- `client_agent.py` - Client software for display devices

**Admin Tools:**
- `create_admin.py` - Secure admin user creation script

**Documentation:**
- `README.md` - This comprehensive guide
- `CLIENT_SETUP.md` - Detailed client setup instructions
- `replit.md` - Project architecture and preferences

**Web Interface:**
- `templates/` - All HTML templates (base.html, dashboard.html, devices.html, etc.)
- `static/` - CSS, JavaScript, and assets

Once uploaded to GitHub, users can install clients with:
```bash
curl -L https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh | bash
```