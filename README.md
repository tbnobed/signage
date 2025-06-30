# Digital Signage Management System

A comprehensive Flask-based web application for managing digital signage displays across multiple remote locations. This system provides a centralized admin dashboard for content management and lightweight client agents for Raspberry Pi or NUC devices.

## Features

### Admin Dashboard
- **Media Management**: Upload and organize images and videos
- **Playlist Creation**: Create ordered sequences of media content
- **Device Management**: Register and monitor remote display devices
- **Real-time Status**: Monitor device connectivity and current playback
- **User Authentication**: Secure admin access with session management

### Client Agent
- **Automatic Synchronization**: Polls server for playlist updates
- **Local Caching**: Downloads and caches media for offline playback
- **Multi-player Support**: Works with omxplayer, VLC, or ffplay
- **Auto-recovery**: Handles crashes and network interruptions
- **Heartbeat Monitoring**: Regular check-ins with server

## Quick Start

### 1. Initial Setup
First, create an admin user using the secure setup script:

```bash
python create_admin.py
```

This script will prompt you to create the first administrator account securely. After this, the setup functionality is disabled for security.

### 2. Start the Application
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

### 3. Access the System
- Open your browser to `http://localhost:5000`
- Log in with the admin credentials you created
- Start adding devices, uploading media, and creating playlists

## Security Features

- **Secure Admin Creation**: Initial admin account created via command-line script only
- **Session Management**: Secure session-based authentication
- **Password Requirements**: Minimum 12-character passwords enforced
- **File Upload Validation**: Restricted file types and size limits
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Template auto-escaping enabled

## Architecture

