#!/usr/bin/env python3
"""
Digital Signage Client Agent with TeamViewer ID Detection
Runs on Ubuntu desktop devices to display media content
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
        """Send heartbeat to server with TeamViewer ID"""
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

    def stop_current_media(self):
        """Stop any currently playing media"""
        if self.current_process:
            try:
                self.logger.info("Stopping current media...")
                self.current_process.terminate()
                self.current_process.wait(timeout=5)
                self.current_process = None
            except subprocess.TimeoutExpired:
                self.logger.warning("Process didn't terminate, killing it...")
                self.current_process.kill()
                self.current_process = None
            except Exception as e:
                self.logger.error(f"Error stopping media: {e}")

    def execute_command(self, command):
        """Execute command from server"""
        self.logger.info(f"Executing command: {command}")
        
        if command == 'reboot':
            self.logger.info("Rebooting system...")
            self.stop_current_media()
            subprocess.run(['sudo', 'reboot'], check=False)
            
        elif command == 'restart':
            self.logger.info("Restarting client...")
            self.stop_current_media()
            os.execv(sys.executable, ['python'] + sys.argv)
            
        elif command.startswith('log:'):
            log_message = command[4:]  # Remove 'log:' prefix
            self.send_log('command', log_message)

    def run(self):
        """Main client loop"""
        last_checkin = datetime.now() - timedelta(seconds=CHECK_INTERVAL)
        
        while self.running:
            try:
                # Regular check-in with server (includes TeamViewer ID)
                if (datetime.now() - last_checkin).seconds >= CHECK_INTERVAL:
                    self.logger.info("Performing regular check-in...")
                    self.send_checkin()
                    last_checkin = datetime.now()
                
                # Handle playlist playback
                if self.current_playlist and self.current_playlist.get('items'):
                    self.play_current_playlist()
                else:
                    time.sleep(5)  # No playlist, check again soon
                    
            except KeyboardInterrupt:
                self.logger.info("Shutting down...")
                self.running = False
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                time.sleep(10)

    def play_current_playlist(self):
        """Play the current playlist"""
        try:
            items = self.current_playlist.get('items', [])
            if not items:
                time.sleep(5)
                return
                
            # Single item - play with looping
            if len(items) == 1:
                media_item = items[0]
                media_path = self.download_media(media_item)
                
                if media_path:
                    # Start VLC with looping enabled
                    command = PLAYER_COMMANDS[self.media_player].copy()
                    command.append(media_path)
                    
                    self.stop_current_media()
                    
                    env = os.environ.copy()
                    env['DISPLAY'] = ':0'
                    
                    self.current_process = subprocess.Popen(
                        command,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        env=env
                    )
                    
                    # Wait indefinitely - let VLC loop
                    self.current_process.wait()
            else:
                # Multiple items - create playlist
                media_paths = []
                for item in items:
                    path = self.download_media(item)
                    if path:
                        media_paths.append(path)
                
                if media_paths:
                    self.play_continuous_playlist(media_paths)
                    
        except Exception as e:
            self.logger.error(f"Error playing playlist: {e}")
            time.sleep(5)

    def play_continuous_playlist(self, media_paths):
        """Play multiple media files continuously"""
        try:
            playlist_file = os.path.join(MEDIA_DIR, 'current_playlist.m3u')
            
            with open(playlist_file, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                for media_path in media_paths:
                    if media_path.startswith(('http://', 'https://', 'rtmp://', 'rtsp://')):
                        f.write(f'{media_path}\n')
                    else:
                        abs_path = os.path.abspath(media_path)
                        file_ext = os.path.splitext(media_path)[1].lower()
                        if file_ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']:
                            f.write(f'#EXTVLCOPT:image-duration=10\n')
                        f.write(f'{abs_path}\n')
            
            command = PLAYER_COMMANDS[self.media_player].copy()
            command.extend([
                '--loop',
                '--image-duration', '10',
                '--playlist-autostart',
                '--no-random',
                '--intf', 'dummy'
            ])
            command.append(playlist_file)
            
            self.stop_current_media()
            
            env = os.environ.copy()
            env['DISPLAY'] = ':0'
            
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
            
            self.current_process.wait()
            
        except Exception as e:
            self.logger.error(f"Error with continuous playlist: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal")
    sys.exit(0)

def main():
    # Handle shutdown signals
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        client = SignageClient()
        client.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        print("Client shutdown complete")

if __name__ == "__main__":
    main()