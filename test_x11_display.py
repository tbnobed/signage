#!/usr/bin/env python3

import subprocess
import time
import os

def test_x11_display():
    """Test X11 display approach"""
    print("Testing X11 display approach...")
    
    media_file = "/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4"
    
    if not os.path.exists(media_file):
        print(f"❌ Media file not found: {media_file}")
        return
    
    # Kill any existing processes
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    subprocess.run(['pkill', '-f', 'Xvfb'], capture_output=True)
    time.sleep(1)
    
    print("=== Step 1: Starting virtual X server ===")
    
    # Start Xvfb on display :1
    xvfb_cmd = ['Xvfb', ':1', '-screen', '0', '1920x1080x24', '-ac', '+extension', 'GLX']
    print(f"Starting: {' '.join(xvfb_cmd)}")
    
    try:
        xvfb_process = subprocess.Popen(xvfb_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)  # Give Xvfb time to start
        
        if xvfb_process.poll() is not None:
            stdout, stderr = xvfb_process.communicate()
            print(f"❌ Xvfb failed to start: {stderr.decode()[:200]}")
            return
        
        print("✅ Xvfb started successfully")
        
        print("\n=== Step 2: Testing VLC with X11 output ===")
        print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
        
        # Set up environment for X11
        env = os.environ.copy()
        env['DISPLAY'] = ':1'
        
        # Test VLC with X11 output
        vlc_cmd = ['vlc', '--fullscreen', '--intf', 'dummy', '--play-and-exit', media_file]
        print(f"Running: {' '.join(vlc_cmd)} (DISPLAY=:1)")
        
        vlc_process = subprocess.Popen(vlc_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait 10 seconds
        time.sleep(10)
        
        if vlc_process.poll() is None:
            print("✅ VLC is running with X11")
            vlc_process.terminate()
            vlc_process.wait()
        else:
            stdout, stderr = vlc_process.communicate()
            print("❌ VLC with X11 exited")
            print(f"stderr: {stderr.decode()[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    finally:
        # Clean up
        subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
        if 'xvfb_process' in locals():
            xvfb_process.terminate()
            xvfb_process.wait()
        print("✅ Cleanup completed")

def test_console_display():
    """Test console-based display options"""
    print("\n=== Testing console display options ===")
    
    media_file = "/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4"
    
    # Kill any existing processes
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    time.sleep(1)
    
    print("=== Testing VLC with console output (no root) ===")
    print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
    
    try:
        # Try VLC with console interface and framebuffer
        vlc_cmd = ['vlc', '--intf', 'dummy', '--vout', 'fb', '--fullscreen', '--play-and-exit', media_file]
        print(f"Running: {' '.join(vlc_cmd)}")
        
        process = subprocess.Popen(vlc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait 10 seconds
        time.sleep(10)
        
        if process.poll() is None:
            print("✅ VLC console mode is running")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print("❌ VLC console mode exited")
            print(f"stderr: {stderr.decode()[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Clean up
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)

if __name__ == "__main__":
    test_console_display()
    test_x11_display()