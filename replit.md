# DisplayHQ

## Overview

This is a comprehensive Flask-based web application for managing display networks across multiple remote locations. DisplayHQ provides a centralized admin dashboard for content management and lightweight client agents that run on remote devices (Raspberry Pi, Intel NUC) to display content on connected TVs.

## System Architecture

### Backend Architecture
- **Framework**: Flask with SQLAlchemy ORM
- **Database**: SQLite (configurable to PostgreSQL via DATABASE_URL)
- **Authentication**: Flask-Login with session-based authentication
- **File Storage**: Local filesystem with configurable upload directory
- **API**: RESTful endpoints for client-server communication

### Frontend Architecture
- **Templates**: Jinja2 templating with Bootstrap 5 dark theme
- **Styling**: Bootstrap CSS with custom CSS enhancements
- **JavaScript**: Vanilla JavaScript with Bootstrap components
- **Icons**: Font Awesome for consistent iconography

### Client Architecture
- **Client Agent**: Standalone Python script for remote devices
- **Media Players**: Supports omxplayer, VLC, and ffplay
- **Communication**: HTTP polling-based client-server communication
- **Caching**: Local media file caching for offline playback

## Key Components

### Web Application Components
1. **User Management**: Authentication system with admin user creation
2. **Device Management**: Registration and monitoring of remote display devices
3. **Media Library**: Upload, organize, and manage images and videos
4. **Playlist System**: Create ordered sequences of media content with timing controls
5. **Dashboard**: Real-time overview of system status and device health

### Client Agent Components
1. **Media Synchronization**: Automatic download and caching of media files
2. **Playback Engine**: Multi-player support with crash recovery
3. **Heartbeat System**: Regular server check-ins for status monitoring
4. **Auto-recovery**: Handles network interruptions and system crashes

### Database Schema
- **Users**: Admin authentication and user management
- **Devices**: Remote display device registration and status tracking
- **MediaFiles**: Media asset management with metadata
- **Playlists**: Content sequence definitions with timing
- **PlaylistItems**: Individual media items within playlists
- **DeviceLogs**: Device activity and error logging

## Data Flow

### Admin-to-Device Flow
1. Admin uploads media files via web dashboard
2. Admin creates/edits playlists containing media sequences
3. Admin assigns playlists to specific devices
4. Client agents poll server for updates (configurable interval)
5. Client agents download new media and update local playlists
6. Media plays in sequence according to playlist configuration

### Device-to-Server Flow
1. Client agents send heartbeat signals with status updates
2. Server tracks device online/offline status and last check-in times
3. Client agents report current playing media and any errors
4. Server logs device activity for monitoring and troubleshooting

## External Dependencies

### Python Packages
- Flask: Web framework
- Flask-SQLAlchemy: Database ORM
- Flask-Login: Authentication management
- Werkzeug: WSGI utilities and security
- Requests: HTTP client for API communication

### Frontend Dependencies
- Bootstrap 5: UI framework with dark theme
- Font Awesome: Icon library
- JavaScript: Client-side interactivity

### Media Players (Client-side)
- omxplayer: Hardware-accelerated player for Raspberry Pi
- VLC: Cross-platform media player
- ffplay: FFmpeg-based media player

## Deployment Strategy

### Server Deployment
- Designed for containerized deployment with Docker support
- Configurable via environment variables
- Supports both SQLite (development) and PostgreSQL (production)
- SSL/TLS termination handled by reverse proxy
- File uploads stored in persistent volume

### Client Deployment
- Interactive setup script (setup_client.py) downloads from GitHub repository
- Lightweight Python script for remote devices
- Auto-start on boot configuration via systemd service
- Minimal dependencies for embedded systems
- User-friendly configuration prompts for server URL and device ID
- Automatic media directory creation and management
- GitHub repository: https://github.com/tbnobed/signage.git

### Network Architecture
- Outbound-only client connections (NAT/firewall friendly)
- Polling-based communication (no inbound ports required)
- Configurable check-in intervals for bandwidth optimization
- Local media caching for offline operation

