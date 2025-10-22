#!/usr/bin/env python3
"""Generate DisplayHQ app icons in various sizes."""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size, output_path):
    """Create a DisplayHQ icon with monitor symbol."""
    # Create image with dark background
    img = Image.new('RGB', (size, size), '#0f1419')
    draw = ImageDraw.Draw(img)
    
    # Calculate sizes
    padding = size // 8
    monitor_width = size - (padding * 2)
    monitor_height = int(monitor_width * 0.6)
    
    # Center the monitor
    x1 = padding
    y1 = (size - monitor_height - padding) // 2
    x2 = x1 + monitor_width
    y2 = y1 + monitor_height
    
    # Draw monitor screen (cyan outline)
    screen_thickness = max(3, size // 60)
    draw.rectangle([x1, y1, x2, y2], outline='#00d9ff', width=screen_thickness)
    
    # Draw monitor stand
    stand_width = monitor_width // 4
    stand_height = size // 12
    stand_x1 = x1 + (monitor_width - stand_width) // 2
    stand_y1 = y2
    stand_x2 = stand_x1 + stand_width
    stand_y2 = stand_y1 + stand_height
    draw.rectangle([stand_x1, stand_y1, stand_x2, stand_y2], fill='#00d9ff')
    
    # Draw monitor base
    base_width = monitor_width // 2
    base_height = size // 20
    base_x1 = x1 + (monitor_width - base_width) // 2
    base_y1 = stand_y2
    base_x2 = base_x1 + base_width
    base_y2 = base_y1 + base_height
    draw.rectangle([base_x1, base_y1, base_x2, base_y2], fill='#00d9ff')
    
    # Add a small phone/tablet icon in the corner of the monitor
    if size >= 192:
        device_size = monitor_width // 5
        device_x = x2 - device_size - (size // 30)
        device_y = y1 + (size // 30)
        draw.rectangle(
            [device_x, device_y, device_x + device_size, device_y + int(device_size * 1.4)],
            outline='#00d9ff',
            width=max(2, size // 80)
        )
    
    img.save(output_path, 'PNG')
    print(f'Created {output_path}')

# Create icons directory
os.makedirs('static/icons', exist_ok=True)

# Generate icons in various sizes
create_icon(192, 'static/icons/icon-192.png')
create_icon(512, 'static/icons/icon-512.png')
create_icon(180, 'static/icons/apple-touch-icon.png')
create_icon(32, 'static/icons/favicon-32x32.png')
create_icon(16, 'static/icons/favicon-16x16.png')

print('All icons created successfully!')
