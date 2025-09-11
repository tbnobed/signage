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
        
        # Start background thread for regular check-ins (TeamViewer ID)
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        self.logger.info("Background heartbeat checking started")
        
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
        """Detect VLC media player for desktop Ubuntu"""
        try:
            subprocess.run(['vlc', '--version'], capture_output=True, timeout=5)
            self.logger.info("Found VLC media player")
            return 'vlc'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.logger.error("VLC media player not found! Please install VLC.")
            return None

    def get_teamviewer_id(self):
        """Get TeamViewer ID from the local system"""
        try:
            # Try to get TeamViewer ID using teamviewer --info command
            result = subprocess.run(['teamviewer', '--info'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse output to find TeamViewer ID line
                for line in result.stdout.split('\n'):
                    if 'TeamViewer ID:' in line:
                        teamviewer_id = line.split(':')[-1].strip()
                        if teamviewer_id and teamviewer_id.isdigit():
                            return teamviewer_id
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            # TeamViewer not installed or not accessible
            pass
        except Exception as e:
            self.logger.debug(f"TeamViewer ID detection error: {e}")
        
        return None
    
    def send_checkin(self):
        """Send heartbeat to server"""
        try:
            current_media = None
            if self.current_playlist and self.current_playlist.get('items'):
                items = self.current_playlist['items']
                if items and self.current_media_index < len(items):
                    current_media = items[self.current_media_index]['original_filename']
            
            # Get TeamViewer ID (cached to avoid frequent subprocess calls)
            if not hasattr(self, '_teamviewer_id_checked'):
                self._cached_teamviewer_id = self.get_teamviewer_id()
                self._teamviewer_id_checked = True
                if self._cached_teamviewer_id:
                    self.logger.info(f"Detected TeamViewer ID: {self._cached_teamviewer_id}")
            
            data = {
                'current_media': current_media,
                'timestamp': datetime.now().isoformat()
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
                '-v',                 # Less verbose than -vvv for single media
            ])
            
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
