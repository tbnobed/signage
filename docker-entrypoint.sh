#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database to be ready..."
until pg_isready -h db -p 5432 -U signage_user -d signage_db > /dev/null 2>&1; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Database is ready!"

# Give PostgreSQL additional time to fully initialize for application connections
echo "Waiting for PostgreSQL to be fully ready for connections..."
sleep 5

# Test actual database connection before proceeding
echo "Testing database connection..."
export PGPASSWORD="${POSTGRES_PASSWORD:-signage_pass}"
max_retries=10
retry_count=0
until psql -h db -U signage_user -d signage_db -c "SELECT 1" > /dev/null 2>&1; do
    retry_count=$((retry_count + 1))
    if [ $retry_count -ge $max_retries ]; then
        echo "Failed to connect to database after $max_retries attempts"
        exit 1
    fi
    echo "Database connection test failed, retrying ($retry_count/$max_retries)..."
    sleep 2
done
unset PGPASSWORD

echo "Database connection verified!"

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
        check_query = text('''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'devices' AND column_name = 'pending_command'
        ''')
        result = db.session.execute(check_query).fetchone()
        
        if not result:
            print('Adding pending_command and command_timestamp columns...')
            alter_query = text('''
                ALTER TABLE devices 
                ADD COLUMN pending_command VARCHAR(50), 
                ADD COLUMN command_timestamp TIMESTAMP
            ''')
            db.session.execute(alter_query)
            db.session.commit()
            print('Reboot functionality migration completed successfully')
        else:
            print('Reboot functionality columns already exist')
            
    except Exception as e:
        print(f'Reboot schema check/migration info: {e}')
        # Not a critical error - might just mean tables don't exist yet
    
    # Add new columns for single media assignment functionality
    try:
        # Check if assigned_media_id column exists
        check_query = text('''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'devices' AND column_name = 'assigned_media_id'
        ''')
        result = db.session.execute(check_query).fetchone()
        
        if not result:
            print('Adding single media assignment columns...')
            alter_query = text('''
                ALTER TABLE devices 
                ADD COLUMN assigned_media_id INTEGER REFERENCES media_files(id),
                ADD COLUMN assignment_updated_at TIMESTAMP
            ''')
            db.session.execute(alter_query)
            db.session.commit()
            print('Single media assignment migration completed successfully')
        else:
            print('Single media assignment columns already exist')
            
    except Exception as e:
        print(f'Single media assignment schema check/migration info: {e}')
        # Not a critical error - might just mean tables don't exist yet
    
    # Add new columns for streaming media functionality
    try:
        # Check if is_stream column exists
        check_query = text('''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'media_files' AND column_name = 'is_stream'
        ''')
        result = db.session.execute(check_query).fetchone()
        
        if not result:
            print('Adding streaming media columns...')
            alter_query = text('''
                ALTER TABLE media_files 
                ADD COLUMN is_stream BOOLEAN DEFAULT FALSE,
                ADD COLUMN stream_url VARCHAR(500),
                ADD COLUMN stream_type VARCHAR(20),
                ALTER COLUMN filename DROP NOT NULL
            ''')
            db.session.execute(alter_query)
            db.session.commit()
            print('Streaming media migration completed successfully')
        else:
            print('Streaming media columns already exist')
            
    except Exception as e:
        print(f'Streaming media schema check/migration info: {e}')
        # Not a critical error - might just mean tables don't exist yet
    
    # Add TeamViewer ID column for remote management
    try:
        # Check if teamviewer_id column exists
        check_query = text('''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'devices' AND column_name = 'teamviewer_id'
        ''')
        result = db.session.execute(check_query).fetchone()
        
        if not result:
            print('Adding TeamViewer ID column...')
            alter_query = text('''
                ALTER TABLE devices 
                ADD COLUMN teamviewer_id VARCHAR(20)
            ''')
            db.session.execute(alter_query)
            db.session.commit()
            print('TeamViewer ID migration completed successfully')
        else:
            print('TeamViewer ID column already exists')
            
    except Exception as e:
        print(f'TeamViewer ID schema check/migration info: {e}')
        # Not a critical error - might just mean tables don't exist yet
    
    # Add client version column for auto-update functionality
    try:
        # Check if client_version column exists
        check_query = text('''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'devices' AND column_name = 'client_version'
        ''')
        result = db.session.execute(check_query).fetchone()
        
        if not result:
            print('Adding client version column...')
            alter_query = text('''
                ALTER TABLE devices 
                ADD COLUMN client_version VARCHAR(20)
            ''')
            db.session.execute(alter_query)
            db.session.commit()
            print('Client version migration completed successfully')
        else:
            print('Client version column already exists')
            
    except Exception as e:
        print(f'Client version schema check/migration info: {e}')
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