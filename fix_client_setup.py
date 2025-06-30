#!/usr/bin/env python3
"""
Quick fix script to move signage client files to correct user directory
and fix permissions
"""

import os
import shutil
import subprocess
import pwd
import grp

def main():
    print("🔧 Fixing signage client setup...")
    
    # Check if running as root
    if os.getuid() != 0:
        print("❌ This script must be run as root (with sudo)")
        print("Usage: sudo python3 fix_client_setup.py")
        exit(1)
    
    # Get target user
    username = input("Enter username to move signage to (default: obtv1): ").strip() or 'obtv1'
    
    try:
        user_info = pwd.getpwnam(username)
        user_home = user_info.pw_dir
        uid = user_info.pw_uid
        gid = user_info.pw_gid
    except KeyError:
        print(f"❌ User '{username}' not found")
        exit(1)
    
    # Paths
    root_signage = "/root/signage"
    user_signage = os.path.join(user_home, "signage")
    
    print(f"Moving from: {root_signage}")
    print(f"Moving to: {user_signage}")
    
    # Stop the service first
    print("🛑 Stopping signage service...")
    subprocess.run(["systemctl", "stop", "signage-client"], check=False)
    
    # Create user signage directory
    os.makedirs(user_signage, exist_ok=True)
    
    # Copy files if root directory exists
    if os.path.exists(root_signage):
        print("📁 Moving files...")
        
        # Copy all files from root to user directory
        for item in os.listdir(root_signage):
            src = os.path.join(root_signage, item)
            dst = os.path.join(user_signage, item)
            
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            
            print(f"   ✅ Moved: {item}")
    
    # Set ownership
    print(f"👤 Setting ownership to {username}...")
    for root, dirs, files in os.walk(user_signage):
        os.chown(root, uid, gid)
        for d in dirs:
            os.chown(os.path.join(root, d), uid, gid)
        for f in files:
            os.chown(os.path.join(root, f), uid, gid)
    
    # Update systemd service file
    print("⚙️  Updating systemd service...")
    
    service_content = f"""[Unit]
Description=Digital Signage Client
After=network.target

[Service]
Type=simple
User={username}
Group={username}
WorkingDirectory={user_signage}
EnvironmentFile={user_signage}/.env
ExecStart=/usr/bin/python3 {user_signage}/client_agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    with open("/etc/systemd/system/signage-client.service", "w") as f:
        f.write(service_content)
    
    # Reload systemd and start service
    print("🔄 Reloading systemd...")
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    
    print("🚀 Starting signage service...")
    result = subprocess.run(["systemctl", "start", "signage-client"], check=False)
    
    if result.returncode == 0:
        print("✅ Service started successfully!")
    else:
        print("❌ Service failed to start, checking status...")
        subprocess.run(["systemctl", "status", "signage-client"], check=False)
    
    # Clean up root directory if everything worked
    if os.path.exists(root_signage) and os.path.exists(user_signage):
        if input("Remove old files from /root/signage? [y/N]: ").strip().lower() == 'y':
            shutil.rmtree(root_signage)
            print("🗑️  Removed old files")
    
    print("\n✅ Fix complete!")
    print(f"Files are now in: {user_signage}")
    print("Check service status with: sudo systemctl status signage-client")

if __name__ == "__main__":
    main()