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
                try:
                    result = response.json()
                    
                    # Ensure we have valid JSON data
                    if result is None:
                        self.logger.error("Received null JSON response from server")
                        return None
                    
                    # Ensure result is actually a dictionary
                    if not isinstance(result, dict):
                        self.logger.error(f"Expected JSON object, got {type(result)}: {result}")
                        return None
                        
                except (ValueError, TypeError) as e:
                    self.logger.error(f"Failed to parse JSON response: {e}")
                    self.logger.debug(f"Response content: {response.text[:200]}")
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
                        self.logger.error("Received null JSON response from server")
                        return False
                    
                    # Ensure data is actually a dictionary
                    if not isinstance(data, dict):
                        self.logger.error(f"Expected JSON object, got {type(data)}: {data}")
                        return False
                        
                except (ValueError, TypeError) as e:
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
                    current_media = getattr(self, 'current_media', None)
                    current_media_id = current_media.get('id') if current_media else None
                    current_timestamp = self.current_playlist.get('last_updated') if self.current_playlist else None
                    current_media_timestamp = current_media.get('last_updated') if current_media else None
                
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
                        self.logger.error("Received null JSON response from server")
                        return False
                    
                    # Ensure data is actually a dictionary
                    if not isinstance(data, dict):
                        self.logger.error(f"Expected JSON object, got {type(data)}: {data}")
                        return False
                        
                except (ValueError, TypeError) as e:
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

    def download_media(self, media_item):
        """Download media file if not cached locally"""
        filename = media_item['filename']
        local_path = os.path.join(MEDIA_DIR, filename)
        
        if os.path.exists(local_path):
            return local_path
        
        try:
            self.logger.info(f"Downloading: {media_item['original_filename']}")
            
            response = requests.get(media_item['url'], stream=True, timeout=30)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Downloaded: {filename}")
            return local_path
            
        except Exception as e:
            self.logger.error(f"Download failed for {filename}: {e}")
            return None

    def play_media(self, media_path, duration=None, allow_loop=False):
        """Play media file using VLC on desktop Ubuntu"""
        if not self.media_player:
            self.logger.error("No media player available")
            return False
        
        try:
            command = PLAYER_COMMANDS[self.media_player].copy()
            
            # Add screen targeting for multi-monitor setups
            if SCREEN_INDEX > 0:
                command.extend(['--qt-fullscreen-screennumber', str(SCREEN_INDEX)])
            
            command.append(media_path)
            
            self.logger.info(f"Playing: {os.path.basename(media_path)}")
            if SCREEN_INDEX > 0:
                self.logger.info(f"Target screen: {SCREEN_INDEX}")
            
            # Kill any existing player process
            self.stop_current_media()
            
            # Use inherited environment (Wayland/X11) from user service
            # Don't override DISPLAY, WAYLAND_DISPLAY, or XDG_SESSION_TYPE
            env = os.environ.copy()
            
            # Log current display environment for debugging
            display_env = env.get('DISPLAY', 'not set')
            wayland_display = env.get('WAYLAND_DISPLAY', 'not set')
            session_type = env.get('XDG_SESSION_TYPE', 'not set')
            self.logger.debug(f"Display environment - DISPLAY: {display_env}, WAYLAND_DISPLAY: {wayland_display}, SESSION_TYPE: {session_type}")
            
            # Only add XAUTHORITY if we have an X11 display and the file exists
            if env.get('DISPLAY') and not env.get('XAUTHORITY'):
                user_home = os.path.expanduser('~')
                xauth_path = f'{user_home}/.Xauthority'
                if os.path.exists(xauth_path):
                    env['XAUTHORITY'] = xauth_path
            
            # Start VLC process
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
            
            # If allow_loop is True, let VLC run indefinitely with its internal loop
            # This prevents the constant stopping/starting that causes visual interruptions
            if allow_loop:
                self.logger.info("Allowing VLC to loop indefinitely")
                # Don't wait with timeout - let VLC loop internally
                # The process will only be stopped when playlist changes or client shuts down
                return True
            
            # For timed playback (multi-item playlists)
            if duration:
                try:
                    self.current_process.wait(timeout=duration)
                except subprocess.TimeoutExpired:
                    self.current_process.terminate()
                    self.current_process.wait()
            else:
                self.current_process.wait()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to play media: {e}")
            return False

    def play_continuous_playlist(self, media_paths, loop=True):
        """Play multiple media files as a continuous VLC playlist without interruptions"""
        if not self.media_player or not media_paths:
            return False
            
        try:
            # Create VLC playlist file (.m3u format for better image support)
            playlist_file = os.path.join(MEDIA_DIR, 'current_playlist.m3u')
            
            # Generate M3U playlist content (simpler and more reliable than XSPF)
            with open(playlist_file, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                for i, media_path in enumerate(media_paths):
                    abs_path = os.path.abspath(media_path)
                    
                    # ARCHITECT FIX: Use EXTVLCOPT for image timing, no EXTINF
                    # This avoids conflicts and gives VLC more reliable per-item control
                    file_ext = os.path.splitext(media_path)[1].lower()
                    if file_ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']:
                        # Images: Use VLC-specific option for 10 second duration
                        f.write(f'#EXTVLCOPT:image-duration=10\n')
                    # Videos: No special options, VLC uses intrinsic duration
                    
                    f.write(f'{abs_path}\n')
            
            self.logger.info(f"Created VLC playlist with {len(media_paths)} items: {playlist_file}")
            
            # Build VLC command for continuous playlist playback
            command = PLAYER_COMMANDS[self.media_player].copy()
            
            # Add screen targeting for multi-monitor setups
            if SCREEN_INDEX > 0:
                command.extend(['--qt-fullscreen-screennumber', str(SCREEN_INDEX)])
            
            # Remove default --loop to control explicitly
            if '--loop' in command:
                command.remove('--loop')
            
            # Force infinite looping for images and videos
            command.extend([
                '--loop',             # Loop the entire playlist (NOT repeat current item)
                '--image-duration', '10',  # Images show for 10 seconds each (backup for EXTVLCOPT)
                '--playlist-autostart',    # Auto start playlist
                '--no-random',        # Play in order
                '--no-qt-error-dialogs',  # No error popups
                '--intf', 'dummy',    # No interface (more stable)
                '--vout', 'x11',      # Force X11 output (Ubuntu/Wayland compatibility)
                '--avcodec-hw', 'none',  # Disable hardware decoding (compatible parameter)
                '-vvv',               # Verbose logging to see VLC errors
            ])
            
            # Add the playlist file
            command.append(playlist_file)
            
            self.logger.info(f"Starting continuous VLC playlist: {len(media_paths)} videos")
            if SCREEN_INDEX > 0:
                self.logger.info(f"Target screen: {SCREEN_INDEX}")
            
            # Kill any existing player process
            self.stop_current_media()
            
            # Use inherited environment (Wayland/X11) from user service
            env = os.environ.copy()
            
            # CRITICAL: Fix X11 authorization for systemd service
            env['DISPLAY'] = ':0'  # Force display :0
            
            # Get current user session's XAUTHORITY file
            import subprocess as sp
            try:
                # Get XAUTHORITY from loginctl session
                result = sp.run(['loginctl', 'show-user', 'obtv', '--property=RuntimePath'], 
                              capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    runtime_path = result.stdout.strip().split('=')[1]
                    env['XDG_RUNTIME_DIR'] = runtime_path
                    
                # Try multiple XAUTHORITY locations
                user_home = os.path.expanduser('~')
                xauth_candidates = [
                    f'{user_home}/.Xauthority',
                    f'{user_home}/.Xauth',
                    '/tmp/.X11-unix/X0'
                ]
                
                for xauth_path in xauth_candidates:
                    if os.path.exists(xauth_path):
                        env['XAUTHORITY'] = xauth_path
                        self.logger.debug(f"Using XAUTHORITY: {xauth_path}")
                        break
                        
            except Exception as e:
                self.logger.debug(f"X11 setup warning: {e}")
            
            # Log current display environment for debugging
            display_env = env.get('DISPLAY', 'not set')
            wayland_display = env.get('WAYLAND_DISPLAY', 'not set')
            session_type = env.get('XDG_SESSION_TYPE', 'not set')
            xauth = env.get('XAUTHORITY', 'not set')
            self.logger.debug(f"Display environment - DISPLAY: {display_env}, WAYLAND_DISPLAY: {wayland_display}, SESSION_TYPE: {session_type}, XAUTHORITY: {xauth}")
            
            # Start VLC with playlist - enable logging to see errors
            log_file = os.path.join(MEDIA_DIR, 'vlc_debug.log')
            with open(log_file, 'w') as vlc_log:
                self.current_process = subprocess.Popen(
                    command,
                    stdout=vlc_log,
                    stderr=subprocess.STDOUT,  # Redirect stderr to stdout to capture all VLC messages
                    env=env
                )
            
            self.logger.info(f"VLC debug output will be written to: {log_file}")
            
            self.logger.info("VLC continuous playlist started - no more visual interruptions between videos!")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating continuous playlist: {e}")
            return False

    def stop_current_media(self):
        """Stop currently playing media"""
        with self._playlist_lock:
            if self.current_process and self.current_process.poll() is None:
                try:
                    self.current_process.terminate()
                    self.current_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                    self.current_process.wait()
                except Exception as e:
                    self.logger.error(f"Error stopping media: {e}")

    def play_content(self):
        """Play current content (playlist or individual media)"""
        # Handle playlist assignment
        if self.current_playlist and self.current_playlist.get('items'):
            items = self.current_playlist['items']
            
            self.logger.info(f"Playing playlist with {len(items)} items - creating continuous VLC playlist")
            
            # Download all media files first
            media_paths = []
            for item in items:
                local_path = self.download_media(item)
                if local_path:
                    media_paths.append(local_path)
                else:
                    self.send_log('error', f"Failed to download: {item['original_filename']}")
            
            if not media_paths:
                self.logger.error("No media files available to play")
                time.sleep(10)
                return
                
            # Create VLC playlist to avoid stopping/starting between videos
            success = self.play_continuous_playlist(media_paths, loop=self.current_playlist.get('loop', True))
        
        # Handle individual media assignment
        elif hasattr(self, 'current_media') and self.current_media:
            media = self.current_media
            
            self.logger.info(f"Playing individual media: {media['original_filename']}")
            
            # Download the media file
            local_path = self.download_media(media)
            if not local_path:
                self.send_log('error', f"Failed to download: {media['original_filename']}")
                time.sleep(10)
                return
            
            # Play single media in a loop (reuse continuous playlist with one item)
            success = self.play_continuous_playlist([local_path], loop=True)
        
        # No content assigned
        else:
            self.logger.debug("No content assigned")
            time.sleep(10)
            return
        
        if success:
            # Keep VLC running continuously
            while self.running and self.current_process and self.current_process.poll() is None:
                time.sleep(5)  # Check every 5 seconds if VLC is still running
                # Content update checks will happen via background thread
            
            self.logger.info("VLC process ended, restarting playback")
        else:
            self.send_log('error', "Failed to start content playback")
            time.sleep(10)

    def cleanup_old_media(self):
        """Remove old media files to save space"""
        try:
            current_files = set()
            
            # Include files from current playlist
            if self.current_playlist and self.current_playlist.get('items'):
                current_files.update(item['filename'] for item in self.current_playlist['items'])
            
            # Include current individual media file
            if hasattr(self, 'current_media') and self.current_media:
                current_files.add(self.current_media['filename'])
            
            for filename in os.listdir(MEDIA_DIR):
                if filename not in current_files and not filename.startswith('.'):
                    file_path = os.path.join(MEDIA_DIR, filename)
                    # Keep files modified in last 24 hours
                    if os.path.getmtime(file_path) < time.time() - 86400:
                        os.remove(file_path)
                        self.logger.info(f"Removed old media: {filename}")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up media: {e}")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("Shutdown signal received")
        self.running = False
        self._stop_event.set()  # Stop the background thread
        self.stop_current_media()

    def run(self):
        """Main client loop"""
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        last_checkin = datetime.now() - timedelta(seconds=CHECK_INTERVAL)
        last_cleanup = datetime.now()
        
        self.send_log('info', 'Signage client started')
        
        while self.running:
            try:
                # Send periodic checkin and full sync
                if datetime.now() - last_checkin >= timedelta(seconds=CHECK_INTERVAL):
                    self.send_checkin()
                    self.fetch_content()
                    last_checkin = datetime.now()
                
                # Rapid checks now run in background thread, no longer needed here
                
                # Play current content (playlist or media)
                self.play_content()
                
                # Cleanup old media files periodically
                if datetime.now() - last_cleanup >= timedelta(hours=6):
                    self.cleanup_old_media()
                    last_cleanup = datetime.now()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in main loop: {e}")
                self.send_log('error', f"Client error: {str(e)}")
                time.sleep(30)  # Wait before retrying
        
        self.logger.info("Signage client stopped")
        self.send_log('info', 'Signage client stopped')

    def execute_command(self, command):
        """Execute remote command from server"""
        self.logger.info(f"Executing remote command: {command}")
        self.send_log('info', f'Executing remote command: {command}')
        
        try:
            if command == 'reboot':
                self.logger.info("Rebooting device as requested by server")
                self.send_log('info', 'Rebooting device as requested by server')
                # Stop current media first
                self.stop_current_media()
                # Execute reboot command
                subprocess.run(['sudo', 'reboot'], timeout=10)
            
            elif command == 'restart_service':
                self.logger.info("Restarting signage service as requested by server")
                self.send_log('info', 'Restarting signage service as requested by server')
                # This will cause the service to restart
                self.running = False
                
            else:
                self.logger.warning(f"Unknown command received: {command}")
                self.send_log('warning', f'Unknown command received: {command}')
                
        except Exception as e:
            error_msg = f"Failed to execute command '{command}': {e}"
            self.logger.error(error_msg)
            self.send_log('error', error_msg)


if __name__ == "__main__":
    client = SignageClient()
    
    try:
        client.run()
    except Exception as e:
        client.logger.error(f"Fatal error: {e}")
        sys.exit(1)
