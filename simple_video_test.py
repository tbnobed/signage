#!/usr/bin/env python3

import subprocess
import time

def test_video_display():
    """Simple video display test"""
    print("Simple video display test")
    print("========================")
    
    media_file = "/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4"
    
    # Kill any existing processes
    subprocess.run(['pkill', '-f', 'mplayer'], capture_output=True)
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    time.sleep(1)
    
    # Test 1: Simple mplayer
    print("\nTest 1: Basic mplayer")
    print("Command: mplayer -fs /path/to/video.mp4")
    print("Starting in 3 seconds...")
    print("3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("STARTING NOW - Watch your monitor!")
    
    # Run mplayer for 15 seconds
    cmd = ['mplayer', '-fs', media_file]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait and show countdown
    for i in range(15, 0, -1):
        print(f"Running... {i} seconds left")
        time.sleep(1)
        if process.poll() is not None:
            print("Process ended early")
            break
    
    # Stop mplayer
    if process.poll() is None:
        process.terminate()
        process.wait()
    
    print("\nTest 1 complete")
    
    # Test 2: mplayer with framebuffer
    print("\nTest 2: mplayer with framebuffer")
    print("Command: mplayer -vo fbdev -fs /path/to/video.mp4")
    print("Starting in 3 seconds...")
    print("3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("STARTING NOW - Watch your monitor!")
    
    cmd = ['mplayer', '-vo', 'fbdev', '-fs', media_file]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait and show countdown
    for i in range(15, 0, -1):
        print(f"Running... {i} seconds left")
        time.sleep(1)
        if process.poll() is not None:
            print("Process ended early")
            break
    
    # Stop mplayer
    if process.poll() is None:
        process.terminate()
        process.wait()
    
    print("\nTest 2 complete")
    
    # Test 3: Simple VLC with framebuffer
    print("\nTest 3: VLC with framebuffer")
    print("Command: vlc --vout fb --intf dummy --fullscreen /path/to/video.mp4")
    print("Starting in 3 seconds...")
    print("3...")
    time.sleep(1)
    print("2...")
    time.sleep(1)
    print("1...")
    time.sleep(1)
    print("STARTING NOW - Watch your monitor!")
    
    cmd = ['vlc', '--vout', 'fb', '--intf', 'dummy', '--fullscreen', media_file]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait and show countdown
    for i in range(15, 0, -1):
        print(f"Running... {i} seconds left")
        time.sleep(1)
        if process.poll() is not None:
            print("Process ended early")
            break
    
    # Stop VLC
    if process.poll() is None:
        process.terminate()
        process.wait()
    
    print("\nTest 3 complete")
    print("\nAll tests finished.")
    print("Did you see video on your monitor during any of the tests?")

if __name__ == "__main__":
    test_video_display()