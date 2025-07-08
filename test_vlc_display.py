#!/usr/bin/env python3

import subprocess
import time
import os

def test_vlc_display():
    """Test VLC display output directly"""
    print("Testing VLC display output...")
    
    media_file = "/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4"
    
    if not os.path.exists(media_file):
        print(f"❌ Media file not found: {media_file}")
        return
    
    # Test VLC with framebuffer output for 10 seconds
    print("Starting VLC with framebuffer output for 10 seconds...")
    print("Check your monitor now - video should be playing fullscreen")
    
    try:
        # Kill any existing VLC processes
        subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
        time.sleep(1)
        
        # Start VLC with framebuffer output
        vlc_cmd = [
            'vlc', '--fullscreen', '--no-osd', '--intf', 'dummy',
            '--no-video-title-show', '--vout', 'fb', '--play-and-exit',
            media_file
        ]
        
        print(f"Running: {' '.join(vlc_cmd)}")
        
        process = subprocess.Popen(vlc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Let it run for 10 seconds
        time.sleep(10)
        
        # Check if process is still running
        if process.poll() is None:
            print("✅ VLC is running")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print(f"❌ VLC exited early")
            print(f"stdout: {stdout.decode()[:200]}")
            print(f"stderr: {stderr.decode()[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_vlc_display()