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
from pathlib import Path
from datetime import datetime, timedelta
import signal
import threading

# Configuration
SERVER_URL = os.environ.get('SIGNAGE_SERVER_URL', 'http://localhost:5000')
DEVICE_ID = os.environ.get('DEVICE_ID', 'device-001')
CHECK_INTERVAL = int(os.environ.get('CHECK_INTERVAL', '60'))  # seconds
MEDIA_DIR = os.path.expanduser('~/signage_media')
LOG_FILE = os.path.expanduser('~/signage_agent.log')

# Media player commands
PLAYER_COMMANDS = {
    'omxplayer': ['omxplayer', '-o', 'hdmi', '--loop', '--no-osd'],
    'vlc': ['vlc', '--fullscreen', '--no-osd', '--loop', '--intf', 'dummy', '--no-video-title-show'],
    'ffplay': ['ffplay', '-fs', '-loop', '0', '-loglevel', 'quiet']
}

class SignageClient:
    def __init__(self):
        self.setup_logging()
        self.current_playlist = None
        self.current_process = None
        self.media_player = self.detect_media_player()
        self.running = True
        self.current_media_index = 0
        self.last_media_change = datetime.now()
        
        # Create media directory
        Path(MEDIA_DIR).mkdir(exist_ok=True)
        
        self.logger.info(f"Signage client started for device: {DEVICE_ID}")
        self.logger.info(f"Server URL: {SERVER_URL}")
        self.logger.info(f"Media player: {self.media_player}")

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def detect_media_player(self):
        """Detect available media player"""
        for player, command in PLAYER_COMMANDS.items():
            try:
                subprocess.run([command[0], '--version'], 
                             capture_output=True, timeout=5)
                self.logger.info(f"Found media player: {player}")
                return player
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        self.logger.error("No supported media player found!")
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
                self.logger.debug(f"Checkin successful: {result}")
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
                f"{SERVER_URL}/api/devices/{DEVICE_ID}/log",
                json=data,
                timeout=5
            )
        except Exception as e:
            self.logger.error(f"Failed to send log to server: {e}")

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
                
                if playlist != self.current_playlist:
                    self.logger.info(f"New playlist received: {playlist['name'] if playlist else 'None'}")
                    self.current_playlist = playlist
                    self.current_media_index = 0
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch playlist: {e}")
            
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

    def play_media(self, media_path, duration=None):
        """Play media file using available player"""
        if not self.media_player:
            self.logger.error("No media player available")
            return False
        
        try:
            command = PLAYER_COMMANDS[self.media_player].copy()
            command.append(media_path)
            
            self.logger.info(f"Playing: {os.path.basename(media_path)}")
            
            # Kill any existing player process
            self.stop_current_media()
            
            # Setup display environment for GUI applications
            env = os.environ.copy()
            env.update({
                'DISPLAY': ':0',
                'XAUTHORITY': '/home/obtv1/.Xauthority',
                'HOME': '/home/obtv1',
                'USER': 'obtv1'
            })
            
            # Start new player process with proper environment
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env
            )
            
            # Wait for specified duration or until process ends
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

    def stop_current_media(self):
        """Stop currently playing media"""
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
        if self.current_media_index >= len(items):
            if self.current_playlist.get('loop', True):
                self.current_media_index = 0
            else:
                self.logger.info("Playlist completed, not looping")
                time.sleep(10)
                return
        
        media_item = items[self.current_media_index]
        local_path = self.download_media(media_item)
        
        if local_path:
            duration = media_item.get('duration', self.current_playlist.get('default_duration', 10))
            success = self.play_media(local_path, duration)
            
            if success:
                self.current_media_index += 1
                self.last_media_change = datetime.now()
            else:
                self.send_log('error', f"Failed to play: {media_item['original_filename']}")
                self.current_media_index += 1  # Skip failed media
        else:
            self.send_log('error', f"Failed to download: {media_item['original_filename']}")
            self.current_media_index += 1  # Skip failed media

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
                # Send periodic checkin
                if datetime.now() - last_checkin >= timedelta(seconds=CHECK_INTERVAL):
                    self.send_checkin()
                    self.fetch_playlist()
                    last_checkin = datetime.now()
                
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


if __name__ == "__main__":
    client = SignageClient()
    
    try:
        client.run()
    except Exception as e:
        client.logger.error(f"Fatal error: {e}")
        sys.exit(1)
