#!/usr/bin/env python3
"""
DisplayHQ Client Agent
Runs on Raspberry Pi or NUC devices to display media content
"""

# Client version - increment when making updates
CLIENT_VERSION = "2.3.5"

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
UPDATE_CHECK_INTERVAL = int(os.environ.get('UPDATE_CHECK_INTERVAL', '21600'))  # 6 hours in seconds
MEDIA_DIR = os.environ.get('MEDIA_DIR', os.path.expanduser('~/signage/media'))
LOG_FILE = os.environ.get('LOG_FILE', os.path.expanduser('~/signage/client.log'))

# Media player commands for desktop Ubuntu
PLAYER_COMMANDS = {
    'mpv': [
        'mpv', '--fs', '--no-osc', '--no-osd-bar', '--osd-level=0', '--no-terminal', 
        '--loop-playlist=inf', '--keep-open=yes', '--prefetch-playlist=yes',
        '--cache=yes', '--cache-secs=20', '--demuxer-readahead-secs=10',
        '--demuxer-max-bytes=500M', '--image-display-duration=10',
        '--vo=gpu', '--video-sync=display-resample'
    ],
    'vlc': ['vlc', '--fullscreen', '--no-osd', '--loop', '--no-video-title-show', '--qt-minimal-view', '--no-qt-privacy-ask', '--intf', 'dummy', '--no-qt-error-dialogs']
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
        
        self.logger.info(f"DisplayHQ client v{CLIENT_VERSION} started for device: {DEVICE_ID}")
        self.logger.info(f"Server URL: {SERVER_URL}")
        self.logger.info(f"Media player: {self.media_player}")
        self.logger.info(f"Rapid playlist checks every {RAPID_CHECK_INTERVAL} seconds for instant updates")
        
        # Start background thread for rapid playlist checks
        self._rapid_check_thread = threading.Thread(target=self._rapid_check_loop, daemon=True)
        self._rapid_check_thread.start()
        self.logger.info("Background rapid playlist checking started")
        
        # Start background thread for regular check-ins (TeamViewer ID)
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        self.logger.info("Background heartbeat checking started")
        
        # Update system is now admin-controlled via server commands (no automatic checking)
        
        # Send immediate check-in to publish TeamViewer ID right away
        self.logger.info("Sending initial check-in with TeamViewer ID...")
        self.send_checkin()
        
        # CRITICAL FIX: Force initial playlist fetch on startup
        self.logger.info("Forcing initial playlist fetch on startup...")
        self.fetch_playlist()

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
        """Detect media player: prefer mpv for gapless playback, fallback to VLC"""
        # Try mpv first (better for seamless looping)
        try:
            subprocess.run(['mpv', '--version'], capture_output=True, timeout=5)
            self.logger.info("Found mpv media player (preferred for gapless playback)")
            return 'mpv'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.logger.info("mpv not found, trying VLC...")
        
        # Fallback to VLC
        try:
            subprocess.run(['vlc', '--version'], capture_output=True, timeout=5)
            self.logger.info("Found VLC media player (fallback)")
            return 'vlc'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.logger.error("No supported media player found! Please install mpv or VLC.")
            return None

    def get_teamviewer_id(self):
        """Get TeamViewer ID from the local system"""
        import re
        try:
            # Set fixed locale for consistent output format
            env = os.environ.copy()
            env['LANG'] = 'C'
            env['LC_ALL'] = 'C'
            
            # Try to get TeamViewer ID using sudo teamviewer --info command
            result = subprocess.run(['sudo', '-n', '/usr/bin/teamviewer', '--info'], 
                                  capture_output=True, text=True, timeout=10, env=env)
            
            # Log failures to debug service context issues
            if result.returncode != 0:
                self.logger.info(f"TeamViewer sudo failed (returncode {result.returncode}): {result.stderr.strip()}")
                return None
            
            # Combine stdout and stderr for parsing
            output = (result.stdout or '') + '\n' + (result.stderr or '')
            
            # Method 1: Look for labeled TeamViewer ID line with regex (handles whitespace)
            match = re.search(r'TeamViewer\s*ID\s*:\s*([0-9]{7,12})', output, re.IGNORECASE)
            if match:
                teamviewer_id = match.group(1)
                self.logger.info(f"Successfully parsed TeamViewer ID from labeled line: {teamviewer_id}")
                return teamviewer_id
            
            # Method 2: Look for standalone numeric lines (fallback)
            for line in output.splitlines():
                line = line.strip()
                if re.fullmatch(r'[0-9]{7,12}', line):
                    self.logger.info(f"Successfully parsed TeamViewer ID from numeric line: {line}")
                    return line
            
            # Method 3: Final fallback - any 7-12 digit sequence
            match = re.search(r'\b([0-9]{7,12})\b', output)
            if match:
                teamviewer_id = match.group(1)
                self.logger.info(f"Successfully parsed TeamViewer ID from fallback: {teamviewer_id}")
                return teamviewer_id
            
            self.logger.debug(f"No TeamViewer ID found in output: {output[:200]}...")
            
        except subprocess.TimeoutExpired:
            self.logger.info("TeamViewer command timed out")
        except FileNotFoundError:
            self.logger.info("TeamViewer binary not found at /usr/bin/teamviewer")
        except Exception as e:
            self.logger.info(f"TeamViewer ID detection error: {e}")
        
        return None
    
    def send_checkin(self):
        """Send heartbeat to server"""
        try:
            current_media = None
            if self.current_playlist and self.current_playlist.get('items'):
                items = self.current_playlist['items']
                if items and self.current_media_index < len(items):
                    current_media = items[self.current_media_index]['original_filename']
            
            # Get TeamViewer ID - retry until success, then cache
            if not hasattr(self, '_cached_teamviewer_id') or not self._cached_teamviewer_id:
                teamviewer_id = self.get_teamviewer_id()
                if teamviewer_id:
                    self._cached_teamviewer_id = teamviewer_id
                    self.logger.info(f"Detected TeamViewer ID: {teamviewer_id}")
            
            data = {
                'current_media': current_media,
                'timestamp': datetime.now().isoformat(),
                'client_version': CLIENT_VERSION
            }
            
            # Include TeamViewer ID if available
            if hasattr(self, '_cached_teamviewer_id') and self._cached_teamviewer_id:
                data['teamviewer_id'] = self._cached_teamviewer_id
            
            response = requests.post(
                f"{SERVER_URL}/api/devices/{DEVICE_ID}/checkin",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
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

    def _heartbeat_loop(self):
        """Background thread that sends regular check-ins with TeamViewer ID"""
        while not self._stop_event.wait(CHECK_INTERVAL):
            try:
                self.logger.info("Performing regular check-in...")
                self.send_checkin()
            except Exception as e:
                self.logger.error(f"Error in heartbeat loop: {e}")

    def handle_update_command(self):
        """Handle update command received from server"""
        try:
            self.logger.info("Received update command from server. Fetching latest version...")
            
            # Get update information from server
            response = requests.get(
                f"{SERVER_URL}/api/client/version?current_version={CLIENT_VERSION}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get('latest_version')
                
                self.logger.info(f"Admin-initiated update: {CLIENT_VERSION} -> {latest_version}")
                self.logger.info(f"Release notes: {data.get('release_notes', 'No release notes available')}")
                
                # Perform the update
                if self.update_client(data):
                    self.logger.info("Update completed successfully. Restarting client...")
                    self.restart_client()
                else:
                    self.logger.error("Update failed. Continuing with current version.")
            else:
                self.logger.warning(f"Failed to get update information: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Error handling update command: {e}")

    def update_client(self, update_data):
        """Download and install client update"""
        try:
            github_repo = update_data.get('github_repo')
            if not github_repo:
                self.logger.error("No GitHub repository URL provided for update")
                return False
            
            self.logger.info(f"Downloading update from: {github_repo}")
            
            # Create temporary directory for update
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                # Clone the repository
                clone_cmd = ['git', 'clone', github_repo, temp_dir]
                result = subprocess.run(clone_cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.logger.error(f"Failed to clone repository: {result.stderr}")
                    return False
                
                # Copy the new client_agent.py
                import shutil
                new_client_path = os.path.join(temp_dir, 'client_agent.py')
                current_client_path = os.path.abspath(__file__)
                
                if os.path.exists(new_client_path):
                    # Backup current version
                    backup_path = f"{current_client_path}.backup"
                    shutil.copy2(current_client_path, backup_path)
                    self.logger.info(f"Backed up current client to: {backup_path}")
                    
                    # Install new version
                    shutil.copy2(new_client_path, current_client_path)
                    self.logger.info("New client version installed successfully")
                    return True
                else:
                    self.logger.error(f"New client_agent.py not found in repository")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error updating client: {e}")
            return False

    def restart_client(self):
        """Restart the client after update by exiting cleanly (systemd will restart automatically)"""
        try:
            self.logger.info("Restarting client after update...")
            self.cleanup()
            
            # For systemd services, just exit cleanly and let systemd restart us
            # This is more reliable than trying to start a new process manually
            self.logger.info("Auto-update complete! Exiting for systemd restart...")
            sys.exit(0)
            
        except Exception as e:
            self.logger.error(f"Error restarting client: {e}")

    def cleanup(self):
        """Clean up resources before exit"""
        try:
            self.logger.info("Cleaning up resources...")
            
            # Stop media playback
            self.stop_current_media()
            
            # Set stop event for all background threads
            self._stop_event.set()
            
            # Give threads a moment to stop gracefully
            import time
            time.sleep(1)
            
            self.logger.info("Cleanup complete")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def check_playlist_status(self):
        """Quick check if playlist has been updated AND check for urgent commands"""
        try:
            self.logger.debug(f"Checking playlist status...")
            response = requests.get(
                f"{SERVER_URL}/api/devices/{DEVICE_ID}/playlist-status",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                playlist_id = data.get('playlist_id')
                last_updated = data.get('last_updated')
                
                # Check for urgent commands (like reboot) during rapid checks
                if 'command' in data:
                    command = data.get('command')
                    self.logger.info(f"Received urgent command from server: {command}")
                    self.execute_command(command)
                    return True  # Command executed, playlist check not needed
                
                with self._playlist_lock:
                    current_id = self.current_playlist.get('id') if self.current_playlist else None
                    current_timestamp = self.current_playlist.get('last_updated') if self.current_playlist else None
                
                self.logger.debug(f"Current playlist: {current_id}, "
                                f"Server playlist: {playlist_id}, "
                                f"Current timestamp: {current_timestamp}, "
                                f"Server timestamp: {last_updated}")
                
                # Check if we need to fetch full playlist
                if (not self.current_playlist or 
                    current_id != playlist_id or
                    current_timestamp != last_updated):
                    
                    self.logger.info(f"Playlist update detected - stopping current media and fetching new playlist")
                    self.stop_current_media()  # Stop immediately to start new content
                    return self.fetch_playlist()
            else:
                self.logger.debug(f"Playlist status check got {response.status_code}")
                    
        except Exception as e:
            self.logger.error(f"Playlist status check failed: {e}")
            
        return False

    def fetch_playlist(self):
        """Fetch current playlist from server"""
        try:
            response = requests.get(
                f"{SERVER_URL}/api/devices/{DEVICE_ID}/playlist",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                playlist = data.get('playlist')
                
                # Always update if we don't have a playlist, or if it's actually different
                if self.current_playlist is None or playlist != self.current_playlist:
                    self.logger.info(f"Playlist received: {playlist['name'] if playlist else 'None'}")
                    self.stop_current_media()  # Stop current media immediately
                    with self._playlist_lock:
                        self.current_playlist = playlist
                        self.current_media_index = 0
                    if playlist:
                        self.logger.info(f"Playlist has {len(playlist.get('items', []))} media items")
                    self.logger.info(f"Starting immediate playback of new playlist")
                    return True
                else:
                    self.logger.debug("Fetched playlist is same as current playlist, no update needed")
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch playlist: {e}")
            
        return False

    def download_media(self, media_item):
        """Download media file if not cached locally, or return stream URL for streaming media"""
        
        # Debug: Log media item structure
        self.logger.debug(f"download_media called with: {media_item.keys()}")
        
        # For streaming media, return the stream URL directly (check both stream_url and url fields)
        if media_item.get('is_stream', False):
            stream_url = media_item.get('stream_url') or media_item.get('url')
            if stream_url and isinstance(stream_url, str) and stream_url.startswith(('http://', 'https://', 'rtmp://', 'rtmps://', 'rtsp://')):
                self.logger.info(f"Using stream URL: {media_item['original_filename']} -> {stream_url}")
                return stream_url
            else:
                self.logger.error(f"Stream media has invalid URL: {stream_url}")
                return None
        
        # For regular media files, download and cache locally
        filename = media_item.get('filename')
        if not filename:
            self.logger.error(f"No filename provided for media item: {media_item}")
            return None
            
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
        """Play media file using mpv (preferred) or VLC for seamless playback"""
        if not self.media_player:
            self.logger.error("No media player available")
            return False
        
        try:
            command = PLAYER_COMMANDS[self.media_player].copy()
            
            # Player-specific configurations
            if self.media_player == 'mpv':
                # For mpv single-file loop, use --loop-file=inf instead of --loop-playlist=inf
                if allow_loop:
                    # Remove playlist loop setting and add single-file loop
                    if '--loop-playlist=inf' in command:
                        command.remove('--loop-playlist=inf')
                    command.append('--loop-file=inf')
                
                # Screen targeting for mpv (different from VLC)
                if SCREEN_INDEX > 0:
                    command.extend(['--fs-screen', str(SCREEN_INDEX)])
            
            elif self.media_player == 'vlc':
                # VLC screen targeting
                if SCREEN_INDEX > 0:
                    command.extend(['--qt-fullscreen-screennumber', str(SCREEN_INDEX)])
            
            command.append(media_path)
            
            self.logger.info(f"Playing with {self.media_player}: {os.path.basename(media_path)}")
            if SCREEN_INDEX > 0:
                self.logger.info(f"Target screen: {SCREEN_INDEX}")
            if allow_loop:
                self.logger.info(f"Looping enabled using {self.media_player}-specific settings")
            
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
            
            # Start media player process
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
            
            # If allow_loop is True, let player run indefinitely with its internal loop
            # This prevents the constant stopping/starting that causes visual interruptions
            if allow_loop:
                self.logger.info(f"Allowing {self.media_player} to loop indefinitely")
                # Don't wait with timeout - let player loop internally
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
        """Play multiple media files as a continuous playlist without interruptions"""
        if not self.media_player or not media_paths:
            return False
            
        try:
            command = PLAYER_COMMANDS[self.media_player].copy()
            
            if self.media_player == 'mpv':
                # MPV: Use direct file arguments - better than playlist files for gapless playback
                self.logger.info(f"Preparing mpv gapless playlist with {len(media_paths)} items")
                
                # Screen targeting for mpv
                if SCREEN_INDEX > 0:
                    command.extend(['--fs-screen', str(SCREEN_INDEX)])
                
                # Add all media paths directly as arguments
                for media_path in media_paths:
                    if media_path.startswith(('http://', 'https://', 'rtmp://', 'rtmps://', 'rtsp://')):
                        # Stream URLs: Use as-is
                        command.append(media_path)
                    else:
                        # Local files: Use absolute paths
                        command.append(os.path.abspath(media_path))
                
                self.logger.info(f"Starting mpv gapless playlist: {len(media_paths)} items")
                
            elif self.media_player == 'vlc':
                # VLC: Create M3U playlist file (existing logic)
                playlist_file = os.path.join(MEDIA_DIR, 'current_playlist.m3u')
                
                # Generate M3U playlist content (simpler and more reliable than XSPF)
                with open(playlist_file, 'w', encoding='utf-8') as f:
                    f.write('#EXTM3U\n')
                    for i, media_path in enumerate(media_paths):
                        # Check if this is a stream URL or local file
                        if media_path.startswith(('http://', 'https://', 'rtmp://', 'rtmps://', 'rtsp://')):
                            # Stream URLs: Use as-is, no file processing
                            f.write(f'{media_path}\n')
                        else:
                            # Local files: Apply absolute path and image duration settings
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
                
                # VLC screen targeting
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
                    # General streaming optimizations for all stream types
                    '--network-caching', '5000',  # 5 second buffer for network streams
                    '--live-caching', '5000',     # 5 second buffer for live streams
                    '--file-caching', '5000',     # 5 second buffer for files
                    '--http-reconnect',           # Auto-reconnect on HTTP errors
                    '-vvv',               # Verbose logging to see VLC errors
                ])
                
                # No additional HLS-specific parameters - the general buffering above is sufficient
                
                # Add the playlist file
                command.append(playlist_file)
                
            
            if SCREEN_INDEX > 0:
                self.logger.info(f"Target screen: {SCREEN_INDEX}")
            
            # Kill any existing player process
            self.stop_current_media()
            
            # Use inherited environment (Wayland/X11) from user service
            env = os.environ.copy()
            
            # CRITICAL: Fix X11 authorization for systemd service
            env['DISPLAY'] = ':0'  # Force display :0
            
            # FIXED: Get proper X11 authorization from logged-in user session
            import subprocess as sp
            try:
                # Method 1: Get from current user's environment (most reliable)
                user_home = os.path.expanduser('~')
                xauth_candidates = [
                    f'{user_home}/.Xauthority',
                    f'{user_home}/.Xauth'
                ]
                
                for xauth_path in xauth_candidates:
                    if os.path.exists(xauth_path):
                        env['XAUTHORITY'] = xauth_path
                        self.logger.info(f"Found XAUTHORITY file: {xauth_path}")
                        break
                
                # Method 2: If systemd service, get from active session
                if not env.get('XAUTHORITY'):
                    try:
                        # Get the active session for user obtv
                        result = sp.run(['loginctl', 'list-sessions', '--no-legend'], 
                                      capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            for line in result.stdout.strip().split('\n'):
                                if line and 'obtv' in line:
                                    session_id = line.strip().split()[0]
                                    self.logger.info(f"Found obtv session: {session_id}")
                                    break
                    except Exception as session_e:
                        self.logger.debug(f"Session detection error: {session_e}")
                
                # Method 3: Last resort - try common locations 
                if not env.get('XAUTHORITY'):
                    common_xauth_paths = [
                        f'/home/obtv/.Xauthority',
                        f'/tmp/.X11-auth-obtv',
                        f'/var/run/user/1000/gdm/Xauthority'
                    ]
                    for xauth_path in common_xauth_paths:
                        if os.path.exists(xauth_path):
                            env['XAUTHORITY'] = xauth_path
                            self.logger.info(f"Using fallback XAUTHORITY: {xauth_path}")
                            break
                        
            except Exception as e:
                self.logger.error(f"X11 setup error: {e}")
            
            # Log current display environment for debugging
            display_env = env.get('DISPLAY', 'not set')
            wayland_display = env.get('WAYLAND_DISPLAY', 'not set')
            session_type = env.get('XDG_SESSION_TYPE', 'not set')
            xauth = env.get('XAUTHORITY', 'not set')
            self.logger.debug(f"Display environment - DISPLAY: {display_env}, WAYLAND_DISPLAY: {wayland_display}, SESSION_TYPE: {session_type}, XAUTHORITY: {xauth}")
            
            # Start media player with playlist - enable logging to see errors
            log_file = os.path.join(MEDIA_DIR, f'{self.media_player}_debug.log')
            with open(log_file, 'w') as player_log:
                self.current_process = subprocess.Popen(
                    command,
                    stdout=player_log,
                    stderr=subprocess.STDOUT,  # Redirect stderr to stdout to capture all player messages
                    env=env
                )
            
            self.logger.info(f"{self.media_player} debug output will be written to: {log_file}")
            
            self.logger.info(f"{self.media_player} continuous playlist started - gapless playback enabled!")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating continuous playlist: {e}")
            return False

    def play_single_media_optimized(self, media_item):
        """Optimized playback for single media files (more efficient than playlist approach)"""
        try:
            # REPLIT-FIX-MARKER: If you see this log, you have the corrected version
            self.logger.info("🔧 REPLIT-STREAMING-FIX-ACTIVE: Using corrected streaming media handler")
            # Debug: Log full media item structure
            self.logger.debug(f"play_single_media_optimized received: {media_item}")
            
            # Download the media file or get stream URL
            local_path = self.download_media(media_item)
            if not local_path:
                self.send_log('error', f"Failed to get media path for: {media_item['original_filename']}")
                return False
            
            # Log what we're about to play (helps with debugging)
            if local_path.startswith(('http://', 'https://', 'rtmp://', 'rtmps://', 'rtsp://')):
                self.logger.info(f"Playing stream URL: {local_path}")
            else:
                self.logger.info(f"Playing local file: {os.path.basename(local_path)}")
            
            self.logger.info(f"Starting optimized single media playback: {media_item['original_filename']}")
            
            # Kill any existing player process
            self.stop_current_media()
            
            # CRITICAL: Fix X11 authorization for systemd service
            env = os.environ.copy()
            env['DISPLAY'] = ':0'  # Force display :0
            
            # FIXED: Get proper X11 authorization from logged-in user session
            import subprocess as sp
            try:
                # Method 1: Get from current user's environment (most reliable)
                user_home = os.path.expanduser('~')
                xauth_candidates = [
                    f'{user_home}/.Xauthority',
                    f'{user_home}/.Xauth'
                ]
                
                for xauth_path in xauth_candidates:
                    if os.path.exists(xauth_path):
                        env['XAUTHORITY'] = xauth_path
                        self.logger.info(f"Found XAUTHORITY file: {xauth_path}")
                        break
                
                # Method 2: If systemd service, get from active session
                if not env.get('XAUTHORITY'):
                    try:
                        # Get the active session for user obtv
                        result = sp.run(['loginctl', 'list-sessions', '--no-legend'], 
                                      capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            for line in result.stdout.strip().split('\n'):
                                if line and 'obtv' in line:
                                    session_id = line.strip().split()[0]
                                    self.logger.info(f"Found obtv session: {session_id}")
                                    break
                    except Exception as session_e:
                        self.logger.debug(f"Session detection error: {session_e}")
                
                # Method 3: Last resort - try common locations 
                if not env.get('XAUTHORITY'):
                    common_xauth_paths = [
                        f'/home/obtv/.Xauthority',
                        f'/tmp/.X11-auth-obtv',
                        f'/var/run/user/1000/gdm/Xauthority'
                    ]
                    for xauth_path in common_xauth_paths:
                        if os.path.exists(xauth_path):
                            env['XAUTHORITY'] = xauth_path
                            self.logger.info(f"Using fallback XAUTHORITY: {xauth_path}")
                            break
                        
            except Exception as e:
                self.logger.error(f"X11 setup error: {e}")
            
            # Log current display environment for debugging
            display_env = env.get('DISPLAY', 'not set')
            wayland_display = env.get('WAYLAND_DISPLAY', 'not set')
            session_type = env.get('XDG_SESSION_TYPE', 'not set')
            xauth = env.get('XAUTHORITY', 'not set')
            self.logger.debug(f"Display environment - DISPLAY: {display_env}, WAYLAND_DISPLAY: {wayland_display}, SESSION_TYPE: {session_type}, XAUTHORITY: {xauth}")
            
            # Build optimized VLC command for single media
            command = ['vlc', '--fullscreen', '--no-osd', '--no-video-title-show']
            
            # Add screen targeting for multi-monitor setups
            if SCREEN_INDEX > 0:
                command.extend(['--qt-fullscreen-screennumber', str(SCREEN_INDEX)])
            
            # Single media optimization - use simpler, more reliable options
            command.extend([
                '--loop',             # Infinite loop for single media
                '--no-random',        # Not needed for single file, but ensures consistency
                '--no-qt-error-dialogs',  # No error popups
                '--intf', 'dummy',    # No interface (more stable)
                '--vout', 'x11',      # Force X11 output (Ubuntu/Wayland compatibility)
                '--avcodec-hw', 'none',  # Disable hardware decoding (compatibility)
                # General streaming optimizations for all stream types
                '--network-caching', '5000',  # 5 second buffer for network streams
                '--live-caching', '5000',     # 5 second buffer for live streams
                '--file-caching', '5000',     # 5 second buffer for files
                '--http-reconnect',           # Auto-reconnect on HTTP errors
                '-v',                 # Less verbose than -vvv for single media
            ])
            
            # No additional HLS-specific parameters - the general buffering above is sufficient
            
            # Set image duration for images (only for local files, not streams)
            if not local_path.startswith(('http://', 'https://', 'rtmp://', 'rtmps://', 'rtsp://')):
                file_ext = os.path.splitext(local_path)[1].lower()
                if file_ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']:
                    command.extend(['--image-duration', '10'])
            
            # Add the media file
            command.append(local_path)
            
            self.logger.info(f"Starting optimized VLC for single media: {' '.join(command)}")
            
            # Start VLC with debug output
            log_file = os.path.join(MEDIA_DIR, 'vlc_single_debug.log')
            with open(log_file, 'w') as vlc_log:
                self.current_process = subprocess.Popen(
                    command,
                    stdout=vlc_log,
                    stderr=subprocess.STDOUT,
                    env=env
                )
            
            self.logger.info(f"Optimized single media VLC started - seamless looping with X11 auth fix!")
            
            # Keep VLC running and monitor it
            while self.running and self.current_process and self.current_process.poll() is None:
                time.sleep(5)  # Check every 5 seconds if VLC is still running
                # Rapid playlist update checks continue in background thread
            
            self.logger.info("Single media VLC process ended, will restart on next loop")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start optimized single media playback: {e}")
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

    def play_playlist(self):
        """Play current playlist"""
        if not self.current_playlist or not self.current_playlist.get('items'):
            self.logger.debug("No playlist or empty playlist")
            time.sleep(10)
            return
        
        items = self.current_playlist['items']
        
        # OPTIMIZATION: Single media files get direct VLC playback (more efficient)
        if len(items) == 1:
            self.logger.info(f"Single media detected: {items[0]['original_filename']} - using optimized direct playback")
            return self.play_single_media_optimized(items[0])
        
        # FIXED: Use continuous playlist for multi-item playlists to prevent VLC restarts
        self.logger.info(f"Multi-item playlist with {len(items)} items - creating continuous VLC playlist to prevent restarts")
        
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
        
        if success:
            # Keep VLC running continuously - no more stopping between videos!
            # VLC will handle all transitions internally without visual interruptions
            while self.running and self.current_process and self.current_process.poll() is None:
                time.sleep(5)  # Check every 5 seconds if VLC is still running
                # Playlist update checks will happen via background thread
            
            self.logger.info("VLC playlist process ended, restarting playback")
        else:
            self.send_log('error', "Failed to start continuous playlist playback")
            time.sleep(10)

    def cleanup_old_media(self):
        """Remove old media files to save space"""
        try:
            current_files = set()
            if self.current_playlist and self.current_playlist.get('items'):
                current_files = {item['filename'] for item in self.current_playlist['items']}
            
            for filename in os.listdir(MEDIA_DIR):
                if filename not in current_files:
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
                    self.fetch_playlist()
                    last_checkin = datetime.now()
                
                # Rapid checks now run in background thread, no longer needed here
                
                # Play current playlist
                self.play_playlist()
                
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
            
            elif command == 'update':
                self.logger.info("Starting client update as requested by admin")
                self.send_log('info', 'Starting client update as requested by admin')
                self.handle_update_command()
            
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
