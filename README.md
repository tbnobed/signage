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

## Architecture

