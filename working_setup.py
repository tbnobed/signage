#!/usr/bin/env python3
"""
Simple working setup script for digital signage client
This version handles permissions correctly
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    print("🔧 Digital Signage Client Setup (Working Version)")
    print()
    
    # Must run as root
    if os.geteuid() != 0:
        print("❌ This script must be run as root")
        print("Usage: sudo python3 working_setup.py")
        sys.exit(1)
    
    # Get target user
    username = input("Enter username to setup for (default: obtv1): ").strip() or "obtv1"
    
    # Get user info
    try:
        import pwd
        user_info = pwd.getpwnam(username)
        user_home = user_info.pw_dir
        uid = user_info.pw_uid
        gid = user_info.pw_gid
    except KeyError:
        print(f"❌ User '{username}' not found")
        sys.exit(1)
    
    # Setup directories
    signage_dir = Path(user_home) / "signage"
    media_dir = signage_dir / "media"
    
    print(f"Setting up for user: {username}")
    print(f"Home directory: {user_home}")
    print(f"Signage directory: {signage_dir}")
    
    # Stop existing service
    print("🛑 Stopping existing service...")
    subprocess.run(["systemctl", "stop", "signage-client"], check=False)
    
    # Create directories
    print("📁 Creating directories...")
    signage_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(exist_ok=True)
    
    # Set ownership
    os.chown(signage_dir, uid, gid)
    os.chown(media_dir, uid, gid)
    
    # Download client script
    print("⬇️ Downloading client...")
    client_script = signage_dir / "client_agent.py"
    
    import urllib.request
    urllib.request.urlretrieve(
        "https://raw.githubusercontent.com/tbnobed/signage/main/client_agent.py",
        client_script
    )
    os.chmod(client_script, 0o755)
    os.chown(client_script, uid, gid)
    
    # Get configuration
    print("\n⚙️ Configuration:")
    server_url = input("Server URL (default: https://display.obtv.io): ").strip() or "https://display.obtv.io"
    device_id = input("Device ID: ").strip()
    
    if not device_id:
        print("❌ Device ID is required")
        sys.exit(1)
    
    check_interval = input("Check interval in seconds (default: 60): ").strip() or "60"
    
    # Create config file
    print("📝 Creating config...")
    config_file = signage_dir / ".env"
    
    config_content = f"""SIGNAGE_SERVER_URL={server_url}
DEVICE_ID={device_id}
CHECK_INTERVAL={check_interval}
"""
    
    with open(config_file, 'w') as f:
        f.write(config_content)
    os.chown(config_file, uid, gid)
    
    # Create systemd service
    print("🚀 Creating service...")
    
    service_content = f"""[Unit]
Description=Digital Signage Client
After=network.target

[Service]
Type=simple
User={username}
Group={username}
WorkingDirectory={signage_dir}
EnvironmentFile={config_file}
ExecStart=/usr/bin/python3 {client_script}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    with open("/etc/systemd/system/signage-client.service", "w") as f:
        f.write(service_content)
    
    # Reload and start service
    print("🔄 Starting service...")
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "signage-client"], check=True)
    subprocess.run(["systemctl", "start", "signage-client"], check=True)
    
    # Check status
    print("\n📊 Service status:")
    result = subprocess.run(["systemctl", "status", "signage-client", "--no-pager"], check=False)
    
    if result.returncode == 0:
        print("\n✅ Setup complete! Service is running.")
    else:
        print("\n❌ Service failed to start")
        print("Check logs with: journalctl -u signage-client -f")
    
    print(f"\n📁 Files created in: {signage_dir}")
    print("🎯 Register device in dashboard at: https://display.obtv.io")

if __name__ == "__main__":
    main()