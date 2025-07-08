#!/usr/bin/env python3

import os
import subprocess
import sys

def check_display_hardware():
    """Check what display hardware is available"""
    print("Checking display hardware...")
    
    # Check for framebuffer devices
    framebuffers = []
    for i in range(8):
        fb_path = f'/dev/fb{i}'
        if os.path.exists(fb_path):
            framebuffers.append(fb_path)
    
    if framebuffers:
        print(f"Found framebuffer devices: {framebuffers}")
        return True
    else:
        print("No framebuffer devices found")
    
    # Check for DRM devices
    drm_devices = []
    if os.path.exists('/dev/dri'):
        drm_devices = [f'/dev/dri/{f}' for f in os.listdir('/dev/dri') if f.startswith('card')]
    
    if drm_devices:
        print(f"Found DRM devices: {drm_devices}")
        return True
    else:
        print("No DRM devices found")
    
    return False

def setup_direct_display():
    """Setup direct display output without X server"""
    print("Setting up direct display output...")
    
    # Install DRM/KMS tools if not present
    try:
        subprocess.run(['sudo', 'apt', 'update'], check=True, capture_output=True)
        subprocess.run(['sudo', 'apt', 'install', '-y', 'libdrm2', 'libdrm-dev'], 
                      check=True, capture_output=True)
        print("DRM tools installed")
    except subprocess.CalledProcessError:
        print("Failed to install DRM tools")
    
    # Configure VLC for direct DRM output
    vlc_config = """
# VLC direct DRM output configuration
[dummy]
intf=dummy

[drm]
vout=drm

[core]
vout=drm
"""
    
    config_dir = os.path.expanduser('~/.config/vlc')
    os.makedirs(config_dir, exist_ok=True)
    
    with open(os.path.join(config_dir, 'vlcrc'), 'w') as f:
        f.write(vlc_config)
    
    print("VLC configured for direct DRM output")

def update_client_for_drm():
    """Update client agent to use DRM output"""
    print("Updating client agent for DRM output...")
    
    # Update VLC command for DRM output
    vlc_cmd = [
        'vlc', '--fullscreen', '--no-osd', '--loop', '--intf', 'dummy',
        '--no-video-title-show', '--vout', 'drm', '--no-audio'
    ]
    
    print(f"VLC command: {' '.join(vlc_cmd)}")
    
    # Test VLC with DRM
    test_video = '/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4'
    if os.path.exists(test_video):
        print(f"Testing VLC with DRM output: {test_video}")
        try:
            # Run VLC with DRM output for 10 seconds
            process = subprocess.Popen(vlc_cmd + [test_video])
            import time
            time.sleep(10)
            process.terminate()
            print("VLC DRM test completed")
        except Exception as e:
            print(f"VLC DRM test failed: {e}")

def main():
    print("Digital Signage Display Fix Script")
    print("=" * 50)
    
    # Check if we're running on a system with display hardware
    if not check_display_hardware():
        print("ERROR: No display hardware detected!")
        print("This system may not be connected to a display device.")
        return
    
    setup_direct_display()
    update_client_for_drm()
    
    print("\nNext steps:")
    print("1. Restart the signage client service:")
    print("   sudo systemctl restart signage-client")
    print("2. Check if video is displaying on connected monitor/TV")
    print("3. Monitor logs: tail -f /home/obtv1/signage_agent.log")

if __name__ == "__main__":
    main()