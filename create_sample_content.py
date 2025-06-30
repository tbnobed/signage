#!/usr/bin/env python3
"""
Create sample content and playlist for testing
"""

from app import app, db
from models import MediaFile, Playlist, PlaylistItem, Device, User
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_image():
    """Create a sample test image"""
    # Create uploads directory if it doesn't exist
    os.makedirs('uploads', exist_ok=True)
    
    # Create a simple test image
    img = Image.new('RGB', (1920, 1080), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 120)
        font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 60)
    except:
        font = ImageFont.load_default()
        font_small = font
    
    # Draw text
    draw.text((960, 400), "Digital Signage", fill='#00d4ff', font=font, anchor='mm')
    draw.text((960, 520), "System Online", fill='#ffffff', font=font_small, anchor='mm')
    draw.text((960, 600), "Tustin Office", fill='#888888', font=font_small, anchor='mm')
    
    # Save image
    filename = 'sample_display.png'
    filepath = os.path.join('uploads', filename)
    img.save(filepath, 'PNG')
    
    return filename, filepath

def create_sample_content():
    """Create sample media file, playlist, and assign to device"""
    with app.app_context():
        # Get admin user (first user)
        admin = User.query.first()
        if not admin:
            print("No admin user found. Create admin first.")
            return
        
        # Create sample image
        filename, filepath = create_sample_image()
        file_size = os.path.getsize(filepath)
        
        # Create media file entry
        media_file = MediaFile(
            filename=filename,
            original_filename='Sample Display Image',
            file_type='image',
            file_size=file_size,
            uploaded_by=admin.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(media_file)
        db.session.flush()  # Get the ID
        
        # Create playlist
        playlist = Playlist(
            name='Default Display Playlist',
            description='Sample playlist for Tustin office display',
            is_active=True,
            loop_playlist=True,
            default_duration=10,  # 10 seconds per image
            created_by=admin.id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(playlist)
        db.session.flush()  # Get the ID
        
        # Create playlist item
        playlist_item = PlaylistItem(
            playlist_id=playlist.id,
            media_file_id=media_file.id,
            order_index=0,
            duration=10
        )
        
        db.session.add(playlist_item)
        
        # Assign playlist to device
        device = Device.query.filter_by(device_id='t-zyw3').first()
        if device:
            device.current_playlist_id = playlist.id
            print(f"Assigned playlist '{playlist.name}' to device '{device.name}'")
        else:
            print("Device t-zyw3 not found")
        
        db.session.commit()
        
        print(f"Created sample content:")
        print(f"- Media file: {filename} ({file_size} bytes)")
        print(f"- Playlist: {playlist.name}")
        print(f"- Device: {device.name if device else 'Not found'}")

if __name__ == "__main__":
    create_sample_content()