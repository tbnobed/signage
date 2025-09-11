#!/usr/bin/env python3
"""
Digital Signage Client Agent
Runs on Raspberry Pi or NUC devices to display media content
"""

import os
import sys
import time
import json
import subprocess
import logging
import requests
import getpass
from pathlib import Path
from datetime import datetime, timedelta
import signal
import threading
from threading import Lock

# Configuration
SERVER_URL = os.environ.get('SIGNAGE_SERVER_URL', 'http://localhost:5000')
DEVICE_ID = os.environ.get('DEVICE_ID', 'device-001')
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '60'))  # seconds
RAPID_CHECK_INTERVAL = int(os.environ.get('RAPID_CHECK_INTERVAL', '2'))  # seconds for playlist status checks
MEDIA_DIR = os.environ.get('MEDIA_DIR', os.path.expanduser('~/signage/media'))
LOG_FILE = os.environ.get('LOG_FILE', os.path.expanduser('~/signage/client.log'))

# Media player commands for desktop Ubuntu
PLAYER_COMMANDS = {
    'vlc': ['vlc', '--fullscreen', '--no-osd', '--loop', '--no-video-title-show', '--qt-minimal-view', '--no-qt-privacy-ask']
}

# Screen targeting support for multi-monitor setups
SCREEN_INDEX = int(os.environ.get('SCREEN_INDEX', '0'))  # Default to primary screen