## Changelog
- June 30, 2025. Initial setup
- June 30, 2025. Security improvements: Removed web-based admin setup, implemented command-line admin creation
- June 30, 2025. Theme update: Changed from purple Replit theme to modern dark theme with cyan accents
- June 30, 2025. GitHub integration: Added GitHub repository (https://github.com/tbnobed/signage.git) for client distribution
- June 30, 2025. Interactive setup script: Created setup_client.py that asks user for device ID and automates client installation
- June 30, 2025. Docker deployment: Complete Docker setup with PostgreSQL, auto-admin creation, and .env configuration - successfully deployed and tested
- June 30, 2025. Client deployment success: Fixed permission issues in setup script, client successfully connecting to production server at https://display.obtv.io with proper user permissions and systemd service
- June 30, 2025. Playlist media management fix: Resolved critical form structure issue preventing media items from being saved to playlists. Media items are now properly added, saved, and displayed in playlists.
- June 30, 2025. UI improvements: Updated playlist edit page with horizontal two-column layout for better space utilization. Left column shows settings and info, right column shows media items and available media grid.
- June 30, 2025. Client display access fix: Enhanced setup_client.py to automatically configure autologin, display environment variables, and screen blanking disable for proper VLC display access.
- June 30, 2025. Critical setup script fixes: Fixed duplicate DEVICE_ID entries in .env files and implemented robust autologin configuration for Ubuntu 24.04 with GDM3, systemd, and LightDM fallbacks. Added automatic screen lock/power management disabling.
- July 8, 2025. Ubuntu Server headless deployment success: Completely redesigned client setup for Ubuntu Server environments. Replaced heavy desktop environment with minimal Xvfb virtual framebuffer approach. Client now successfully runs headless with VLC displaying media via virtual display :99. Setup script installs only essential packages (xvfb, x11-utils, pulseaudio, alsa-utils) and creates robust systemd service with proper Xvfb management.
- September 11, 2025. Single media assignment system: Implemented complete single media file assignment capability for devices. Added database schema for assigned_media_id and assignment_updated_at fields. Created backward-compatible API endpoints using synthetic playlists with negative integer IDs. Built elegant tabbed UI interface for both playlist and single media assignment with dynamic tab activation. Includes Docker deployment migration and maintains zero client changes requirement - existing client_agent.py works unchanged with instant content switching.
- September 11, 2025. Kiosk mode enhancement: Enhanced setup_client.py with comprehensive kiosk mode configuration for Ubuntu 22.04. Features include: complete notification disabling, power management configuration (never sleep/suspend), screen lock disabling, TBN logo background setup, automatic updates disabling, TeamViewer remote management installation, and persistent settings restoration. Creates autostart script to maintain kiosk settings across reboots and user sessions. Provides true production-ready kiosk mode for unattended digital signage deployment.
- September 12, 2025. Auto-update system implementation: Built comprehensive auto-update system with client version tracking (CLIENT_VERSION = "2.1.0"), server API endpoint for version checking, 6-hour background update checks, secure Git-based download and installation process, and client version display in admin dashboard. Updated Docker build files with client_version database column migration to ensure proper deployment support for the auto-update functionality.
- October 21, 2025. Admin-controlled update system: Redesigned update system from automatic 6-hour checking to admin-controlled push updates via devices page. Added "Update Client" button with confirmation modal, server route for update commands, and client handler for on-demand updates. Upgraded to CLIENT_VERSION = "2.2.0" with mpv integration for gapless video playback.
- October 21, 2025. Inline device editing: Added inline editing capabilities for device names and locations directly from devices page. Click edit icon to modify fields without page reload, with real-time AJAX updates and success/error notifications.
- October 21, 2025. Raspberry Pi optimization (CLIENT_VERSION = "2.3.0"): Implemented comprehensive Raspberry Pi hardware detection in both setup script and client. Setup script now automatically detects Raspberry Pi and installs mpv with optimized packages (libraspberrypi-bin, mesa-utils) instead of VLC which has display errors. Client detects Raspberry Pi hardware and configures mpv with DRM video output (--vo=gpu --hwdec=auto --gpu-context=drm) for proper hardware-accelerated playback. Eliminates VLC "window not available" and "video output creation failed" errors on Raspberry Pi.

## User Preferences

Preferred communication style: Simple, everyday language.
Design preferences: Dark theme preferred, avoid purple colors, prefers modern cyan/blue color scheme.