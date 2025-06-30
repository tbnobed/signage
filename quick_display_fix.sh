#!/bin/bash
# Quick fix for display issue - run this on the client device

echo "=== Quick Display Fix for Digital Signage ==="

# Stop the current service
echo "Stopping signage service..."
sudo systemctl stop signage-client

# Kill any running VLC processes
echo "Stopping VLC processes..."
sudo pkill -f vlc

# Set up autologin for obtv1 user
echo "Setting up autologin..."
sudo tee /etc/gdm3/custom.conf > /dev/null << 'EOF'
[daemon]
AutomaticLoginEnable=True
AutomaticLogin=obtv1

[security]

[xdmcp]

[chooser]

[debug]
EOF

# Update the systemd service to run as user with proper display access
echo "Updating systemd service..."
sudo tee /etc/systemd/system/signage-client.service > /dev/null << 'EOF'
[Unit]
Description=Digital Signage Client
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
User=obtv1
Group=obtv1
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/obtv1/.Xauthority
Environment=HOME=/home/obtv1
Environment=USER=obtv1
WorkingDirectory=/home/obtv1/signage
ExecStartPre=/bin/sleep 30
ExecStart=/usr/bin/python3 /home/obtv1/signage/client_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=graphical-session.target
EOF

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload
sudo systemctl enable signage-client

# Add user to video group
echo "Adding user to video group..."
sudo usermod -a -G video obtv1

# Create autostart directory and disable screen blanking
echo "Setting up screen blanking disable..."
sudo -u obtv1 mkdir -p /home/obtv1/.config/autostart

sudo -u obtv1 tee /home/obtv1/.config/autostart/disable-blanking.desktop > /dev/null << 'EOF'
[Desktop Entry]
Type=Application
Name=Disable Screen Blanking
Exec=bash -c "xset s off; xset -dpms; xset s noblank"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

# Set proper ownership
sudo chown -R obtv1:obtv1 /home/obtv1/.config

echo ""
echo "✓ Display fix complete!"
echo ""
echo "Next steps:"
echo "1. Reboot the system: sudo reboot"
echo "2. The system should auto-login and start displaying media"
echo "3. If you still see the login screen, wait 30 seconds for the service to start"
echo ""
echo "To check status after reboot:"
echo "sudo systemctl status signage-client"