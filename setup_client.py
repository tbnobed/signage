#!/usr/bin/env python3
"""
Digital Signage Client Setup Script
Setup script for desktop Ubuntu client devices

This script:
1. Downloads the latest client agent from GitHub
2. Installs VLC media player if needed
3. Asks user for configuration details
4. Sets up environment and systemd service
5. Tests the connection

Usage:
    curl -L https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.py | python3
    # OR
    wget https://raw.githubusercontent.com/tbnobed/signage/main/setup_client.py && python3 setup_client.py
"""

import os
import sys
import subprocess
import urllib.request
import urllib.error
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
        self.screen_index = 0
        
        # Always initialize with user home directory - will be updated if running as root
        current_user = os.getenv('USER', 'user')
        self.target_user = current_user
        self.target_uid = None
        self.target_gid = None
        
        # Set default setup directory
        if os.geteuid() == 0:
            # Use SUDO_USER when running as root
            sudo_user = os.getenv('SUDO_USER', 'user')
            self.setup_dir = Path(f"/home/{sudo_user}/signage")
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
        """Install required dependencies for desktop Ubuntu"""
        print("📦 Installing dependencies for desktop Ubuntu...")
        
        # Check if we have sudo access
        has_sudo = self.check_sudo_access()
        if not has_sudo:
            print("❌ This setup requires sudo access to install VLC and other packages.")
            print("   Please run: sudo python3 setup_client.py")
            sys.exit(1)
        
        # Install VLC and Python requirements
        self.install_desktop_packages()
        
        # Install Python requests module 
        self.install_python_requests()
        
        # Verify VLC installation
        print("\n🎬 Verifying VLC installation...")
        if shutil.which('vlc'):
            print("   ✅ VLC media player installed")
        else:
            print("   ❌ VLC not found after installation!")
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
    
    def install_desktop_packages(self):
        """Install packages for desktop Ubuntu"""
        print("   Installing packages for desktop Ubuntu...")
        
        # Update package list
        print("   Updating package list...")
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=True, capture_output=True, timeout=60)
            print("   ✅ Package list updated")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"   ⚠️  Package update had issues: {e}")
        
        # Essential packages for desktop Ubuntu
        packages = [
            'vlc',               # VLC media player
            'python3-pip',       # Python package manager
            'python3-requests',  # Python HTTP library
        ]
        
        for package in packages:
            print(f"   Installing {package}...")
            try:
                subprocess.run(['sudo', 'apt', 'install', '-y', package], 
                             check=True, capture_output=True, timeout=120)
                print(f"   ✅ {package} installed")
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️  Failed to install {package}")
            except subprocess.TimeoutExpired:
                print(f"   ⏰ {package} installation timed out")
    
    
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
    
    
    def get_user_input(self):
        """Get configuration from user"""
        print("⚙️  Configuration")
        print("-" * 20)
        
        # Default to interactive mode unless explicitly running non-interactive
        is_interactive = os.environ.get('FORCE_NON_INTERACTIVE', '0') != '1'
        
        # If running as root, ask for target user
        if os.geteuid() == 0:
            # Get target user
            if is_interactive:
                current_user = os.getenv('SUDO_USER', 'user')
                target_user = input(f"Username to run signage as (default: {current_user}): ").strip() or current_user
            else:
                target_user = os.getenv('SUDO_USER', 'user')
                print(f"Non-interactive mode: Using user '{target_user}'")
            
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
            
            # Screen index for multi-monitor HDMI targeting
            if is_interactive:
                print()
                print("🖥️  Multi-monitor setup:")
                print("   Screen 0: Primary display (usually laptop/main monitor)")
                print("   Screen 1: Secondary display (usually HDMI/external monitor)")
                print("   Screen 2+: Additional monitors if connected")
                
                while True:
                    screen_input = input(f"Which screen for fullscreen display? (default: {self.screen_index}): ").strip()
                    if not screen_input:
                        break
                    try:
                        self.screen_index = int(screen_input)
                        if self.screen_index < 0:
                            print("❌ Screen index must be 0 or higher")
                            continue
                        if self.screen_index > 0:
                            print(f"   Will target screen {self.screen_index} (external monitor)")
                        break
                    except ValueError:
                        print("❌ Please enter a valid number")
            else:
                # Non-interactive: keep default (primary screen)
                print(f"Non-interactive mode: Using default screen {self.screen_index} (primary)")
            
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
        print(f"  Target Screen: {self.screen_index} {'(external/HDMI)' if self.screen_index > 0 else '(primary)'}")
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
RAPID_CHECK_INTERVAL=2
SCREEN_INDEX={self.screen_index}
MEDIA_DIR={self.setup_dir}/media
LOG_FILE={self.setup_dir}/client.log
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
    
    def configure_kiosk_mode(self):
        """Configure kiosk mode for Ubuntu 22.04: disable notifications, power management, set background"""
        print("🖥️  Configuring kiosk mode for Ubuntu 22.04...")
        
        username = self.target_user or getpass.getuser()
        user_home = f"/home/{username}"
        
        # Download TBN logo background
        print("   📄 Downloading TBN logo background...")
        background_url = "http://msm.livestudios.tv/wp-content/uploads/2024/05/TBNLogo.png"
        background_path = Path(user_home) / "Pictures" / "TBNLogo.png"
        
        try:
            # Create Pictures directory if it doesn't exist
            background_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download background image
            urllib.request.urlretrieve(background_url, background_path)
            
            # Set ownership if running as root
            if os.geteuid() == 0 and self.target_uid is not None and self.target_gid is not None:
                os.chown(background_path, self.target_uid, self.target_gid)
                os.chown(background_path.parent, self.target_uid, self.target_gid)
            
            print(f"   ✅ Background downloaded: {background_path}")
        except Exception as e:
            print(f"   ⚠️  Failed to download background: {e}")
            print("   Using default background")
            background_path = None
        
        # Configure GNOME settings for kiosk mode
        gsettings_commands = [
            # Disable all notifications
            "gsettings set org.gnome.desktop.notifications show-banners false",
            "gsettings set org.gnome.desktop.notifications show-in-lock-screen false",
            
            # Power settings - never suspend, never turn off screen
            "gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'",
            "gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'",
            "gsettings set org.gnome.desktop.session idle-delay 0",
            
            # Screen saver settings
            "gsettings set org.gnome.desktop.screensaver lock-enabled false",
            "gsettings set org.gnome.desktop.screensaver idle-activation-enabled false",
            
            # Disable automatic updates notifications
            "gsettings set org.gnome.software download-updates false",
            "gsettings set org.gnome.software download-updates-notify false",
            
            # Hide desktop icons and taskbar auto-hide for cleaner kiosk look
            "gsettings set org.gnome.desktop.background show-desktop-icons false",
            "gsettings set org.gnome.shell.extensions.dash-to-dock autohide true",
            "gsettings set org.gnome.shell.extensions.dash-to-dock dock-fixed false",
            
            # Disable screen lock
            "gsettings set org.gnome.desktop.lockdown disable-lock-screen true",
        ]
        
        # Set background if download was successful
        if background_path and background_path.exists():
            gsettings_commands.extend([
                f"gsettings set org.gnome.desktop.background picture-uri 'file://{background_path}'",
                f"gsettings set org.gnome.desktop.background picture-uri-dark 'file://{background_path}'",
                "gsettings set org.gnome.desktop.background picture-options 'centered'",
                "gsettings set org.gnome.desktop.background primary-color '#000000'",
            ])
        
        # Execute gsettings commands
        print("   ⚙️  Configuring GNOME settings...")
        for cmd in gsettings_commands:
            try:
                if os.geteuid() == 0:  # Running as root, execute as target user
                    import pwd
                    user_uid = pwd.getpwnam(username).pw_uid
                    user_env = {
                        'XDG_RUNTIME_DIR': f'/run/user/{user_uid}',
                        'HOME': user_home,
                        'USER': username,
                        'DISPLAY': ':0',  # Ensure we can access the display
                        'DBUS_SESSION_BUS_ADDRESS': f'unix:path=/run/user/{user_uid}/bus'
                    }
                    
                    subprocess.run(['sudo', '-u', username] + 
                                 [f'{k}={v}' for k, v in user_env.items()] +
                                 cmd.split(), 
                                 check=True, capture_output=True, 
                                 env={**os.environ, **user_env}, timeout=10)
                else:
                    # Running as regular user
                    subprocess.run(cmd.split(), check=True, capture_output=True, timeout=10)
                    
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️  Warning: Failed to execute: {cmd}")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Warning: Timeout executing: {cmd}")
            except Exception as e:
                print(f"   ⚠️  Warning: Error with {cmd}: {e}")
        
        # Configure additional power management settings via systemd
        print("   🔋 Configuring power management...")
        power_commands = [
            # Prevent system suspend
            "sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target",
            
            # Configure logind to not suspend on lid close (for laptops)
            "sudo bash -c \"echo 'HandleLidSwitch=ignore' >> /etc/systemd/logind.conf\"",
            "sudo bash -c \"echo 'HandleLidSwitchExternalPower=ignore' >> /etc/systemd/logind.conf\"",
            "sudo bash -c \"echo 'IdleAction=ignore' >> /etc/systemd/logind.conf\"",
        ]
        
        for cmd in power_commands:
            try:
                subprocess.run(cmd, shell=True, check=True, capture_output=True, timeout=15)
            except subprocess.CalledProcessError as e:
                print(f"   ⚠️  Warning: Power command failed: {cmd}")
            except subprocess.TimeoutExpired:
                print(f"   ⚠️  Warning: Power command timeout: {cmd}")
        
        # Disable Ubuntu's unattended upgrades to prevent reboot prompts
        print("   📦 Disabling automatic updates...")
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', 'unattended-upgrades'], 
                         check=True, capture_output=True, timeout=10)
            subprocess.run(['sudo', 'systemctl', 'disable', 'unattended-upgrades'], 
                         check=True, capture_output=True, timeout=10)
            print("   ✅ Automatic updates disabled")
        except subprocess.CalledProcessError:
            print("   ⚠️  Could not disable automatic updates")
        except subprocess.TimeoutExpired:
            print("   ⚠️  Timeout disabling automatic updates")
        
        # Create a script to re-apply kiosk settings on login (in case they get reset)
        kiosk_script_path = Path(user_home) / ".local" / "bin" / "kiosk-setup.sh"
        kiosk_script_path.parent.mkdir(parents=True, exist_ok=True)
        
        kiosk_script_content = f"""#!/bin/bash
# Kiosk mode settings - run on login
# Generated by signage setup

# Wait for desktop to load
sleep 5

# Re-apply critical kiosk settings
gsettings set org.gnome.desktop.notifications show-banners false
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
gsettings set org.gnome.desktop.session idle-delay 0

# Set background if exists
if [ -f "{background_path}" ]; then
    gsettings set org.gnome.desktop.background picture-uri 'file://{background_path}'
    gsettings set org.gnome.desktop.background picture-uri-dark 'file://{background_path}'
fi

# Hide cursor after 3 seconds of inactivity (optional)
# unclutter -idle 3 &
"""
        
        try:
            with open(kiosk_script_path, 'w') as f:
                f.write(kiosk_script_content)
            os.chmod(kiosk_script_path, 0o755)
            
            # Set ownership if running as root
            if os.geteuid() == 0 and self.target_uid is not None and self.target_gid is not None:
                os.chown(kiosk_script_path, self.target_uid, self.target_gid)
            
            print(f"   ✅ Kiosk settings script created: {kiosk_script_path}")
        except Exception as e:
            print(f"   ⚠️  Failed to create kiosk script: {e}")
        
        # Add the kiosk script to autostart
        autostart_dir = Path(user_home) / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        
        autostart_file = autostart_dir / "kiosk-setup.desktop"
        autostart_content = f"""[Desktop Entry]
Type=Application
Name=Kiosk Setup
Exec={kiosk_script_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=Apply kiosk mode settings on login
"""
        
        try:
            with open(autostart_file, 'w') as f:
                f.write(autostart_content)
            
            # Set ownership if running as root
            if os.geteuid() == 0 and self.target_uid is not None and self.target_gid is not None:
                os.chown(autostart_file, self.target_uid, self.target_gid)
                os.chown(autostart_dir, self.target_uid, self.target_gid)
            
            print("   ✅ Kiosk setup added to autostart")
        except Exception as e:
            print(f"   ⚠️  Failed to create autostart entry: {e}")
        
        print("   ✅ Kiosk mode configuration completed!")
        print("   📋 Kiosk features applied:")
        print("      • All notifications disabled")
        print("      • Power management disabled (never sleep/suspend)")
        print("      • Screen saver and lock disabled") 
        print("      • TBN logo set as background")
        print("      • Automatic updates disabled")
        print("      • Settings will re-apply on each login")
        print()
    
    def install_teamviewer(self):
        """Download and install TeamViewer for remote management"""
        print("📱 Installing TeamViewer for remote management...")
        
        # TeamViewer download URL
        teamviewer_url = "https://download.teamviewer.com/download/linux/teamviewer_amd64.deb?utm_source=google&utm_medium=cpc&utm_campaign=us%7Cb%7Cpr%7C22%7Caug%7Ctv-core-download-sn%7Cnew%7Ct0%7C0&utm_content=Download&utm_term=teamviewer+download"
        
        # Download path
        download_dir = Path("/tmp")
        teamviewer_deb = download_dir / "teamviewer_amd64.deb"
        
        try:
            print("   ⬇️  Downloading TeamViewer package...")
            urllib.request.urlretrieve(teamviewer_url, teamviewer_deb)
            print(f"   ✅ Downloaded: {teamviewer_deb}")
            
            # Verify file was downloaded and has reasonable size
            if teamviewer_deb.exists() and teamviewer_deb.stat().st_size > 1024:  # At least 1KB
                file_size_mb = teamviewer_deb.stat().st_size / (1024 * 1024)
                print(f"   📦 Package size: {file_size_mb:.1f} MB")
            else:
                print("   ❌ Downloaded file appears invalid")
                return False
            
            # Install TeamViewer using dpkg
            print("   📦 Installing TeamViewer package...")
            try:
                # First try to install the package
                subprocess.run(['sudo', 'dpkg', '-i', str(teamviewer_deb)], 
                             check=True, capture_output=True, timeout=60)
                print("   ✅ TeamViewer package installed")
            except subprocess.CalledProcessError as e:
                print("   ⚠️  Package installation had dependency issues, fixing...")
                # Try to fix dependency issues
                try:
                    subprocess.run(['sudo', 'apt', 'install', '-f', '-y'], 
                                 check=True, capture_output=True, timeout=120)
                    print("   ✅ Dependencies resolved")
                except subprocess.CalledProcessError:
                    print("   ❌ Could not resolve dependencies automatically")
                    return False
            
            # Verify TeamViewer was installed
            if shutil.which('teamviewer'):
                print("   ✅ TeamViewer installed successfully")
                
                # Enable TeamViewer daemon to start on boot
                try:
                    subprocess.run(['sudo', 'systemctl', 'enable', 'teamviewerd'], 
                                 check=True, capture_output=True, timeout=10)
                    print("   ✅ TeamViewer daemon enabled for auto-start")
                except subprocess.CalledProcessError:
                    print("   ⚠️  Could not enable TeamViewer daemon (this is usually ok)")
                
                # Start TeamViewer daemon
                try:
                    subprocess.run(['sudo', 'systemctl', 'start', 'teamviewerd'], 
                                 check=True, capture_output=True, timeout=15)
                    print("   ✅ TeamViewer daemon started")
                except subprocess.CalledProcessError:
                    print("   ⚠️  Could not start TeamViewer daemon (will start on reboot)")
                
                # Show TeamViewer ID information
                try:
                    result = subprocess.run(['teamviewer', '--info'], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0 and "TeamViewer ID:" in result.stdout:
                        for line in result.stdout.split('\n'):
                            if 'TeamViewer ID:' in line:
                                print(f"   🆔 {line.strip()}")
                    else:
                        print("   ⚠️  TeamViewer ID not available yet (will show after reboot)")
                except Exception:
                    print("   ⚠️  TeamViewer ID not available yet (will show after reboot)")
                
            else:
                print("   ❌ TeamViewer installation failed")
                return False
            
            # Clean up downloaded package
            try:
                teamviewer_deb.unlink()
                print("   🧹 Cleaned up installation package")
            except Exception:
                pass
                
            return True
            
        except urllib.error.URLError as e:
            print(f"   ❌ Failed to download TeamViewer: {e}")
            print("   Check your internet connection and try again")
            return False
        except subprocess.TimeoutExpired:
            print("   ❌ TeamViewer installation timed out")
            return False
        except Exception as e:
            print(f"   ❌ TeamViewer installation error: {e}")
            return False
    
    def configure_sudo_permissions(self):
        """Configure passwordless sudo for reboot commands"""
        print("🔒 Configuring sudo permissions for reboot functionality...")
        
        # Get the target username
        username = self.target_user or getpass.getuser()
        
        # Define sudoers file and content
        sudoers_file = f"/etc/sudoers.d/signage-reboot-{username}"
        sudoers_content = f"""# Allow {username} to reboot without password for digital signage
{username} ALL=(ALL) NOPASSWD: /sbin/reboot, /usr/sbin/reboot, /bin/systemctl reboot, /usr/bin/systemctl reboot
"""
        
        # Create temporary file for validation
        import tempfile
        try:
            # Create temporary file with sudoers content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tmp', delete=False) as temp_file:
                temp_file.write(sudoers_content)
                temp_file_path = temp_file.name
            
            # Validate the sudoers content using visudo
            print("   Validating sudoers configuration...")
            try:
                subprocess.run(['sudo', 'visudo', '-cf', temp_file_path], 
                             check=True, capture_output=True, timeout=10)
                print("   ✅ Sudoers configuration is valid")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Invalid sudoers configuration: {e}")
                os.unlink(temp_file_path)  # Clean up temp file
                return False
            
            # Install the validated file with proper ownership and permissions
            try:
                subprocess.run(['sudo', 'install', '-m', '440', '-o', 'root', '-g', 'root', 
                               temp_file_path, sudoers_file], 
                             check=True, capture_output=True, timeout=10)
                print(f"   ✅ Sudo permissions installed: {sudoers_file}")
                print(f"   User '{username}' can now reboot without password")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to install sudoers file: {e}")
                os.unlink(temp_file_path)  # Clean up temp file
                return False
            
            # Clean up temporary file
            os.unlink(temp_file_path)
            
            # Verify the configuration works
            try:
                result = subprocess.run(['sudo', '-l', '-U', username], 
                                      capture_output=True, text=True, timeout=5)
                # Check if any of the required commands are listed
                required_commands = ['/sbin/reboot', '/usr/sbin/reboot', '/bin/systemctl reboot', '/usr/bin/systemctl reboot']
                found_commands = [cmd for cmd in required_commands if cmd in result.stdout]
                
                if found_commands:
                    print(f"   ✅ Sudo configuration verified: {', '.join(found_commands)}")
                else:
                    print("   ⚠️  Sudo configuration created but verification unclear")
            except Exception:
                print("   ⚠️  Could not verify sudo configuration, but file was installed")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to configure sudo permissions: {e}")
            print("   Manual configuration required. Add this line to /etc/sudoers:")
            print(f"   {username} ALL=(ALL) NOPASSWD: /sbin/reboot, /usr/sbin/reboot, /bin/systemctl reboot, /usr/bin/systemctl reboot")
            return False
    
    def create_systemd_service(self):
        """Create systemd user service for desktop Ubuntu with Wayland support"""
        print("🚀 Setting up auto-start user service...")
        
        # Use the target user we already determined
        username = self.target_user or getpass.getuser()
        
        # Create user systemd directory
        user_systemd_dir = Path(f"/home/{username}/.config/systemd/user")
        user_systemd_dir.mkdir(parents=True, exist_ok=True)
        
        # Update service file path to user directory
        self.service_file = user_systemd_dir / "signage-client.service"
        
        # Service configuration for desktop Ubuntu user service
        service_content = f"""[Unit]
Description=Digital Signage Client
After=graphical-session.target network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={self.setup_dir}
EnvironmentFile={self.config_file}
ExecStart=/usr/bin/python3 {self.client_script}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=graphical-session.target
"""
        
        try:
            # Write service file directly to user directory (no sudo needed)
            with open(self.service_file, 'w') as f:
                f.write(service_content)
            
            print(f"   ✅ Service created: {self.service_file}")
            
            # Set ownership and permissions if running as root
            if os.geteuid() == 0:  # If running as root, change ownership to user
                import pwd
                user_uid = pwd.getpwnam(username).pw_uid
                user_gid = pwd.getpwnam(username).pw_gid
                os.chown(self.service_file, user_uid, user_gid)
                # Also ensure the .config/systemd/user directory is owned by user
                os.chown(user_systemd_dir, user_uid, user_gid)
                os.chown(user_systemd_dir.parent, user_uid, user_gid)  # .config/systemd
                os.chown(user_systemd_dir.parent.parent, user_uid, user_gid)  # .config
            
            # Reload user systemd and enable service in proper user context
            if os.geteuid() == 0:  # If running as root, run as target user
                import pwd
                user_uid = pwd.getpwnam(username).pw_uid
                user_env = {
                    'XDG_RUNTIME_DIR': f'/run/user/{user_uid}',
                    'HOME': f'/home/{username}',
                    'USER': username
                }
                
                subprocess.run(['sudo', '-u', username] + 
                             [f'{k}={v}' for k, v in user_env.items()] +
                             ['systemctl', '--user', 'daemon-reload'], 
                             check=True, env={**os.environ, **user_env})
                
                subprocess.run(['sudo', '-u', username] + 
                             [f'{k}={v}' for k, v in user_env.items()] +
                             ['systemctl', '--user', 'enable', 'signage-client.service'], 
                             check=True, env={**os.environ, **user_env})
            else:
                # Running as regular user
                subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
                subprocess.run(['systemctl', '--user', 'enable', 'signage-client.service'], check=True)
            
            print("   ✅ User service enabled for auto-start")
            
            # Enable lingering so service starts on boot even without login
            try:
                subprocess.run(['sudo', 'loginctl', 'enable-linger', username], 
                             check=True, capture_output=True)
                print("   ✅ User lingering enabled (starts on boot)")
            except subprocess.CalledProcessError:
                print("   ⚠️  Could not enable user lingering")
                print("       Service will start when user logs in")
            
        except Exception as e:
            print(f"   ❌ Service setup error: {e}")
            return False
            
        return True
    
    def start_service(self):
        """Start the user signage service"""
        username = self.target_user or getpass.getuser()
        
        if self.ask_yes_no("Start the signage client now?", default=True):
            try:
                # Start user service in proper user context
                if os.geteuid() == 0:  # If running as root, run as target user
                    import pwd
                    user_uid = pwd.getpwnam(username).pw_uid
                    user_env = {
                        'XDG_RUNTIME_DIR': f'/run/user/{user_uid}',
                        'HOME': f'/home/{username}',
                        'USER': username
                    }
                    
                    subprocess.run(['sudo', '-u', username] + 
                                 [f'{k}={v}' for k, v in user_env.items()] +
                                 ['systemctl', '--user', 'start', 'signage-client.service'], 
                                 check=True, env={**os.environ, **user_env})
                    
                    print("   ✅ User service started")
                    
                    # Show service status
                    print("\n📊 Service Status:")
                    subprocess.run(['sudo', '-u', username] + 
                                 [f'{k}={v}' for k, v in user_env.items()] +
                                 ['systemctl', '--user', 'status', 'signage-client.service', '--no-pager', '-l'], 
                                 check=False, env={**os.environ, **user_env})
                else:
                    # Running as regular user
                    subprocess.run(['systemctl', '--user', 'start', 'signage-client.service'], check=True)
                    print("   ✅ User service started")
                    
                    # Show service status
                    print("\n📊 Service Status:")
                    subprocess.run(['systemctl', '--user', 'status', 'signage-client.service', '--no-pager', '-l'], check=False)
                
            except subprocess.CalledProcessError:
                print("   ❌ Failed to start user service")
                print(f"   Try manually: systemctl --user start signage-client.service")
                print(f"   Or as root: sudo -u {username} systemctl --user start signage-client.service")
    
    def show_completion_info(self):
        """Show completion information"""
        print("\n" + "=" * 60)
        print("🎉 Setup Complete!")
        print("=" * 60)
        print()
        print("Your digital signage client is now configured in kiosk mode!")
        print()
        print("🖥️  Kiosk Mode Features:")
        print("   • All notifications disabled")
        print("   • Power management disabled (never sleep/suspend)")
        print("   • Screen saver and lock screen disabled")
        print("   • TBN logo set as desktop background")
        print("   • Automatic system updates disabled")
        print("   • Settings auto-restore on each login")
        print("   • TeamViewer installed for remote management")
        print()
        print("📋 Next Steps:")
        print("1. Register this device in your web dashboard:")
        print(f"   - Server: {self.server_url}")  
        print(f"   - Device ID: {self.device_id}")
        print("2. Create playlists and assign them to this device")
        print("3. Media will automatically download and play in fullscreen")
        print("4. Reboot to ensure all kiosk settings take effect")
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
            
            # Configure sudo permissions for remote reboot
            self.configure_sudo_permissions()
            
            # Configure kiosk mode for Ubuntu 22.04
            self.configure_kiosk_mode()
            
            # Install TeamViewer for remote management
            self.install_teamviewer()
            
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