# Digital Signage Management System

## Overview

This is a comprehensive Flask-based web application for managing digital signage displays across multiple remote locations. The system provides a centralized admin dashboard for content management and lightweight client agents that run on remote devices (Raspberry Pi, Intel NUC) to display content on connected TVs.

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
- Lightweight Python script for remote devices
- Auto-start on boot configuration
- Minimal dependencies for embedded systems
- Configurable server URL and device identification
- Automatic media directory creation and management

### Network Architecture
- Outbound-only client connections (NAT/firewall friendly)
- Polling-based communication (no inbound ports required)
- Configurable check-in intervals for bandwidth optimization
- Local media caching for offline operation

## Changelog
- June 30, 2025. Initial setup
- June 30, 2025. Security improvements: Removed web-based admin setup, implemented command-line admin creation
- June 30, 2025. Theme update: Changed from purple Replit theme to modern dark theme with cyan accents

## User Preferences

Preferred communication style: Simple, everyday language.
Design preferences: Dark theme preferred, avoid purple colors, prefers modern cyan/blue color scheme.