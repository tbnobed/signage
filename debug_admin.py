#!/usr/bin/env python3
"""
Debug script to check admin user in database
Run this inside the container to verify what admin user exists
"""

from app import app, db
from models import User
import os

def main():
    with app.app_context():
        print("=== Admin User Debug ===")
        print()
        
        # Check environment variables
        print("Environment Variables:")
        print(f"ADMIN_USER: {os.environ.get('ADMIN_USER', 'NOT SET')}")
        print(f"ADMIN_EMAIL: {os.environ.get('ADMIN_EMAIL', 'NOT SET')}")
        print(f"ADMIN_PASSWORD: {'SET' if os.environ.get('ADMIN_PASSWORD') else 'NOT SET'}")
        print()
        
        # Check all users in database
        print("Users in Database:")
        users = User.query.all()
        if not users:
            print("No users found in database!")
        else:
            for user in users:
                print(f"  ID: {user.id}")
                print(f"  Username: {user.username}")
                print(f"  Email: {user.email}")
                print(f"  Is Admin: {user.is_admin}")
                print(f"  Password Hash: {user.password_hash[:20]}..." if user.password_hash else "No password hash!")
                print(f"  Created: {user.created_at}")
                print()
        
        # Test password verification
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            test_password = os.environ.get('ADMIN_PASSWORD', '')
            if test_password:
                password_works = admin_user.check_password(test_password)
                print(f"Password verification test: {'SUCCESS' if password_works else 'FAILED'}")
            else:
                print("No ADMIN_PASSWORD environment variable to test")
        else:
            print("No admin user found to test password")

if __name__ == "__main__":
    main()