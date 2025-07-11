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
import time
from pathlib import Path

# Configuration
GITHUB_REPO = "https://raw.githubusercontent.com/tbnobed/signage/main"
CLIENT_SCRIPT_URL = f"{GITHUB_REPO}/client_agent.py"

class SignageSetup:
    def __init__(self):
        # Default configuration
        self.server_url = ""
        self.device_id = ""
        self.check_interval = 60
        
        # Always initialize with user home directory - will be updated if running as root
        current_user = os.getenv('USER', 'pi')
        self.target_user = current_user
        self.target_uid = None
        self.target_gid = None
        
        # Set default setup directory
        if os.geteuid() == 0:
            # Default to pi user when running as root
            self.setup_dir = Path("/home/pi/signage")
        else:
            self.setup_dir = Path.home() / "signage"
        
        # Initialize paths
        self.config_file = self.setup_dir / ".env"
        self.client_script = self.setup_dir / "client_agent.py"
        self.service_file = "/etc/systemd/system/signage-client.service"
        
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
        
    def install_dependencies(self):
        """Install required dependencies including media players"""
        print("📦 Installing dependencies...")
        
        # Check system type
        package_manager = self.detect_package_manager()
        if not package_manager:
            print("⚠️  Unsupported system. Please install dependencies manually:")
            print("   - Python 3 and pip")
            print("   - Media player (omxplayer, vlc, or ffmpeg)")
            print("   - requests module: pip3 install requests")
            if not self.ask_yes_no("Continue anyway?", default=True):
                sys.exit(1)
            return
        
        # Check if we have sudo access
        has_sudo = self.check_sudo_access()
        
        if package_manager == 'apt':
            self.install_with_apt(has_sudo)
        elif package_manager == 'yum':
            self.install_with_yum(has_sudo)
        elif package_manager == 'dnf':
            self.install_with_dnf(has_sudo)
        
        # Install Python requests module via pip
        self.install_python_requests()
        
        # Verify essential tools are available after installation
        print("\n🔍 Verifying installations...")
        
        # Check if pip is now available
        if shutil.which('pip3') or shutil.which('pip'):
            print("   ✅ pip/pip3 available")
        else:
            print("   ⚠️  pip/pip3 not found after installation")
        
        # Check if requests module is importable
        try:
            import requests
            print("   ✅ Python requests module available")
        except ImportError:
            print("   ❌ Python requests module not available")
            print("   This may cause connection issues")
        
        # Verify media players
        print("\n🎬 Verifying media players...")
        if not self.detect_media_players():
            print("❌ No media players were successfully installed!")
            if not self.ask_yes_no("Continue anyway?", default=False):
                print("Setup cancelled.")
                sys.exit(1)
        
        print()
    
    def detect_package_manager(self):
        """Detect available package manager"""
        managers = ['apt', 'yum', 'dnf', 'pacman']
        for manager in managers:
            if shutil.which(manager):
                return manager
        return None
    
    def check_sudo_access(self):
        """Check if we have sudo access"""
        try:
            subprocess.run(['sudo', '-n', 'true'], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  No sudo access detected. Some installations may fail.")
            print("   Re-run with sudo for automatic package installation.")
            print("   Continuing with limited functionality...")
            return False
    
    def install_with_apt(self, has_sudo):
        """Install dependencies using apt (Debian/Ubuntu)"""
        print("   Using apt package manager...")
        
        # Update package list with better error handling
        if has_sudo:
            print("   Updating package list...")
            try:
                result = subprocess.run(['sudo', 'apt', 'update'], 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    print("   ✅ Package list updated")
                else:
                    print(f"   ⚠️  Package list update had warnings: {result.stderr[:100]}")
            except subprocess.TimeoutExpired:
                print("   ⚠️  Package list update timed out")
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️  Failed to update package list: {e}")
        
        # Install essential Python packages with better error handling
        essential_packages = ['python3-pip', 'python3-requests', 'python3-setuptools', 'python3-dev']
        
        if has_sudo:
            for package in essential_packages:
                try:
                    result = subprocess.run(['sudo', 'apt', 'install', '-y', package], 
                                         capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        print(f"   ✅ {package} installed")
                    else:
                        print(f"   ⚠️  Failed to install {package}: {result.stderr[:100]}")
                except subprocess.TimeoutExpired:
                    print(f"   ⏰ {package} installation timed out")
                except subprocess.CalledProcessError as e:
                    print(f"   ⚠️  Failed to install {package}: {e}")
        else:
            print("   ❌ Cannot install Python packages without sudo")
        
        # Check if this is Ubuntu Server (no desktop environment)
        is_server = not os.path.exists('/usr/bin/gnome-session') and not os.path.exists('/usr/bin/startx')
        
        # Install display components for Ubuntu Server - focus on direct hardware output
        if is_server and has_sudo:
            print("   Detected Ubuntu Server - installing display components...")
            print("   ⚠️  Installing packages for direct display output...")
            
            # Set non-interactive mode to prevent prompts
            env = os.environ.copy()
            env['DEBIAN_FRONTEND'] = 'noninteractive'
            
            # Install packages for KMS (Kernel Mode Setting) direct hardware output
            essential_packages = [
                'libdrm2',       # Direct Rendering Manager
                'mesa-utils',    # OpenGL utilities
                'pulseaudio',    # Audio system
                'alsa-utils'     # Audio drivers
            ]
            
            for package in essential_packages:
                print(f"   Installing {package}...")
                try:
                    # Quick install with shorter timeout
                    result = subprocess.run(['sudo', 'apt', 'install', '-y', package], 
                                         env=env, timeout=120, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        print(f"   ✅ {package} installed")
                    else:
                        print(f"   ⚠️  Failed to install {package}")
                        
                except subprocess.TimeoutExpired:
                    print(f"   ⏰ {package} installation timed out (2 minutes)")
                except Exception as e:
                    print(f"   ⚠️  Error installing {package}: {e}")
            
            print("   Display components installed!")
        
        # Install media players based on platform
        is_raspberry_pi = self.detect_raspberry_pi()
        if is_raspberry_pi:
            print("   Detected Raspberry Pi - installing omxplayer...")
            media_packages = ['omxplayer', 'vlc']
        else:
            print("   Detected generic Linux - installing VLC and FFmpeg...")
            media_packages = ['vlc', 'ffmpeg']
        
        for package in media_packages:
            if has_sudo:
                try:
                    subprocess.run(['sudo', 'apt', 'install', '-y', package], 
                                 check=True, capture_output=True)
                    print(f"   ✅ {package} installed")
                except subprocess.CalledProcessError:
                    print(f"   ⚠️  Failed to install {package}")
            else:
                print(f"   ❌ Cannot install {package} without sudo")
    
    def install_with_yum(self, has_sudo):
        """Install dependencies using yum (CentOS/RHEL)"""
        print("   Using yum package manager...")
        
        media_packages = ['vlc', 'ffmpeg']
        
        for package in media_packages:
            if has_sudo:
                try:
                    subprocess.run(['sudo', 'yum', 'install', '-y', package], 
                                 check=True, capture_output=True)
                    print(f"   ✅ {package} installed")
                except subprocess.CalledProcessError:
                    print(f"   ⚠️  Failed to install {package}")
            else:
                print(f"   ❌ Cannot install {package} without sudo")
    
    def install_with_dnf(self, has_sudo):
        """Install dependencies using dnf (Fedora)"""
        print("   Using dnf package manager...")
        
        media_packages = ['vlc', 'ffmpeg']
        
        for package in media_packages:
            if has_sudo:
                try:
                    subprocess.run(['sudo', 'dnf', 'install', '-y', package], 
                                 check=True, capture_output=True)
                    print(f"   ✅ {package} installed")
                except subprocess.CalledProcessError:
                    print(f"   ⚠️  Failed to install {package}")
            else:
                print(f"   ❌ Cannot install {package} without sudo")
    
    def install_python_requests(self):
        """Install Python requests module"""
        # First check if requests is already available
        try:
            import requests
            print("   ✅ Python requests module already available")
            return
        except ImportError:
            pass
        
        # Try to install requests if not available
        try:
            # Try user install first
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', 'requests'], 
                         check=True, capture_output=True)
            print("   ✅ Python requests module installed (user)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            try:
                # Try system install with sudo
                subprocess.run(['sudo', sys.executable, '-m', 'pip', 'install', 'requests'], 
                             check=True, capture_output=True)
                print("   ✅ Python requests module installed (system)")
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    # Try pip3 as fallback if it exists
                    if shutil.which('pip3'):
                        subprocess.run(['pip3', 'install', '--user', 'requests'], 
                                     check=True, capture_output=True)
                        print("   ✅ Python requests module installed (pip3)")
                    else:
                        # pip not available, system package should work
                        print("   ⚠️  pip not available, using system python3-requests package")
                        print("   This should be sufficient for the client to work")
                except subprocess.CalledProcessError:
                    print("   ⚠️  Failed to install Python requests module")
                    print("   The system python3-requests package should work")
    
    def detect_raspberry_pi(self):
        """Detect if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpu_info = f.read()
            return 'BCM' in cpu_info or 'Raspberry Pi' in cpu_info
        except:
            return False
    
    def detect_media_players(self):
        """Detect available media players"""
        players = {
            'omxplayer': 'Hardware-accelerated (Raspberry Pi)',
            'vlc': 'Cross-platform media player',
            'ffplay': 'FFmpeg-based player (part of ffmpeg)',
            'mplayer': 'Classic media player'
        }
        
        available_players = []
        for player, description in players.items():
            if shutil.which(player):
                available_players.append(f"   ✅ {player} - {description}")
            else:
                available_players.append(f"   ❌ {player} - {description}")
        
        print("\n".join(available_players))
        
        if not any("✅" in player for player in available_players):
            print("   ⚠️  No media players detected!")
        
        return any("✅" in player for player in available_players)
    
    def get_user_input(self):
        """Get configuration from user"""
        print("⚙️  Configuration")
        print("-" * 20)
        
        # Check if we're in non-interactive mode (piped from curl)
        # Force interactive mode unless explicitly disabled
        is_interactive = sys.stdin.isatty() or os.environ.get('FORCE_INTERACTIVE', '1') == '1'
        
        # If running as root, ask for target user
        if os.geteuid() == 0:
            # Get target user
            if is_interactive:
                target_user = input("Username to run signage as (default: obtv1): ").strip() or "obtv1"
            else:
                target_user = "obtv1"
                print(f"Non-interactive mode: Using default user '{target_user}'")
            
            # For existing obtv1 user on this system, try to use it
            if target_user == "pi":
                try:
                    import pwd
                    pwd.getpwnam("obtv1")
                    target_user = "obtv1"
                    print("Found obtv1 user, using that instead of pi")
                except KeyError:
                    pass
            
            try:
                import pwd
                user_info = pwd.getpwnam(target_user)
                self.target_user = target_user
                self.target_uid = user_info.pw_uid
                self.target_gid = user_info.pw_gid
                self.setup_dir = Path(user_info.pw_dir) / "signage"
                
                # Update paths with correct setup directory
                self.config_file = self.setup_dir / ".env"
                self.client_script = self.setup_dir / "client_agent.py"
                
                print(f"Setting up for user: {self.target_user}")
                print(f"Home directory: {user_info.pw_dir}")
                print()
            except KeyError:
                print(f"❌ User '{target_user}' not found")
                print("Please create the user first or run as the target user")
                sys.exit(1)
        
        try:
            # Server URL
            if is_interactive:
                while True:
                    self.server_url = input("Server URL (default: https://display.obtv.io): ").strip()
                    if not self.server_url:
                        self.server_url = "https://display.obtv.io"
                    if self.server_url:
                        # Clean up URL
                        if not self.server_url.startswith(('http://', 'https://')):
                            self.server_url = 'https://' + self.server_url
                        if self.server_url.endswith('/'):
                            self.server_url = self.server_url[:-1]
                        break
                    else:
                        print("❌ Server URL is required!")
            else:
                # Non-interactive mode: use defaults
                self.server_url = "https://display.obtv.io"
                print(f"Non-interactive mode: Using default server URL '{self.server_url}'")
            
            # Device ID
            if is_interactive:
                while True:
                    self.device_id = input("Device ID (unique identifier): ").strip()
                    if self.device_id:
                        # Clean up device ID
                        self.device_id = self.device_id.lower().replace(' ', '-')
                        break
                    print("❌ Device ID is required!")
            else:
                # Non-interactive: check if device ID is provided as environment variable
                existing_device_id = os.environ.get('DEVICE_ID')
                if existing_device_id:
                    self.device_id = existing_device_id
                    print(f"Using device ID from environment: '{self.device_id}'")
                else:
                    # Check if there's an existing config file with device ID
                    if self.config_file.exists():
                        try:
                            with open(self.config_file, 'r') as f:
                                content = f.read()
                                for line in content.split('\n'):
                                    if line.startswith('DEVICE_ID='):
                                        self.device_id = line.split('=', 1)[1].strip()
                                        print(f"Found existing device ID: '{self.device_id}'")
                                        break
                        except Exception:
                            pass
                    
                    if not self.device_id:
                        print("❌ ERROR: Device ID not found!")
                        print("")
                        print("To set up this client, run:")
                        print("  DEVICE_ID=t-zyw3 python3 setup_client.py")
                        print("")
                        print("Or create a config file first:")
                        print("  echo 'DEVICE_ID=t-zyw3' > .env")
                        print("  python3 setup_client.py")
                        sys.exit(1)
            
            # Check interval
            if is_interactive:
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
            else:
                # Non-interactive: keep default
                print(f"Non-interactive mode: Using default check interval {self.check_interval} seconds")
            
        except (EOFError, KeyboardInterrupt):
            print("\n❌ Configuration cancelled by user or non-interactive session")
            print("   Device ID is required and must be registered in the dashboard first.")
            print("")
            print("📋 To complete setup:")
            print("   1. Register device in dashboard at: https://display.obtv.io")
            print("   2. Run setup interactively: python3 setup_client.py")
            print("   3. Or download and run manually:")
            print("      wget https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.py")
            print("      python3 setup_client.py")
            sys.exit(1)
        
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
        self.setup_dir.mkdir(parents=True, exist_ok=True)
        
        # Set ownership if running as root
        if os.geteuid() == 0 and self.target_uid is not None and self.target_gid is not None:
            os.chown(self.setup_dir, self.target_uid, self.target_gid)
            print(f"   Set ownership to: {self.target_user}")
        
        print(f"   Created: {self.setup_dir}")
        
        # Create media directory
        media_dir = self.setup_dir / "media"
        media_dir.mkdir(exist_ok=True)
        
        if os.geteuid() == 0 and self.target_uid is not None and self.target_gid is not None:
            os.chown(media_dir, self.target_uid, self.target_gid)
        
    def download_client(self):
        """Download client script from GitHub"""
        print("⬇️  Downloading client script...")
        
        try:
            urllib.request.urlretrieve(CLIENT_SCRIPT_URL, self.client_script)
            # Make executable
            os.chmod(self.client_script, 0o755)
            
            # Set ownership if running as root
            if os.geteuid() == 0 and self.target_uid is not None and self.target_gid is not None:
                os.chown(self.client_script, self.target_uid, self.target_gid)
            
            print(f"   Downloaded: {self.client_script}")
        except Exception as e:
            print(f"❌ Failed to download client script: {e}")
            print("   Please check your internet connection and try again.")
            sys.exit(1)
    
    def create_config(self):
        """Create environment configuration file"""
        print("📝 Creating configuration file...")
        
        # Remove existing config file to prevent duplicates
        if self.config_file.exists():
            self.config_file.unlink()
            print("   Removed existing configuration file")
        
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
        
        # Set ownership if running as root
        if os.geteuid() == 0 and self.target_uid is not None and self.target_gid is not None:
            os.chown(self.config_file, self.target_uid, self.target_gid)
        
        print(f"   Created: {self.config_file}")
        print(f"   Device ID: {self.device_id}")
        print(f"   Server URL: {self.server_url}")
    
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
    
    def setup_display_access(self, username):
        """Setup autologin and display access for digital signage"""
        print("   📺 Setting up display access...")
        
        try:
            # Setup autologin via LightDM (more reliable for headless systems)
            lightdm_config = f"""[Seat:*]
autologin-user={username}
autologin-user-timeout=0
user-session=openbox
"""
            
            # Ensure lightdm directory exists and write config
            subprocess.run(['sudo', 'mkdir', '-p', '/etc/lightdm'], check=False)
            
            process = subprocess.Popen(['sudo', 'tee', '/etc/lightdm/lightdm.conf'], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            stdout, stderr = process.communicate(input=lightdm_config)
            
            # For Ubuntu 24.04, also configure systemd auto-login
            systemd_override_dir = "/etc/systemd/system/getty@tty1.service.d"
            subprocess.run(['sudo', 'mkdir', '-p', systemd_override_dir], check=False)
            
            systemd_override = f"""[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin {username} --noclear %I $TERM
"""
            
            process3 = subprocess.Popen(['sudo', 'tee', f'{systemd_override_dir}/override.conf'], 
                                      stdin=subprocess.PIPE, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      text=True)
            stdout3, stderr3 = process3.communicate(input=systemd_override)
            
            # Also configure NodeDM/LightDM as fallback
            lightdm_config = f"""[Seat:*]
autologin-user={username}
autologin-user-timeout=0
autologin-session=ubuntu
"""
            subprocess.run(['sudo', 'mkdir', '-p', '/etc/lightdm'], check=False)
            
            process_lightdm = subprocess.Popen(['sudo', 'tee', '/etc/lightdm/lightdm.conf'], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            stdout_lightdm, stderr_lightdm = process_lightdm.communicate(input=lightdm_config)
            
            # Reload systemd to apply changes
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=False)
            subprocess.run(['sudo', 'systemctl', 'set-default', 'graphical.target'], check=False)
            
            # Disable screen locking and power management for the user
            user_home = f"/home/{username}"
            
            # Create script to disable screensaver and power management
            disable_script = f"""{user_home}/.disable-screensaver.sh"""
            script_content = f"""#!/bin/bash
# Disable screen lock and screensaver
export DISPLAY=:0
gsettings set org.gnome.desktop.session idle-delay 0
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.screensaver ubuntu-lock-on-suspend false
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'

# Disable DPMS (monitor power management)
xset -dpms
xset s off
xset s noblank
"""
            
            # Create the disable script
            process4 = subprocess.Popen(['sudo', '-u', username, 'tee', disable_script], 
                                      stdin=subprocess.PIPE, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      text=True)
            stdout4, stderr4 = process4.communicate(input=script_content)
            subprocess.run(['sudo', 'chmod', '+x', disable_script], check=False)
            
            # Add to user's .profile to run on login
            profile_addition = f"""
# Digital Signage - Disable screensaver and power management
if [ "$DISPLAY" != "" ]; then
    {disable_script} &
fi
"""
            
            process5 = subprocess.Popen(['sudo', '-u', username, 'tee', '-a', f'{user_home}/.profile'], 
                                      stdin=subprocess.PIPE, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE,
                                      text=True)
            stdout5, stderr5 = process5.communicate(input=profile_addition)
            
            if process.returncode == 0 or process3.returncode == 0:
                print("   ✅ Autologin configured (GDM3 + systemd)")
                print("   ✅ Screen lock and power management disabled")
                print("   ⚠️  Reboot required for autologin to take effect")
            else:
                print("   ⚠️  Could not configure autologin (may require manual setup)")
            
            # Add user to video group for hardware access
            subprocess.run(['sudo', 'usermod', '-a', '-G', 'video', username], 
                          check=False)
            
            # Setup screen blanking disable
            autostart_dir = f"/home/{username}/.config/autostart"
            subprocess.run(['sudo', '-u', username, 'mkdir', '-p', autostart_dir], 
                          check=False)
            
            disable_script = """[Desktop Entry]
Type=Application
Name=Disable Screen Blanking
Exec=bash -c "xset s off; xset -dpms; xset s noblank"
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
            
            disable_file = f"{autostart_dir}/disable-blanking.desktop"
            process = subprocess.Popen(['sudo', 'tee', disable_file], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            stdout, stderr = process.communicate(input=disable_script)
            
            # Fix ownership
            subprocess.run(['sudo', 'chown', '-R', f'{username}:{username}', 
                           f'/home/{username}/.config'], check=False)
            
            print("   ✅ Display access configured")
            
        except Exception as e:
            print(f"   ⚠️  Display setup warning: {e}")
    
    def create_systemd_service(self):
        """Create systemd service for auto-start with display access"""
        print("🚀 Setting up auto-start service...")
        
        # Use the target user we already determined
        username = self.target_user or getpass.getuser()
        
        # Setup autologin and display access first
        self.setup_display_access(username)
        
        # Create display setup script for direct hardware output
        display_script = f"""#!/bin/bash
# Setup direct display output for digital signage

# Add user to video and render groups for display access
usermod -a -G video,render {self.target_user or 'obtv1'}

# Check for display hardware and set up KMS access
if [ -d /dev/dri ]; then
    echo "DRM devices detected in /dev/dri"
    chmod 666 /dev/dri/card*
    chmod 666 /dev/dri/renderD*
    # Set up KMS for direct hardware output
    echo "Setting up KMS for direct display output"
elif [ -e /dev/fb0 ]; then
    echo "Framebuffer device detected: /dev/fb0"
    chmod 666 /dev/fb0
else
    echo "No display hardware detected"
fi

# Configure VLC for framebuffer output (confirmed working)
mkdir -p {self.setup_dir}/.config/vlc
cat > {self.setup_dir}/.config/vlc/vlcrc << 'EOF'
[dummy]
intf=dummy

[core]
vout=fb
aout=pulse
EOF

# Set permissions
chown -R {self.target_user or 'obtv1'}:{self.target_user or 'obtv1'} {self.setup_dir}/.config

echo "Display setup complete"
"""
        
        with open(f'{self.setup_dir}/setup_display.sh', 'w') as f:
            f.write(display_script)
        
        subprocess.run(['chmod', '+x', f'{self.setup_dir}/setup_display.sh'], check=True)
        
        service_content = f"""[Unit]
Description=Digital Signage Client
After=multi-user.target
Wants=multi-user.target

[Service]
Type=simple
User={username}
Group={username}
Environment=HOME=/home/{username}
Environment=USER={username}
Environment=PULSE_RUNTIME_PATH=/home/{username}/.pulse
WorkingDirectory={self.setup_dir}
EnvironmentFile={self.config_file}
ExecStartPre={self.setup_dir}/setup_display.sh
ExecStart=/usr/bin/python3 {self.client_script}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
        
        try:
            # Check if we have sudo privileges
            sudo_check = subprocess.run(['sudo', '-n', 'true'], 
                                      capture_output=True, check=False)
            
            if sudo_check.returncode != 0:
                print("   ⚠️  This script needs sudo privileges to create systemd service")
                print("   Please run the setup with sudo:")
                print("   sudo python3 setup_client.py")
                print("")
                print("   Or run these commands manually after setup:")
                print(f"   sudo tee /etc/systemd/system/signage-client.service > /dev/null << 'EOF'")
                print(service_content.strip())
                print("EOF")
                print("   sudo systemctl daemon-reload")
                print("   sudo systemctl enable signage-client.service")
                print("   sudo systemctl start signage-client.service")
                return False
            
            # Use sudo to create the service file
            process = subprocess.Popen(['sudo', 'tee', self.service_file], 
                                     stdin=subprocess.PIPE, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            stdout, stderr = process.communicate(input=service_content)
            
            if process.returncode != 0:
                print(f"   ❌ Failed to create service file: {stderr}")
                return False
            
            # Reload systemd and enable service with sudo
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            subprocess.run(['sudo', 'systemctl', 'enable', 'signage-client.service'], check=True)
            
            print(f"   ✅ Service created: {self.service_file}")
            print("   ✅ Service enabled for auto-start")
            
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to setup service: {e}")
            print("   Please run this script with sudo privileges")
            return False
        except Exception as e:
            print(f"   ❌ Service setup error: {e}")
            return False
            
        return True
    
    def start_service(self):
        """Start the signage service"""
        if self.ask_yes_no("Start the signage client now?", default=True):
            try:
                subprocess.run(['sudo', 'systemctl', 'start', 'signage-client.service'], check=True)
                print("   ✅ Service started")
                
                # Show service status
                print("\n📊 Service Status:")
                subprocess.run(['sudo', 'systemctl', 'status', 'signage-client.service', '--no-pager', '-l'])
                
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
        
        try:
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
        except (EOFError, KeyboardInterrupt):
            # Handle non-interactive execution
            print(f"\nUsing default: {'yes' if default else 'no'}")
            return default
    
    def run(self):
        """Run the complete setup process"""
        try:
            self.print_header()
            self.check_system()
            self.install_dependencies()
            self.get_user_input()
            self.create_directory()
            self.download_client()
            self.create_config()
            
            # Always try to create systemd service regardless of connection test
            connection_ok = self.test_connection()
            if self.create_systemd_service():
                if connection_ok:
                    self.start_service()
                else:
                    print("   ⚠️  Service created but not started due to connection issues")
            
            if not connection_ok:
                print("⚠️  Setup completed but connection test failed.")
                print("   Please verify your server URL and network settings.")
                print("   The service was created and can be started once connection is working.")
            
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