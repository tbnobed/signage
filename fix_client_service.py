#!/usr/bin/env python3

import subprocess
import os
import time

def check_service_status():
    """Check current service status and logs"""
    print("=== Checking service status ===")
    
    # Check service status
    result = subprocess.run(['systemctl', 'status', 'signage-client'], 
                          capture_output=True, text=True)
    print("Service Status:")
    print(result.stdout)
    
    print("\n=== Recent service logs ===")
    result = subprocess.run(['journalctl', '-u', 'signage-client', '-n', '20'], 
                          capture_output=True, text=True)
    print(result.stdout)
    
    print("\n=== Check if VLC is running ===")
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    vlc_processes = [line for line in result.stdout.split('\n') if 'vlc' in line]
    if vlc_processes:
        for proc in vlc_processes:
            print(f"VLC process: {proc}")
    else:
        print("No VLC processes found")

def restart_service():
    """Restart the service with proper configuration"""
    print("\n=== Restarting service ===")
    
    # Stop service
    subprocess.run(['systemctl', 'stop', 'signage-client'])
    
    # Kill any remaining VLC processes
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    time.sleep(2)
    
    # Start service
    subprocess.run(['systemctl', 'start', 'signage-client'])
    time.sleep(3)
    
    # Check status
    result = subprocess.run(['systemctl', 'status', 'signage-client'], 
                          capture_output=True, text=True)
    print("Service Status after restart:")
    print(result.stdout)

def test_manual_vlc():
    """Test VLC manually with exact service parameters"""
    print("\n=== Testing VLC manually ===")
    
    media_file = "/home/obtv1/signage_media/452bf30e25f440098021a2286724b298.mp4"
    
    if not os.path.exists(media_file):
        print(f"❌ Media file not found: {media_file}")
        return
    
    # Kill any existing VLC
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)
    time.sleep(1)
    
    # Test exact VLC command that service uses
    cmd = ['vlc', '--fullscreen', '--no-osd', '--loop', '--intf', 'dummy', 
           '--no-video-title-show', '--vout', 'fb', media_file]
    
    print(f"Testing command: {' '.join(cmd)}")
    print("*** WATCH YOUR MONITOR FOR 10 SECONDS ***")
    
    # Set environment like the service does
    env = os.environ.copy()
    env.pop('DISPLAY', None)  # Remove DISPLAY for console mode
    
    try:
        process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(10)
        
        if process.poll() is None:
            print("✅ Manual VLC test - process running")
            process.terminate()
            process.wait()
        else:
            stdout, stderr = process.communicate()
            print("❌ Manual VLC test - process exited")
            print(f"stderr: {stderr.decode()[:300]}")
            
    except Exception as e:
        print(f"❌ Manual VLC test - exception: {e}")
    
    # Cleanup
    subprocess.run(['pkill', '-f', 'vlc'], capture_output=True)

if __name__ == "__main__":
    check_service_status()
    test_manual_vlc()
    restart_service()