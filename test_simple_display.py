#!/usr/bin/env python3

import subprocess
import time
import os

def test_simple_display():
    """Test the simplest possible display output"""
    print("Testing simple display output...")
    
    media_file = "/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4"
    
    if not os.path.exists(media_file):
        print(f"❌ Media file not found: {media_file}")
        return
    
    # Kill any existing processes
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    subprocess.run(['pkill', '-f', 'mplayer'], capture_output=True)
    time.sleep(1)
    
    print("\n=== Testing basic VLC (no special options) ===")
    print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
    
    try:
        # Most basic VLC command
        cmd = ['vlc', '--play-and-exit', media_file]
        print(f"Running: {' '.join(cmd)}")
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait 10 seconds
        time.sleep(10)
        
        if process.poll() is None:
            print("✅ Basic VLC is running")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print("❌ Basic VLC exited")
            print(f"stderr: {stderr.decode()[:200]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Kill any remaining
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    time.sleep(1)
    
    print("\n=== Testing mplayer (if available) ===")
    print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
    
    try:
        # Try mplayer
        cmd = ['mplayer', '-fs', media_file]
        print(f"Running: {' '.join(cmd)}")
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait 10 seconds
        time.sleep(10)
        
        if process.poll() is None:
            print("✅ mplayer is running")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print("❌ mplayer exited")
            print(f"stderr: {stderr.decode()[:200]}")
            
    except FileNotFoundError:
        print("❌ mplayer not available")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_simple_display()