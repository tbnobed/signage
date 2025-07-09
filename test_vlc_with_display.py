#!/usr/bin/env python3

import subprocess
import time
import os

def test_vlc_with_display():
    """Test VLC with proper display setup"""
    print("Testing VLC with display setup...")
    
    media_file = "/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4"
    
    # Kill existing processes
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
    time.sleep(2)
    
    print("=== Method 1: VLC with Xvfb virtual display ===")
    
    # Start Xvfb
    xvfb_cmd = ['Xvfb', ':99', '-screen', '0', '1920x1080x24', '-ac']
    print(f"Starting Xvfb: {' '.join(xvfb_cmd)}")
    
    try:
        xvfb_process = subprocess.Popen(xvfb_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        
        if xvfb_process.poll() is not None:
            print("❌ Xvfb failed to start")
            return
        
        print("✅ Xvfb started")
        
        # Test VLC with DISPLAY=:99
        print("Testing VLC with DISPLAY=:99...")
        print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
        
        env = os.environ.copy()
        env['DISPLAY'] = ':99'
        
        vlc_cmd = ['vlc', '--fullscreen', '--intf', 'dummy', '--play-and-exit', media_file]
        vlc_process = subprocess.Popen(vlc_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(10)
        
        if vlc_process.poll() is None:
            print("✅ VLC running with virtual display")
            vlc_process.terminate()
            vlc_process.wait()
        else:
            stdout, stderr = vlc_process.communicate()
            print("❌ VLC exited with virtual display")
            print(f"stderr: {stderr.decode()[:200]}")
        
        # Clean up Xvfb
        xvfb_process.terminate()
        xvfb_process.wait()
        
    except Exception as e:
        print(f"❌ Virtual display test failed: {e}")
    
    time.sleep(2)
    
    print("\n=== Method 2: Direct console with no DISPLAY ===")
    print("Testing VLC without DISPLAY variable...")
    print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
    
    # Remove DISPLAY and try console output
    env = os.environ.copy()
    env.pop('DISPLAY', None)
    
    vlc_cmd = ['vlc', '--intf', 'dummy', '--vout', 'fb', '--fullscreen', '--play-and-exit', media_file]
    vlc_process = subprocess.Popen(vlc_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(10)
    
    if vlc_process.poll() is None:
        print("✅ VLC running in console mode")
        vlc_process.terminate()
        vlc_process.wait()
    else:
        stdout, stderr = vlc_process.communicate()
        print("❌ VLC exited in console mode")
        print(f"stderr: {stderr.decode()[:200]}")
    
    # Final cleanup
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)

if __name__ == "__main__":
    test_vlc_with_display()