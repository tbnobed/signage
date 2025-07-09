#!/usr/bin/env python3

import subprocess
import time
import os

def test_real_display():
    """Test actual display output methods"""
    print("Testing real display output...")
    
    media_file = "/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4"
    
    # Kill any existing processes
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    subprocess.run(['pkill', '-f', 'X'], capture_output=True)
    time.sleep(2)
    
    print("=== Method 1: Direct X server on console ===")
    print("Starting X server directly on console...")
    
    # Start X server on the console (not virtual)
    x_cmd = ['X', ':0', '-nolisten', 'tcp']
    print(f"Starting: {' '.join(x_cmd)}")
    
    try:
        x_process = subprocess.Popen(x_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)  # Give X time to start
        
        if x_process.poll() is not None:
            stdout, stderr = x_process.communicate()
            print(f"❌ X server failed: {stderr.decode()[:200]}")
        else:
            print("✅ X server started")
            
            # Test VLC with X server
            print("Testing VLC with X server...")
            print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
            
            env = os.environ.copy()
            env['DISPLAY'] = ':0'
            
            vlc_cmd = ['vlc', '--fullscreen', '--intf', 'dummy', '--play-and-exit', media_file]
            vlc_process = subprocess.Popen(vlc_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            time.sleep(10)
            
            if vlc_process.poll() is None:
                print("✅ VLC with X server - running")
                vlc_process.terminate()
                vlc_process.wait()
            else:
                stdout, stderr = vlc_process.communicate()
                print("❌ VLC with X server - exited")
                print(f"stderr: {stderr.decode()[:200]}")
            
            # Clean up X server
            x_process.terminate()
            x_process.wait()
            
    except Exception as e:
        print(f"❌ X server test failed: {e}")
    
    time.sleep(2)
    
    print("\n=== Method 2: Console with Plymouth (if available) ===")
    try:
        # Try to use Plymouth for console graphics
        subprocess.run(['plymouth', 'quit'], capture_output=True)
        time.sleep(1)
        
        print("Testing VLC with console graphics...")
        print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
        
        env = os.environ.copy()
        env.pop('DISPLAY', None)
        
        vlc_cmd = ['vlc', '--fullscreen', '--intf', 'dummy', '--vout', 'fb', 
                   '--fbdev', '/dev/fb0', '--play-and-exit', media_file]
        
        process = subprocess.Popen(vlc_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(10)
        
        if process.poll() is None:
            print("✅ VLC with console graphics - running")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print("❌ VLC with console graphics - exited")
            print(f"stderr: {stderr.decode()[:200]}")
            
    except Exception as e:
        print(f"❌ Console graphics test failed: {e}")
    
    print("\n=== Method 3: Direct DRM output ===")
    try:
        print("Testing VLC with direct DRM output...")
        print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
        
        env = os.environ.copy()
        env.pop('DISPLAY', None)
        
        vlc_cmd = ['vlc', '--fullscreen', '--intf', 'dummy', '--vout', 'drm', 
                   '--play-and-exit', media_file]
        
        process = subprocess.Popen(vlc_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(10)
        
        if process.poll() is None:
            print("✅ VLC with DRM output - running")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print("❌ VLC with DRM output - exited")
            print(f"stderr: {stderr.decode()[:200]}")
            
    except Exception as e:
        print(f"❌ DRM output test failed: {e}")
    
    # Final cleanup
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    subprocess.run(['pkill', '-f', 'X'], capture_output=True)

if __name__ == "__main__":
    test_real_display()