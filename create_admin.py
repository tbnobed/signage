#!/usr/bin/env python3
"""
Secure admin user creation script for Digital Signage Management System
Run this script to create the initial admin user securely.

Usage:
    python create_admin.py                    # Interactive mode
    python create_admin.py admin admin@example.com mypassword123  # Direct mode
    python create_admin.py --help            # Show help
"""

import os
import sys
import getpass
from app import app, db
from models import User

def create_admin_user(username=None, email=None, password=None):
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
        
        # If credentials provided via command line
        if username and email and password:
            print(f"Creating admin user: {username}")
            print(f"Email: {email}")
            
            # Validate password strength
            if len(password) < 12:
                print("Error: Password must be at least 12 characters long.")
                return False
            
        else:
            # Interactive mode - check if we can read input
            try:
                # Get username
                while True:
                    if not username:
                        username = input("Enter admin username: ").strip()
                    if not username:
                        print("Username cannot be empty.")
                        username = None
                        continue
                    if len(username) < 3:
                        print("Username must be at least 3 characters long.")
                        username = None
                        continue
                    break
                
                # Get email
                while True:
                    if not email:
                        email = input("Enter admin email: ").strip()
                    if not email or '@' not in email:
                        print("Please enter a valid email address.")
                        email = None
                        continue
                    break
                
                # Get password securely
                while True:
                    if not password:
                        password = getpass.getpass("Enter admin password (min 12 characters): ")
                    if len(password) < 12:
                        print("Password must be at least 12 characters long.")
                        password = None
                        continue
                    
                    confirm_password = getpass.getpass("Confirm password: ")
                    if password != confirm_password:
                        print("Passwords do not match.")
                        password = None
                        continue
                    break
                    
            except (EOFError, KeyboardInterrupt):
                print("\nInteractive mode not available in this environment.")
                print("Usage: python create_admin.py <username> <email> <password>")
                print("Example: python create_admin.py admin admin@example.com mypassword123")
                return False
        
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
    
    # Check for command line arguments
    if len(sys.argv) == 4:
        # Direct mode: username email password
        username, email, password = sys.argv[1], sys.argv[2], sys.argv[3]
        success = create_admin_user(username, email, password)
    else:
        # Interactive mode
        success = create_admin_user()
    
    sys.exit(0 if success else 1)