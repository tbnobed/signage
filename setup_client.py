#!/usr/bin/env python3
"""
Digital Signage Client Setup Script
Interactive setup script for client devices

This script:
1. Downloads the latest client agent from GitHub
2. Asks user for configuration details
3. Sets up environment and systemd service
4. Tests the connection

Usage:
    curl -L https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.py | python3
    # OR
    wget https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.py && python3 setup_client.py
"""

import os
import sys
import subprocess
import urllib.request
import json
import getpass
import platform
import shutil
from pathlib import Path

# Configuration
GITHUB_REPO = "https://raw.githubusercontent.com/tbnobed/signage/main"
CLIENT_SCRIPT_URL = f"{GITHUB_REPO}/client_agent.py"

class SignageSetup:
    def __init__(self):
        self.setup_dir = Path.home() / "signage"
        self.config_file = self.setup_dir / ".env"
        self.client_script = self.setup_dir / "client_agent.py"
        self.service_file = "/etc/systemd/system/signage-client.service"
        
        self.server_url = ""
        self.device_id = ""
        self.check_interval = 60
        
    def print_header(self):
        print("=" * 60)
        print("     Digital Signage Client Setup")
        print("=" * 60)
        print()
        print("This script will help you set up a digital signage client device.")
        print("It will download the latest client software and configure your system.")
        print()
        
    def check_system(self):
        """Check system requirements"""
        print("🔍 Checking system requirements...")
        
        # Check if running as root for systemd setup
        if os.geteuid() == 0:
            print("⚠️  Warning: Running as root. This is okay for initial setup.")
            print("   The service will run as a regular user for security.")
            print()
        
        # Check Python version
        if sys.version_info < (3, 6):
            print("❌ Error: Python 3.6 or higher is required")
            print(f"   Current version: {sys.version}")
            sys.exit(1)
        
        print(f"✅ Python {sys.version.split()[0]} - OK")
        
        # Check for required commands
        required_commands = ['systemctl', 'wget', 'curl']
        missing_commands = []
        
        for cmd in required_commands:
            if not shutil.which(cmd):
                missing_commands.append(cmd)
        
        if missing_commands:
            print(f"⚠️  Missing commands: {', '.join(missing_commands)}")
            print("   You may need to install these manually.")
        
        print()
        
    def detect_media_players(self):
        """Detect available media players"""
        print("🎬 Detecting media players...")
        
        players = {
            'omxplayer': 'Hardware-accelerated (Raspberry Pi)',
            'vlc': 'Cross-platform media player',
            'ffplay': 'FFmpeg-based player',
            'mplayer': 'Classic media player'
        }
        
        available_players = []
        for player, description in players.items():
            if shutil.which(player):
                available_players.append(f"   ✅ {player} - {description}")
            else:
                available_players.append(f"   ❌ {player} - {description}")
        
        print("\n".join(available_players))
        print()
        
        if not any("✅" in player for player in available_players):
            print("⚠️  No media players detected!")
            print("   Install one of the following:")
            print("   - sudo apt install omxplayer     (Raspberry Pi)")
            print("   - sudo apt install vlc           (Most systems)")  
            print("   - sudo apt install ffmpeg        (Lightweight)")
            print()
            
            if self.ask_yes_no("Continue anyway?", default=False):
                return
            else:
                print("Setup cancelled.")
                sys.exit(1)
    
    def get_user_input(self):
        """Get configuration from user"""
        print("⚙️  Configuration")
        print("-" * 20)
        
        # Server URL
        while True:
            self.server_url = input("Server URL (e.g., http://192.168.1.100:5000): ").strip()
            if self.server_url:
                # Clean up URL
                if not self.server_url.startswith(('http://', 'https://')):
                    self.server_url = 'http://' + self.server_url
                if self.server_url.endswith('/'):
                    self.server_url = self.server_url[:-1]
                break
            print("❌ Server URL is required!")
        
        # Device ID
        while True:
            self.device_id = input("Device ID (unique identifier): ").strip()
            if self.device_id:
                # Clean up device ID
                self.device_id = self.device_id.lower().replace(' ', '-')
                break
            print("❌ Device ID is required!")
        
        # Check interval
        while True:
            interval_input = input(f"Check interval in seconds (default: {self.check_interval}): ").strip()
            if not interval_input:
                break
            try:
                self.check_interval = int(interval_input)
                if self.check_interval < 10:
                    print("⚠️  Warning: Very short intervals may cause server load")
                break
            except ValueError:
                print("❌ Please enter a valid number")
        
        print()
        print("Configuration Summary:")
        print(f"  Server URL: {self.server_url}")
        print(f"  Device ID: {self.device_id}")
        print(f"  Check Interval: {self.check_interval} seconds")
        print()
        
        if not self.ask_yes_no("Is this correct?", default=True):
            print("Restarting configuration...")
            return self.get_user_input()
    
    def create_directory(self):
        """Create signage directory"""
        print("📁 Creating signage directory...")
        self.setup_dir.mkdir(exist_ok=True)
        print(f"   Created: {self.setup_dir}")
        
    def download_client(self):
        """Download client script from GitHub"""
        print("⬇️  Downloading client script...")
        
        try:
            urllib.request.urlretrieve(CLIENT_SCRIPT_URL, self.client_script)
            # Make executable
            os.chmod(self.client_script, 0o755)
            print(f"   Downloaded: {self.client_script}")
        except Exception as e:
            print(f"❌ Failed to download client script: {e}")
            print("   Please check your internet connection and try again.")
            sys.exit(1)
    
    def create_config(self):
        """Create environment configuration file"""
        print("📝 Creating configuration file...")
        
        config_content = f"""# Digital Signage Client Configuration
SIGNAGE_SERVER_URL={self.server_url}
DEVICE_ID={self.device_id}
CHECK_INTERVAL={self.check_interval}

# Optional: Custom directories
# MEDIA_DIR={self.setup_dir}/media
# LOG_FILE={self.setup_dir}/client.log
"""
        
        with open(self.config_file, 'w') as f:
            f.write(config_content)
        
        print(f"   Created: {self.config_file}")
    
    def test_connection(self):
        """Test connection to server"""
        print("🔌 Testing server connection...")
        
        try:
            # Set environment variables for test
            env = os.environ.copy()
            env.update({
                'SIGNAGE_SERVER_URL': self.server_url,
                'DEVICE_ID': self.device_id,
                'CHECK_INTERVAL': str(self.check_interval)
            })
            
            # Try to ping the server
            import urllib.request
            import urllib.error
            
            test_url = f"{self.server_url}/api/devices/ping"
            try:
                urllib.request.urlopen(test_url, timeout=10)
                print("   ✅ Server is reachable")
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    print("   ✅ Server is reachable (404 is expected for ping)")
                else:
                    print(f"   ⚠️  Server responded with error: {e.code}")
            except Exception as e:
                print(f"   ❌ Cannot reach server: {e}")
                print("   Please check the server URL and network connection")
                return False
                
        except Exception as e:
            print(f"   ❌ Connection test failed: {e}")
            return False
        
        return True
    
    def create_systemd_service(self):
        """Create systemd service for auto-start"""
        print("🚀 Setting up auto-start service...")
        
        # Get current user for service
        username = getpass.getuser()
        if username == 'root':
            # If running as root, ask for the user to run as
            username = input("Username to run service as (default: pi): ").strip() or 'pi'
        
        service_content = f"""[Unit]
Description=Digital Signage Client
After=network.target

[Service]
Type=simple
User={username}
Group={username}
WorkingDirectory={self.setup_dir}
EnvironmentFile={self.config_file}
ExecStart=/usr/bin/python3 {self.client_script}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        try:
            with open(self.service_file, 'w') as f:
                f.write(service_content)
            
            # Reload systemd and enable service
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', 'signage-client.service'], check=True)
            
            print(f"   ✅ Service created: {self.service_file}")
            print("   ✅ Service enabled for auto-start")
            
        except PermissionError:
            print("   ⚠️  Cannot create systemd service (permission denied)")
            print("   Run with sudo to enable auto-start, or start manually:")
            print(f"   python3 {self.client_script}")
            return False
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to setup service: {e}")
            return False
        except Exception as e:
            print(f"   ❌ Service setup error: {e}")
            return False
            
        return True
    
    def start_service(self):
        """Start the signage service"""
        if self.ask_yes_no("Start the signage client now?", default=True):
            try:
                subprocess.run(['systemctl', 'start', 'signage-client.service'], check=True)
                print("   ✅ Service started")
                
                # Show service status
                print("\n📊 Service Status:")
                subprocess.run(['systemctl', 'status', 'signage-client.service', '--no-pager', '-l'])
                
            except subprocess.CalledProcessError:
                print("   ❌ Failed to start service")
                print("   Try manually: sudo systemctl start signage-client.service")
    
    def show_completion_info(self):
        """Show completion information"""
        print("\n" + "=" * 60)
        print("🎉 Setup Complete!")
        print("=" * 60)
        print()
        print("Your digital signage client is now configured!")
        print()
        print("📋 Next Steps:")
        print("1. Register this device in your web dashboard:")
        print(f"   - Server: {self.server_url}")  
        print(f"   - Device ID: {self.device_id}")
        print("2. Create playlists and assign them to this device")
        print("3. Media will automatically download and play")
        print()
        print("🔧 Useful Commands:")
        print("   sudo systemctl status signage-client    # Check status")
        print("   sudo systemctl restart signage-client   # Restart service")
        print("   sudo systemctl stop signage-client      # Stop service")
        print(f"   tail -f {self.setup_dir}/client.log      # View logs")
        print()
        print("📁 Files Created:")
        print(f"   {self.client_script}")
        print(f"   {self.config_file}")
        if os.path.exists(self.service_file):
            print(f"   {self.service_file}")
        print()
        
    def ask_yes_no(self, question, default=True):
        """Ask yes/no question"""
        if default:
            prompt = f"{question} [Y/n]: "
        else:
            prompt = f"{question} [y/N]: "
        
        while True:
            answer = input(prompt).strip().lower()
            if answer in ['y', 'yes']:
                return True
            elif answer in ['n', 'no']:
                return False
            elif answer == '':
                return default
            else:
                print("Please answer yes or no (y/n)")
    
    def run(self):
        """Run the complete setup process"""
        try:
            self.print_header()
            self.check_system()
            self.detect_media_players()
            self.get_user_input()
            self.create_directory()
            self.download_client()
            self.create_config()
            
            if self.test_connection():
                if self.create_systemd_service():
                    self.start_service()
                self.show_completion_info()
            else:
                print("⚠️  Setup completed but connection test failed.")
                print("   Please verify your server URL and network settings.")
                self.show_completion_info()
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Setup cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    setup = SignageSetup()
    setup.run()

if __name__ == '__main__':
    main()