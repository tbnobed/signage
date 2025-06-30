#!/usr/bin/env python3
"""
Secure admin user creation script for Digital Signage Management System
Run this script to create the initial admin user securely.
"""

import os
import sys
import getpass
from app import app, db
from models import User

def create_admin_user():
    """Create an admin user securely via command line"""
    
    with app.app_context():
        # Check if any users already exist
        if User.query.first():
            print("Error: Admin user already exists. Cannot create additional admin users via this script.")
            print("Use the web interface to manage users after initial setup.")
            return False
        
        print("=== Digital Signage Admin Setup ===")
        print("Creating the first administrator account...")
        print()
        
        # Get username
        while True:
            username = input("Enter admin username: ").strip()
            if not username:
                print("Username cannot be empty.")
                continue
            if len(username) < 3:
                print("Username must be at least 3 characters long.")
                continue
            break
        
        # Get email
        while True:
            email = input("Enter admin email: ").strip()
            if not email or '@' not in email:
                print("Please enter a valid email address.")
                continue
            break
        
        # Get password securely
        while True:
            password = getpass.getpass("Enter admin password (min 12 characters): ")
            if len(password) < 12:
                print("Password must be at least 12 characters long.")
                continue
            
            confirm_password = getpass.getpass("Confirm password: ")
            if password != confirm_password:
                print("Passwords do not match.")
                continue
            break
        
        try:
            # Create admin user
            admin_user = User(
                username=username,
                email=email,
                is_admin=True
            )
            admin_user.set_password(password)
            
            db.session.add(admin_user)
            db.session.commit()
            
            print()
            print("✓ Admin user created successfully!")
            print(f"  Username: {username}")
            print(f"  Email: {email}")
            print()
            print("You can now log in to the web interface using these credentials.")
            print("For security, this setup script is now disabled.")
            
            return True
            
        except Exception as e:
            print(f"Error creating admin user: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        sys.exit(0)
    
    success = create_admin_user()
    sys.exit(0 if success else 1)