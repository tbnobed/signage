#!/usr/bin/env python3
"""
Device registration script for Digital Signage Management System
Run this to register a new device in the database
"""

import sys
from app import app, db
from models import Device
from datetime import datetime

def register_device(device_id, device_name, location=None):
    """Register a new device"""
    with app.app_context():
        # Check if device already exists
        existing_device = Device.query.filter_by(device_id=device_id).first()
        if existing_device:
            print(f"Device {device_id} already registered")
            return
        
        # Create new device
        device = Device(
            name=device_name,
            device_id=device_id,
            location=location or "Unknown",
            status='offline',
            created_at=datetime.utcnow()
        )
        
        db.session.add(device)
        db.session.commit()
        
        print(f"Device {device_id} ({device_name}) registered successfully")
        print(f"Location: {location or 'Unknown'}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python register_device.py <device_id> <device_name> [location]")
        print("Example: python register_device.py t-zyw3 'Tustin Office Display' 'Tustin Office'")
        return
    
    device_id = sys.argv[1]
    device_name = sys.argv[2]
    location = sys.argv[3] if len(sys.argv) > 3 else None
    
    register_device(device_id, device_name, location)

if __name__ == "__main__":
    main()