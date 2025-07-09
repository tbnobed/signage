#!/usr/bin/env python3

import subprocess
import time
import os

def test_mplayer():
    """Test mplayer with different output methods"""
    print("Testing mplayer video output...")
    
    media_file = "/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4"
    
    if not os.path.exists(media_file):
        print(f"❌ Media file not found: {media_file}")
        return
    
    # Kill any existing processes
    subprocess.run(['pkill', '-f', 'mplayer'], capture_output=True)
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    time.sleep(2)
    
    # Test different mplayer output methods
    test_methods = [
        ('fbdev', ['mplayer', '-vo', 'fbdev', '-fs', '-loop', '0', media_file]),
        ('fbdev2', ['mplayer', '-vo', 'fbdev2', '-fs', '-loop', '0', media_file]),
        ('directfb', ['mplayer', '-vo', 'directfb', '-fs', '-loop', '0', media_file]),
        ('caca', ['mplayer', '-vo', 'caca', '-fs', '-loop', '0', media_file]),
        ('default', ['mplayer', '-fs', '-loop', '0', media_file])
    ]
    
    for method, cmd in test_methods:
        print(f"\n=== Testing mplayer with {method} output ===")
        print(f"Command: {' '.join(cmd)}")
        print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
        
        try:
            # Set environment for console mode
            env = os.environ.copy()
            env.pop('DISPLAY', None)
            
            # Start mplayer
            process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait 10 seconds
            time.sleep(10)
            
            # Check if still running
            if process.poll() is None:
                print(f"✅ {method} - mplayer running")
                process.terminate()
                process.wait()
                
                # Ask user if they saw video
                response = input(f"Did you see video on your monitor with {method}? (y/n): ").lower()
                if response.startswith('y'):
                    print(f"🎉 SUCCESS! {method} method works!")
                    return method
                    
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {method} - mplayer exited")
                if stderr:
                    print(f"Error: {stderr.decode()[:100]}")
                    
        except Exception as e:
            print(f"❌ {method} - Exception: {e}")
            
        # Kill any remaining processes
        subprocess.run(['pkill', '-f', 'mplayer'], capture_output=True)
        time.sleep(2)
    
    print("\n❌ None of the mplayer methods worked")
    return None

if __name__ == "__main__":
    test_mplayer()