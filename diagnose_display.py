#!/usr/bin/env python3

import subprocess
import os

def diagnose_display():
    """Diagnose display hardware and configuration"""
    print("Display Hardware Diagnosis")
    print("=========================")
    
    # Check connected displays
    print("\n1. Connected displays:")
    try:
        result = subprocess.run(['xrandr', '--listmonitors'], capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("xrandr not available or no X server running")
    except:
        print("xrandr not available")
    
    # Check DRM devices
    print("\n2. DRM devices:")
    try:
        result = subprocess.run(['ls', '-la', '/dev/dri/'], capture_output=True, text=True)
        print(result.stdout)
    except:
        print("No DRM devices found")
    
    # Check framebuffer
    print("\n3. Framebuffer devices:")
    try:
        result = subprocess.run(['ls', '-la', '/dev/fb*'], capture_output=True, text=True, shell=True)
        print(result.stdout)
    except:
        print("No framebuffer devices found")
    
    # Check kernel modules
    print("\n4. Graphics kernel modules:")
    try:
        result = subprocess.run(['lsmod'], capture_output=True, text=True)
        graphics_modules = [line for line in result.stdout.split('\n') if any(mod in line for mod in ['drm', 'i915', 'fb', 'video'])]
        for module in graphics_modules:
            print(module)
    except:
        print("Could not check kernel modules")
    
    # Check video devices
    print("\n5. Video devices:")
    try:
        result = subprocess.run(['ls', '-la', '/dev/video*'], capture_output=True, text=True, shell=True)
        print(result.stdout)
    except:
        print("No video devices found")
    
    # Check display resolution
    print("\n6. Display resolution:")
    try:
        result = subprocess.run(['fbset'], capture_output=True, text=True)
        print(result.stdout)
    except:
        print("fbset not available")
    
    # Check if console is on framebuffer
    print("\n7. Console configuration:")
    try:
        with open('/proc/cmdline', 'r') as f:
            cmdline = f.read().strip()
            print(f"Kernel command line: {cmdline}")
    except:
        print("Could not read kernel command line")
    
    # Check current TTY
    print("\n8. Current TTY:")
    try:
        result = subprocess.run(['tty'], capture_output=True, text=True)
        print(f"Current TTY: {result.stdout.strip()}")
    except:
        print("Could not determine current TTY")

def test_simple_framebuffer():
    """Test if framebuffer is actually working"""
    print("\n\nFramebuffer Test")
    print("================")
    
    # Try to write directly to framebuffer
    if os.path.exists('/dev/fb0'):
        print("Attempting to write to framebuffer...")
        try:
            # Fill framebuffer with pattern (this should show colored bars)
            cmd = ['dd', 'if=/dev/urandom', 'of=/dev/fb0', 'bs=1024', 'count=1000']
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Successfully wrote to framebuffer")
                print("*** CHECK YOUR MONITOR - You should see colored noise/bars ***")
                input("Press Enter when you've checked your monitor...")
                
                # Clear framebuffer
                cmd = ['dd', 'if=/dev/zero', 'of=/dev/fb0', 'bs=1024', 'count=1000']
                subprocess.run(cmd, capture_output=True)
                print("Framebuffer cleared")
            else:
                print(f"❌ Failed to write to framebuffer: {result.stderr}")
        except Exception as e:
            print(f"❌ Exception writing to framebuffer: {e}")
    else:
        print("❌ No framebuffer device found")

if __name__ == "__main__":
    diagnose_display()
    test_simple_framebuffer()