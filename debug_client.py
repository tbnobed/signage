#!/usr/bin/env python3

import os
import requests
import subprocess
import time

# Test the actual client functionality
SERVER_URL = 'https://display.obtv.io'
DEVICE_ID = 't-zyw3'

def test_server_connection():
    """Test server connection and API responses"""
    print("Testing server connection...")
    
    # Test checkin
    try:
        response = requests.post(f"{SERVER_URL}/api/devices/{DEVICE_ID}/checkin", 
                               json={"status": "online"}, timeout=10)
        print(f"Checkin response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Checkin failed: {e}")
    
    # Test playlist fetch
    try:
        response = requests.get(f"{SERVER_URL}/api/devices/{DEVICE_ID}/playlist", timeout=10)
        print(f"Playlist response: {response.status_code} - {response.text}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Playlist fetch failed: {e}")
        return None

def test_xvfb():
    """Test if Xvfb is running"""
    print("Testing Xvfb...")
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'Xvfb :99' in result.stdout:
            print("✅ Xvfb is running")
        else:
            print("❌ Xvfb is not running")
            
        # Check if display is available
        env = os.environ.copy()
        env['DISPLAY'] = ':99'
        result = subprocess.run(['xdpyinfo'], capture_output=True, text=True, env=env)
        if result.returncode == 0:
            print("✅ Display :99 is accessible")
        else:
            print("❌ Display :99 is not accessible")
    except Exception as e:
        print(f"Xvfb test failed: {e}")

def test_vlc():
    """Test VLC with virtual display"""
    print("Testing VLC...")
    
    env = os.environ.copy()
    env['DISPLAY'] = ':99'
    
    try:
        # Test VLC version
        result = subprocess.run(['vlc', '--version'], capture_output=True, text=True, env=env)
        if result.returncode == 0:
            print("✅ VLC is working")
        else:
            print("❌ VLC version check failed")
            
        # Check if VLC is currently running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'vlc' in result.stdout:
            print("✅ VLC process is running")
        else:
            print("❌ VLC process is not running")
            
    except Exception as e:
        print(f"VLC test failed: {e}")

if __name__ == "__main__":
    print("=== Digital Signage Client Debug ===")
    
    playlist = test_server_connection()
    test_xvfb()
    test_vlc()
    
    print("\n=== Summary ===")
    if playlist:
        print(f"Playlist assigned: {playlist.get('playlist', {}).get('name', 'None')}")
        items = playlist.get('playlist', {}).get('items', [])
        print(f"Media items: {len(items)}")
        for i, item in enumerate(items):
            print(f"  {i+1}. {item.get('original_filename', 'Unknown')}")
    else:
        print("No playlist data received")