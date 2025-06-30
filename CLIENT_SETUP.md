# Digital Signage Client Setup Guide

This guide explains how to set up and connect client devices (Raspberry Pi, Intel NUC, or any Linux device) to your digital signage management system.

## Quick Setup Overview

1. **Register device** in the web dashboard
2. **Download client script** to your device
3. **Install dependencies** on the device
4. **Configure environment** variables
5. **Start the client** agent

## Step 1: Register Your Device

### Using the Web Dashboard
1. Log into your signage management system
2. Go to **Devices** page
3. Click **Add Device**
4. Fill in device details:
   - **Name**: Friendly name (e.g., "Reception TV", "Lobby Display")
   - **Device ID**: Unique identifier (e.g., "lobby-tv-01")
   - **Location**: Physical location description

### Using Admin Commands
You can also register devices via the database directly if needed.

## Step 2: Prepare Your Client Device

### Supported Devices
- **Raspberry Pi** (3B+, 4, Zero 2W)
- **Intel NUC** or similar mini PCs
- **Any Linux computer** with video output

### Required Software
The client will automatically detect and use the best available media player:

**Preferred (Hardware Accelerated):**
- `omxplayer` (Raspberry Pi - best performance)

**Alternative Players:**
- `vlc` (Cross-platform)
- `ffplay` (Part of FFmpeg)

## Step 3: One-Line Installation

### Automatic Setup (Recommended)
The easiest way to set up a client device is using our automated installation script:

```bash
curl -L https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh | bash
```

This script will:
1. **Install Python 3** and all required dependencies
2. **Install media players** (omxplayer for Pi, VLC/FFmpeg for PC)
3. **Download the client software** from GitHub
4. **Ask for your configuration** (server URL, device ID)
5. **Set up auto-start service** (systemd)
6. **Test the connection** and start the service

### Manual Download (Alternative)
If you prefer to download and run manually:
```bash
# Download the setup script
wget https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.sh

# Make it executable and run
chmod +x setup_client.sh
./setup_client.sh
```

## Step 4: Interactive Configuration

The setup script will ask you for:

### Set Environment Variables
Create a configuration file:

```bash
nano ~/signage/.env
```

Add these settings (replace with your values):
```bash
# Your signage server URL
SIGNAGE_SERVER_URL=https://display.obtv.io

# Unique device identifier (must match what you registered)
DEVICE_ID=your-device-id

# Check interval in seconds (how often to contact server)
CHECK_INTERVAL=60

# Optional: Custom media directory
# MEDIA_DIR=/home/pi/signage_media

# Optional: Custom log file location
# LOG_FILE=/home/pi/signage_agent.log
```

### Load Environment Variables
```bash
# Add to your shell profile for automatic loading
echo 'export $(cat ~/signage/.env | xargs)' >> ~/.bashrc
source ~/.bashrc
```

## Step 5: Test the Client

### Manual Test Run
```bash
cd ~/signage
python3 client_agent.py
```

You should see output like:
```
INFO: Signage client started for device: your-device-id
INFO: Server URL: http://YOUR_SERVER:5000
INFO: Media player: omxplayer
INFO: Successfully checked in with server
```

### Check Dashboard
- Go to your web dashboard
- Navigate to **Devices**
- Your device should show as "Online"
- Check the last check-in time

## Step 6: Auto-Start Setup

### Create Systemd Service (Recommended)
```bash
sudo nano /etc/systemd/system/signage-client.service
```

Add this content (adjust paths for your user):
```ini
[Unit]
Description=Digital Signage Client
After=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/signage
Environment=SIGNAGE_SERVER_URL=http://YOUR_SERVER:5000
Environment=DEVICE_ID=your-device-id
Environment=CHECK_INTERVAL=60
ExecStart=/usr/bin/python3 /home/pi/signage/client_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable signage-client.service
sudo systemctl start signage-client.service

# Check status
sudo systemctl status signage-client.service
```

### Alternative: Cron Job
Add to crontab for startup:
```bash
crontab -e
```

Add this line:
```bash
@reboot cd /home/pi/signage && python3 client_agent.py &
```

## Step 7: Assign Content

### Create Playlists
1. In the web dashboard, go to **Media**
2. Upload your images and videos
3. Go to **Playlists**
4. Create a new playlist and add media files
5. Set timing for each item

### Assign to Device
1. Go to **Devices**
2. Find your device
3. Click **Assign Playlist**
4. Select the playlist you created
5. The device will automatically download and play the content

## Troubleshooting

### Client Not Connecting
1. **Check network connectivity:**
   ```bash
   ping YOUR_SERVER_IP
   curl http://YOUR_SERVER_IP:5000
   ```

2. **Verify environment variables:**
   ```bash
   echo $SIGNAGE_SERVER_URL
   echo $DEVICE_ID
   ```

3. **Check firewall settings** on both client and server

### Media Not Playing
1. **Test media player manually:**
   ```bash
   # Test with a sample file
   omxplayer /path/to/test/video.mp4
   # OR
   vlc /path/to/test/video.mp4
   ```

2. **Check media directory permissions:**
   ```bash
   ls -la ~/signage_media/
   ```

3. **Review client logs:**
   ```bash
   tail -f ~/signage_agent.log
   ```

### Performance Issues
1. **For Raspberry Pi:**
   - Use omxplayer for best performance
   - Ensure adequate power supply (2.5A+ for Pi 4)
   - Use fast SD card (Class 10 or better)

2. **For all devices:**
   - Check available disk space
   - Monitor CPU/memory usage
   - Reduce media file sizes if needed

## Remote Management

### View Device Status
- Check the **Dashboard** for real-time device status
- **Devices** page shows detailed information
- Device logs are available in the web interface

### Update Content
- Upload new media files
- Modify playlists
- Reassign playlists to devices
- Changes are automatically synced

### Remote Troubleshooting
- View device logs through the web interface
- Check last check-in times
- Monitor current playing media
- Review error messages

## Advanced Configuration

### Custom Media Players
Edit `client_agent.py` to add support for custom players:
```python
PLAYER_COMMANDS = {
    'custom_player': ['your_player', '--fullscreen', '--loop'],
    # Add your player configuration
}
```

### Network Optimization
- Adjust `CHECK_INTERVAL` based on your needs
- Use local caching (enabled by default)
- Configure media cleanup intervals

### Security
- Use HTTPS for production deployments
- Implement VPN for remote devices
- Regularly update client devices

## Getting Help

### Log Files
- Client log: `~/signage_agent.log`
- System service log: `sudo journalctl -u signage-client.service`

### Common Commands
```bash
# Check service status
sudo systemctl status signage-client.service

# Restart service
sudo systemctl restart signage-client.service

# View logs
tail -f ~/signage_agent.log

# Test connectivity
curl http://YOUR_SERVER:5000/api/devices/ping
```

### Support
Check the main README.md for additional troubleshooting information and project details.