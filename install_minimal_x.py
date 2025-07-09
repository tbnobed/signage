#!/usr/bin/env python3

import subprocess
import os

def install_minimal_x():
    """Install minimal X server components for video display"""
    print("Installing minimal X server components...")
    
    # Update package list
    print("Updating package list...")
    subprocess.run(['apt', 'update'], check=True)
    
    # Install minimal X server and Intel graphics drivers
    packages = [
        'xserver-xorg-core',      # Minimal X server
        'xserver-xorg-video-intel', # Intel graphics driver
        'xinit',                  # X initialization
        'xvfb'                    # Virtual framebuffer (backup)
    ]
    
    print(f"Installing: {' '.join(packages)}")
    
    cmd = ['apt', 'install', '-y'] + packages
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ X server components installed successfully")
        
        # Create basic X configuration
        print("Creating X configuration...")
        xorg_conf = """
Section "Device"
    Identifier "Intel Graphics"
    Driver "intel"
    Option "TearFree" "true"
EndSection

Section "Screen"
    Identifier "Screen0"
    Device "Intel Graphics"
    DefaultDepth 24
    SubSection "Display"
        Depth 24
        Modes "1920x1080" "1680x1050" "1280x1024" "1024x768"
    EndSubSection
EndSection
"""
        
        os.makedirs('/etc/X11/xorg.conf.d', exist_ok=True)
        with open('/etc/X11/xorg.conf.d/20-intel.conf', 'w') as f:
            f.write(xorg_conf)
        
        print("✅ X configuration created")
        
    else:
        print(f"❌ Installation failed: {result.stderr}")
        
if __name__ == "__main__":
    install_minimal_x()