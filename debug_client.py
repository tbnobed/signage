#!/usr/bin/env python3

import subprocess
import os

def test_server_connection():
    """Test server connection and API responses"""
    print("=== Server Connection Test ===")
    
    try:
        # Test device checkin
        result = subprocess.run([
            'curl', '-s', 'https://display.obtv.io/api/devices/t-zyw3/checkin', '-X', 'POST'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Server checkin successful")
        else:
            print(f"❌ Server checkin failed: {result.stderr}")
            
        # Test playlist fetch
        result = subprocess.run([
            'curl', '-s', 'https://display.obtv.io/api/devices/t-zyw3/playlist'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Playlist fetch successful")
            print(f"Response: {result.stdout[:200]}...")
        else:
            print(f"❌ Playlist fetch failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

def test_vlc_outputs():
    """Test available VLC output modules"""
    print("\n=== VLC Output Modules ===")
    
    try:
        # List available video output modules
        result = subprocess.run([
            'vlc', '--list', '--intf', 'dummy'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            video_outputs = []
            capture = False
            
            for line in lines:
                if 'video output' in line.lower():
                    capture = True
                elif capture and line.strip():
                    if line.strip().startswith(' '):
                        video_outputs.append(line.strip())
                    elif not line.strip().startswith(' ') and video_outputs:
                        break
            
            print("Available video output modules:")
            for output in video_outputs[:10]:  # Show first 10
                print(f"  {output}")
                
        else:
            print(f"❌ Could not list VLC modules: {result.stderr}")
            
    except Exception as e:
        print(f"❌ VLC module test failed: {e}")

def test_vlc_playback():
    """Test VLC media playback with different outputs"""
    print("\n=== VLC Playback Test ===")
    
    media_dir = os.path.expanduser('~/signage_media')
    if not os.path.exists(media_dir):
        print("❌ No media directory found")
        return
        
    media_files = [f for f in os.listdir(media_dir) if f.endswith(('.mp4', '.avi', '.mkv'))]
    if not media_files:
        print("❌ No media files found")
        return
        
    test_file = os.path.join(media_dir, media_files[0])
    print(f"Testing with: {test_file}")
    
    # Test different output methods
    outputs_to_test = ['fb', 'drm', 'vdummy', 'vmem']
    
    for output in outputs_to_test:
        print(f"\nTesting --vout {output}:")
        try:
            # Run VLC for 3 seconds with each output
            process = subprocess.Popen([
                'vlc', '--vout', output, '--intf', 'dummy', '--play-and-exit', 
                '--run-time', '3', test_file
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            stdout, stderr = process.communicate(timeout=5)
            
            if process.returncode == 0:
                print(f"  ✅ {output} worked")
            else:
                print(f"  ❌ {output} failed: {stderr.decode()[:100]}...")
                
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"  ⏰ {output} timed out")
        except Exception as e:
            print(f"  ❌ {output} error: {e}")

def check_display_permissions():
    """Check display device permissions"""
    print("\n=== Display Permissions ===")
    
    # Check framebuffer permissions
    if os.path.exists('/dev/fb0'):
        stat = os.stat('/dev/fb0')
        print(f"fb0 permissions: {oct(stat.st_mode)[-3:]}")
        
        # Check if user can read/write
        try:
            with open('/dev/fb0', 'rb') as f:
                f.read(1)
            print("✅ Can read fb0")
        except:
            print("❌ Cannot read fb0")
    
    # Check DRM permissions
    if os.path.exists('/dev/dri'):
        for device in os.listdir('/dev/dri'):
            if device.startswith('card'):
                dev_path = f'/dev/dri/{device}'
                stat = os.stat(dev_path)
                print(f"{device} permissions: {oct(stat.st_mode)[-3:]}")
    
    # Check group membership
    result = subprocess.run(['groups'], capture_output=True, text=True)
    print(f"User groups: {result.stdout.strip()}")

def main():
    print("Digital Signage Client Debug Script")
    print("=" * 50)
    
    test_server_connection()
    check_display_permissions()
    test_vlc_outputs()
    test_vlc_playback()

if __name__ == "__main__":
    main()