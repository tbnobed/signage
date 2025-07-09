#!/usr/bin/env python3

import subprocess

def install_mplayer():
    """Install mplayer which often works better for console video"""
    print("Installing mplayer for console video playback...")
    
    try:
        subprocess.run(['apt', 'update'], check=True)
        subprocess.run(['apt', 'install', '-y', 'mplayer'], check=True)
        print("✅ mplayer installed successfully")
        
    except Exception as e:
        print(f"❌ Installation failed: {e}")

if __name__ == "__main__":
    install_mplayer()