class SignageClient:
    def __init__(self):
        self.setup_logging()
        self.current_playlist = None
        self.current_process = None
        self.media_player = self.detect_media_player()
        self.running = True
        self.current_media_index = 0
        self.last_media_change = datetime.now()
        self.last_playlist_check = None  # Track when we last got playlist timestamp
        
        # Thread safety for concurrent access
        self._playlist_lock = Lock()
        self._stop_event = threading.Event()
        
        # Create media directory
        Path(MEDIA_DIR).mkdir(exist_ok=True)
        
        self.logger.info(f"Signage client started for device: {DEVICE_ID}")
        self.logger.info(f"Server URL: {SERVER_URL}")
        self.logger.info(f"Media player: {self.media_player}")
        self.logger.info(f"Rapid playlist checks every {RAPID_CHECK_INTERVAL} seconds for instant updates")
        
        # Start background thread for rapid playlist checks
        self._rapid_check_thread = threading.Thread(target=self._rapid_check_loop, daemon=True)
        self._rapid_check_thread.start()
        self.logger.info("Background rapid playlist checking started")

    def setup_logging(self):
        logging.basicConfig(
            level=logging.DEBUG,  # Enable debug logging to see rapid checks
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def detect_media_player(self):
        """Detect VLC media player for desktop Ubuntu"""
        try:
            subprocess.run(['vlc', '--version'], capture_output=True, timeout=5)
            self.logger.info("Found VLC media player")
            return 'vlc'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.logger.error("VLC media player not found! Please install VLC.")
            return None

    def send_checkin(self):
        """Send heartbeat to server"""
        try:
            current_media = None
            if self.current_playlist and self.current_playlist.get('items'):
                items = self.current_playlist['items']
                if items and self.current_media_index < len(items):
                    current_media = items[self.current_media_index]['original_filename']
            
            data = {
                'current_media': current_media,
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                f"{SERVER_URL}/api/devices/{DEVICE_ID}/checkin",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Ensure we have valid JSON data
                if result is None:
                    self.logger.error("Received empty JSON response from server")
                    return None
                    
                self.logger.debug(f"Checkin successful: {result}")
                
                # Check for pending commands from server
                if 'command' in result:
                    command = result.get('command')
                    self.logger.info(f"Received command from server: {command}")
                    self.execute_command(command)
                
                return result
            else:
                self.logger.error(f"Checkin failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Checkin error: {e}")
        
        return None

    def send_log(self, log_type, message):
        """Send log message to server"""
        try:
            data = {
                'type': log_type,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            requests.post(
                f"{SERVER_URL}/api/devices/{DEVICE_ID}/logs",
                json=data,
                timeout=5
            )
        except Exception as e:
            self.logger.error(f"Failed to send log to server: {e}")

    def _rapid_check_loop(self):
        """Background thread that runs rapid playlist checks"""
        while not self._stop_event.wait(RAPID_CHECK_INTERVAL):
            try:
                self.logger.info("Running rapid playlist check (background thread)...")
                self.check_playlist_status()
            except Exception as e:
                self.logger.error(f"Error in rapid check loop: {e}")

    def check_playlist_status(self):
        """Quick check if content (playlist or media) has been updated AND check for urgent commands"""
        try:
            self.logger.debug(f"Checking content status...")
            response = requests.get(
                f"{SERVER_URL}/api/devices/{DEVICE_ID}/playlist-status",
                timeout=5
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Ensure we have valid JSON data
                    if data is None:
                        self.logger.error("Received empty JSON response from server")
                        return False
                        
                    # Check if data is actually a dictionary
                    if not isinstance(data, dict):
                        self.logger.error(f"Expected JSON object, got {type(data)}: {data}")
                        return False
                        
                except (ValueError, json.JSONDecodeError) as e:
                    self.logger.error(f"Failed to parse JSON response: {e}")
                    self.logger.debug(f"Response content: {response.text[:200]}")
                    return False
                
                playlist_id = data.get('playlist_id')
                media_id = data.get('media_id')
                last_updated = data.get('last_updated')
                
                # Check for urgent commands (like reboot) during rapid checks
                if 'command' in data:
                    command = data.get('command')
                    self.logger.info(f"Received urgent command from server: {command}")
                    self.execute_command(command)
                    return True  # Command executed, content check not needed
                
                with self._playlist_lock:
                    # Check current assignment type and ID
                    current_playlist_id = self.current_playlist.get('id') if self.current_playlist else None
                    current_media_id = getattr(self, 'current_media', {}).get('id') if hasattr(self, 'current_media') else None
                    current_timestamp = self.current_playlist.get('last_updated') if self.current_playlist else None
                    current_media_timestamp = getattr(self, 'current_media', {}).get('last_updated') if hasattr(self, 'current_media') else None
                
                self.logger.debug(f"Current - playlist: {current_playlist_id}, media: {current_media_id}, "
                                f"Server - playlist: {playlist_id}, media: {media_id}, "
                                f"Timestamps - current_playlist: {current_timestamp}, current_media: {current_media_timestamp}, server: {last_updated}")
                
                # Check if we need to fetch new content
                assignment_changed = False
                if playlist_id and (current_playlist_id != playlist_id or current_timestamp != last_updated):
                    assignment_changed = True
                    self.logger.info(f"Playlist assignment change detected")
                elif media_id and (current_media_id != media_id or current_media_timestamp != last_updated):
                    assignment_changed = True
                    self.logger.info(f"Media assignment change detected")
                elif not playlist_id and not media_id and (current_playlist_id or current_media_id):
                    assignment_changed = True
                    self.logger.info(f"Assignment cleared")
                elif not self.current_playlist and not hasattr(self, 'current_media'):
                    assignment_changed = True
                    self.logger.info(f"Initial content fetch needed")
                
                if assignment_changed:
                    self.logger.info(f"Content update detected - stopping current media and fetching new content")
                    self.stop_current_media()  # Stop immediately to start new content
                    return self.fetch_content()
            else:
                self.logger.debug(f"Content status check got {response.status_code}")
                    
        except Exception as e:
            self.logger.error(f"Content status check failed: {e}")
            
        return False

    def fetch_content(self):
        """Fetch current content (playlist or media) from server"""
        try:
            response = requests.get(
                f"{SERVER_URL}/api/devices/{DEVICE_ID}/playlist",
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Ensure we have valid JSON data
                    if data is None:
                        self.logger.error("Received empty JSON response from server")
                        return False
                        
                    # Check if data is actually a dictionary
                    if not isinstance(data, dict):
                        self.logger.error(f"Expected JSON object, got {type(data)}: {data}")
                        return False
                        
                except (ValueError, json.JSONDecodeError) as e:
                    self.logger.error(f"Failed to parse JSON response: {e}")
                    self.logger.debug(f"Response content: {response.text[:200]}")
                    return False
                
                playlist = data.get('playlist')
                media = data.get('media')
                
                content_updated = False
                
                # Handle playlist assignment
                if playlist:
                    if playlist != self.current_playlist:
                        self.logger.info(f"New playlist received: {playlist['name']}")
                        self.stop_current_media()  # Stop current media immediately
                        with self._playlist_lock:
                            self.current_playlist = playlist
                            self.current_media = None  # Clear single media
                            self.current_media_index = 0
                        content_updated = True
                
                # Handle individual media assignment
                elif media:
                    if not hasattr(self, 'current_media') or media != getattr(self, 'current_media', None):
                        self.logger.info(f"New media assignment received: {media['original_filename']}")
                        self.stop_current_media()  # Stop current media immediately
                        with self._playlist_lock:
                            self.current_playlist = None  # Clear playlist
                            self.current_media = media
                            self.current_media_index = 0
                        content_updated = True
                
                # Handle no assignment
                else:
                    if self.current_playlist or hasattr(self, 'current_media'):
                        self.logger.info(f"No content assigned - clearing current assignment")
                        self.stop_current_media()
                        with self._playlist_lock:
                            self.current_playlist = None
                            self.current_media = None
                            self.current_media_index = 0
                        content_updated = True
                
                if content_updated:
                    self.logger.info(f"Starting immediate playback of new content")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch content: {e}")
            
        return False

    def execute_command(self, command):
        """Execute a command received from server"""
        if command == 'reboot':
            self.logger.info("Executing reboot command...")
            # Stop current media first
            self.stop_current_media()
            
            # Give some time for cleanup
            time.sleep(2)
            
            # Execute reboot
            try:
                subprocess.run(['sudo', 'reboot'], check=True)
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to execute reboot: {e}")
                self.send_log('error', f'Failed to execute reboot: {e}')
        else:
            self.logger.warning(f"Unknown command received: {command}")

    def download_media(self, media_items):
        """Download media files from server"""
        for item in media_items:
            filename = item['filename']
            local_path = Path(MEDIA_DIR) / filename
            
            # Skip if file already exists and has same size
            if local_path.exists():
                try:
                    local_size = local_path.stat().st_size
                    if local_size == item.get('file_size', 0):
                        self.logger.debug(f"Skipping download, {filename} already exists")
                        continue
                except:
                    pass
            
            self.logger.info(f"Downloading {filename}...")
            
            try:
                response = requests.get(
                    f"{SERVER_URL}/media/download/{filename}",
                    timeout=30,
                    stream=True
                )
                
                if response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    self.logger.info(f"Downloaded {filename}")
                else:
                    self.logger.error(f"Failed to download {filename}: {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Error downloading {filename}: {e}")

    def play_content(self):
        """Play current content (playlist or individual media)"""
        if not self.media_player:
            self.logger.error("No media player available")
            return False
            
        with self._playlist_lock:
            # Handle individual media assignment
            if hasattr(self, 'current_media') and self.current_media:
                return self.play_individual_media()
            
            # Handle playlist assignment
            elif self.current_playlist and self.current_playlist.get('items'):
                return self.play_playlist()
            
            else:
                self.logger.debug("No content assigned to play")
                return False

    def play_individual_media(self):
        """Play a single media file"""
        media = self.current_media
        if not media:
            return False
            
        filename = media.get('filename')
        if not filename:
            self.logger.error("Media has no filename")
            return False
            
        local_path = Path(MEDIA_DIR) / filename
        
        # Download if not exists
        if not local_path.exists():
            self.logger.info(f"Downloading media file: {filename}")
            self.download_media([media])
            
        if not local_path.exists():
            self.logger.error(f"Failed to download media: {filename}")
            return False
            
        self.logger.info(f"Playing individual media: {filename}")
        return self.create_and_play_vlc_playlist([media])

    def play_playlist(self):
        """Play current playlist"""
        if not self.current_playlist or not self.current_playlist.get('items'):
            return False
            
        items = self.current_playlist['items']
        
        # Download missing media
        missing_items = []
        for item in items:
            local_path = Path(MEDIA_DIR) / item['filename']
            if not local_path.exists():
                missing_items.append(item)
                
        if missing_items:
            self.logger.info(f"Downloading {len(missing_items)} missing media files...")
            self.download_media(missing_items)
        
        # Play the playlist
        self.logger.info(f"Playing playlist: {self.current_playlist['name']} with {len(items)} items")
        return self.create_and_play_vlc_playlist(items)

    def create_and_play_vlc_playlist(self, media_items):
        """Create M3U playlist and play with VLC"""
        playlist_path = Path(MEDIA_DIR) / "current_playlist.m3u"
        
        try:
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write("#EXTM3U\n")
                
                for item in media_items:
                    filename = item['filename']
                    local_path = Path(MEDIA_DIR) / filename
                    
                    if local_path.exists():
                        # Add duration for images (10 seconds default)
                        if any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                            f.write("#EXTVLCOPT:image-duration=10\n")
                        
                        f.write(f"{local_path.absolute()}\n")
                    else:
                        self.logger.warning(f"Media file not found: {filename}")
            
            # Count actual media items in playlist
            with open(playlist_path, 'r') as f:
                content = f.read()
                media_count = len([line for line in content.split('\n') if line and not line.startswith('#')])
            
            if media_count == 0:
                self.logger.error("No media files available to play")
                return False
                
            self.logger.info(f"Created VLC playlist with {media_count} items: {playlist_path}")
            return self.start_vlc_continuous_playlist(playlist_path, media_count)
            
        except Exception as e:
            self.logger.error(f"Failed to create playlist: {e}")
            return False

    def start_vlc_continuous_playlist(self, playlist_path, video_count):
        """Start VLC with continuous playlist playback"""
        try:
            # Stop any existing media
            self.stop_current_media()
            
            self.logger.info(f"Starting continuous VLC playlist: {video_count} videos")
            
            # Set up display environment for VLC
            env = os.environ.copy()
            
            # Handle different display scenarios
            if os.environ.get('WAYLAND_DISPLAY'):
                # Wayland environment
                env['QT_QPA_PLATFORM'] = 'wayland'
                self.logger.debug(f"Using Wayland display: {os.environ.get('WAYLAND_DISPLAY')}")
            elif os.environ.get('DISPLAY'):
                # X11 environment
                display = os.environ.get('DISPLAY')
                
                # Try to find X authority file
                xauth_file = None
                possible_xauth = [
                    os.environ.get('XAUTHORITY'),
                    f'/tmp/.X11-unix/X{display.split(":")[1].split(".")[0]}' if ':' in display else None,
                    os.path.expanduser('~/.Xauthority'),
                ]
                
                for auth_file in possible_xauth:
                    if auth_file and os.path.exists(auth_file):
                        xauth_file = auth_file
                        break
                
                if xauth_file:
                    env['XAUTHORITY'] = xauth_file
                    self.logger.debug(f"Using XAUTHORITY: {xauth_file}")
                else:
                    self.logger.warning("No X authority file found")
                    
                self.logger.debug(f"Using X11 display: {display}")
            else:
                self.logger.warning("No display environment detected")
            
            # Log display environment for debugging
            self.logger.debug(f"Display environment - DISPLAY: {env.get('DISPLAY')}, "
                            f"WAYLAND_DISPLAY: {env.get('WAYLAND_DISPLAY')}, "
                            f"SESSION_TYPE: {env.get('SESSION_TYPE')}, "
                            f"XAUTHORITY: {env.get('XAUTHORITY')}")
            
            # VLC command for continuous playlist
            vlc_cmd = [
                'vlc', 
                '--intf', 'dummy',           # No interface
                '--fullscreen',              # Fullscreen mode
                '--no-osd',                  # No on-screen display
                '--loop',                    # Loop the playlist
                '--no-video-title-show',     # Don't show video title
                '--no-qt-privacy-ask',       # Don't ask about privacy
                '--quiet',                   # Reduce console output
                '--no-interact',             # Non-interactive mode
                str(playlist_path)           # Playlist file
            ]
            
            # Add debug logging
            debug_log = Path(MEDIA_DIR) / "vlc_debug.log"
            vlc_cmd.extend(['--extraintf', 'logger', '--logfile', str(debug_log)])
            self.logger.info(f"VLC debug output will be written to: {debug_log}")
            
            # Start VLC process
            self.current_process = subprocess.Popen(
                vlc_cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            self.logger.info("VLC continuous playlist started - no more visual interruptions between videos!")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start VLC playlist: {e}")
            return False

    def stop_current_media(self):
        """Stop currently playing media"""
        if self.current_process:
            try:
                self.logger.debug("Stopping current media process...")
                self.current_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.current_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.logger.debug("Process didn't terminate gracefully, killing...")
                    self.current_process.kill()
                    self.current_process.wait()
                
                self.current_process = None
                self.logger.debug("Media process stopped")
                
            except Exception as e:
                self.logger.error(f"Error stopping media: {e}")

    def monitor_playback(self):
        """Monitor VLC process and restart if needed"""
        if self.current_process and self.current_process.poll() is not None:
            self.logger.info("VLC process ended, restarting playback")
            self.current_process = None
            return True
        return False

    def run(self):
        """Main client loop"""
        self.logger.info("Starting main client loop...")
        
        # Initial content fetch
        self.send_checkin()
        self.fetch_content()
        
        last_checkin = datetime.now()
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Monitor playback and restart if needed
                if self.monitor_playback():
                    self.play_content()
                
                # Start playback if nothing is playing and we have content
                if not self.current_process:
                    if self.play_content():
                        self.logger.info("Started media playback")
                
                # Regular checkin with server
                if (current_time - last_checkin).total_seconds() >= CHECK_INTERVAL:
                    self.send_checkin()
                    last_checkin = current_time
                
                # Short sleep to prevent busy waiting
                time.sleep(1)
                
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(5)  # Wait before retrying
        
        # Cleanup
        self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up...")
        self.running = False
        self._stop_event.set()
        self.stop_current_media()

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

if __name__ == '__main__':
    client = SignageClient()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, client.signal_handler)
    signal.signal(signal.SIGINT, client.signal_handler)
    
    try:
        client.run()
    except KeyboardInterrupt:
        client.logger.info("Interrupted by user")
    except Exception as e:
        client.logger.error(f"Fatal error: {e}")
    finally:
        client.cleanup()