#!/usr/bin/env python3
"""
Fix display service configuration for digital signage
This script sets up proper autologin and display access
"""

import os
import subprocess
import sys

def setup_autologin():
    """Setup Ubuntu autologin for the obtv1 user"""
    print("Setting up autologin...")
    
    # Create gdm3 custom.conf for autologin
    gdm_config = """[daemon]
AutomaticLoginEnable=True
AutomaticLogin=obtv1

[security]

[xdmcp]

[chooser]

[debug]
"""
    
    try:
        # Write gdm3 config
        with open('/etc/gdm3/custom.conf', 'w') as f:
            f.write(gdm_config)
        print("✓ GDM3 autologin configured")
        
        # Also try systemd-logind approach for newer systems
        subprocess.run(['sudo', 'systemctl', 'edit', '--force', '--full', 'getty@tty1.service'], 
                      input="""[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin obtv1 --noclear %I $TERM
""", text=True, check=False)
        
        return True
    except Exception as e:
        print(f"Error setting up autologin: {e}")
        return False

def update_systemd_service():
    """Update the signage systemd service for proper display access"""
    print("Updating systemd service...")
    
    service_content = """[Unit]
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
"""
    
    try:
        # Write new service file
        with open('/etc/systemd/system/signage-client.service', 'w') as f:
            f.write(service_content)
        
        # Reload systemd and restart service
        subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
        subprocess.run(['sudo', 'systemctl', 'stop', 'signage-client'], check=False)
        subprocess.run(['sudo', 'systemctl', 'enable', 'signage-client'], check=True)
        
        print("✓ Systemd service updated")
        return True
    except Exception as e:
        print(f"Error updating systemd service: {e}")
        return False

def setup_display_permissions():
    """Setup proper display permissions"""
    print("Setting up display permissions...")
    
    try:
        # Add obtv1 to video group
        subprocess.run(['sudo', 'usermod', '-a', '-G', 'video', 'obtv1'], check=True)
        
        # Create xorg conf for auto-start X server
        xorg_conf = """Section "ServerLayout"
    Identifier "Layout0"
    Screen 0 "Screen0" 0 0
EndSection

Section "Screen"
    Identifier "Screen0"
    Monitor "Monitor0"
    DefaultDepth 24
EndSection

Section "Monitor"
    Identifier "Monitor0"
EndSection
"""
        
        # Ensure X server starts automatically
        subprocess.run(['sudo', 'systemctl', 'set-default', 'graphical.target'], check=True)
        
        print("✓ Display permissions configured")
        return True
    except Exception as e:
        print(f"Error setting up display permissions: {e}")
        return False

def disable_screen_blanking():
    """Disable screen blanking and power management"""
    print("Disabling screen blanking...")
    
    try:
        # Create autostart directory
        autostart_dir = '/home/obtv1/.config/autostart'
        os.makedirs(autostart_dir, exist_ok=True)
        
        # Create disable-blanking script
        disable_script = """[Desktop Entry]
Type=Application
Name=Disable Screen Blanking
Exec=bash -c "xset s off; xset -dpms; xset s noblank"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
        
        with open(f'{autostart_dir}/disable-blanking.desktop', 'w') as f:
            f.write(disable_script)
        
        # Set ownership
        subprocess.run(['sudo', 'chown', '-R', 'obtv1:obtv1', '/home/obtv1/.config'], check=True)
        
        print("✓ Screen blanking disabled")
        return True
    except Exception as e:
        print(f"Error disabling screen blanking: {e}")
        return False

def main():
    if os.geteuid() != 0:
        print("This script must be run as root (sudo)")
        sys.exit(1)
    
    print("=== Digital Signage Display Fix ===")
    
    success = True
    success &= setup_autologin()
    success &= update_systemd_service()
    success &= setup_display_permissions()
    success &= disable_screen_blanking()
    
    if success:
        print("\n✓ Display configuration complete!")
        print("Please reboot the system for all changes to take effect:")
        print("sudo reboot")
    else:
        print("\n✗ Some configurations failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()