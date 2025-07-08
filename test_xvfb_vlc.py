#!/usr/bin/env python3

import os
import subprocess
import time
import sys

def test_xvfb_vlc():
    """Test Xvfb and VLC functionality"""
    
    print("Testing Xvfb and VLC setup...")
    
    # Start Xvfb
    print("1. Starting Xvfb...")
    subprocess.run(['pkill', '-f', 'Xvfb :99'], capture_output=True)
    time.sleep(1)
    
    xvfb_process = subprocess.Popen([
        'Xvfb', ':99', '-screen', '0', '1920x1080x24', '-ac', '+extension', 'GLX'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    time.sleep(2)
    
    # Check if Xvfb is running
    if xvfb_process.poll() is None:
        print("   ✅ Xvfb started successfully")
    else:
        print("   ❌ Xvfb failed to start")
        return False
    
    # Test VLC
    print("2. Testing VLC...")
    env = os.environ.copy()
    env['DISPLAY'] = ':99'
    
    try:
        # Test VLC version
        result = subprocess.run(['vlc', '--version'], 
                              capture_output=True, text=True, env=env, timeout=10)
        if result.returncode == 0:
            print("   ✅ VLC is working")
        else:
            print("   ❌ VLC version check failed")
            return False
    except Exception as e:
        print(f"   ❌ VLC test failed: {e}")
        return False
    
    # Clean up
    print("3. Cleaning up...")
    xvfb_process.terminate()
    xvfb_process.wait()
    print("   ✅ Cleanup complete")
    
    return True

if __name__ == "__main__":
    success = test_xvfb_vlc()
    if success:
        print("\n🎉 All tests passed! The system is ready for digital signage.")
    else:
        print("\n❌ Tests failed. Please check the installation.")
        sys.exit(1)