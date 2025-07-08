#!/usr/bin/env python3

import subprocess
import time
import os

def test_vlc_outputs():
    """Test different VLC output methods"""
    print("Testing VLC output methods...")
    
    media_file = "/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4"
    
    if not os.path.exists(media_file):
        print(f"❌ Media file not found: {media_file}")
        return
    
    # Kill any existing VLC processes
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    time.sleep(1)
    
    # Test different output methods
    test_methods = [
        ('directfb', ['vlc', '--vout', 'directfb', '--fullscreen', '--intf', 'dummy', media_file]),
        ('fb', ['vlc', '--vout', 'fb', '--fullscreen', '--intf', 'dummy', media_file]),
        ('kms', ['vlc', '--vout', 'kms', '--fullscreen', '--intf', 'dummy', media_file]),
        ('caca', ['vlc', '--vout', 'caca', '--fullscreen', '--intf', 'dummy', media_file]),
        ('aa', ['vlc', '--vout', 'aa', '--fullscreen', '--intf', 'dummy', media_file]),
        ('default', ['vlc', '--fullscreen', '--intf', 'dummy', media_file])
    ]
    
    for method, cmd in test_methods:
        print(f"\n=== Testing {method} output ===")
        print(f"Command: {' '.join(cmd)}")
        print("*** WATCH YOUR MONITOR FOR 5 SECONDS ***")
        
        try:
            # Start VLC
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait 5 seconds
            time.sleep(5)
            
            # Check if still running
            if process.poll() is None:
                print(f"✅ {method} - VLC running (check monitor)")
                process.terminate()
                process.wait()
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {method} - VLC exited")
                if stderr:
                    print(f"Error: {stderr.decode()[:100]}")
                    
        except Exception as e:
            print(f"❌ {method} - Exception: {e}")
            
        # Kill any remaining processes
        subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
        time.sleep(1)

if __name__ == "__main__":
    test_vlc_outputs()