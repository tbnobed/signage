#!/usr/bin/env python3

import os
import subprocess
import sys
import time
import requests

def check_display_environment():
    """Check if display environment is properly configured"""
    print("=== Display Environment Check ===")
    
    # Check if Xvfb is running
    result = subprocess.run(['pgrep', '-f', 'Xvfb.*:99'], capture_output=True)
    if result.returncode == 0:
        print("✅ Xvfb is running")
        
        # Test display accessibility
        env = os.environ.copy()
        env['DISPLAY'] = ':99'
        
        try:
            result = subprocess.run(['xdpyinfo'], capture_output=True, env=env, timeout=5)
            if result.returncode == 0:
                print("✅ Display :99 is accessible")
            else:
                print("❌ Display :99 is not accessible")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Display test timed out")
            return False
    else:
        print("❌ Xvfb is not running")
        return False
    
    return True

def test_vlc_playback():
    """Test VLC media playback"""
    print("\n=== VLC Playback Test ===")
    
    env = os.environ.copy()
    env['DISPLAY'] = ':99'
    
    # Check if VLC is installed
    try:
        result = subprocess.run(['which', 'vlc'], capture_output=True, timeout=5)
        if result.returncode != 0:
            print("❌ VLC not found")
            return False
        print("✅ VLC is installed")
    except subprocess.TimeoutExpired:
        print("❌ VLC check timed out")
        return False
    
    # Check if media file exists
    media_dir = os.path.expanduser('~/signage_media')
    if not os.path.exists(media_dir):
        print(f"❌ Media directory {media_dir} does not exist")
        return False
    
    media_files = os.listdir(media_dir)
    if not media_files:
        print("❌ No media files found")
        return False
    
    print(f"✅ Found {len(media_files)} media files")
    
    # Test VLC with a media file
    test_file = os.path.join(media_dir, media_files[0])
    print(f"Testing VLC with: {test_file}")
    
    try:
        # Start VLC and let it run for 5 seconds
        vlc_process = subprocess.Popen([
            'vlc', '--fullscreen', '--no-osd', '--intf', 'dummy', 
            '--no-video-title-show', '--play-and-exit', test_file
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(5)
        
        if vlc_process.poll() is None:
            print("✅ VLC is playing media")
            vlc_process.terminate()
            vlc_process.wait()
            return True
        else:
            stdout, stderr = vlc_process.communicate()
            print(f"❌ VLC failed to play: {stderr.decode()[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ VLC test failed: {e}")
        return False

def fix_display_issues():
    """Fix common display issues"""
    print("\n=== Fixing Display Issues ===")
    
    # Kill any existing Xvfb processes
    subprocess.run(['pkill', '-f', 'Xvfb.*:99'], capture_output=True)
    time.sleep(2)
    
    # Start Xvfb with proper configuration
    print("Starting Xvfb...")
    xvfb_process = subprocess.Popen([
        'Xvfb', ':99', '-screen', '0', '1920x1080x24', '-ac', 
        '+extension', 'GLX', '-nolisten', 'tcp', '-dpi', '96'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(3)
    
    if xvfb_process.poll() is None:
        print("✅ Xvfb started successfully")
        return True
    else:
        stdout, stderr = xvfb_process.communicate()
        print(f"❌ Xvfb failed to start: {stderr.decode()}")
        return False

def check_client_service():
    """Check signage client service status"""
    print("\n=== Client Service Check ===")
    
    try:
        result = subprocess.run(['systemctl', 'is-active', 'signage-client'], 
                              capture_output=True, text=True)
        if result.stdout.strip() == 'active':
            print("✅ Signage client service is active")
        else:
            print(f"❌ Signage client service is {result.stdout.strip()}")
            
        # Check service logs
        result = subprocess.run(['journalctl', '-u', 'signage-client', '-n', '10', '--no-pager'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("Recent service logs:")
            print(result.stdout[-500:])  # Show last 500 chars
        
    except Exception as e:
        print(f"Service check failed: {e}")

def main():
    print("Digital Signage Display Fix Script")
    print("=" * 40)
    
    # Check current state
    display_ok = check_display_environment()
    
    if not display_ok:
        print("\nAttempting to fix display issues...")
        if fix_display_issues():
            display_ok = check_display_environment()
    
    if display_ok:
        vlc_ok = test_vlc_playback()
        if not vlc_ok:
            print("\n❌ VLC playback test failed")
    
    check_client_service()
    
    print("\n" + "=" * 40)
    if display_ok:
        print("✅ Display environment is working")
    else:
        print("❌ Display environment needs attention")
        
    print("\nTo restart the client service:")
    print("sudo systemctl restart signage-client")

if __name__ == "__main__":
    main()