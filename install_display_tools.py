#!/usr/bin/env python3

import subprocess

def install_display_tools():
    """Install tools needed for proper display output"""
    print("Installing display tools...")
    
    # Install additional display tools
    packages = [
        'plymouth',           # Boot splash and console graphics
        'mesa-utils-extra',   # Additional Mesa utilities
        'libdrm-dev',        # DRM development headers
        'vainfo',            # Video acceleration info
        'intel-gpu-tools'    # Intel GPU utilities
    ]
    
    print(f"Installing: {' '.join(packages)}")
    
    try:
        subprocess.run(['apt', 'update'], check=True)
        subprocess.run(['apt', 'install', '-y'] + packages, check=True)
        print("✅ Display tools installed")
        
        # Check hardware acceleration
        print("\n=== Checking hardware acceleration ===")
        result = subprocess.run(['vainfo'], capture_output=True, text=True)
        print(result.stdout)
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")

if __name__ == "__main__":
    install_display_tools()