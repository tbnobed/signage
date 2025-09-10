#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h db -p 5432 -U signage_user -d signage_db; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Database is ready!"

# Ensure upload directories exist
echo "Setting up upload directories..."
mkdir -p /app/uploads /app/logs
# Note: Permissions handled by Docker volume mounts and user context

# Initialize database tables and handle schema updates
echo "Initializing database tables..."
python3 -c "
from app import app, db
from sqlalchemy import text
with app.app_context():
    # Create all tables (handles new deployments)
    db.create_all()
    print('Database tables created successfully')
    
    # Handle schema migration for existing deployments
    # Add new columns for reboot functionality if they don't exist
    try:
        # Check if pending_command column exists
        check_sql = '''SELECT column_name FROM information_schema.columns 
                       WHERE table_name=%s AND column_name=%s'''
        result = db.session.execute(text(check_sql), ('devices', 'pending_command')).fetchone()
        
        if not result:
            print('Adding pending_command and command_timestamp columns...')
            alter_sql = '''ALTER TABLE devices 
                          ADD COLUMN pending_command VARCHAR(50), 
                          ADD COLUMN command_timestamp TIMESTAMP'''
            db.session.execute(text(alter_sql))
            db.session.commit()
            print('Schema migration completed successfully')
        else:
            print('Schema is up to date')
            
    except Exception as e:
        print(f'Schema check/migration info: {e}')
        # Not a critical error - might just mean tables don't exist yet
"

# Check if we need to create an admin user
echo "Checking for admin user..."
python3 -c "
from app import app, db
from models import User
import os
import sys

with app.app_context():
    admin_exists = User.query.filter_by(is_admin=True).first()
    if not admin_exists:
        # Create default admin if environment variables are set
        admin_user = os.environ.get('ADMIN_USER', 'admin')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@signage.local')
        admin_pass = os.environ.get('ADMIN_PASSWORD')
        
        if admin_pass:
            user = User(
                username=admin_user,
                email=admin_email,
                is_admin=True
            )
            user.set_password(admin_pass)
            db.session.add(user)
            db.session.commit()
            print(f'Created admin user: {admin_user}')
        else:
            print('No admin user exists and no ADMIN_PASSWORD provided')
            print('You will need to create an admin user manually')
    else:
        print('Admin user already exists')
"

# Start the application
echo "Starting application..."
exec "$@"